"""Expose the standard-library tooling package for isolated CLI regression tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
