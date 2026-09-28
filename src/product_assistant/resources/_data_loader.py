"""Shared loader for static resource data files."""

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Dict


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=16)
def _read_json_cached(file_name: str) -> Dict[str, Any]:
    """Read and cache JSON content from the data directory."""
    file_path = DATA_DIR / file_name
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_data(file_name: str) -> Dict[str, Any]:
    """Return a copy of static JSON data by file name."""
    return deepcopy(_read_json_cached(file_name))
