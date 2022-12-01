import os
from pathlib import Path

from installer.destinations import SchemeDictionaryDestination
from installer.utils import Scheme
from packaging.version import Version


class WheelMultiDestination(SchemeDictionaryDestination):
    version: Version
    distribution: str

    def _path_with_destdir(self, scheme: Scheme, path: str) -> str:
        scheme_path = Path(self.scheme_dict[scheme])
        if scheme in {"purelib", "platlib"}:
            scheme_path = scheme_path.parent / f"multi-{scheme_path.name}"
        file = scheme_path / self.distribution / str(self.version) / path
        if self.destdir is not None:
            file_path = Path(file)
            rel_path = file_path.relative_to(file_path.anchor)
            return os.path.join(self.destdir, rel_path)
        return str(file)
