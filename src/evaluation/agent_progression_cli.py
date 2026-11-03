"""CLI for the four-stage PrismKE agent-progression evaluation."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Annotated, Any

import orjson
import typer
from rich.console import Console

from src.core.settings import Settings
from src.evaluation.agent_progression import (
    evaluation_status,
    export_results,
    prepare_experiment,
    run_all,
    run_mner_test,
    run_mner_validation,
    run_mre_test,
    run_mre_validation,
)

app = typer.Typer(no_args_is_help=True, help="PrismKE four-stage agent progression")
console = Console()

DEFAULT_OUTPUT = Path("runtime/evaluation/agent-progression-v1")
DEFAULT_TWITTER_SOURCE = Path("runtime/evaluation/twitter2017")
DEFAULT_MNRE_SOURCE = Path("runtime/evaluation/mnre-v2")
DEFAULT_COMPONENT_V4 = Path("runtime/evaluation/component-ablation-v4")
DEFAULT_TWITTER_DATASET = Path("data/benchmarks/twitter2017")
DEFAULT_TWITTER_SCHEMA = Path("configs/evaluation/twitter2017-ner-schema.yaml")
DEFAULT_MNRE_SCHEMA = Path("configs/evaluation/mnre-v2-re-schema.yaml")
DEFAULT_INVALID_IMAGES = Path(
    "data/manifests/benchmarks/twitter2017.invalid-images.json"
)


def _print(value: object) -> None:
    console.print_json(orjson.dumps(value, option=orjson.OPT_INDENT_2).decode())


@app.command("prepare")
def prepare(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    twitter_source: Annotated[
        Path, typer.Option("--twitter-source", exists=True, file_okay=False)
    ] = DEFAULT_TWITTER_SOURCE,
    mnre_source: Annotated[
        Path, typer.Option("--mnre-source", exists=True, file_okay=False)
    ] = DEFAULT_MNRE_SOURCE,
    component_v4_output: Annotated[
        Path, typer.Option("--component-v4-output", exists=True, file_okay=False)
    ] = DEFAULT_COMPONENT_V4,
    twitter_dataset: Annotated[
        Path, typer.Option("--twitter-dataset", exists=True, file_okay=False)
    ] = DEFAULT_TWITTER_DATASET,
    twitter_schema: Annotated[
        Path, typer.Option("--twitter-schema", exists=True, dir_okay=False)
    ] = DEFAULT_TWITTER_SCHEMA,
    mnre_schema: Annotated[
        Path, typer.Option("--mnre-schema", exists=True, dir_okay=False)
    ] = DEFAULT_MNRE_SCHEMA,
    invalid_images: Annotated[
        Path, typer.Option("--invalid-images", exists=True, dir_okay=False)
    ] = DEFAULT_INVALID_IMAGES,
) -> None:
    """Freeze data, model, schemas, case libraries, vectors, and code hashes."""
    _print(
        prepare_experiment(
            output,
            twitter_source,
            mnre_source,
            component_v4_output,
            twitter_dataset,
            twitter_schema,
            mnre_schema,
            invalid_images,
            Settings(),
        )
    )


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


@app.command("run-mner-validation")
def mner_validation(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 20.0,
) -> None:
    """Tune on 100 MNER dev cases and run the 623-case frozen holdout once."""
    _execute(run_mner_validation, output, concurrency, budget_limit_cny)


@app.command("run-mner-test")
def mner_test(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 20.0,
) -> None:
    """Run all four stages on the complete 723-case MNER test split."""
    _execute(run_mner_test, output, concurrency, budget_limit_cny)


@app.command("run-mre-validation")
def mre_validation(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 20.0,
) -> None:
    """Tune on 200 MRE dev cases and run the 1,423-case frozen holdout once."""
    _execute(run_mre_validation, output, concurrency, budget_limit_cny)


@app.command("run-mre-test")
def mre_test(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 20.0,
) -> None:
    """Run all four stages on the complete 1,614-case MRE test split."""
    _execute(run_mre_test, output, concurrency, budget_limit_cny)


@app.command("run-all")
def all_experiments(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 20.0,
) -> None:
    """Run MNER validation/test, gate it, then run MRE validation/test."""
    _execute(run_all, output, concurrency, budget_limit_cny)


@app.command("export")
def export(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Export JSON/CSV metrics and paired-bootstrap statistics."""
    _print(export_results(output))


@app.command("status")
def status(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Show resumable progress, selected prompts, failures, and budget."""
    _print(evaluation_status(output))


if __name__ == "__main__":
    app()
