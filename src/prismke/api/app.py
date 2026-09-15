"""FastAPI adapter for the shared PrismKE application service."""

from __future__ import annotations

import hmac
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import Response

from prismke.api.models import ReviewRequest, RollbackRequest, RunAccepted
from prismke.core.errors import GraphIntegrityError, LegacyCheckpointError
from prismke.core.settings import Settings
from prismke.workflow import PrismKEService

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
MAX_UPLOAD_BYTES = 64 * 1024 * 1024


def _safe_suffix(filename: str | None) -> str:
    suffix = Path(filename or "upload.bin").suffix.lower()
    return suffix if suffix and len(suffix) <= 12 else ".bin"


async def _save_upload(upload: UploadFile, directory: Path) -> Path:
    content = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="upload exceeds 64 MiB")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid4().hex}{_safe_suffix(upload.filename)}"
    path.write_bytes(content)
    return path


def create_app(
    settings: Settings | None = None,
    service: PrismKEService | None = None,
    *,
    mount_ui: bool = True,
) -> FastAPI:
    settings = settings or Settings()
    if settings.api_host not in LOOPBACK_HOSTS and not settings.api_token:
        raise ValueError("PRISMKE_API_TOKEN is required for non-loopback API binding")
    service = service or PrismKEService(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await service.close()

    app = FastAPI(title="PrismKE API", version="0.3.0", lifespan=lifespan)
    app.state.prismke_service = service

    async def authorize(authorization: str | None = Header(default=None)) -> None:
        if not settings.api_token:
            return
        expected = f"Bearer {settings.api_token}"
        if authorization is None or not hmac.compare_digest(authorization, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid API token",
            )

    api = APIRouter(prefix="/api/v1", dependencies=[Depends(authorize)])

    async def execute_safely(run_id: str) -> None:
        try:
            await service.execute_run(run_id)
        except Exception:
            # The workflow records a sanitized failure in RunRepository.
            return

    @api.post("/runs", response_model=RunAccepted, status_code=202)
    async def create_run(
        background_tasks: BackgroundTasks,
        document: Annotated[UploadFile, File()],
        schema_file: Annotated[UploadFile, File(alias="schema")],
        provider: Annotated[str, Form()] = "mock",
        ocr_provider: Annotated[str, Form()] = "disabled",
        vlm_provider: Annotated[str, Form()] = "disabled",
        allow_remote_assets: Annotated[bool, Form()] = False,
    ) -> RunAccepted:
        document_path = await _save_upload(document, settings.uploads_dir / "documents")
        schema_path = await _save_upload(schema_file, settings.uploads_dir / "schemas")
        state, created = service.create_run(
            document_path,
            schema_path,
            provider,
            ocr_provider,
            vlm_provider,
            allow_remote_assets,
        )
        if created:
            background_tasks.add_task(execute_safely, state.run_id)
        return RunAccepted(run_id=state.run_id, status=state.status, created=created)

    @api.get("/runs/{run_id}")
    async def get_run(run_id: str) -> object:
        try:
            return service.show_run(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc

    @api.post("/runs/{run_id}/resume", status_code=202)
    async def resume_run(run_id: str, background_tasks: BackgroundTasks) -> RunAccepted:
        try:
            state = service.show_run(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc

        async def resume_safely() -> None:
            try:
                await service.resume(run_id)
            except Exception:
                return

        background_tasks.add_task(resume_safely)
        return RunAccepted(run_id=run_id, status=state.status, created=False)

    @api.get("/runs/{run_id}/claims")
    async def get_run_claims(run_id: str) -> object:
        try:
            return service.show_run(run_id).claims
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc

    @api.get("/evidence/{evidence_id}")
    async def get_evidence(evidence_id: str) -> object:
        try:
            return await service.evidence_store.get(evidence_id)
        except Exception as exc:
            graph_evidence = await service.graph_store.get_evidence(evidence_id)
            if graph_evidence is None:
                raise HTTPException(status_code=404, detail="evidence not found") from exc
            return graph_evidence

    @api.get("/evidence/{evidence_id}/content")
    async def get_evidence_content(evidence_id: str) -> Response:
        try:
            content = await service.evidence_store.crop(evidence_id)
        except Exception as exc:
            raise HTTPException(status_code=404, detail="evidence content not found") from exc
        return Response(content=content, media_type="application/octet-stream")

    @api.post("/reviews/{task_id}")
    async def submit_review(task_id: str, request: ReviewRequest) -> object:
        try:
            state, claim_id = service.runs.find_review(task_id)
            return await service.review(state.run_id, claim_id, request.decision)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except LegacyCheckpointError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api.get("/entities/{entity_id}/neighborhood")
    async def get_neighborhood(
        entity_id: str, depth: int = Query(default=1, ge=1, le=3)
    ) -> object:
        try:
            return await service.graph_store.get_neighborhood(entity_id, depth)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api.get("/revisions")
    async def list_revisions(limit: int = Query(default=50, ge=1, le=500)) -> object:
        return await service.graph_store.list_revisions(limit)

    @api.get("/revisions/diff")
    async def diff_revisions(
        from_id: str = Query(alias="from"), to_id: str = Query(alias="to")
    ) -> object:
        try:
            return await service.graph_store.diff_revisions(from_id, to_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @api.post("/revisions/{revision_id}/rollback")
    async def rollback_revision(revision_id: str, _: RollbackRequest) -> object:
        try:
            revision = await service.graph_store.rollback_revision(revision_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except GraphIntegrityError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        service.audit.record(
            "rollback", revision_id, {"compensation_revision_id": revision.id}
        )
        return revision

    @api.get("/health")
    async def health() -> object:
        graph = await service.graph_store.healthcheck()
        return {"status": "ok" if graph.healthy else "degraded", "graph": graph}

    app.include_router(api)
    if mount_ui:
        try:
            from prismke.web.app import mount_gradio
        except ImportError:
            pass
        else:
            app = mount_gradio(app, service)
    return app
