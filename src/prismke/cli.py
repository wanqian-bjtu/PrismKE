"""PrismKE command-line interface."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import orjson
import typer
from pydantic import BaseModel
from rich.console import Console

from prismke.core.errors import ProviderConfigurationError
from prismke.core.settings import Settings
from prismke.domain import ReviewDecision, load_schema
from prismke.evaluation import evaluate_manifest
from prismke.persistence import FileEvidenceStore, Neo4jGraphStore, migrate_json_graph
from prismke.workflow import PrismKEService

app = typer.Typer(no_args_is_help=True, help="PrismKE knowledge construction CLI")
console = Console()


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


@app.command()
def run(
    input_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    schema: Annotated[Path, typer.Option("--schema", exists=True, dir_okay=False)],
    provider: Annotated[str, typer.Option("--provider")] = "mock",
    ocr_provider: Annotated[str, typer.Option("--ocr-provider")] = "disabled",
    vlm_provider: Annotated[str, typer.Option("--vlm-provider")] = "disabled",
    allow_remote_assets: Annotated[bool, typer.Option("--allow-remote-assets")] = False,
) -> None:
    """Run the complete PrismKE workflow for one document."""
    state = asyncio.run(
        PrismKEService().run(
            input_path, schema, provider, ocr_provider, vlm_provider, allow_remote_assets
        )
    )
    console.print(f"run_id={state.run_id} status={state.status}")
    _print_model(state)


@app.command("show-run")
def show_run(run_id: str) -> None:
    """Print the latest serialized state of a run."""
    _print_model(PrismKEService().show_run(run_id))


@app.command()
def review(
    run_id: str,
    claim_id: Annotated[str, typer.Option("--claim-id")],
    decision: Annotated[ReviewDecision, typer.Option("--decision")],
) -> None:
    """Record a human decision for one claim."""
    state = asyncio.run(PrismKEService().review(run_id, claim_id, decision))
    console.print(f"review recorded: run_id={state.run_id} claim_id={claim_id}")


@app.command()
def resume(run_id: str) -> None:
    """Resume a failed or reviewed run from its latest SQLite snapshot."""
    state = asyncio.run(PrismKEService().resume(run_id))
    console.print(f"run_id={state.run_id} status={state.status}")
    _print_model(state)


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


@app.command("migrate-graph")
def migrate_graph(
    source: Annotated[
        Path, typer.Option("--from-json", exists=True, dir_okay=False)
    ],
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
                raise ProviderConfigurationError(
                    "migration requires PRISMKE_NEO4J_PASSWORD"
                )
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


@app.command()
def serve(
    host: Annotated[str | None, typer.Option("--host")] = None,
    port: Annotated[int | None, typer.Option("--port")] = None,
) -> None:
    """Start the FastAPI service and mounted Gradio workspace."""
    try:
        import uvicorn

        from prismke.api import create_app
    except ImportError as exc:
        raise typer.BadParameter("web dependencies are missing; run `uv sync --extra web`") from exc
    overrides: dict[str, object] = {}
    if host is not None:
        overrides["api_host"] = host
    if port is not None:
        overrides["api_port"] = port
    settings = Settings(**overrides)
    uvicorn.run(
        create_app(settings),
        host=settings.api_host,
        port=settings.api_port,
        log_config=None,
    )


if __name__ == "__main__":
    app()
