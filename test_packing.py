"""
Testy poprawności algorytmu pakowania.

Uruchomienie (bez żadnych zależności poza standardową biblioteką):
    python3 test_packing.py
Działa też pod pytest:
    pytest test_packing.py
"""

from __future__ import annotations

import carton_fit as cf
from packing import Container, ProductType, pack, validate


def test_rotation_flag_is_respected():
    """Produkt z rotatable=False nie może zmienić orientacji."""
    carton = Container(40, 40, 60)
    products = [
        ProductType("A", 10, 10, 4, 50, rotatable=True),
        ProductType("B", 15, 10, 8, 20, rotatable=False),
    ]
    result = pack(carton, products)
    for p in result.placements:
        if p.product == "B":
            assert (p.dx, p.dy, p.dz) == (15, 10, 8), f"Produkt B obrócony: {p}"


def test_no_collisions_and_inside_carton():
    """Nic nie wystaje poza karton i nic się nie przenika."""
    carton = Container(30, 30, 30)
    products = [
        ProductType("A", 12, 8, 5, 60, rotatable=True),
        ProductType("B", 7, 7, 20, 25, rotatable=False),
        ProductType("C", 4, 4, 4, 80, rotatable=True),
    ]
    result = pack(carton, products)
    assert validate(result) == []
    assert result.fill_ratio > 0.8, f"słabe wypełnienie: {result.fill_ratio:.2%}"


def test_quantities_are_not_exceeded():
    """Nie da się zapakować więcej sztuk, niż jest dostępnych."""
    carton = Container(100, 100, 100)
    products = [ProductType("A", 10, 10, 10, 5, rotatable=True)]
    result = pack(carton, products)
    assert result.packed_counts["A"] == 5
    assert result.unpacked_counts["A"] == 0


def test_oversized_product_is_reported_as_unpacked():
    """Produkt większy niż karton trafia na listę niezapakowanych."""
    carton = Container(10, 10, 10)
    products = [
        ProductType("za duży", 20, 5, 5, 3, rotatable=True),
        ProductType("pasuje", 5, 5, 5, 4, rotatable=True),
    ]
    result = pack(carton, products)
    assert result.unpacked_counts["za duży"] == 3
    assert result.packed_counts["pasuje"] == 4


def test_rotation_enables_a_fit_that_is_impossible_without_it():
    """Produkt 10x10x30 wejdzie do kartonu 30x10x10 tylko po obrocie."""
    carton = Container(30, 10, 10)
    fixed = pack(carton, [ProductType("p", 10, 10, 30, 1, rotatable=False)])
    rotatable = pack(carton, [ProductType("p", 10, 10, 30, 1, rotatable=True)])
    assert fixed.packed_counts["p"] == 0
    assert rotatable.packed_counts["p"] == 1


def test_perfect_fill():
    """Osiem kostek 5x5x5 wypełnia karton 10x10x10 w 100%."""
    result = pack(Container(10, 10, 10),
                  [ProductType("kostka", 5, 5, 5, 8, rotatable=True)],
                  support_ratio=1.0)
    assert len(result.placements) == 8
    assert abs(result.fill_ratio - 1.0) < 1e-9


def test_support_constraint_leaves_nothing_floating():
    """Każdy produkt stoi na dnie albo ma wymagane podparcie od dołu."""
    carton = Container(30, 30, 30)
    products = [ProductType("A", 12, 8, 5, 40, rotatable=True),
                ProductType("B", 9, 9, 7, 20, rotatable=True)]
    result = pack(carton, products, support_ratio=0.7)
    for p in result.placements:
        if p.z == 0:
            continue
        supported = 0.0
        for q in result.placements:
            if q is p or abs(q.z + q.dz - p.z) > 1e-6:
                continue
            ox = min(p.x + p.dx, q.x + q.dx) - max(p.x, q.x)
            oy = min(p.y + p.dy, q.y + q.dy) - max(p.y, q.y)
            if ox > 0 and oy > 0:
                supported += ox * oy
        assert supported / (p.dx * p.dy) >= 0.7 - 1e-9, f"lewitujący produkt: {p}"


def test_example_from_the_brief_packs_everything():
    """Dane z zadania: wszystkie 70 sztuk musi się zmieścić."""
    result = pack(Container(40, 40, 60),
                  [ProductType("Produkt A", 10, 10, 4, 50, rotatable=True),
                   ProductType("Produkt B", 15, 10, 8, 20, rotatable=False)])
    assert len(result.placements) == 70
    assert validate(result) == []




# ---------------------------------------------------------------------------
# Testy modułu carton_fit (ile sztuk płaskiego produktu wejdzie do kartonu)
# ---------------------------------------------------------------------------



def test_flat_size_parsing():
    """Rozmiar płaski rozpoznany, trójwymiarowy odrzucony."""
    assert cf.parse_flat_size("ca.37x25 cm") == (37.0, 25.0)
    assert cf.parse_flat_size("ca. 22,5x32,5 cm") == (22.5, 32.5)
    assert cf.parse_flat_size("ca. 53x40x10cm") is None   # ma fałdę
    assert cf.parse_flat_size("Ø ca. 9 cm") is None
    assert cf.parse_flat_size("") is None


def test_thickness_of_laminate_is_a_sum():
    """Laminat 'A + B' to suma grubości warstw, nie podwojona jedna z nich."""
    assert cf.parse_thickness("wool felt 3mm").mm == 3.0
    assert cf.parse_thickness("recycled leather + wool felt 3mm").mm == 3.6
    assert cf.parse_thickness("recycled leather 0,6mm").mm == 0.6


def test_thickness_flags_unknown_component():
    """Nieznana grubość składnika musi być zgłoszona, a nie zgadnięta."""
    t = cf.parse_thickness("washable paper + wool felt  3mm")
    assert t.mm == 3.0
    assert "washable paper" in t.unknown_parts
    assert cf.parse_thickness("washable paper").mm is None


def test_layer_packing_matches_hand_count():
    """Układ warstwy zgodny z ręcznym przeliczeniem."""
    C = cf.CM
    assert cf.max_fit_2d(40 * C, 50 * C, 10 * C, 10 * C) == 20   # 4 x 5
    assert cf.max_fit_2d(40 * C, 50 * C, 37 * C, 25 * C) == 2
    assert cf.max_fit_2d(40 * C, 50 * C, 12 * C, 12 * C) == 12   # 3 x 4
    # 15x10: 2x5 w bloku + 3 obrócone w pasku przy ściance
    assert cf.max_fit_2d(40 * C, 50 * C, 15 * C, 10 * C) == 13


def test_carton_count_is_layers_times_layer():
    """Wynik to iloczyn sztuk na warstwie i liczby warstw."""
    f = cf.fit_in_carton((40, 50, 60), (37, 25, 0.4))   # filc 4 mm
    assert f.per_layer == 2 and f.layers == 150 and f.count == 300


def test_item_larger_than_carton_gives_zero():
    assert cf.fit_in_carton((40, 50, 60), (60, 60, 1.0)).count == 0


def test_flat_stacking_never_beats_free_orientation():
    """Wariant 'na płasko' jest zachowawczy wobec optimum geometrycznego."""
    item = (12, 12, 0.36)
    assert (cf.fit_in_carton((40, 50, 60), item, flat_only=True).count
            <= cf.fit_in_carton((40, 50, 60), item, flat_only=False).count)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  OK   {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"  BŁĄD {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} testów przeszło.")
    raise SystemExit(1 if failures else 0)
