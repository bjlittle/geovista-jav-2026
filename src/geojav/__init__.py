# Copyright (c) 2021, GeoVista Contributors.
#
# This file is part of GeoVista and is distributed under the 3-Clause BSD license.
# See the LICENSE file in the package root directory for licensing details.

from __future__ import annotations

from pathlib import Path

import pooch

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__all__ = ["CACHE"]

BASE_DIR: Path = Path(__file__).parent / "cache"
BASE_URL: str = "https://github.com/bjlittle/geovista-data-jav-2026/raw/{version}/assets"
CACHE_DIR: Path = BASE_DIR / "assets"
DATA_VERSION: str = "2026.03.0"
REGISTRY: Path = BASE_DIR / "registry.txt"
RETRY_ATTEMPTS: int = 3

CACHE: pooch.Pooch = pooch.create(
        path=CACHE_DIR,
        base_url=BASE_URL,
        version=DATA_VERSION,
        version_dev="main",
        registry=None,
        retry_if_failed=RETRY_ATTEMPTS,
)

# load the registry
with (REGISTRY).open("r", encoding="utf-8", errors="strict") as text_io:
    CACHE.load_registry(text_io)
