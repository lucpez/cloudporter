from typing import Annotated

import typer

from cloudporter import __version__

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
