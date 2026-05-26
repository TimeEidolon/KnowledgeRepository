#!/usr/bin/env python3
"""Sync Coohom Help Center articles to knowledge/*.mdx (Mintlify)."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from sync_helpcenter import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
