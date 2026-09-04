"""Versioned scoring configuration.

Thresholds and weights live in data, not in code, so a change to how the Book
is ranked is a reviewable configuration change with a version attached.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).parent
SCORING_CONFIG_FILE = "scoring.v1.json"


@lru_cache(maxsize=4)
def load_scoring_config(filename: str = SCORING_CONFIG_FILE) -> dict[str, Any]:
    with (CONFIG_DIR / filename).open(encoding="utf-8") as handle:
        return json.load(handle)


def factor_config(name: str, filename: str = SCORING_CONFIG_FILE) -> dict[str, Any]:
    return load_scoring_config(filename)["urgency"]["factors"][name]
