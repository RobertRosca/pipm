import subprocess
import sys
import sysconfig
from pathlib import Path

from installer.sources import WheelFile
from typer import Typer, echo

from pipm._installer import install
from pipm._installer.destinations import WheelMultiDestination

app = Typer()


def edit_sitecustomize():
    sitecustomize = Path(sysconfig.get_path("purelib")) / "sitecustomize.py"
    text = sitecustomize.read_text()
    line = "import sys; from pipm.path_finder import PipmPathFinder; sys.meta_path.insert(0, PipmPathFinder())"
    if line not in text:
        print("Edited sitecustomize.py")
        text = "\n".join([text, line])
        sitecustomize.write_text(text)


@app.command()
def main(path: Path = Path.cwd(), sitecustomize: bool = True):
    """Download wheels for current project into `tmp-wheelhouse`, and install
    them into the multi-site-packages directory."""

    if sitecustomize:
        edit_sitecustomize()

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
