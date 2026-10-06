"""H3 forest cells: habitat potential H, legal mask and stand description (docs/SPEC.md, chapters 3 and 6)."""

import logging

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import Polygon

from pipeline import suitability as s

log = logging.getLogger(__name__)

# Mask reasons, in the order shown to the user.
BAN_LABELS = {
    "park_narodowy": "park narodowy",
    "rezerwat": "rezerwat przyrody",
    "wojsko": "teren wojskowy",
    "uprawa": "uprawa leśna (młodnik do ok. 4 m)",
    "OCH OSTOJ": "ostoja zwierząt",
    "OCH NAS": "drzewostan nasienny",
    "OCH BADAW": "powierzchnia doświadczalna",
    "REZ": "rezerwat (wg BDL)",
}


def lp_units(stands: gpd.GeoDataFrame, params: dict) -> gpd.GeoDataFrame:
    """State Forest stands (area_type D-STAN) with H per species and unit-level bans."""
    st = stands[stands["area_type"] == "D-STAN"].copy()
    age = st["spec_age"].astype("float")
    share = pd.to_numeric(st["part_cd"], errors="coerce")
    for sp in params["species"]:
        st[f"h_{sp}"] = [
            s.h_stand(sp, code, None if np.isnan(sh) else int(sh), None if np.isnan(a) else a, site, params)
            for code, sh, a, site in zip(st["species_cd"], share, age, st["site_type"])
        ]
    ban = pd.Series(None, index=st.index, dtype="object")
    ban[st["forest_fun"].isin(params["bdl_ban_forest_fun"])] = "REZ"
    ban[st["prot_categ"].isin(params["bdl_ban_prot_categ"])] = st["prot_categ"]
    ban[age.le(params["crop_age_max"])] = "uprawa"
    st["unit_ban"] = ban
    st["source"] = "lp"
    st["tree"] = [s.tree_group(c, params) for c in st["species_cd"]]
    st["age"] = age
    return st[["source", "tree", "age", "site_type", "unit_ban", *[f"h_{sp}" for sp in params["species"]], "geometry"]]


def non_lp_units(forests: gpd.GeoDataFrame, stands: gpd.GeoDataFrame, params: dict) -> gpd.GeoDataFrame:
    """OSM forests outside the State Forest stands (any BDL land type), flagged as possibly private."""
    rest = forests.reset_index(drop=True)
    lp = stands.geometry.make_valid().reset_index(drop=True)
    # Subtract only the stands that touch each OSM polygon (one union of the whole BDL layer is far too slow).
    left, right = lp.sindex.query(rest.geometry, predicate="intersects")
    touching = pd.Series(right).groupby(left).apply(list)
    geoms = rest.geometry.to_numpy().copy()
    for i, idx in touching.items():
        geoms[i] = geoms[i].difference(shapely.union_all(lp.iloc[idx].to_numpy()))
    rest = rest.set_geometry(gpd.GeoSeries(geoms, crs=2180))
    rest = rest[~rest.geometry.is_empty]
    rest = rest.explode(index_parts=False)
    rest = rest[rest.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    rest = rest[rest.area >= params["non_lp"]["min_area_m2"]].copy()
    # Overlapping OSM polygons (landuse=forest + natural=wood) must not be counted twice:
    # dissolve per leaf type, then give overlaps to the more specific leaf type.
    parts, taken = [], None
    for leaf in ["needleleaved", "broadleaved", "mixed", "unknown"]:
        sel = rest[rest["leaf_type"] == leaf]
        if sel.empty:
            continue
        geom = sel.geometry.union_all()
        if taken is not None:
            geom = geom.difference(taken)
        taken = geom if taken is None else taken.union(geom)
        parts.append(gpd.GeoDataFrame({"leaf_type": [leaf]}, geometry=[geom], crs=2180))
    rest = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=2180).explode(index_parts=False)
    rest = rest[rest.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    rest = rest[rest.area >= params["non_lp"]["min_area_m2"]].reset_index(drop=True)
    for sp in params["species"]:
        rest[f"h_{sp}"] = [s.h_non_lp(sp, lt, params) for lt in rest["leaf_type"]]
    rest = rest.assign(source="non_lp", tree=None, age=np.nan, site_type=None, unit_ban=None)
    return rest[["source", "tree", "age", "site_type", "unit_ban", *[f"h_{sp}" for sp in params["species"]], "geometry"]]


def hexagons(region: gpd.GeoDataFrame, resolution: int) -> gpd.GeoDataFrame:
    """H3 cells overlapping the region, as polygons in EPSG:2180."""
    poly = region.to_crs(4326).geometry.iloc[0]
    parts = poly.geoms if poly.geom_type == "MultiPolygon" else [poly]
    ids = set()
    for part in parts:
        shape = h3.LatLngPoly([(y, x) for x, y in part.exterior.coords],
                              *[[(y, x) for x, y in ring.coords] for ring in part.interiors])
        ids.update(h3.polygon_to_cells_experimental(shape, resolution, contain="overlap"))
    ids = sorted(ids)
    geoms = [Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)]) for c in ids]
    return gpd.GeoDataFrame({"cell": ids}, geometry=geoms, crs=4326).to_crs(2180)


def build_cells(units: gpd.GeoDataFrame, mask: gpd.GeoDataFrame, region: gpd.GeoDataFrame, params: dict) -> pd.DataFrame:
    """Aggregate forest units to H3 cells. Returns one row per cell with forest."""
    species = params["species"]
    hexes = hexagons(region, params["h3_resolution"])
    log.info("H3 cells overlapping region: %d", len(hexes))

    units = units.reset_index(drop=True)
    units["uid"] = units.index
    pieces = gpd.overlay(units, hexes, how="intersection", keep_geom_type=True)
    pieces = pieces[pieces.intersects(region.geometry.iloc[0])]
    pieces["area"] = pieces.area
    log.info("Forest pieces after cutting by cells: %d", len(pieces))

    # Geometric mask (parks, reserves, military): masked area of each piece, by reason.
    pieces["pid"] = np.arange(len(pieces))
    masked = gpd.overlay(pieces[["pid", "geometry"]], mask[["kind", "geometry"]], how="intersection",
                         keep_geom_type=True)
    masked["marea"] = masked.area
    by_reason = masked.groupby(["pid", "kind"])["marea"].sum().unstack(fill_value=0.0)
    geo_masked = by_reason.sum(axis=1).reindex(pieces["pid"]).fillna(0.0).clip(upper=pieces["area"].values)
    pieces["geo_masked"] = geo_masked.values
    # Unit-level bans (crop, animal refuge, seed stand...) cover the whole piece.
    pieces["ban_area"] = np.where(pieces["unit_ban"].notna(), pieces["area"], pieces["geo_masked"])
    pieces["free_area"] = pieces["area"] - pieces["ban_area"]

    rows = []
    reasons_geo = by_reason.reindex(pieces["pid"]).fillna(0.0)
    reasons_geo.index = pieces.index
    for cell, grp in pieces.groupby("cell"):
        forest = grp["area"].sum()
        if forest < params["min_cell_forest_m2"]:
            continue
        free = grp["free_area"].sum()
        ban_share = grp["ban_area"].sum() / forest
        row = {"cell": cell, "forest_ha": forest / 1e4, "ban_share": ban_share,
               "banned": ban_share > params["ban_share_threshold"]}

        reasons = {}
        for code, area in grp.loc[grp["unit_ban"].notna()].groupby("unit_ban")["area"].sum().items():
            reasons[code] = reasons.get(code, 0.0) + area
        for code in reasons_geo.columns:
            area = reasons_geo.loc[grp.index, code].where(grp["unit_ban"].isna(), 0.0).sum()
            if area > 0:
                reasons[code] = reasons.get(code, 0.0) + area
        row["ban_reasons"] = [BAN_LABELS[c] for c, a in sorted(reasons.items(), key=lambda kv: -kv[1])
                              if a / forest >= 0.05]

        weights = grp["free_area"].to_numpy()
        for sp in species:
            row[f"h_{sp}"] = float(np.dot(grp[f"h_{sp}"], weights) / free) if free > 0 else 0.0
        row["h_max"] = max(row[f"h_{sp}"] for sp in species)

        non_lp = grp.loc[grp["source"] == "non_lp", "area"].sum()
        row["non_lp_share"] = non_lp / forest
        row["private_maybe"] = row["non_lp_share"] >= 0.5

        lp = grp[grp["source"] == "lp"]
        row["trees"] = _tree_summary(lp)
        aged = lp[lp["age"].notna()]
        row["age_mean"] = float(np.average(aged["age"], weights=aged["area"])) if aged["area"].sum() > 0 else None
        row["habitat"] = lp.groupby("site_type")["area"].sum().idxmax() if lp["site_type"].notna().any() else None
        rows.append(row)
    cells = pd.DataFrame(rows)
    log.info("Cells with forest: %d", len(cells))
    return cells


def _tree_summary(lp: pd.DataFrame) -> str | None:
    """Dominant species by area, e.g. 'So 78%, Db 12%, Brz 6%' (State Forest part only)."""
    if lp.empty:
        return None
    shares = lp.groupby("tree")["area"].sum() / lp["area"].sum()
    top = shares.sort_values(ascending=False).head(3)
    return ", ".join(f"{t} {round(v * 100)}%" for t, v in top.items() if v >= 0.05)


def weather_point(lat: float, lng: float, step: float) -> str:
    """Id of the nearest weather grid point, e.g. '51.8_19.4'."""
    decimals = max(0, -int(np.floor(np.log10(step))))
    return f"{round(round(lat / step) * step, decimals):.{decimals}f}_{round(round(lng / step) * step, decimals):.{decimals}f}"
