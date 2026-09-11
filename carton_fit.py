"""
Ile sztuk płaskiego produktu wchodzi do jednego kartonu.

Moduł wyspecjalizowany pod jeden typ produktu naraz (single-SKU). Ogólny
algorytm z packing.py radzi sobie z mieszanką różnych produktów, ale dla
jednego powtarzalnego pudełka jest niepotrzebnie wolny: przy kilkuset
sztukach w kartonie jego złożoność O(n^2) robi się nie do przyjęcia.

Dla jednego typu produktu optymalne ułożenie jest regularne, więc liczymy je
wprost:
  * warstwa  – dwuwymiarowe układanie identycznych prostokątów metodą cięć
               gilotynowych (rekurencja z memoizacją), z obrotem o 90 stopni,
  * wysokość – ile takich warstw wejdzie na wysokość kartonu, plus ewentualna
               resztka wysokości dołożona w innej orientacji.

Wszystkie obliczenia idą na liczbach całkowitych w dziesiątych milimetra,
żeby uniknąć błędów zaokrągleń (grubość skóry 0,6 mm musi być dokładna).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

# Jednostka wewnętrzna: 0,1 mm. 1 cm = 100 jednostek, 1 mm = 10 jednostek.
CM = 100
MM = 10


# ---------------------------------------------------------------------------
# Rozczytywanie danych z arkusza
# ---------------------------------------------------------------------------

# "ca. 53x40x10cm", "c. 43x40x15 cm", "ca.15x12x5 cm"
_RE_3D = re.compile(
    r'(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)', re.I)
# "ca.37x25 cm", "ca. 22,5x32,5 cm"  – produkt płaski, bez grubości
_RE_2D = re.compile(
    r'^\s*(?:ca\.?|c\.)?\s*(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*(?:cm)?\s*$', re.I)

_num = lambda s: float(s.replace(",", "."))


def parse_flat_size(text: str) -> tuple[float, float] | None:
    """Zwraca (długość, szerokość) w cm dla zapisu płaskiego, inaczej None.

    Świadomie odrzucamy zapisy trójwymiarowe – produkt z trzecim wymiarem ma
    fałdę i nie jest płaski, więc nie należy do tej grupy.
    """
    if not text or _RE_3D.search(text):
        return None
    m = _RE_2D.match(text.strip())
    if not m:
        return None
    a, b = _num(m.group(1)), _num(m.group(2))
    return (a, b) if a > 0 and b > 0 else None


# Grubości materiałów, których arkusz nie podaje przy każdej pozycji.
# Wartość wzięta z samego arkusza: pozycje opisane jako "recycled leather 0,6mm".
KNOWN_THICKNESS_MM = {"recycled leather": 0.6}

# Materiały, których grubości nie ma nigdzie w pliku. Jeśli produkt jest z nich
# złożony, wynik oznaczamy jako niepełny zamiast zgadywać.
UNKNOWN_MATERIALS = [
    "washable paper", "press board", "pressboard", "tyvek", "cotton",
    "neoprene", "pu- leather", "pu-leather", "polyester band", "wp/rl",
]

_RE_MM = re.compile(r'(\d+(?:[.,]\d+)?)\s*mm', re.I)


@dataclass
class Thickness:
    """Grubość jednej sztuki wraz z uzasadnieniem, skąd się wzięła."""
    mm: float | None
    basis: str                 # co złożyło się na tę liczbę
    unknown_parts: list[str]   # składniki o nieznanej grubości


def parse_thickness(material: str) -> Thickness:
    """Wylicza grubość spakowanej sztuki na podstawie kolumny Material.

    Produkty złożone (zapis "A + B") są laminatem dwóch materiałów – to one
    występują w arkuszu jako "double" / "2-layer". Ich grubość to SUMA grubości
    warstw, a nie podwojona grubość jednej z nich.
    """
    if not material:
        return Thickness(None, "brak danych o materiale", [])

    text = material.strip()
    parts = [p.strip() for p in re.split(r'\+', text) if p.strip()]
    total, basis, unknown = 0.0, [], []

    for part in parts:
        found = _RE_MM.findall(part)
        if found:
            # w jednym składniku bywa tylko jedna liczba, ale sumujemy dla pewności
            v = sum(_num(x) for x in found)
            total += v
            basis.append(f"{part.strip()} = {v:g} mm")
            continue

        low = part.lower()
        hit = next((k for k in KNOWN_THICKNESS_MM if k in low), None)
        if hit:
            total += KNOWN_THICKNESS_MM[hit]
            basis.append(f"{part.strip()} = {KNOWN_THICKNESS_MM[hit]:g} mm (z arkusza)")
        elif any(u in low for u in UNKNOWN_MATERIALS):
            unknown.append(part.strip())
        else:
            unknown.append(part.strip())

    if total <= 0:
        return Thickness(None, "brak grubości w opisie materiału", unknown)
    return Thickness(total, " + ".join(basis), unknown)


# ---------------------------------------------------------------------------
# Geometria: ile identycznych prostokątów wejdzie na jedną warstwę
# ---------------------------------------------------------------------------

def _grid(W: int, H: int, w: int, h: int) -> int:
    """Zwykła siatka: rzędy x kolumny, w obu obrotach o 90 stopni."""
    best = 0
    if w <= W and h <= H:
        best = (W // w) * (H // h)
    if h <= W and w <= H:
        best = max(best, (W // h) * (H // w))
    return best


def _grid_with_strips(W: int, H: int, w: int, h: int) -> int:
    """Główny blok w jednej orientacji + resztkowe paski w dowolnej orientacji.

    Tak układa się towar ręcznie: jak najwięcej sztuk równo w rzędach, a to,
    co zostanie przy ściance, dokłada się obrócone. Metoda nierekurencyjna,
    więc bezpieczna nawet dla bardzo cienkich produktów, gdzie liczba
    możliwych cięć idzie w tysiące.
    """
    best = 0
    for aw, ah in ((w, h), (h, w)):
        if aw > W or ah > H:
            continue
        nx, ny = W // aw, H // ah
        used_w, used_h = nx * aw, ny * ah
        n = nx * ny
        n += _grid(W - used_w, H, w, h)          # pasek przy prawej ściance
        n += _grid(used_w, H - used_h, w, h)     # pasek pod głównym blokiem
        best = max(best, n)
    return best


def max_fit_2d(W: int, H: int, w: int, h: int) -> int:
    """Maksymalna liczba prostokątów w x h na prostokącie W x H (obrót 90 OK).

    Dla produktów dużych względem kartonu liczymy dokładnie, metodą cięć
    gilotynowych z memoizacją: prostokąt tniemy na dwie części i sumujemy
    najlepsze wypełnienia, rozważając tylko cięcia osiągalne przez ustawienie
    produktów jeden za drugim.

    Dla produktów drobnych taka rekurencja miałaby tysiące punktów cięcia i
    nic by nie wniosła – przy dużej liczbie sztuk zwykła siatka z paskami jest
    praktycznie optymalna, więc używamy jej.
    """
    if w <= 0 or h <= 0:
        return 0
    base = _grid_with_strips(W, H, w, h)
    if base == 0:
        return 0

    # ile sztuk wchodzi z grubsza – przy dużej liczbie rezygnujemy z rekurencji
    rough = max(W // w, W // h, 1) * max(H // w, H // h, 1)
    if rough > 400:
        return base

    def cuts(limit: int) -> list[int]:
        """Osiągalne miejsca cięcia: sumy i*w + j*h, nie dalej niż w połowie boku."""
        out, i = set(), 0
        while i * w <= limit:
            j = 0
            while i * w + j * h <= limit:
                if i or j:
                    out.add(i * w + j * h)
                j += 1
            i += 1
        out.discard(0)
        return sorted(out)

    @lru_cache(maxsize=None)
    def solve(cw: int, ch: int) -> int:
        best = _grid(cw, ch, w, h)
        if best == 0:
            return 0
        for x in cuts(cw // 2):
            best = max(best, solve(x, ch) + solve(cw - x, ch))
        for y in cuts(ch // 2):
            best = max(best, solve(cw, y) + solve(cw, ch - y))
        return best

    return max(base, solve(W, H))


# ---------------------------------------------------------------------------
# Ile sztuk wejdzie do kartonu
# ---------------------------------------------------------------------------

@dataclass
class Fit:
    """Wynik dla jednego produktu."""
    count: int
    per_layer: int
    layers: int
    vertical_cm: float      # który wymiar produktu stoi pionowo
    extra: int              # sztuki dołożone w resztce wysokości
    layout: str             # opis słowny układu


def fit_in_carton(carton_cm: tuple[float, float, float],
                  item_cm: tuple[float, float, float],
                  flat_only: bool = True) -> Fit:
    """Ile sztuk produktu item_cm zmieści się w kartonie carton_cm.

    item_cm to (długość, szerokość, grubość).

    flat_only=True  – produkty leżą na płasko, jeden na drugim: pionowo stoi
                      grubość. Tak realnie pakuje się towar miękki i płaski,
                      i taki układ da się odtworzyć w magazynie.
    flat_only=False – dopuszczamy też ustawienie produktu na sztorc (jak płyty
                      w pudełku). Bywa wyższe, ale dla miękkich wyrobów bez
                      przekładek jest nierealne.
    """
    L, W, H = (round(v * CM) for v in carton_cm)
    dims = [round(v * CM) for v in item_cm]
    if min(dims) <= 0:
        return Fit(0, 0, 0, 0, 0, "brak wymiarów")

    def variant(vi: int) -> tuple[int, int, int, int]:
        """vi = indeks wymiaru ustawionego pionowo."""
        v = dims[vi]
        a, b = [dims[i] for i in range(3) if i != vi]
        if v > H:
            return (0, 0, 0, 0)
        layers = H // v
        per = max_fit_2d(L, W, a, b)
        return (layers * per, per, layers, H - layers * v)

    # indeks 2 to grubość produktu – przy układaniu na płasko stoi pionowo
    candidates = [2] if flat_only else [0, 1, 2]
    best_i, best = candidates[0], (0, 0, 0, 0)
    for i in candidates:
        r = variant(i)
        if r[0] > best[0]:
            best_i, best = i, r
    total, per, layers, rest = best
    if total == 0:
        return Fit(0, 0, 0, 0, 0, "produkt nie mieści się w kartonie")

    # resztka wysokości – może zmieści się jeszcze warstwa w innej orientacji
    extra = 0
    extra_desc = ""
    for i in ([] if flat_only else range(3)):
        if i == best_i:
            continue
        v = dims[i]
        if v <= 0 or v > rest:
            continue
        a, b = [dims[j] for j in range(3) if j != i]
        n = (rest // v) * max_fit_2d(L, W, a, b)
        if n > extra:
            extra = n
            extra_desc = f" + {n} szt. w resztce {rest / CM:g} cm"

    layout = (f"{per} szt. na warstwie x {layers} warstw"
              f" (pionowo {dims[best_i] / CM:g} cm){extra_desc}")
    return Fit(total + extra, per, layers, dims[best_i] / CM, extra, layout)
