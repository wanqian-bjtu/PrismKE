"""Typer commands for the isolated MNRE-V2 relation extraction experiment."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Literal

import orjson
import typer
from rich.console import Console

from src.core.settings import Settings
from src.evaluation.mnre_v2 import (
    build_vectors,
    evaluation_status,
    finalize_case_library,
    generate_captions,
    prepare_dataset,
    run_prompt_dev,
    run_prompt_holdout,
    run_test,
)

app = typer.Typer(no_args_is_help=True, help="MNRE-V2 case-library and relation evaluation")
console = Console()

DEFAULT_DATASET = Path("data/benchmarks/mnre-v2")
DEFAULT_SCHEMA = Path("configs/evaluation/mnre-v2-re-schema.yaml")
DEFAULT_OUTPUT = Path("runtime/evaluation/mnre-v2")


def _print(value: object) -> None:
    console.print_json(orjson.dumps(value, option=orjson.OPT_INDENT_2).decode())


@app.command("prepare")
def prepare(
    dataset: Annotated[Path, typer.Option(exists=True, file_okay=False)] = DEFAULT_DATASET,
    schema: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_SCHEMA,
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Parse MNRE-V2, audit leakage/conflicts and create the fixed validation split."""
    _print(prepare_dataset(dataset, schema, output))


@app.command("caption")
def caption(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    split: Annotated[
        Literal["train", "validation", "all", "final", "test"], typer.Option()
    ] = "all",
    limit: Annotated[int | None, typer.Option(min=1)] = None,
    smoke: Annotated[bool, typer.Option()] = False,
    concurrency: Annotated[int, typer.Option(min=1, max=2)] = 1,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 80.0,
) -> None:
    """Generate resumable objective captions, deduplicated by image SHA-256."""
    _print(
        asyncio.run(
            generate_captions(
                output,
                Settings(),
                split=split,
                limit=limit,
                smoke=smoke,
                concurrency=concurrency,
                budget_limit_cny=budget_limit_cny,
            )
        )
    )


@app.command("embed")
def embed(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    mode: Annotated[Literal["tuning", "final", "test"], typer.Option()] = "tuning",
) -> None:
    """Build offline BGE-M3 vectors for tuning, final-library, or test inputs."""
    _print(asyncio.run(build_vectors(output, Settings(), mode=mode)))


@app.command("split-validation")
def split_validation(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Show the immutable 200/1423 validation split."""
    path = output / "validation_split.json"
    if not path.exists():
        raise typer.BadParameter("run mnre-v2 prepare first")
    _print(orjson.loads(path.read_bytes()))


@app.command("run-dev")
def run_dev(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    schema: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_SCHEMA,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 80.0,
) -> None:
    """Evaluate three prompt versions and top-k values on the fixed 200 cases."""
    _print(
        asyncio.run(
            run_prompt_dev(output, schema, Settings(), budget_limit_cny=budget_limit_cny)
        )
    )


@app.command("run-holdout")
def run_holdout(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    schema: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_SCHEMA,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 80.0,
) -> None:
    """Run the frozen configuration once on the 1,423-case holdout."""
    _print(
        asyncio.run(
            run_prompt_holdout(
                output, schema, Settings(), budget_limit_cny=budget_limit_cny
            )
        )
    )


@app.command("finalize-library")
def finalize_library(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Merge clean train+validation cases and build the final BGE-M3 index."""
    report = finalize_case_library(output)
    report["vectors"] = asyncio.run(build_vectors(output, Settings(), mode="final"))
    _print(report)


@app.command("run-test")
def test(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    schema: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_SCHEMA,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 80.0,
    caption_concurrency: Annotated[int, typer.Option(min=1, max=2)] = 1,
) -> None:
    """Run the final frozen configuration on the untouched test split."""
    _print(
        asyncio.run(
            run_test(
                output,
                schema,
                Settings(),
                budget_limit_cny=budget_limit_cny,
                caption_concurrency=caption_concurrency,
            )
        )
    )


@app.command("status")
def status(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Report progress, hashes, costs, errors, and frozen configuration."""
    _print(evaluation_status(output))
