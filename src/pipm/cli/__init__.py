import subprocess
import sys
import sysconfig
from pathlib import Path

from installer.sources import WheelFile
from typer import Typer, echo

from pipm._installer import install
from pipm._installer.destinations import WheelMultiDestination

app = Typer()


@app.command()
def main(path: Path = Path.cwd()):
    """Download wheels for current project into `tmp-wheelhouse`, and install
    them into the multi-site-packages directory."""
    echo("Fetching wheels...")
    subprocess.run(["pip", "download", ".", "-d", f"{path / 'tmp-wheelhouse'}"])

    destination = WheelMultiDestination(
        sysconfig.get_paths(),
        interpreter=sys.executable,
        script_kind="posix",
    )

    for wheel in path.glob("tmp-wheelhouse/*.whl"):
        echo(f"Installing {wheel.name}")
        with WheelFile.open(wheel) as source:
            install(
                source=source,
                destination=destination,
                additional_metadata={
                    "INSTALLER": b"pipm 0.1.0",
                },
            )


if __name__ == "__main__":
    app()
