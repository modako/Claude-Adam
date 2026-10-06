"""Forest stands (wydzielenia) from the BDL WFS of the State Forests.

Verified behaviour of the service is documented in docs/DATA_SOURCES.md.
Pages are cached on disk, so an interrupted download resumes where it stopped.
"""

import gzip
import json
import logging
import re
from datetime import date

import geopandas as gpd
import pandas as pd

from pipeline.paths import CACHE_DIR
from pipeline.sources.http import get

log = logging.getLogger(__name__)

WFS_URL = "https://wfs.bdl.lasy.gov.pl/geoserver/BDL/ows"
RDLP_LAYERS = [
    "Białystok", "Gdańsk", "Katowice", "Kraków", "Krosno", "Lublin", "Olsztyn", "Piła", "Poznań",
    "Radom", "Szczecin", "Szczecinek", "Toruń", "Warszawa", "Wrocław", "Zielona_Góra", "Łódź",
]
PAGE_SIZE = 5000
FIELDS = [
    "a_i_num", "adr_for", "area_type", "site_type", "stand_stru", "prot_categ", "forest_fun",
    "species_cd", "part_cd", "spec_age", "sub_area", "a_year", "nazwa",
]


def _bbox_param(bounds) -> str:
    # WFS 2.0 + urn CRS uses the EPSG axis order of 2180: northing first (see DATA_SOURCES.md).
    minx, miny, maxx, maxy = bounds
    return f"{miny},{minx},{maxy},{maxx},urn:ogc:def:crs:EPSG::2180"


def _hits(layer: str, bounds) -> int:
    params = dict(service="WFS", version="2.0.0", request="GetFeature", typeNames=f"BDL:RDLP_{layer}_wydzielenia",
                  resultType="hits", bbox=_bbox_param(bounds))
    match = re.search(r'numberMatched="(\d+)"', get(WFS_URL, params).text)
    return int(match.group(1)) if match else 0


def _page(layer: str, bounds, start: int) -> dict:
    path = CACHE_DIR / "bdl" / layer / f"{_bbox_key(bounds)}_{start:07d}.json.gz"
    if path.exists():
        return json.loads(gzip.decompress(path.read_bytes()))
    params = dict(service="WFS", version="2.0.0", request="GetFeature", typeNames=f"BDL:RDLP_{layer}_wydzielenia",
                  outputFormat="application/json", bbox=_bbox_param(bounds), sortBy="a_i_num",
                  count=PAGE_SIZE, startIndex=start)
    data = get(WFS_URL, params, timeout=300).json()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(data).encode()))
    return data


def _bbox_key(bounds) -> str:
    return "_".join(str(int(v)) for v in bounds)


def fetch_stands(region: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    """All stands intersecting the region polygon (EPSG:2180) and a source record."""
    bounds = tuple(region.total_bounds)
    frames, layers_used = [], {}
    for layer in RDLP_LAYERS:
        n = _hits(layer, bounds)
        if n == 0:
            continue
        layers_used[layer] = n
        log.info("BDL %s: %d stands in region bbox", layer, n)
        for start in range(0, n, PAGE_SIZE):
            feats = _page(layer, bounds, start)["features"]
            if feats:
                gdf = gpd.GeoDataFrame.from_features(feats, crs=2180)
                gdf["rdlp"] = layer
                frames.append(gdf)
            log.info("  %s: %d/%d", layer, min(start + PAGE_SIZE, n), n)
    stands = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=2180)
    stands = stands.drop_duplicates(subset=["a_i_num"])
    stands = stands[stands.intersects(region.geometry.iloc[0])].reset_index(drop=True)
    years = sorted(stands["a_year"].dropna().astype(int).unique().tolist())
    source = {
        "name": "Bank Danych o Lasach (BDL), Lasy Państwowe",
        "url": WFS_URL,
        "layers": {f"BDL:RDLP_{k}_wydzielenia": v for k, v in layers_used.items()},
        "data_years": years,
        "downloaded": _cache_date(layers_used),
        "features_in_region": int(len(stands)),
    }
    return stands[FIELDS + ["rdlp", "geometry"]], source


def _cache_date(layers: dict) -> str:
    """Date of the oldest cached page (BDL requires stating the download date)."""
    dates = [
        date.fromtimestamp(p.stat().st_mtime)
        for layer in layers
        for p in (CACHE_DIR / "bdl" / layer).glob("*.json.gz")
    ]
    return min(dates).isoformat() if dates else date.today().isoformat()
