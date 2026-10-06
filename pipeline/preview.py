"""Single-file HTML preview of the forest cells (MapLibre GL JS, data inlined)."""

import json
from pathlib import Path

import geopandas as gpd

ASSETS = Path(__file__).resolve().parent / "assets"
TEMPLATE = Path(__file__).resolve().parent / "preview_template.html"


def write_preview(geojson: dict, region: gpd.GeoDataFrame, places: list[dict], stats: dict, dates: dict,
                  path: Path) -> None:
    outline = region.simplify(200).to_crs(4326)
    region_obj = {"bbox": [round(v, 4) for v in outline.total_bounds],
                  "geojson": json.loads(outline.to_json())}
    html = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "/*__MAPLIBRE_CSS__*/": (ASSETS / "maplibre-gl-4.7.1.css").read_text(encoding="utf-8"),
        "/*__CELLS__*/null": _js(geojson),
        "/*__REGION__*/null": _js(region_obj),
        "/*__PLACES__*/[]": _js(places),
        "/*__STATS__*/{}": _js(stats),
        "__PARAMS__": geojson["params_version"],
        "__GENERATED__": geojson["generated_at"][:10],
        "__BDL_DATE__": dates["bdl"],
        "__GDOS_DATE__": dates["gdos"],
    }
    for key, value in replacements.items():
        html = html.replace(key, value)
    path.write_text(html, encoding="utf-8")


def _js(obj) -> str:
    # "</" inside inline JSON would end the <script> element.
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
