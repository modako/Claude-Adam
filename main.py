"""
Optymalne pakowanie produktów do kartonu (3D bin packing) - skrypt uruchomieniowy.

Dane wejściowe zdefiniowane są jako zwykłe zmienne na górze pliku.
Logika pakowania siedzi w packing.py, rysowanie w visualization.py.

Uruchomienie:
    python3 main.py
"""

from __future__ import annotations

import time

import packing
import visualization
from packing import Container, ProductType

# ===========================================================================
# DANE WEJŚCIOWE  <- tutaj zmieniasz karton i listę produktów
# ===========================================================================

CARTON = Container(length=40, width=40, height=60, name="Karton")

PRODUCTS = [
    ProductType(
        name="Produkt A",
        length=10, width=10, height=4,     # cm
        quantity=50,                       # ile sztuk mam do spakowania
        rotatable=True,                    # można obracać we wszystkich osiach
    ),
    ProductType(
        name="Produkt B",
        length=15, width=10, height=8,
        quantity=20,
        rotatable=False,                   # musi stać "górą do góry"
    ),
]

# Minimalny ułamek podstawy produktu, który musi opierać się na podłodze
# kartonu lub na innym produkcie. 0.7 = co najmniej 70% podparcia.
SUPPORT_RATIO = 0.7

# Pliki wyjściowe z wizualizacją
OUTPUT_MAIN = "packing_3d.png"
OUTPUT_VIEWS = "packing_views.png"
OUTPUT_LAYERS = "packing_layers.png"


# ===========================================================================
# RAPORT TEKSTOWY
# ===========================================================================


def print_input(container: Container, products, support_ratio: float) -> None:
    print("=" * 78)
    print("DANE WEJŚCIOWE")
    print("=" * 78)
    print(f"{container.name}: {container.length:g} x {container.width:g} x "
          f"{container.height:g} cm   (objętość {container.volume:,.0f} cm3)"
          .replace(",", " "))
    print(f"Wymagane podparcie podstawy: {support_ratio * 100:.0f}%")
    print()
    print(f"{'Produkt':<12}{'Wymiary [cm]':<20}{'Szt.':>6}{'Obrót':>10}"
          f"{'Objętość razem':>18}")
    print("-" * 78)
    total = 0.0
    for p in products:
        total += p.total_volume
        print(f"{p.name:<12}"
              f"{f'{p.length:g} x {p.width:g} x {p.height:g}':<20}"
              f"{p.quantity:>6}"
              f"{('tak' if p.rotatable else 'nie'):>10}"
              f"{p.total_volume:>15,.0f} cm3".replace(",", " "))
    print("-" * 78)
    print(f"Łączna objętość produktów: {total:,.0f} cm3 "
          f"= {total / container.volume * 100:.2f}% objętości kartonu"
          .replace(",", " "))
    print("(to jest teoretyczna górna granica wypełnienia, bez uwzględnienia "
          "kształtów)")
    print()


def print_placements(result: packing.PackingResult) -> None:
    print("=" * 78)
    print("CO SIĘ ZMIEŚCIŁO - lista ułożonych sztuk")
    print("=" * 78)
    print(f"{'#':>4}  {'Produkt':<12}{'poz. X':>8}{'poz. Y':>8}{'poz. Z':>8}"
          f"{'  wymiary po obrocie':<24}{'orientacja':<16}")
    print("-" * 78)
    # sortujemy warstwami od dołu - tak jak realnie układałby to człowiek
    ordered = sorted(result.placements, key=lambda p: (p.z, p.y, p.x, p.product))
    for i, p in enumerate(ordered, start=1):
        print(f"{i:>4}  {p.product:<12}{p.x:>8g}{p.y:>8g}{p.z:>8g}"
              f"{f'  {p.dx:g} x {p.dy:g} x {p.dz:g}':<24}{p.orientation:<16}")
    print()
    print("Pozycja = współrzędne lewego-przedniego-dolnego narożnika produktu.")
    print("Orientacja = która oryginalna krawędź leży wzdłuż osi X, Y i Z")
    print("             (D = długość, S = szerokość, W = wysokość produktu).")
    print()


def print_summary(result: packing.PackingResult, elapsed: float) -> None:
    unpacked = result.unpacked_counts
    packed = result.packed_counts

    print("=" * 78)
    print("CO SIĘ NIE ZMIEŚCIŁO")
    print("=" * 78)
    leftovers = {name: n for name, n in unpacked.items() if n > 0}
    if not leftovers:
        print("Nic - wszystkie produkty zmieściły się w kartonie.")
    else:
        for name, n in leftovers.items():
            product = next(p for p in result.products if p.name == name)
            print(f"{name:<12} {n} szt. "
                  f"(pozostała objętość {n * product.volume:,.0f} cm3)"
                  .replace(",", " "))
    print()

    print("=" * 78)
    print("PODSUMOWANIE")
    print("=" * 78)
    print(f"{'Produkt':<12}{'zapakowano':>12}{'nie weszło':>12}"
          f"{'dostępnych':>12}{'objętość':>16}")
    print("-" * 78)
    for product in result.products:
        n = packed.get(product.name, 0)
        print(f"{product.name:<12}{n:>12}{unpacked[product.name]:>12}"
              f"{product.quantity:>12}{n * product.volume:>13,.0f} cm3"
              .replace(",", " "))
    print("-" * 78)
    total_qty = sum(p.quantity for p in result.products)
    print(f"{'RAZEM':<12}{len(result.placements):>12}"
          f"{total_qty - len(result.placements):>12}{total_qty:>12}"
          f"{result.packed_volume:>13,.0f} cm3".replace(",", " "))
    print()
    print(f"Objętość kartonu:             {result.container.volume:,.0f} cm3"
          .replace(",", " "))
    print(f"Objętość zapakowana:          {result.packed_volume:,.0f} cm3"
          .replace(",", " "))
    print(f"WYKORZYSTANIE OBJĘTOŚCI:      {result.fill_ratio * 100:.2f} %")
    print(f"Wysokość zajętego stosu:      {result.max_used_height:g} cm "
          f"z {result.container.height:g} cm")
    print(f"Wybrana strategia:            {result.strategy}")
    print(f"Czas obliczeń:                {elapsed:.2f} s")
    print()


def main() -> packing.PackingResult:
    print_input(CARTON, PRODUCTS, SUPPORT_RATIO)

    print("=" * 78)
    print("PRZEBIEG OPTYMALIZACJI (multi-start: kolejność x sposób oceny miejsca)")
    print("=" * 78)
    start = time.perf_counter()
    result = packing.pack(CARTON, PRODUCTS, support_ratio=SUPPORT_RATIO,
                          verbose=True)
    elapsed = time.perf_counter() - start
    print()

    # Kontrola poprawności: nic nie wystaje poza karton i nic się nie przenika.
    problems = packing.validate(result)
    print("=" * 78)
    print("WALIDACJA WYNIKU")
    print("=" * 78)
    if problems:
        for problem in problems:
            print(f"  BŁĄD: {problem}")
    else:
        print("  OK - żaden produkt nie wystaje poza karton i nie ma kolizji.")
    print()

    print_placements(result)
    print_summary(result, elapsed)

    print("=" * 78)
    print("WIZUALIZACJA 3D")
    print("=" * 78)
    for path in (visualization.render_main_view(result, OUTPUT_MAIN),
                 visualization.render_multi_view(result, OUTPUT_VIEWS),
                 visualization.render_layers(result, OUTPUT_LAYERS)):
        if path:
            print(f"  zapisano: {path}")
    print()
    return result


if __name__ == "__main__":
    main()
