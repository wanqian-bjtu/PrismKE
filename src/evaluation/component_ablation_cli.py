"""CLI for the four-level component ablation experiment."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Literal

import orjson
import typer
from rich.console import Console

from src.core.settings import Settings
from src.evaluation.component_ablation import (
    evaluation_status,
    export_results,
    prepare_experiment,
    run_all_main,
    run_all_stability,
    run_smoke,
    run_variant,
)

app = typer.Typer(no_args_is_help=True, help="Twitter/MNRE four-level component ablation")
console = Console()

DEFAULT_OUTPUT = Path("runtime/evaluation/component-ablation-v1")
DEFAULT_TWITTER_SOURCE = Path("runtime/evaluation/twitter2017")
DEFAULT_MNRE_SOURCE = Path("runtime/evaluation/mnre-v2")
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
    """Freeze source artifacts, test cases, smoke split, and experiment hashes."""
    _print(
        prepare_experiment(
            output,
            twitter_source,
            mnre_source,
            twitter_dataset,
            twitter_schema,
            mnre_schema,
            invalid_images,
            Settings(),
        )
    )


@app.command("smoke")
def smoke(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 30.0,
) -> None:
    """Validate all eight dataset/variant cells on frozen validation samples."""
    _print(
        asyncio.run(
            run_smoke(
                output,
                Settings(),
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    )


@app.command("run")
def run(
    dataset: Annotated[Literal["twitter2017", "mnre-v2"], typer.Option()],
    variant: Annotated[
        Literal["vanilla", "schema", "multimodal", "full"], typer.Option()
    ],
    stage: Annotated[Literal["smoke", "main", "stability"], typer.Option()] = "main",
    repetition: Annotated[int, typer.Option(min=0, max=3)] = 0,
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 30.0,
) -> None:
    """Run or resume one dataset/variant cell."""
    _print(
        asyncio.run(
            run_variant(
                output,
                dataset,
                variant,
                stage,
                Settings(),
                repetition=repetition,
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    )


@app.command("run-all")
def run_all(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 30.0,
    include_stability: Annotated[bool, typer.Option("--stability/--no-stability")] = True,
) -> None:
    """Run all main cells, optional stability repetitions, and export JSON/CSV results."""

    async def execute() -> dict[str, object]:
        main = await run_all_main(
            output,
            Settings(),
            concurrency=concurrency,
            budget_limit_cny=budget_limit_cny,
        )
        stability = (
            await run_all_stability(
                output,
                Settings(),
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
            if include_stability
            else None
        )
        results = export_results(output)
        return {"main": main, "stability": stability, "results": results}

    _print(asyncio.run(execute()))


@app.command("export")
def export(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Rebuild consolidated JSON and CSV outputs from completed predictions."""
    _print(export_results(output))


@app.command("status")
def status(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Show progress, frozen configuration, artifacts, and cost."""
    _print(evaluation_status(output))
