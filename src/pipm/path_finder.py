import sys
import sysconfig
from importlib.machinery import PathFinder
from pathlib import Path
from typing import Optional
from functools import cache

import tomli


@cache
def get_closest_lockfile(directory: Path) -> Optional[Path]:
    while True:
        poetry_lock = directory / "poetry.lock"
        if poetry_lock.exists():
            return poetry_lock
        if directory == directory.parent:
            break
        directory = directory.parent

    return None


@cache
def get_packages(lockfile: Path) -> dict:
    if lockfile is None:
        return {}
    packages = tomli.load(lockfile.open("rb"))["package"]
    return {p["name"]: p["version"] for p in packages}


class PipmPathFinder:
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if path is None:
            path = sys.path
        packages = get_packages(get_closest_lockfile(Path.cwd()))
        if fullname in packages:
            version = packages[fullname]
            msp = sysconfig.get_paths()["platstdlib"] + "/multi-site-packages"
            path.insert(0, f"{msp}/{fullname}/{version}")
        spec = PathFinder.find_spec(fullname, path, target)
        return spec
