from importlib.machinery import PathFinder
from pathlib import Path
import sys
from typing import Optional
import tomli


class LockfileSpecs:
    def __init__(self):
        self.path = self.get_closest_lockfile()

    @property
    def packages(self) -> dict:
        if self.path is None:
            return {}
        packages = tomli.load(self.path.open("rb"))["package"]
        return {p["name"]: p["version"] for p in packages}

    def get_closest_lockfile(self) -> Optional[Path]:
        directory = Path.cwd()

        while True:
            poetry_lock = directory / "poetry.lock"
            if poetry_lock.exists():
                return poetry_lock
            if directory == directory.parent:
                break
            directory = directory.parent

        return None


LFS = LockfileSpecs().packages


class PipzPathFinder:
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if path is None:
            path = sys.path
        if fullname in LFS:
            version = LFS[fullname]
            path.insert(
                0,
                (
                    "/home/roscar/work/github.com/RobertRosca/python-multi-package/"
                    f".venv/lib/python3.10/multi-site-packages/{fullname}/{version}"
                ),
            )
        spec = PathFinder.find_spec(fullname, path, target)
        return spec
