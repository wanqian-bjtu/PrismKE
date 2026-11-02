"""Typer commands for the isolated Twitter-2017 experiment."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Literal

import orjson
import typer
from rich.console import Console

from src.core.settings import Settings
from src.evaluation.twitter2017 import (
    build_vectors,
    evaluation_status,
    generate_captions,
    prepare_dataset,
    run_prompt_dev,
    run_prompt_holdout,
)

app = typer.Typer(no_args_is_help=True, help="Twitter-2017 case-library and NER evaluation")
console = Console()

DEFAULT_DATASET = Path("data/benchmarks/twitter2017")
DEFAULT_INVALID = Path("data/manifests/benchmarks/twitter2017.invalid-images.json")
DEFAULT_SCHEMA = Path("configs/evaluation/twitter2017-ner-schema.yaml")
DEFAULT_OUTPUT = Path("runtime/evaluation/twitter2017")


def _print(value: object) -> None:
    console.print_json(orjson.dumps(value, option=orjson.OPT_INDENT_2).decode())


@app.command("prepare")
def prepare(
    dataset: Annotated[Path, typer.Option(exists=True, file_okay=False)] = DEFAULT_DATASET,
    invalid_manifest: Annotated[
        Path, typer.Option("--invalid-manifest", exists=True, dir_okay=False)
    ] = DEFAULT_INVALID,
    schema: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_SCHEMA,
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Parse BIO data, audit leakage and create the fixed validation split."""
    _print(prepare_dataset(dataset, invalid_manifest, schema, output))


@app.command("caption")
def caption(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    split: Annotated[Literal["train", "validation", "all"], typer.Option()] = "all",
    limit: Annotated[int | None, typer.Option(min=1)] = None,
    smoke: Annotated[bool, typer.Option()] = False,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 80.0,
) -> None:
    """Generate resumable objective image descriptions with a CNY hard limit."""
    _print(
        asyncio.run(
            generate_captions(
                output,
                Settings(),
                split=split,
                limit=limit,
                smoke=smoke,
                budget_limit_cny=budget_limit_cny,
            )
        )
    )


@app.command("embed")
def embed(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Build local BGE-M3 vectors for training cases and validation queries."""
    _print(asyncio.run(build_vectors(output, Settings())))


@app.command("split-validation")
def split_validation(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Show the immutable 100/623 validation split produced by prepare."""
    path = output / "validation_split.json"
    if not path.exists():
        raise typer.BadParameter("run twitter2017 prepare first")
    _print(orjson.loads(path.read_bytes()))


@app.command("run-dev")
def run_dev(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    schema: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_SCHEMA,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 80.0,
) -> None:
    """Evaluate three prompt versions and top-k values on the fixed 100 cases."""
    _print(
        asyncio.run(
            run_prompt_dev(
                output, schema, Settings(), budget_limit_cny=budget_limit_cny
            )
        )
    )


@app.command("run-holdout")
def run_holdout(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
    schema: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_SCHEMA,
    budget_limit_cny: Annotated[float, typer.Option("--budget-limit-cny", min=0.01)] = 80.0,
) -> None:
    """Run the frozen configuration once on the 623-case holdout."""
    _print(
        asyncio.run(
            run_prompt_holdout(
                output, schema, Settings(), budget_limit_cny=budget_limit_cny
            )
        )
    )


@app.command("status")
def status(
    output: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_OUTPUT,
) -> None:
    """Report artifacts, progress, accounting and the frozen configuration."""
    _print(evaluation_status(output))
