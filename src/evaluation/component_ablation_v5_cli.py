"""CLI for the V5 paired visual contribution experiment."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import orjson
import typer
from rich.console import Console

from src.core.settings import Settings
from src.evaluation.component_ablation_v5 import (
    evaluation_status,
    export_results,
    prepare_experiment,
    run_multimodal,
    run_validation,
)

app = typer.Typer(no_args_is_help=True, help="V5 paired visual contribution ablation")
console = Console()

DEFAULT_OUTPUT = Path("runtime/evaluation/component-ablation-v5")
DEFAULT_V4_OUTPUT = Path("runtime/evaluation/component-ablation-v4")


def _print(value: object) -> None:
    console.print_json(orjson.dumps(value, option=orjson.OPT_INDENT_2).decode())


@app.command("prepare")
def prepare(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    source_v4: Annotated[
        Path, typer.Option("--source-v4", exists=True, file_okay=False)
    ] = DEFAULT_V4_OUTPUT,
) -> None:
    """Verify and import immutable V4 predictions into a self-contained V5 directory."""
    _print(prepare_experiment(output, source_v4, Settings()))


@app.command("run-validation")
def validation(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 10.0,
) -> None:
    """Run the frozen holdouts once without tuning."""
    _print(
        asyncio.run(
            run_validation(
                output,
                Settings(),
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    )


@app.command("run-multimodal")
def multimodal(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 10.0,
) -> None:
    """Run paired MNER then paired MRE on the complete test sets."""
    _print(
        asyncio.run(
            run_multimodal(
                output,
                Settings(),
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    )


@app.command("export")
def export(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Assemble V5 JSON and CSV results from reused and paired predictions."""
    _print(export_results(output))


@app.command("status")
def status(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Show provenance, progress, budget, failures, and completed results."""
    _print(evaluation_status(output))


if __name__ == "__main__":
    app()
