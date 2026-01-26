"""Command-line interface."""

import sys
import click
from PyQt6.QtWidgets import QApplication, QStyleFactory
from .interface import FaceRecoApp


@click.command()
@click.version_option()
@click.option("--gui", is_flag=True, default=True, help="Launch the GUI interface.")
def main(gui: bool) -> None:
    """Facial Recognition."""
    if gui:
        app = QApplication(sys.argv)
        app.setStyle(QStyleFactory.create("Fusion"))
        window = FaceRecoApp()
        window.show()
        sys.exit(app.exec())
    else:
        click.echo("CLI mode not implemented yet. Use --gui.")


if __name__ == "__main__":
    main(prog_name="facial-recognition")  # pragma: no cover
