"""Region outline from geoBoundaries (POL ADM1, OSM-derived, ODbL)."""

import geopandas as gpd

from pipeline.paths import CACHE_DIR
from pipeline.sources.http import get

ADM1_URL = (
    "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/"
    "releaseData/gbOpen/POL/ADM1/geoBoundaries-POL-ADM1.geojson"
)
ATTRIBUTION = "Granice województw: geoBoundaries (POL ADM1), © autorzy OpenStreetMap, ODbL"


def region_polygon(voivodeships: list[str]) -> gpd.GeoDataFrame:
    """Dissolved region polygon in EPSG:2180."""
    path = CACHE_DIR / "boundaries" / "pol_adm1.geojson"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(get(ADM1_URL).content)
    adm1 = gpd.read_file(path)
    missing = set(voivodeships) - set(adm1["shapeName"])
    if missing:
        raise ValueError(f"Unknown voivodeships in region config: {sorted(missing)}")
    sel = adm1[adm1["shapeName"].isin(voivodeships)].to_crs(2180)
    return gpd.GeoDataFrame(geometry=[sel.union_all()], crs=2180)
