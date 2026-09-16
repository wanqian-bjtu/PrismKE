"""FastAPI adapter for the shared PrismKE application service."""

from __future__ import annotations

import hmac
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal, cast
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
from filelock import Timeout

from prismke import __version__
from prismke.api.models import (
    EntityReviewRequest,
    MergeProposalRequest,
    ReviewRequest,
    RollbackRequest,
    RunAccepted,
    SplitProposalRequest,
    ValidationExcludeRequest,
)
from prismke.core.errors import (
    GraphIntegrityError,
    LegacyCheckpointError,
    ProviderConfigurationError,
)
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

    app = FastAPI(title="PrismKE API", version=__version__, lifespan=lifespan)
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
        if service.review_metadata:
            raise HTTPException(status_code=409, detail="review workspace forbids extraction")
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

    @api.get("/runs")
    async def list_runs() -> object:
        return [
            {**service.review_progress(item.run_id), "filename": Path(item.input_path).name}
            for item in service.runs.list(limit=1000)
        ]

    @api.get("/runs/{run_id}/review-progress")
    async def review_progress(run_id: str) -> object:
        try:
            return service.review_progress(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc

    @api.get("/runs/{run_id}/entity-reviews/{task_id}")
    async def entity_review_detail(run_id: str, task_id: str) -> object:
        try:
            return await service.entity_review_detail(run_id, task_id)
        except (KeyError, FileNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="entity review task not found") from exc

    @api.get("/runs/{run_id}/reviews/{task_id}")
    async def claim_review_detail(run_id: str, task_id: str) -> object:
        try:
            return service.claim_review_detail(run_id, task_id)
        except (KeyError, FileNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="claim review task not found") from exc

    @api.post("/runs/{run_id}/confirm-commit")
    async def confirm_commit(
        run_id: str, request: RollbackRequest, reviewer: str = Query(min_length=1)
    ) -> object:
        try:
            return await service.confirm_review_commit(run_id, reviewer)
        except (ValueError, GraphIntegrityError, Timeout) as exc:
            raise HTTPException(
                status_code=409, detail="submission unavailable or graph changed"
            ) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc

    @api.get("/runs/{run_id}")
    async def get_run(run_id: str) -> object:
        try:
            return service.show_run(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc

    @api.get("/runs/{run_id}/validation")
    async def run_validation(run_id: str) -> object:
        try:
            return await service.validate_run(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api.post("/runs/{run_id}/validation-issues/{issue_id}/exclude")
    async def exclude_validation(
        run_id: str, issue_id: str, request: ValidationExcludeRequest
    ) -> object:
        try:
            return await service.exclude_validation_issue(
                run_id, issue_id, request.reviewer, request.comment
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc
        except (ValueError, LegacyCheckpointError, Timeout) as exc:
            raise HTTPException(
                status_code=409, detail="校验问题已处理、过期或当前不可排除"
            ) from exc

    @api.post("/runs/{run_id}/resume", status_code=202)
    async def resume_run(run_id: str, background_tasks: BackgroundTasks) -> RunAccepted:
        try:
            state = service.show_run(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="run not found") from exc

        if not service.review_progress(run_id)["can_resume"]:
            raise HTTPException(
                status_code=409,
                detail="resolve pending reviews or confirm preview first",
            )

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
            return await service.review(
                state.run_id,
                claim_id,
                request.decision,
                request.reviewer,
                request.comment,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (ValueError, LegacyCheckpointError, ProviderConfigurationError, Timeout) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api.get("/entities/search")
    async def search_entities(
        q: str = Query(min_length=1),
        entity_type: str = Query(min_length=1),
        limit: int = Query(default=10, ge=1, le=100),
    ) -> object:
        return await service.search_entities(q, entity_type, limit)

    @api.get("/entity-reviews")
    async def list_entity_reviews(
        review_status: str | None = Query(default=None, alias="status"),
    ) -> object:
        if review_status not in {None, "pending", "resolved"}:
            raise HTTPException(status_code=422, detail="invalid entity review status")
        return service.list_entity_reviews(review_status)

    @api.post("/entity-reviews/{task_id}")
    async def submit_entity_review(task_id: str, request: EntityReviewRequest) -> object:
        try:
            if request.action in {"approve", "reject"} and request.run_id is None:
                return await service.review_entity_operation(
                    task_id,
                    approve=request.action == "approve",
                    reviewer=request.reviewer,
                )
            if request.run_id is None or request.action not in {"link", "create", "reject"}:
                raise HTTPException(
                    status_code=422,
                    detail="run_id and link/create/reject required",
                )
            return await service.review_entity(
                request.run_id,
                task_id,
                cast(Literal["link", "create", "reject"], request.action),
                request.selected_entity_id,
                request.reviewer,
                request.comment,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (
            ValueError,
            GraphIntegrityError,
            ProviderConfigurationError,
            LegacyCheckpointError,
            Timeout,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api.post("/entities/merge-proposals", status_code=202)
    async def propose_entity_merge(request: MergeProposalRequest) -> object:
        try:
            return await service.propose_entity_merge(
                request.source_entity_ids, request.target_entity_id, request.reasons
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @api.post("/entities/{entity_id}/split-proposals", status_code=202)
    async def propose_entity_split(entity_id: str, request: SplitProposalRequest) -> object:
        try:
            return await service.propose_entity_split(
                entity_id,
                request.target_entities,
                request.claim_assignments,
                request.reasons,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @api.get("/entities/{entity_id}/history")
    async def get_entity_history(entity_id: str) -> object:
        if await service.graph_store.get_entity(entity_id) is None:
            raise HTTPException(status_code=404, detail="entity not found")
        return await service.entity_history(entity_id)

    @api.get("/entities/{entity_id}/neighborhood")
    async def get_neighborhood(entity_id: str, depth: int = Query(default=1, ge=1, le=3)) -> object:
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
        service.audit.record("rollback", revision_id, {"compensation_revision_id": revision.id})
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
