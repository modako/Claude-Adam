"""OpenStreetMap layers extracted by .github/workflows/osm-extract.yml (data/manual/osm/)."""

import re
import zipfile

import geopandas as gpd

from pipeline.paths import CACHE_DIR, MANUAL_DIR

ATTRIBUTION = "© autorzy OpenStreetMap, ODbL 1.0"


def _layer(name: str) -> gpd.GeoDataFrame:
    target = CACHE_DIR / "osm" / f"{name}.gpkg"
    archive = MANUAL_DIR / "osm" / "osm_layers.zip"
    if not target.exists() or target.stat().st_mtime < archive.stat().st_mtime:
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as zf:
            target.write_bytes(zf.read(f"{name}.gpkg"))
    return gpd.read_file(target).to_crs(2180)


def _tag(other_tags, key: str) -> str | None:
    if not isinstance(other_tags, str):
        return None
    match = re.search(rf'"{key}"=>"([^"]*)"', other_tags)
    return match.group(1) if match else None


def data_timestamp() -> str:
    with zipfile.ZipFile(MANUAL_DIR / "osm" / "osm_layers.zip") as zf:
        return zf.read("timestamp.txt").decode().strip()


def military(region: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = _layer("military")
    is_military = (gdf["landuse"] == "military") | gdf["other_tags"].map(lambda t: _tag(t, "military") is not None)
    gdf = gdf[is_military]
    gdf = gdf.assign(kind="wojsko", geometry=gdf.geometry.make_valid())
    return gdf[gdf.intersects(region.geometry.iloc[0])][["kind", "name", "geometry"]].reset_index(drop=True)


def forests(region: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = _layer("forest")
    gdf = gdf[(gdf["landuse"] == "forest") | (gdf["natural"] == "wood")]
    leaf = gdf["other_tags"].map(lambda t: _tag(t, "leaf_type"))
    gdf = gdf.assign(leaf_type=leaf.where(leaf.isin(["needleleaved", "broadleaved", "mixed"]), "unknown"),
                     geometry=gdf.geometry.make_valid())
    return gdf[gdf.intersects(region.geometry.iloc[0])][["osm_id", "osm_way_id", "leaf_type", "geometry"]]
