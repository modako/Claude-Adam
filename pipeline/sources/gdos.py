"""National parks and nature reserves from GDOŚ (hand-downloaded, see data/manual/gdos/SOURCES.md)."""

import geopandas as gpd
import pandas as pd

from pipeline.paths import MANUAL_DIR

LAYERS = {
    "park_narodowy": ("ParkiNarodowe.zip", "ParkiNarodowePolygon.shp"),
    "rezerwat": ("Rezerwaty.zip", "RezerwatyPolygon.shp"),
}
DOWNLOADED = "2026-10-05"
ATTRIBUTION = f"Formy ochrony przyrody: Generalna Dyrekcja Ochrony Środowiska, dane pobrane {DOWNLOADED}"


def protected_areas(region: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Parks and reserves (buffer zones excluded) intersecting the region, EPSG:2180."""
    frames = []
    for kind, (zip_name, shp) in LAYERS.items():
        gdf = gpd.read_file(f"zip://{MANUAL_DIR / 'gdos' / zip_name}!{shp}", encoding="cp1250").to_crs(2180)
        # Buffer zones ("otulina") share the layer with the protected area itself but are not a ban.
        gdf = gdf[~gdf["nazwa"].str.contains("otulina", case=False, na=False)]
        gdf = gdf.assign(kind=kind, name=gdf["nazwa"], geometry=gdf.geometry.make_valid())
        frames.append(gdf[["kind", "name", "geometry"]])
    out = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=2180)
    return out[out.intersects(region.geometry.iloc[0])].reset_index(drop=True)
