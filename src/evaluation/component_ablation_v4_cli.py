"""CLI for the V4 text-first, visually gated component ablation."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import orjson
import typer
from rich.console import Console

from src.core.settings import Settings
from src.evaluation.component_ablation_v4 import (
    evaluation_status,
    export_results,
    prepare_experiment,
    run_all,
    run_mner,
    run_mre,
    run_smoke,
)

app = typer.Typer(no_args_is_help=True, help="V4 Twitter/MNRE component ablation")
console = Console()

DEFAULT_OUTPUT = Path("runtime/evaluation/component-ablation-v4")
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
    """Prepare the isolated V4 manifest, data splits, and hashes."""
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
    """Run structural checks for all eight cells and freeze the V4 protocol."""
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


@app.command("run-mner")
def mner(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 30.0,
) -> None:
    """Run Twitter validation and all four complete MNER test cells."""
    _print(
        asyncio.run(
            run_mner(
                output,
                Settings(),
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    )


@app.command("run-mre")
def mre(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 30.0,
) -> None:
    """Run MNRE validation and all four complete MRE test cells."""
    _print(
        asyncio.run(
            run_mre(
                output,
                Settings(),
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    )


@app.command("run-all")
def all_experiments(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 30.0,
) -> None:
    """Run MNER, gate it, continue to MRE, and export results."""
    async def execute() -> dict[str, object]:
        summary = await run_all(
            output,
            Settings(),
            concurrency=concurrency,
            budget_limit_cny=budget_limit_cny,
        )
        return {"summary": summary, "results": export_results(output)}

    _print(asyncio.run(execute()))


@app.command("export")
def export(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Rebuild V4 JSON and CSV results from complete main predictions."""
    _print(export_results(output))


@app.command("status")
def status(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Show resumable progress, gate state, hashes, failures, and cost."""
    _print(evaluation_status(output))


if __name__ == "__main__":
    app()
