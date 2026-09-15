"""PrismKE command-line interface."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import orjson
import typer
from rich.console import Console

from prismke.models import ReviewDecision
from prismke.schema import load_schema
from prismke.service import PrismKEService

app = typer.Typer(no_args_is_help=True, help="PrismKE knowledge construction CLI")
console = Console()


def _print_model(model: object) -> None:
    if hasattr(model, "model_dump"):
        model = model.model_dump(mode="json")  # type: ignore[union-attr]
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
) -> None:
    """Run the complete PrismKE workflow for one document."""
    state = asyncio.run(PrismKEService().run(input_path, schema, provider))
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
    state = PrismKEService().review(run_id, claim_id, decision)
    console.print(f"review recorded: run_id={state.run_id} claim_id={claim_id}")


@app.command()
def resume(run_id: str) -> None:
    """Resume a failed or reviewed run from its latest SQLite snapshot."""
    state = asyncio.run(PrismKEService().resume(run_id))
    console.print(f"run_id={state.run_id} status={state.status}")
    _print_model(state)


if __name__ == "__main__":
    app()
