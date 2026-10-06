import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from pipeline import cells
from pipeline.params import model_params

P = model_params()


@pytest.mark.parametrize("lat,lng,expected", [(51.76, 19.46, "51.8_19.5"), (51.74, 19.44, "51.7_19.4"),
                                              (52.0, 20.0, "52.0_20.0")])
def test_weather_point(lat, lng, expected):
    assert cells.weather_point(lat, lng, 0.1) == expected


def _units(rows):
    df = pd.DataFrame(rows)
    for sp in P["species"]:
        df[f"h_{sp}"] = df.pop("h") if sp == P["species"][0] else df[f"h_{P['species'][0]}"]
    return gpd.GeoDataFrame(df, geometry="geometry", crs=2180)


def _region():
    # ~3 x 3 km square near Łódź (EPSG:2180)
    return gpd.GeoDataFrame(geometry=[box(530000, 380000, 533000, 383000)], crs=2180)


def test_ban_mask_and_weighting():
    region = _region()
    units = _units([
        dict(source="lp", tree="So", age=60.0, site_type="BŚW", unit_ban=None, h=1.0,
             geometry=box(530000, 380000, 533000, 381500)),
        dict(source="lp", tree="So", age=5.0, site_type="BŚW", unit_ban="uprawa", h=0.0,
             geometry=box(530000, 381500, 533000, 383000)),
    ])
    mask = gpd.GeoDataFrame({"kind": ["rezerwat"]}, geometry=[box(530000, 380000, 531000, 381500)], crs=2180)
    out = cells.build_cells(units, mask, region, P)
    assert not out.empty
    # Banned area (crop or reserve) never contributes to H, so free forest keeps H = 1.0.
    free = out[out["ban_share"] < 1]
    assert (free["h_max"].round(6) == 1.0).all()
    assert out["banned"].any()
    reasons = {r for rs in out["ban_reasons"] for r in rs}
    assert {"rezerwat przyrody", "uprawa leśna (młodnik do ok. 4 m)"} <= reasons


def test_private_flag():
    region = _region()
    units = _units([dict(source="non_lp", tree=None, age=float("nan"), site_type=None, unit_ban=None, h=0.3,
                         geometry=box(530000, 380000, 533000, 383000))])
    empty_mask = gpd.GeoDataFrame({"kind": []}, geometry=[], crs=2180)
    out = cells.build_cells(units, empty_mask, region, P)
    assert out["private_maybe"].all()
    assert not out["banned"].any()
