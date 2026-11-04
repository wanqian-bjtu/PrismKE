"""CLI for the post-hoc MNER governance reject-gate V2 experiment."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Annotated, Any, Literal

import orjson
import typer
from rich.console import Console

from src.core.settings import Settings
from src.evaluation.agent_progression_mner_v2 import (
    evaluation_status,
    export_results,
    prepare_experiment,
    reaggregate_governance,
    run_all,
    run_fusion_stage,
    run_test,
    run_validation,
)

app = typer.Typer(no_args_is_help=True, help="Post-hoc MNER governance reject-gate V2")
console = Console()

DEFAULT_OUTPUT = Path("runtime/evaluation/agent-progression-mner-v2")
DEFAULT_SOURCE = Path("runtime/evaluation/agent-progression-v1")
DEFAULT_SCHEMA = Path("configs/evaluation/twitter2017-ner-schema.yaml")


def _print(value: object) -> None:
    console.print_json(orjson.dumps(value, option=orjson.OPT_INDENT_2).decode())


def _execute(
    command: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
    output: Path,
    concurrency: int,
    budget_limit_cny: float,
) -> None:
    _print(
        asyncio.run(
            command(
                output,
                Settings(),
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    )


@app.command("prepare")
def prepare(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    source_experiment: Annotated[
        Path, typer.Option("--source-experiment", exists=True, file_okay=False)
    ] = DEFAULT_SOURCE,
    twitter_schema: Annotated[
        Path, typer.Option("--twitter-schema", exists=True, dir_okay=False)
    ] = DEFAULT_SCHEMA,
) -> None:
    """Verify and freeze all V1 prediction and protocol sources."""
    _print(prepare_experiment(output, source_experiment, twitter_schema, Settings()))


@app.command("reaggregate-governance")
def reaggregate(
    stage: Annotated[Literal["dev", "holdout", "main"], typer.Option("--stage")],
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Apply the deterministic reject-only gate without provider calls."""
    _print(reaggregate_governance(output, stage))


@app.command("run-fusion")
def fusion(
    stage: Annotated[Literal["dev", "holdout", "main"], typer.Option("--stage")],
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 5.0,
) -> None:
    """Run or reuse the frozen Fusion/Review v3 stage for V2 inputs."""
    _execute(
        lambda selected_output, settings, **kwargs: run_fusion_stage(
            selected_output, stage, settings, **kwargs
        ),
        output,
        concurrency,
        budget_limit_cny,
    )


@app.command("run-validation")
def validation(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 5.0,
) -> None:
    """Run dev and the one-time frozen holdout, enforcing the ordering gate."""
    _execute(run_validation, output, concurrency, budget_limit_cny)


@app.command("run-test")
def test(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 5.0,
) -> None:
    """Run the complete 723-case test set once after validation passes."""
    _execute(run_test, output, concurrency, budget_limit_cny)


@app.command("run-all")
def all_experiments(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 5.0,
) -> None:
    """Run validation, gated test, and export in protocol order."""
    _execute(run_all, output, concurrency, budget_limit_cny)


@app.command("export")
def export(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Export metrics, bootstrap intervals, transitions, and paired tests."""
    _print(export_results(output))


@app.command("status")
def status(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Show frozen sources, progress, structural gates, and budget."""
    _print(evaluation_status(output))


if __name__ == "__main__":
    app()
