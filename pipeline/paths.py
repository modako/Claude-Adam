"""Filesystem layout of the pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "pipeline" / "config"
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
MANUAL_DIR = DATA_DIR / "manual"
STATIC_DIR = DATA_DIR / "static"
PREVIEW_DIR = DATA_DIR / "preview"
