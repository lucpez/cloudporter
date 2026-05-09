import warnings
from pathlib import Path
from typing import Annotated

import typer
import yaml
from pydantic import ValidationError
from rich.console import Console

from cloudporter import __version__
from cloudporter.manifest.loader import load
from cloudporter.manifest.schema import Manifest
from cloudporter.translator.translate import translate

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


def _load_manifest(mannifest: Path) -> Manifest:
    try:
        return load(mannifest)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] file not found: {mannifest}")
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
    mannifest: Annotated[Path, typer.Argument(help="Path to the manifest file.")],
) -> None:
    """Validate a CloudPorter manifest file."""
    manifest = _load_manifest(mannifest)

    console.print(f"[green]✓[/green] Manifest [bold]{manifest.name}[/bold] is valid")

    for resource in manifest.resources:
        console.print(f"  - {resource.name} ({resource.type})")


@app.command(name="translate")
def translate_cmd(
    mannifest: Annotated[Path, typer.Argument(help="Path to the manifest file.")],
    provider: Annotated[str, typer.Option(help="Target cloud provider.")],
    output: Annotated[Path | None, typer.Option(help="Output directory.")] = None,
) -> None:
    """Translate a CloudPorter manifest to OpenTofu templates."""
    manifest = _load_manifest(mannifest)
    output_dir = output or Path.cwd() / manifest.name

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            tofu_files = translate(manifest, output_dir, provider)
        for w in caught:
            console.print(f"[yellow]Warning:[/yellow] {w.message}")
    except AttributeError:
        console.print(
            f"[red]Error:[/red] provider {provider!r} does not implement render_tofu"
        )
        raise typer.Exit(code=1) from None
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]✓[/green] Translated to [bold]{output_dir}[/bold]")
    for filename in tofu_files:
        console.print(f"  - {filename}")
