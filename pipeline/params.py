"""Loading of pipeline configuration files."""

from functools import lru_cache

import yaml

from pipeline.paths import CONFIG_DIR


@lru_cache
def model_params() -> dict:
    with open(CONFIG_DIR / "model_params.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache
def region_config() -> dict:
    with open(CONFIG_DIR / "region.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
