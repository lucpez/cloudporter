from pathlib import Path
from typing import Annotated

import typer
import yaml
from pydantic import ValidationError
from rich.console import Console

from cloudporter import __version__
from cloudporter.manifest.loader import load

console = Console()

app = typer.Typer(
    name="cloudporter",
    help="A cloud agnostic infrastructure deployment tool.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"cloudporter {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    pass


@app.command()
def validate(
    file: Annotated[Path, typer.Argument(help="Path to the manifest file.")],
) -> None:
    """Validate a CloudPorter manifest file."""
    try:
        manifest = load(file)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] file not found: {file}")
        raise typer.Exit(code=1) from None
    except yaml.YAMLError as exc:
        console.print(f"[red]Error:[/red] invalid YAML: {exc}")
        raise typer.Exit(code=1) from exc
    except ValidationError as exc:
        console.print("[red]Manifest is invalid:[/red]")
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            console.print(f"  [red]✗[/red] {field}: {error['msg']}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]✓[/green] Manifest [bold]{manifest.name}[/bold] is valid")

    for resource in manifest.resources:
        console.print(f"  - {resource.name} ({resource.type})")
