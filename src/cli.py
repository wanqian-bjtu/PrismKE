"""PrismKE command-line interface."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

import orjson
import typer
from pydantic import BaseModel
from rich.console import Console

from src import __version__
from src.core.errors import ProviderConfigurationError
from src.core.settings import Settings
from src.domain import (
    BatchResult,
    BatchRun,
    EntitySourceMode,
    PDFParseMode,
    ProvidedEntity,
    ReviewDecision,
    TaskMode,
    load_schema,
)
from src.evaluation import (
    EntityLinkingEvaluationReport,
    evaluate_entity_linking_manifest,
    evaluate_manifest,
    evaluate_reflection_manifest,
)
from src.evaluation.annotations import export_reviewed_annotations
from src.evaluation.component_ablation_cli import app as component_ablation_app
from src.evaluation.mnre_v2_cli import app as mnre_v2_app
from src.evaluation.twitter2017_cli import app as twitter2017_app
from src.governance import rebuild_entity_index
from src.persistence import FileEvidenceStore, Neo4jGraphStore, migrate_json_graph
from src.persistence.legacy_evidence import (
    closure_commit,
    existing_maintenance,
    legacy_snapshot,
    read_manifest,
    require_isolated_database,
    restore_sample_evidence,
    verify_active_claims,
)
from src.providers import BGEM3EmbeddingProvider, MockEmbeddingProvider
from src.providers.base import EmbeddingProvider
from src.workflow import PrismKEService

app = typer.Typer(no_args_is_help=True, help="PrismKE knowledge construction CLI")
app.add_typer(twitter2017_app, name="twitter2017")
app.add_typer(mnre_v2_app, name="mnre-v2")
app.add_typer(component_ablation_app, name="component-ablation")
console = Console()


@app.command("version")
def version() -> None:
    """Show the software version (independent of checkpoint protocol)."""
    console.print(__version__)


def _print_model(model: object) -> None:
    if isinstance(model, BaseModel):
        model = model.model_dump(mode="json")
    console.print_json(orjson.dumps(model).decode())


@app.command("validate-schema")
def validate_schema(
    schema: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
) -> None:
    """Validate and summarize a YAML or JSON schema."""
    parsed = load_schema(schema)
    console.print(
        f"valid schema: {parsed.schema_id}@{parsed.version} "
        f"({len(parsed.entity_types)} entity types, {len(parsed.relations)} relations)"
    )


@app.command("validate-run")
def validate_run(run_id: str) -> None:
    """Read-only validation of a stored run; exit 1 when blocking issues remain."""
    service = PrismKEService()

    async def execute() -> object:
        try:
            return await service.validate_run(run_id)
        finally:
            await service.close()

    result = asyncio.run(execute())
    _print_model(result)
    if getattr(result, "blocking_count", 0):
        raise typer.Exit(1)


@app.command("repair-legacy-evidence")
def repair_legacy_evidence(
    source_evidence: Annotated[
        Path, typer.Option("--source-evidence", exists=True, file_okay=False)
    ],
    target_evidence: Annotated[Path, typer.Option("--target-evidence", file_okay=False)],
    expected_data_dir: Annotated[
        Path, typer.Option("--expected-data-dir", exists=True, file_okay=False)
    ],
    manifest: Annotated[
        Path | None, typer.Option("--manifest", exists=True, dir_okay=False)
    ] = None,
    apply: Annotated[bool, typer.Option("--apply")] = False,
) -> None:
    """Preview or apply the audited legacy-test closure on an isolated Neo4j clone."""
    settings = Settings()
    canary_root = (Path.cwd() / "runtime/canary-v092").resolve()
    if (
        settings.neo4j_uri != "bolt://127.0.0.1:17687"
        or not expected_data_dir.resolve().is_relative_to(canary_root)
        or not target_evidence.resolve().is_relative_to(canary_root)
        or source_evidence.resolve() == target_evidence.resolve()
        or (apply and manifest is None)
    ):
        raise typer.BadParameter("legacy repair requires the dedicated v0.9.2 clone and a manifest")
    password = settings.neo4j_password
    if password is None:
        raise typer.BadParameter("Neo4j password is not configured")

    async def execute() -> dict[str, object]:
        source = FileEvidenceStore(source_evidence)
        store = Neo4jGraphStore(
            settings.neo4j_uri,
            settings.neo4j_user,
            password,
            settings.neo4j_database,
        )
        try:
            await require_isolated_database(store, expected_data_dir)
            previous = await existing_maintenance(store)
            if previous is not None:
                if not apply or manifest is None:
                    raise ValueError(
                        "maintenance already applied; use the original manifest to verify"
                    )
                pinned = read_manifest(manifest)
                expected_ids = [item["id"] for item in pinned["governance"]]
                claims = {claim.id: claim for claim in await store.list_claims()}
                if (
                    previous.parent_id != pinned["parent_id"]
                    or sorted(previous.claim_ids) != sorted(expected_ids)
                    or any(claims[claim_id].tx_to is None for claim_id in expected_ids)
                ):
                    raise ValueError("existing maintenance revision does not match the manifest")
                target = FileEvidenceStore(target_evidence)
                return {
                    "status": "already_applied",
                    "active_claims": await verify_active_claims(store, target),
                }

            snapshot = await legacy_snapshot(store, source)
            if not apply:
                return snapshot
            assert manifest is not None
            if read_manifest(manifest) != snapshot:
                raise ValueError("manifest differs from the latest graph snapshot")
            target = FileEvidenceStore(target_evidence)
            await restore_sample_evidence(store, source, target)
            excluded = {item["id"] for item in snapshot["governance"]}
            await verify_active_claims(store, target, exclude_ids=excluded)
            transaction = closure_commit(snapshot, await store.list_claims())
            store.evidence_store = target
            await store.commit(transaction)
            return {
                "status": "applied",
                "revision_id": transaction.revision.id,
                "closed_claims": len(transaction.claims),
                "active_claims": await verify_active_claims(store, target),
            }
        finally:
            await store.close()

    _print_model(asyncio.run(execute()))


@app.command()
def run(
    input_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    schema: Annotated[Path, typer.Option("--schema", exists=True, dir_okay=False)],
    provider: Annotated[str, typer.Option("--provider")] = "mock",
    ocr_provider: Annotated[str, typer.Option("--ocr-provider")] = "disabled",
    vlm_provider: Annotated[str, typer.Option("--vlm-provider")] = "disabled",
    allow_remote_assets: Annotated[bool, typer.Option("--allow-remote-assets")] = False,
    case_mode: Annotated[Literal["none", "good", "good_bad"], typer.Option("--cases")] = "none",
    reflection: Annotated[bool, typer.Option("--reflection/--no-reflection")] = False,
    reflection_provider: Annotated[str, typer.Option("--reflection-provider")] = "disabled",
    reflection_max_attempts: Annotated[int, typer.Option("--reflection-max-attempts")] = 2,
    reflection_token_budget: Annotated[int, typer.Option("--reflection-token-budget")] = 20_000,
    reflection_time_budget: Annotated[int, typer.Option("--reflection-time-budget")] = 180,
    semantic_advisor: Annotated[str, typer.Option("--semantic-advisor")] = "disabled",
    agent_token_budget: Annotated[int, typer.Option("--agent-token-budget")] = 20_000,
    task_mode: Annotated[TaskMode, typer.Option("--task-mode")] = (
        TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION
    ),
    entity_source_mode: Annotated[EntitySourceMode, typer.Option("--entity-source")] = (
        EntitySourceMode.AUTO
    ),
    entities: Annotated[
        Path | None, typer.Option("--entities", exists=True, dir_okay=False)
    ] = None,
    output: Annotated[Path | None, typer.Option("--output", dir_okay=False)] = None,
    pdf_parser: Annotated[PDFParseMode, typer.Option("--pdf-parser")] = PDFParseMode.AUTO,
) -> None:
    """Run one document in the selected extraction or construction mode."""
    provided = (
        [ProvidedEntity.model_validate(item) for item in orjson.loads(entities.read_bytes())]
        if entities
        else []
    )
    state = asyncio.run(
        PrismKEService().run(
            input_path,
            schema,
            provider,
            ocr_provider,
            vlm_provider,
            allow_remote_assets,
            case_mode,
            reflection,
            reflection_provider,
            reflection_max_attempts,
            reflection_token_budget,
            reflection_time_budget,
            semantic_advisor,
            agent_token_budget,
            task_mode=task_mode,
            entity_source_mode=entity_source_mode,
            provided_entities=provided,
            pdf_parse_mode=pdf_parser,
        )
    )
    console.print(f"run_id={state.run_id} status={state.status}")
    result: object = state.extraction_result or state
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = result.model_dump(mode="json") if isinstance(result, BaseModel) else result
        output.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        console.print(f"result={output.resolve()}")
    else:
        _print_model(result)


@app.command("run-batch")
def run_batch(
    documents: Annotated[list[Path], typer.Argument(exists=True, dir_okay=False)],
    schema: Annotated[Path, typer.Option("--schema", exists=True, dir_okay=False)],
    task_mode: Annotated[TaskMode, typer.Option("--task-mode")] = (
        TaskMode.KNOWLEDGE_GRAPH_CONSTRUCTION
    ),
    provider: Annotated[str, typer.Option("--provider")] = "mock",
    ocr_provider: Annotated[str, typer.Option("--ocr-provider")] = "disabled",
    vlm_provider: Annotated[str, typer.Option("--vlm-provider")] = "disabled",
    entity_source_mode: Annotated[EntitySourceMode, typer.Option("--entity-source")] = (
        EntitySourceMode.AUTO
    ),
    entities: Annotated[
        Path | None, typer.Option("--entities", exists=True, dir_okay=False)
    ] = None,
    operator: Annotated[str, typer.Option("--operator")] = "CLI",
    output: Annotated[Path | None, typer.Option("--output", dir_okay=False)] = None,
    pdf_parser: Annotated[PDFParseMode, typer.Option("--pdf-parser")] = PDFParseMode.AUTO,
) -> None:
    """Run a bounded multi-document batch and export per-file results."""
    provided = (
        [ProvidedEntity.model_validate(item) for item in orjson.loads(entities.read_bytes())]
        if entities
        else []
    )
    service = PrismKEService()

    async def execute() -> tuple[BatchRun, list[BatchResult]]:
        try:
            batch, _ = service.create_batch(
                documents,
                schema,
                task_mode=task_mode,
                entity_source_mode=entity_source_mode,
                provided_entities=provided,
                provider_name=provider,
                ocr_provider_name=ocr_provider,
                vlm_provider_name=vlm_provider,
                operator=operator,
                pdf_parse_mode=pdf_parser,
            )
            for run_id in dict.fromkeys(item.run_id for item in batch.items if item.run_id):
                state = service.show_run(run_id)
                if state.status not in {
                    "completed",
                    "awaiting_review",
                    "failed",
                    "parser_blocked",
                }:
                    await service.execute_run(run_id)
            batch = service.refresh_batch(batch.id)
            return batch, service.batch_results(batch.id)
        finally:
            await service.close()

    batch, results = asyncio.run(execute())
    payload = {
        "batch": batch.model_dump(mode="json"),
        "results": [item.model_dump(mode="json") for item in results],
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        console.print(f"result={output.resolve()}")
    else:
        _print_model(payload)


@app.command("show-run")
def show_run(run_id: str) -> None:
    """Print the latest serialized state of a run."""
    _print_model(PrismKEService().show_run(run_id))


@app.command("pdf-parser-fallback")
def pdf_parser_fallback(
    run_id: str,
    operator: Annotated[str, typer.Option("--operator")],
    reason: Annotated[str, typer.Option("--reason")],
    expected_version: Annotated[int | None, typer.Option("--expected-version")] = None,
    request_id: Annotated[str | None, typer.Option("--request-id")] = None,
) -> None:
    """Confirm an audited PyMuPDF retry for an auto-routed blocked PDF."""
    service = PrismKEService()
    version = (
        expected_version
        if expected_version is not None
        else int(service.executions.view(run_id)["version"])
    )
    _print_model(
        service.approve_pdf_parser_fallback(
            run_id,
            operator,
            reason,
            request_id or uuid4().hex,
            version,
        )
    )


@app.command("agent-traces")
def agent_traces(run_id: str) -> None:
    """Show the sanitized, idempotent decisions of the three agents."""
    _print_model(PrismKEService().show_run(run_id).agent_traces)


@app.command("list-media")
def list_media_command(
    document_id: Annotated[str | None, typer.Option("--document-id")] = None,
    media_type: Annotated[str | None, typer.Option("--media-type")] = None,
) -> None:
    """List active media occurrences without exposing blobs or server paths."""

    async def execute() -> object:
        service = PrismKEService()
        try:
            contents = {
                item.id: item for item in await service.graph_store.list_media_contents()
            }
            return [
                {
                    "occurrence": item.model_dump(mode="json"),
                    "content": contents[item.media_content_id].model_dump(mode="json"),
                }
                for item in await service.graph_store.list_media_occurrences()
                if item.active
                and (document_id is None or item.document_id == document_id)
                and (
                    media_type is None
                    or contents[item.media_content_id].asset_type.value == media_type
                )
            ]
        finally:
            await service.close()

    _print_model(asyncio.run(execute()))


@app.command("show-media")
def show_media_command(occurrence_id: str) -> None:
    """Show one media occurrence, its immutable content and graph assertions."""

    async def execute() -> object:
        service = PrismKEService()
        try:
            occurrence = await service.graph_store.get_media_occurrence(occurrence_id)
            if occurrence is None:
                raise typer.BadParameter(f"media occurrence not found: {occurrence_id}")
            content = next(
                (
                    item
                    for item in await service.graph_store.list_media_contents()
                    if item.id == occurrence.media_content_id
                ),
                None,
            )
            return {
                "occurrence": occurrence.model_dump(mode="json"),
                "content": content.model_dump(mode="json") if content else None,
                "relations": [
                    item.model_dump(mode="json")
                    for item in await service.graph_store.list_media_relations()
                    if item.occurrence_id == occurrence_id
                ],
                "visual_assertions": [
                    item.model_dump(mode="json")
                    for item in await service.graph_store.list_visual_assertions()
                    if item.occurrence_id == occurrence_id
                ],
            }
        finally:
            await service.close()

    _print_model(asyncio.run(execute()))


@app.command("list-visual-reviews")
def list_visual_reviews_command(run_id: str) -> None:
    """List versioned visual review tasks and decisions for one run."""
    state = PrismKEService().show_run(run_id)
    _print_model(
        {
            "tasks": [item.model_dump(mode="json") for item in state.visual_review_tasks],
            "events": [item.model_dump(mode="json") for item in state.visual_review_events],
        }
    )


@app.command("review-visual")
def review_visual_command(
    run_id: str,
    task_id: str,
    decision: Annotated[Literal["approve", "reject", "defer"], typer.Option("--decision")],
    reviewer: Annotated[str, typer.Option("--reviewer")],
    reason: Annotated[str, typer.Option("--reason")],
    expected_version: Annotated[int, typer.Option("--expected-version", min=0)],
    request_id: Annotated[str | None, typer.Option("--request-id")] = None,
) -> None:
    """Record one idempotent visual decision with optimistic version checking."""
    _print_model(
        asyncio.run(
            PrismKEService().review_visual(
                run_id,
                task_id,
                decision,
                reviewer,
                reason,
                request_id or uuid4().hex,
                expected_version,
            )
        )
    )


@app.command("list-cases")
def list_cases_command(
    case_type: Annotated[str | None, typer.Option("--type")] = None,
    task_type: Annotated[str | None, typer.Option("--task-type")] = None,
    language: Annotated[str | None, typer.Option("--language")] = None,
    include_disabled: Annotated[bool, typer.Option("--include-disabled")] = False,
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 200,
) -> None:
    """List immutable review cases without exposing embedding vectors."""
    _print_model(
        PrismKEService().list_cases(
            case_type=case_type,
            task_type=task_type,
            language=language,
            active_only=not include_disabled,
            limit=limit,
        )
    )


@app.command("disable-case")
def disable_case_command(
    case_id: str,
    operator: Annotated[str, typer.Option("--operator")],
    reason: Annotated[str, typer.Option("--reason")],
) -> None:
    """Append a disabling event; the historical case remains immutable."""
    _print_model(
        PrismKEService().disable_case(
            case_id,
            operator=operator,
            reason=reason,
            request_id=uuid4().hex,
        )
    )


@app.command("rebuild-case-index")
def rebuild_case_index_command(
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Rebuild missing or stale case embeddings."""
    service = PrismKEService()

    async def execute() -> object:
        try:
            return await service.rebuild_case_index(dry_run=dry_run)
        finally:
            await service.close()

    _print_model(asyncio.run(execute()))


@app.command("execution-status")
def execution_status(run_id: str) -> None:
    """Read durable task status without starting a worker."""
    _print_model(PrismKEService().executions.view(run_id))


@app.command("cancel")
def cancel_execution(
    run_id: str,
    operator: Annotated[str, typer.Option("--operator")],
    reason: Annotated[str, typer.Option("--reason")],
) -> None:
    """Persist a cooperative cancellation without taking worker ownership."""
    service = PrismKEService()
    view = service.executions.view(run_id)
    _print_model(service.executions.cancel(run_id, operator, reason, uuid4().hex, view["version"]))


@app.command()
def review(
    run_id: str,
    claim_id: Annotated[str, typer.Option("--claim-id")],
    decision: Annotated[ReviewDecision, typer.Option("--decision")],
    reviewer: Annotated[str | None, typer.Option("--reviewer")] = None,
    comment: Annotated[str | None, typer.Option("--comment")] = None,
) -> None:
    """Record a human decision for one claim."""
    state = asyncio.run(PrismKEService().review(run_id, claim_id, decision, reviewer, comment))
    console.print(f"review recorded: run_id={state.run_id} claim_id={claim_id}")


@app.command("review-entity")
def review_entity_command(
    run_id: str,
    task_id: Annotated[str, typer.Option("--task-id")],
    action: Annotated[str, typer.Option("--action")],
    reviewer: Annotated[str, typer.Option("--reviewer")],
    selected_entity_id: Annotated[str | None, typer.Option("--selected-entity-id")] = None,
    comment: Annotated[str | None, typer.Option("--comment")] = None,
) -> None:
    """Record a single entity decision; real tasks have no bulk approval command."""
    from typing import Literal, cast

    if action not in {"link", "create", "reject"}:
        raise typer.BadParameter("--action must be link/create/reject")
    _print_model(
        asyncio.run(
            PrismKEService().review_entity(
                run_id,
                task_id,
                cast(Literal["link", "create", "reject"], action),
                selected_entity_id,
                reviewer,
                comment,
            )
        )
    )


@app.command("review-progress")
def review_progress_command(run_id: str) -> None:
    """Inspect pending tasks and the isolated graph submission summary."""
    _print_model(PrismKEService().review_progress(run_id))


@app.command()
def resume(run_id: str) -> None:
    """Resume a failed or reviewed run from its latest SQLite snapshot."""
    state = asyncio.run(PrismKEService().resume(run_id))
    console.print(f"run_id={state.run_id} status={state.status}")
    _print_model(state)


@app.command("import-review-run")
def import_review_run_command(
    source: Annotated[Path, typer.Option("--source", exists=True, file_okay=False)],
    run_id: Annotated[str, typer.Option("--run-id")],
    target: Annotated[Path, typer.Option("--target", file_okay=False)],
) -> None:
    """Copy a verified paused extraction into a new offline review workspace."""
    from src.workflow.review_workspace import import_review_run

    state = asyncio.run(import_review_run(source, run_id, target))
    console.print(f"isolated review imported: run_id={state.run_id} target={target.resolve()}")


@app.command("confirm-review-commit")
def confirm_review_commit_command(
    run_id: str,
    reviewer: Annotated[str, typer.Option("--reviewer")],
    confirm: Annotated[bool, typer.Option("--confirm")] = False,
) -> None:
    """Explicitly confirm an isolated graph commit after viewing its preview."""
    if not confirm:
        raise typer.BadParameter("--confirm is required after inspecting review-progress")
    _print_model(asyncio.run(PrismKEService().confirm_review_commit(run_id, reviewer)))


@app.command("show-evidence")
def show_evidence(evidence_id: str) -> None:
    """Print immutable evidence metadata."""
    service = PrismKEService()
    evidence = asyncio.run(service.evidence_store.get(evidence_id))
    _print_model(evidence)


@app.command("export-evidence")
def export_evidence(
    evidence_id: str,
    output: Annotated[Path, typer.Option("--output", dir_okay=False)],
) -> None:
    """Export an evidence image or region as PNG/binary data."""
    service = PrismKEService()
    payload = asyncio.run(service.evidence_store.crop(evidence_id))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    console.print(f"evidence exported: {output.resolve()}")


@app.command("evaluate")
def evaluate(
    manifest: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output", dir_okay=False)],
    provider: Annotated[str, typer.Option("--provider")] = "mock",
    ocr_provider: Annotated[str, typer.Option("--ocr-provider")] = "disabled",
    vlm_provider: Annotated[str, typer.Option("--vlm-provider")] = "disabled",
) -> None:
    """Run a reproducible evaluation manifest and write a JSON report."""

    report = asyncio.run(
        evaluate_manifest(
            manifest,
            PrismKEService(),
            provider_name=provider,
            ocr_provider_name=ocr_provider,
            vlm_provider_name=vlm_provider,
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(orjson.dumps(report.model_dump(mode="json"), option=orjson.OPT_INDENT_2))
    console.print(
        f"evaluation completed={report.completed_cases} failed={report.failed_cases} "
        f"claim_f1={report.claim_f1:.4f} output={output.resolve()}"
    )


@app.command("evaluate-entities")
def evaluate_entities(
    manifest: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output", dir_okay=False)],
    embedding_provider: Annotated[str | None, typer.Option("--embedding-provider")] = None,
    protocol: Annotated[str | None, typer.Option("--protocol")] = None,
) -> None:
    """Evaluate semantic linking, NIL decisions and cross-document clustering."""
    settings = Settings()
    if embedding_provider is not None:
        settings.embedding_provider = embedding_provider
    if protocol not in {None, "fixed", "sequential"}:
        raise typer.BadParameter("protocol must be fixed or sequential")
    provider_instance: EmbeddingProvider
    if settings.embedding_provider == "mock":
        provider_instance = MockEmbeddingProvider()
    elif settings.embedding_provider == "bge-m3":
        provider_instance = BGEM3EmbeddingProvider(
            model_name=settings.embedding_model,
            model_revision=settings.embedding_model_revision,
            device=settings.embedding_device,
            use_fp16=settings.embedding_use_fp16,
            batch_size=settings.embedding_batch_size,
            max_tokens=settings.embedding_max_tokens,
            cache_dir=settings.embedding_cache_dir,
            model_cache_dir=settings.embedding_model_cache_dir,
            allow_download=False,
        )
    else:
        raise typer.BadParameter("entity evaluation requires explicit mock or bge-m3")

    async def execute() -> EntityLinkingEvaluationReport:
        return await evaluate_entity_linking_manifest(
            manifest,
            provider_instance,
            top_k=settings.entity_top_k,
            auto_link_threshold=settings.entity_auto_link_threshold,
            review_threshold=settings.entity_review_threshold,
            min_margin=settings.entity_min_margin,
            protocol=protocol,  # type: ignore[arg-type]
        )

    report = asyncio.run(execute())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(orjson.dumps(report.model_dump(mode="json"), option=orjson.OPT_INDENT_2))
    _print_model(report)


@app.command("export-entity-annotations")
def export_entity_annotations(
    workbook: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    package: Annotated[Path, typer.Option("--package", exists=True, file_okay=False)],
    output: Annotated[Path, typer.Option("--output", file_okay=False)],
) -> None:
    """Export human-confirmed entity answers without modifying the workbook."""
    try:
        _print_model(export_reviewed_annotations(workbook, package, output))
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command("validate-documents")
def validate_real_documents(
    manifest: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output", file_okay=False)],
    token_limit: Annotated[int, typer.Option("--token-limit")] = 100_000,
    stop_at: Annotated[int, typer.Option("--stop-at")] = 90_000,
    budget_ledger: Annotated[Path | None, typer.Option("--budget-ledger", exists=True)] = None,
    extend_budget: Annotated[bool, typer.Option("--extend-budget")] = False,
) -> None:
    """Run budgeted real-model document validation on an isolated JSON graph."""
    from src.evaluation.document_validation import validate_documents

    if not 0 < stop_at < token_limit:
        raise typer.BadParameter("budget must satisfy 0 < stop_at < token_limit")
    report = asyncio.run(
        validate_documents(
            manifest,
            Settings(),
            output,
            token_limit=token_limit,
            stop_at=stop_at,
            budget_ledger=budget_ledger,
            extend_budget=extend_budget,
        )
    )
    finished = sum(case["status"] in {"completed", "awaiting_review"} for case in report["cases"])
    console.print(
        f"Attempted {len(report['cases'])}; finished {finished}; tokens={report['total_tokens']}"
    )


@app.command("evaluate-reflection")
def evaluate_reflection_command(
    manifest: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output", file_okay=False)],
    reflection_provider: Annotated[str, typer.Option("--reflection-provider")] = "mock",
    embedding_provider: Annotated[str, typer.Option("--embedding-provider")] = "mock",
    token_limit: Annotated[int, typer.Option("--token-limit")] = 200_000,
    stop_at: Annotated[int, typer.Option("--stop-at")] = 180_000,
) -> None:
    """Run the isolated nine-cell case retrieval and Reflection evaluation."""
    if not 0 < stop_at < token_limit:
        raise typer.BadParameter("budget must satisfy 0 < stop_at < token_limit")
    report = asyncio.run(
        evaluate_reflection_manifest(
            manifest,
            output,
            reflection_provider_name=reflection_provider,
            embedding_provider_name=embedding_provider,
            token_limit=token_limit,
            stop_at=stop_at,
        )
    )
    _print_model(
        {
            "publish_ready": report["publish_ready"],
            "metrics": report["metrics"],
            "stopped_reason": report["stopped_reason"],
            "report": str(output / "report.json"),
        }
    )
    console.print(f"Report: {output / 'report.json'}")


@app.command("migrate-graph")
def migrate_graph(
    source: Annotated[Path, typer.Option("--from-json", exists=True, dir_okay=False)],
    destination: Annotated[str, typer.Option("--to")] = "neo4j",
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Validate or migrate a JSON graph into the configured Neo4j backend."""
    if destination != "neo4j":
        raise typer.BadParameter("only the neo4j destination is supported")
    settings = Settings()

    async def execute() -> object:
        target = None
        if not dry_run:
            if not settings.neo4j_password:
                raise ProviderConfigurationError("migration requires PRISMKE_NEO4J_PASSWORD")
            target = Neo4jGraphStore(
                settings.neo4j_uri,
                settings.neo4j_user,
                settings.neo4j_password,
                settings.neo4j_database,
            )
        evidence = FileEvidenceStore(source.resolve().parent.parent / "evidence")
        try:
            return await migrate_json_graph(
                source.resolve(), target, evidence_store=evidence, dry_run=dry_run
            )
        finally:
            if target is not None:
                await target.close()

    _print_model(asyncio.run(execute()))


@app.command("prepare-model")
def prepare_model(
    embedding: Annotated[str, typer.Option("--embedding")] = "BAAI/bge-m3",
) -> None:
    """Download and validate the configured local embedding model."""
    settings = Settings(
        embedding_provider="bge-m3",
        embedding_model=embedding,
        embedding_allow_download=True,
    )

    async def execute() -> dict[str, object]:
        service = PrismKEService(settings)
        try:
            vector = (await service.embedding_provider().encode(["PrismKE entity index"]))[0]
            return {
                "model": embedding,
                "revision": settings.embedding_model_revision,
                "device": settings.embedding_device,
                "model_cache": str(settings.embedding_model_cache_dir),
                "fingerprint": service.embedding_provider().fingerprint(),
                "dimension": len(vector),
                "status": "ready",
            }
        finally:
            await service.close()

    _print_model(asyncio.run(execute()))


@app.command("rebuild-entity-index")
def rebuild_entity_index_command(
    backend: Annotated[str, typer.Option("--backend")] = "neo4j",
    batch_size: Annotated[int, typer.Option("--batch-size", min=1)] = 32,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Build missing or outdated entity vectors without changing graph revisions."""
    if backend not in {"json", "neo4j"}:
        raise typer.BadParameter("backend must be json or neo4j")
    settings = Settings(graph_store=backend)

    async def execute() -> object:
        service = PrismKEService(settings)
        try:
            return await rebuild_entity_index(
                service.graph_store,
                service.embedding_provider(),
                backend=backend,
                batch_size=batch_size,
                dry_run=dry_run,
            )
        finally:
            await service.close()

    _print_model(asyncio.run(execute()))


@app.command()
def serve(
    host: Annotated[str | None, typer.Option("--host")] = None,
    port: Annotated[int | None, typer.Option("--port")] = None,
) -> None:
    """Start the FastAPI service and mounted Gradio workspace."""
    try:
        import uvicorn

        from src.api import create_app
    except ImportError as exc:
        raise typer.BadParameter("web dependencies are missing; run `uv sync --extra web`") from exc
    settings = Settings()
    if host is not None:
        settings.api_host = host
    if port is not None:
        settings.api_port = port
    uvicorn.run(
        create_app(settings),
        host=settings.api_host,
        port=settings.api_port,
        log_config=None,
    )


if __name__ == "__main__":
    app()
