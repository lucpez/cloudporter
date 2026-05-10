import json
import subprocess
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


def _translate(manifest: Manifest, output_dir: Path, provider: str) -> None:
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


def _init(output_dir: Path, verbose: bool) -> None:
    # raises FileNotFoundError if tofu binary is not in PATH
    result = subprocess.run(
        ["tofu", "init"],
        cwd=output_dir,
        capture_output=not verbose,
        text=not verbose,
    )
    if result.returncode != 0:
        if not verbose and result.stderr:
            console.print(f"[red]Error:[/red] tofu init failed:\n{result.stderr}")
        raise typer.Exit(code=1)

    console.print("[green]✓[/green] tofu init complete")


def _print_resource_summary(output_dir: Path, manifest: Manifest) -> None:
    result = subprocess.run(
        ["tofu", "show", "-json"], cwd=output_dir, capture_output=True, text=True
    )
    if result.returncode != 0:
        return
    data = json.loads(result.stdout)
    resources = data.get("values", {}).get("root_module", {}).get("resources", [])
    if not resources:
        return

    tf_name_to_type = {
        r.name.replace("-", "_").replace(" ", "_"): r.type for r in manifest.resources
    }

    for r in resources:
        if r.get("mode") != "managed":
            continue
        tf_name = str(r.get("name", ""))
        manifest_type = tf_name_to_type.get(tf_name, str(r.get("type", "")))
        resource_id = str(r.get("values", {}).get("id", ""))
        console.print(f"  - {tf_name}    {manifest_type}    {resource_id}")


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
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Show tofu output.")
    ] = False,
) -> None:
    """Translate a CloudPorter manifest to OpenTofu templates."""
    manifest = _load_manifest(mannifest)
    output_dir = output or Path.cwd() / manifest.name
    _translate(manifest, output_dir, provider)
    try:
        _init(output_dir, verbose)
    except FileNotFoundError:  # tofu binary not found in PATH
        console.print("[yellow]Warning:[/yellow] tofu is not installed; skipping init")
        return


@app.command(name="deploy")
def deploy_cmd(
    mannifest: Annotated[Path, typer.Argument(help="Path to the manifest file.")],
    provider: Annotated[str, typer.Option(help="Target cloud provider.")],
    output: Annotated[Path | None, typer.Option(help="Output directory.")] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Run tofu plan instead of apply.")
    ] = False,
    auto_approve: Annotated[
        bool, typer.Option("--auto-approve", help="Skip interactive confirmation.")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Stream tofu output.")
    ] = False,
) -> None:
    """Deploy cloud infrastructure from a CloudPorter manifest."""
    manifest = _load_manifest(mannifest)
    output_dir = output or Path.cwd() / manifest.name

    if not dry_run and (output_dir / "terraform.tfstate").exists():
        console.print(
            "[yellow]Warning:[/yellow] existing state found"
            " — this will modify live infrastructure"
        )

    _translate(manifest, output_dir, provider)
    try:
        _init(output_dir, verbose)
    except FileNotFoundError:  # tofu binary not found in PATH
        console.print("[red]Error:[/red] tofu is not installed")
        raise typer.Exit(code=1) from None

    if dry_run:
        cmd = ["tofu", "plan"]
        capture = not verbose
    elif auto_approve:
        cmd = ["tofu", "apply", "-auto-approve"]
        capture = not verbose
    else:
        cmd = ["tofu", "apply"]
        capture = False  # must stream so user sees the interactive prompt

    try:
        result = subprocess.run(
            cmd, cwd=output_dir, capture_output=capture, text=capture
        )
    except FileNotFoundError:
        console.print("[red]Error:[/red] tofu is not installed")
        raise typer.Exit(code=1) from None

    if result.returncode != 0:
        if capture and result.stderr:
            console.print(f"[red]Error:[/red] tofu failed:\n{result.stderr}")
        raise typer.Exit(code=1)

    if dry_run:
        console.print("[green]✓[/green] dry run complete")
        return

    console.print("[green]✓[/green] Deploy complete")
    _print_resource_summary(output_dir, manifest)
