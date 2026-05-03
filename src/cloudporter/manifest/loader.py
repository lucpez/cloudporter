from pathlib import Path

import yaml

from cloudporter.manifest.schema import Manifest


def load(path: Path) -> Manifest:
    with open(path) as f:
        data: object = yaml.safe_load(f)
    return Manifest.model_validate(data)
