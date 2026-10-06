import pytest

from pipeline import suitability as s
from pipeline.params import model_params

P = model_params()


def test_params_mirror_spec_basics():
    assert P["params_version"] == "0.2.0"
    assert len(P["species"]) == 9
    for table in ("tree", "age_nodes", "habitat"):
        assert set(P[table]) == set(P["species"])


@pytest.mark.parametrize("code,group", [("SO", "So"), ("DB.B", "Db"), ("BRZ.O", "Brz"), ("ŚW", "Św"),
                                        ("JW", "inne"), (None, "inne"), ("ol", "Ol")])
def test_tree_group(code, group):
    assert s.tree_group(code, P) == group


def test_borowik_values_from_research():
    # SPEC 3.2-3.4 [R]: So/Św/Bk/Db = 1.0, Brz = 0.6, Ol = 0.1; age 30-80 = 1.0, 15 = 0.6, >120 = 0.7;
    # BŚW/BMŚW/LMŚW = 1.0, BB/OL = 0.2.
    assert s.suit_tree("borowik", "BK", 10, P) == 1.0
    assert s.suit_tree("borowik", "BRZ", 10, P) == 0.6
    assert s.suit_tree("borowik", "OL", 10, P) == 0.1
    assert s.suit_age("borowik", 50, P) == 1.0
    assert s.suit_age("borowik", 15, P) == 0.6
    assert s.suit_age("borowik", 150, P) == 0.7
    assert s.suit_habitat("borowik", "BMŚW", P) == 1.0
    assert s.suit_habitat("borowik", "BB", P) == 0.2
    assert s.suit_habitat("borowik", "OL", P) == 0.2


def test_interp_nodes():
    nodes = [[10, 0.3], [15, 0.6], [30, 1.0]]
    assert s.interp_nodes(0, nodes) == 0.3
    assert s.interp_nodes(12.5, nodes) == pytest.approx(0.45)
    assert s.interp_nodes(22.5, nodes) == pytest.approx(0.8)
    assert s.interp_nodes(99, nodes) == 1.0


def test_share_blends_with_other_trees():
    # 60% pine, rest "inne" (0.3 for borowik): 0.6*1.0 + 0.4*0.3
    assert s.suit_tree("borowik", "SO", 6, P) == pytest.approx(0.72)
    # missing share = pure stand
    assert s.suit_tree("borowik", "SO", None, P) == 1.0


def test_unknown_habitat_uses_default():
    assert s.suit_habitat("kurka", None, P) == P["hab_default"]
    assert s.suit_habitat("kurka", "BWG", P) == P["hab_default"]
    assert s.suit_habitat("kurka", " bśw ", P) == 1.0


def test_crop_is_zero_for_all_species():
    h = s.h_all(dict(dominant_code="SO", share_tenths=10, age=8, site_type="BŚW"), P)
    assert all(v == 0.0 for v in h.values())


def test_pine_60y_fresh_pine_forest():
    h = s.h_all(dict(dominant_code="SO", share_tenths=10, age=60, site_type="BŚW"), P)
    assert h["podgrzybek"] == 1.0
    assert h["borowik"] == 1.0
    # koźlarz: pine 0.2, age 60 between nodes 50: 1.0 and 80: 0.6, BŚW 0.8
    assert h["kozlarz"] == pytest.approx(0.2 * (1.0 - 0.4 * 10 / 30) * 0.8)
    assert h["h_max"] == 1.0
    assert all(0.0 <= v <= 1.0 for v in h.values())


def test_young_pine_favours_maslak_over_podgrzybek():
    h = s.h_all(dict(dominant_code="SO", share_tenths=10, age=20, site_type="BS"), P)
    assert h["maslak"] > h["podgrzybek"]


def test_birch_wet_forest_favours_kozlarz():
    h = s.h_all(dict(dominant_code="BRZ", share_tenths=8, age=30, site_type="BW"), P)
    assert max(P["species"], key=lambda sp: h[sp]) == "kozlarz"


def test_non_lp_forest_is_capped_by_unknowns():
    for leaf in ("needleleaved", "broadleaved", "mixed", None, "weird"):
        for sp in P["species"]:
            h = s.h_non_lp(sp, leaf, P)
            assert 0.0 <= h <= P["non_lp"]["age_factor"] * P["hab_default"]
    assert s.h_non_lp("podgrzybek", "needleleaved", P) > s.h_non_lp("podgrzybek", "broadleaved", P)
