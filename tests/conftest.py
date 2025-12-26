"""Test configuration for ensuring project modules are importable."""
from __future__ import annotations

import sys
from pathlib import Path

# Add repository root to PYTHONPATH so tests can import top-level modules
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
