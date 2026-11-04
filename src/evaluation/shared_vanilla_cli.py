"""CLI for the single shared text-only Vanilla baseline."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import orjson
import typer
from rich.console import Console

from src.core.settings import Settings
from src.evaluation.shared_vanilla import (
    BUDGET_LIMIT_CNY,
    evaluation_status,
    export_integrated_results,
    prepare_experiment,
    run_all,
    run_dataset,
    run_smoke,
)

app = typer.Typer(no_args_is_help=True, help="Shared text-only Vanilla baseline")
console = Console()

DEFAULT_OUTPUT = Path("runtime/evaluation/shared-vanilla-v1")
DEFAULT_TWITTER_SOURCE = Path("runtime/evaluation/twitter2017")
DEFAULT_MNRE_SOURCE = Path("runtime/evaluation/mnre-v2")
DEFAULT_TWITTER_DATASET = Path("data/benchmarks/twitter2017")
DEFAULT_INVALID_IMAGES = Path(
    "data/manifests/benchmarks/twitter2017.invalid-images.json"
)
DEFAULT_COMPONENT_OUTPUT = Path("runtime/evaluation/component-ablation-v4")
DEFAULT_AGENT_OUTPUT = Path("runtime/evaluation/agent-progression-v1")


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
    invalid_images: Annotated[
        Path, typer.Option("--invalid-images", exists=True, dir_okay=False)
    ] = DEFAULT_INVALID_IMAGES,
) -> None:
    """Freeze canonical labels, prompts, data, model settings, and source hashes."""
    _print(
        prepare_experiment(
            output,
            twitter_source,
            mnre_source,
            twitter_dataset,
            invalid_images,
            Settings(),
        )
    )


@app.command("smoke")
def smoke(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
) -> None:
    """Run the fixed 20+20 format-only smoke sample without tuning."""
    _print(asyncio.run(run_smoke(output, Settings(), concurrency=concurrency)))


@app.command("run-mner")
def mner(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
) -> None:
    """Run or resume all 723 Twitter-2017 test predictions."""
    _print(
        asyncio.run(
            run_dataset(
                output,
                "twitter2017",
                "main",
                Settings(),
                concurrency=concurrency,
                budget_limit_cny=BUDGET_LIMIT_CNY,
            )
        )
    )


@app.command("run-mre")
def mre(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
) -> None:
    """Run or resume all 1,614 MNRE-V2 test predictions after MNER passes."""
    _print(
        asyncio.run(
            run_dataset(
                output,
                "mnre-v2",
                "main",
                Settings(),
                concurrency=concurrency,
                budget_limit_cny=BUDGET_LIMIT_CNY,
            )
        )
    )


@app.command("run-all")
def all_experiments(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 2,
) -> None:
    """Run smoke, complete MNER, gate it, then complete MRE and export."""

    async def execute() -> dict[str, object]:
        summary = await run_all(output, Settings(), concurrency=concurrency)
        return {"summary": summary, "results": export_integrated_results(output)}

    _print(asyncio.run(execute()))


@app.command("status")
def status(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Show counts, reports, hashes, errors, milestones, and budget."""
    _print(evaluation_status(output))


@app.command("export")
def export(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    component_output: Annotated[
        Path | None, typer.Option("--component-output", exists=True, file_okay=False)
    ] = None,
    agent_output: Annotated[
        Path | None, typer.Option("--agent-output", exists=True, file_okay=False)
    ] = None,
) -> None:
    """Export shared rows and optionally rebuild both paper tables offline."""
    _print(export_integrated_results(output, component_output, agent_output))


if __name__ == "__main__":
    app()
