"""
Logika pakowania 3D (3D bin packing) dla wielu typów produktów naraz.

Algorytm: heurystyka oparta na "punktach ekstremalnych" (Extreme Points,
Crainic, Perron & Toth 2008) z wyborem najlepszego miejsca (best-fit) oraz
wielostartowym przeszukiwaniem różnych kolejności produktów.

Dlaczego własna implementacja zamiast py3dbp - patrz README.md.

Układ współrzędnych:
    x -> długość kartonu, y -> szerokość kartonu, z -> wysokość (góra).
    Punkt (0,0,0) to lewy-przedni-dolny narożnik kartonu.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Iterable, Sequence

# Tolerancja numeryczna - wymiary podajemy w cm, ale liczymy na floatach.
EPS = 1e-9

# Etykiety osi oryginalnego produktu: D = długość, S = szerokość, W = wysokość.
_AXIS_LABELS = ("D", "S", "W")


# ---------------------------------------------------------------------------
# Model danych
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Orientation:
    """Jedno dopuszczalne ustawienie produktu w przestrzeni.

    dx/dy/dz to wymiary produktu *po obrocie*, wyrażone wzdłuż osi kartonu.
    `label` mówi, która oryginalna krawędź produktu leży wzdłuż X, Y i Z,
    np. "SDW" = szerokość wzdłuż X, długość wzdłuż Y, wysokość wzdłuż Z.
    """

    dx: float
    dy: float
    dz: float
    label: str

    @property
    def volume(self) -> float:
        return self.dx * self.dy * self.dz


@dataclass(frozen=True)
class Container:
    """Karton, do którego pakujemy."""

    length: float  # wzdłuż X
    width: float   # wzdłuż Y
    height: float  # wzdłuż Z
    name: str = "Karton"

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass
class ProductType:
    """Typ produktu wraz z liczbą dostępnych sztuk i flagą obracania."""

    name: str
    length: float
    width: float
    height: float
    quantity: int
    rotatable: bool = True
    color: str | None = None

    # cache orientacji, liczony raz (wykorzystywany w gorącej pętli algorytmu)
    _orientations: tuple[Orientation, ...] = field(
        default=(), init=False, repr=False, compare=False
    )

    @property
    def volume(self) -> float:
        """Objętość pojedynczej sztuki."""
        return self.length * self.width * self.height

    @property
    def total_volume(self) -> float:
        return self.volume * self.quantity

    def orientations(self) -> tuple[Orientation, ...]:
        """Lista dopuszczalnych orientacji.

        - rotatable=False -> tylko orientacja oryginalna (produkt musi stać
          "górą do góry", np. butelka albo pudełko z nadrukiem),
        - rotatable=True  -> wszystkie 6 permutacji wymiarów. Permutacje
          dające identyczne wymiary (np. sześcian) są deduplikowane, żeby
          nie sprawdzać w kółko tego samego ustawienia.
        """
        if self._orientations:
            return self._orientations

        dims = (self.length, self.width, self.height)
        if not self.rotatable:
            result = (Orientation(dims[0], dims[1], dims[2], "DSW (bez obrotu)"),)
        else:
            unique: dict[tuple[float, float, float], Orientation] = {}
            for perm in itertools.permutations(range(3)):
                d = (dims[perm[0]], dims[perm[1]], dims[perm[2]])
                if d not in unique:
                    label = "".join(_AXIS_LABELS[i] for i in perm)
                    unique[d] = Orientation(d[0], d[1], d[2], label)
            result = tuple(unique.values())

        object.__setattr__(self, "_orientations", result)
        return result


@dataclass(frozen=True)
class Placement:
    """Konkretna sztuka produktu umieszczona w kartonie."""

    product: str
    x: float
    y: float
    z: float
    dx: float
    dy: float
    dz: float
    orientation: str

    @property
    def volume(self) -> float:
        return self.dx * self.dy * self.dz

    @property
    def max_corner(self) -> tuple[float, float, float]:
        return (self.x + self.dx, self.y + self.dy, self.z + self.dz)


@dataclass
class PackingResult:
    """Wynik pakowania: co weszło, co nie weszło i statystyki."""

    container: Container
    products: Sequence[ProductType]
    placements: list[Placement]
    strategy: str = ""

    @property
    def packed_volume(self) -> float:
        return sum(p.volume for p in self.placements)

    @property
    def fill_ratio(self) -> float:
        """Procent wykorzystania objętości kartonu (0..1)."""
        return self.packed_volume / self.container.volume if self.container.volume else 0.0

    @property
    def packed_counts(self) -> dict[str, int]:
        counts = {p.name: 0 for p in self.products}
        for pl in self.placements:
            counts[pl.product] = counts.get(pl.product, 0) + 1
        return counts

    @property
    def unpacked_counts(self) -> dict[str, int]:
        packed = self.packed_counts
        return {p.name: p.quantity - packed.get(p.name, 0) for p in self.products}

    @property
    def max_used_height(self) -> float:
        return max((p.z + p.dz for p in self.placements), default=0.0)

    def sort_key(self) -> tuple[float, int]:
        """Klucz porównywania wariantów: najpierw objętość, potem liczba sztuk."""
        return (self.packed_volume, len(self.placements))


# ---------------------------------------------------------------------------
# Algorytm
# ---------------------------------------------------------------------------


class ExtremePointPacker:
    """Pakowarka oparta na punktach ekstremalnych (Extreme Points).

    Idea:
      1. Utrzymujemy zbiór punktów-kandydatów (EP), w których może stanąć
         lewy-przedni-dolny narożnik kolejnego produktu. Na starcie jest to
         wyłącznie (0,0,0).
      2. Dla każdej sztuki produktu sprawdzamy wszystkie pary
         (punkt kandydujący x dopuszczalna orientacja) i wybieramy tę
         o najlepszej ocenie (best-fit), a nie pierwszą pasującą.
      3. Po wstawieniu produktu generujemy nowe punkty ekstremalne: narożniki
         wstawionego pudełka oraz ich *rzuty* na najbliższe napotkane ściany
         innych produktów / ścianki kartonu. Dzięki rzutom algorytm potrafi
         wykorzystać szczeliny obok i pod już ułożonymi produktami, czego nie
         robi naiwne "trzy narożniki".
    """

    def __init__(
        self,
        container: Container,
        support_ratio: float = 0.7,
        score_mode: str = "dblf",
    ) -> None:
        """
        support_ratio: minimalny ułamek podstawy produktu, który musi opierać
            się na podłodze kartonu lub na innych produktach (0..1). Chroni
            przed "lewitującymi" pudełkami i daje fizycznie sensowny stos.
        score_mode:
            'dblf'    - najpierw jak najniżej/najbliżej narożnika (Deepest
                        Bottom-Left-Fill), styk jako kryterium rozstrzygające,
            'contact' - najpierw maksymalny styk ścianek (ciasne upakowanie),
                        położenie jako kryterium rozstrzygające.
        """
        self.container = container
        self.support_ratio = support_ratio
        self.score_mode = score_mode

    # -- sprawdzanie wykonalności ------------------------------------------

    def _fits(self, pos: tuple[float, float, float], o: Orientation,
              placed: list[Placement]) -> bool:
        """Czy produkt zmieści się w kartonie i nie przetnie innych produktów."""
        x, y, z = pos
        if x < -EPS or y < -EPS or z < -EPS:
            return False
        if (x + o.dx > self.container.length + EPS
                or y + o.dy > self.container.width + EPS
                or z + o.dz > self.container.height + EPS):
            return False

        x2, y2, z2 = x + o.dx, y + o.dy, z + o.dz
        for q in placed:
            # Kolizja tylko wtedy, gdy przedziały nachodzą na WSZYSTKICH osiach.
            if (q.x < x2 - EPS and x < q.x + q.dx - EPS
                    and q.y < y2 - EPS and y < q.y + q.dy - EPS
                    and q.z < z2 - EPS and z < q.z + q.dz - EPS):
                return False
        return True

    def _supported(self, pos: tuple[float, float, float], o: Orientation,
                   placed: list[Placement]) -> bool:
        """Czy podstawa produktu ma wystarczające podparcie od dołu."""
        x, y, z = pos
        if z <= EPS:                      # stoi na dnie kartonu
            return True

        base_area = o.dx * o.dy
        supported = 0.0
        for q in placed:
            if abs(q.z + q.dz - z) > 1e-6:   # górna ścianka q nie jest na poziomie z
                continue
            ox = min(x + o.dx, q.x + q.dx) - max(x, q.x)
            oy = min(y + o.dy, q.y + q.dy) - max(y, q.y)
            if ox > EPS and oy > EPS:
                supported += ox * oy

        ratio = supported / base_area if base_area else 0.0
        # Nawet przy support_ratio=0 wymagamy jakiegokolwiek kontaktu z podłożem.
        return ratio >= max(self.support_ratio, EPS)

    # -- ocena kandydata ----------------------------------------------------

    def _contact_area(self, pos: tuple[float, float, float], o: Orientation,
                      placed: list[Placement]) -> float:
        """Pole ścianek stykających się ze ściankami kartonu i innych produktów.

        Im większy styk, tym ciaśniejsze (i stabilniejsze) upakowanie -
        to nasza miara "jak dobrze produkt wpasował się w lukę".
        """
        x, y, z = pos
        x2, y2, z2 = x + o.dx, y + o.dy, z + o.dz
        area = 0.0

        # styk ze ściankami kartonu
        if x <= EPS:
            area += o.dy * o.dz
        if abs(x2 - self.container.length) <= EPS:
            area += o.dy * o.dz
        if y <= EPS:
            area += o.dx * o.dz
        if abs(y2 - self.container.width) <= EPS:
            area += o.dx * o.dz
        if z <= EPS:
            area += o.dx * o.dy
        if abs(z2 - self.container.height) <= EPS:
            area += o.dx * o.dy

        # styk z już ułożonymi produktami (ścianka do ścianki)
        for q in placed:
            qx2, qy2, qz2 = q.x + q.dx, q.y + q.dy, q.z + q.dz
            ox = min(x2, qx2) - max(x, q.x)
            oy = min(y2, qy2) - max(y, q.y)
            oz = min(z2, qz2) - max(z, q.z)
            if abs(x2 - q.x) <= EPS or abs(qx2 - x) <= EPS:
                if oy > EPS and oz > EPS:
                    area += oy * oz
            if abs(y2 - q.y) <= EPS or abs(qy2 - y) <= EPS:
                if ox > EPS and oz > EPS:
                    area += ox * oz
            if abs(z2 - q.z) <= EPS or abs(qz2 - z) <= EPS:
                if ox > EPS and oy > EPS:
                    area += ox * oy
        return area

    def _score(self, pos: tuple[float, float, float], o: Orientation,
               placed: list[Placement]) -> tuple:
        """Mniejsza wartość = lepsze miejsce."""
        x, y, z = pos
        contact = self._contact_area(pos, o, placed)
        if self.score_mode == "contact":
            return (-contact, z, y, x)
        # 'dblf': buduj warstwami od dna, remisy rozstrzygaj ciasnością styku
        return (z, y, x, -contact)

    # -- generowanie punktów ekstremalnych ---------------------------------

    def _project(self, point: tuple[float, float, float], axis: int,
                 placed: list[Placement]) -> tuple[float, float, float]:
        """Rzutuje punkt wstecz wzdłuż osi `axis` (0=X, 1=Y, 2=Z).

        Punkt "spada" w kierunku początku układu aż natrafi na ściankę już
        ułożonego produktu albo na ściankę kartonu (współrzędna 0).
        """
        p = list(point)
        best = 0.0
        # osie prostopadłe do kierunku rzutowania - po nich sprawdzamy przekrycie
        a, b = [i for i in range(3) if i != axis]
        pa, pb = p[a], p[b]

        for q in placed:
            lo = (q.x, q.y, q.z)
            hi = q.max_corner
            # czy produkt q "zasłania" ten punkt w płaszczyźnie (a, b)?
            if not (lo[a] - EPS <= pa < hi[a] - EPS):
                continue
            if not (lo[b] - EPS <= pb < hi[b] - EPS):
                continue
            # bierzemy najdalszą ściankę, która leży pod punktem
            if hi[axis] <= p[axis] + EPS and hi[axis] > best:
                best = hi[axis]

        p[axis] = best
        return (p[0], p[1], p[2])

    def _new_extreme_points(self, placement: Placement,
                            placed: list[Placement]) -> list[tuple[float, float, float]]:
        """Nowe punkty kandydujące powstałe po wstawieniu `placement`."""
        x, y, z = placement.x, placement.y, placement.z
        x2, y2, z2 = placement.max_corner

        # Trzy "oczywiste" narożniki: obok, za i nad wstawionym produktem.
        corners = [(x2, y, z), (x, y2, z), (x, y, z2)]
        points = list(corners)

        # Oraz ich rzuty na sąsiednie powierzchnie - to one pozwalają
        # dosunąć kolejne produkty do już istniejących ścianek/szczelin.
        points.append(self._project((x2, y, z), 1, placed))  # w kierunku -Y
        points.append(self._project((x2, y, z), 2, placed))  # w dół
        points.append(self._project((x, y2, z), 0, placed))  # w kierunku -X
        points.append(self._project((x, y2, z), 2, placed))  # w dół
        points.append(self._project((x, y, z2), 0, placed))  # w kierunku -X
        points.append(self._project((x, y, z2), 1, placed))  # w kierunku -Y
        return points

    def _prune(self, points: Iterable[tuple[float, float, float]],
               placed: list[Placement]) -> list[tuple[float, float, float]]:
        """Usuwa duplikaty, punkty poza kartonem i punkty wewnątrz produktów."""
        result: list[tuple[float, float, float]] = []
        seen: set[tuple[float, float, float]] = set()
        for p in points:
            key = (round(p[0], 6), round(p[1], 6), round(p[2], 6))
            if key in seen:
                continue
            if (key[0] > self.container.length - EPS
                    or key[1] > self.container.width - EPS
                    or key[2] > self.container.height - EPS):
                continue
            inside = False
            for q in placed:
                if (q.x - EPS < key[0] < q.x + q.dx - EPS
                        and q.y - EPS < key[1] < q.y + q.dy - EPS
                        and q.z - EPS < key[2] < q.z + q.dz - EPS):
                    inside = True
                    break
            if inside:
                continue
            seen.add(key)
            result.append(key)
        # Sortowanie od dna daje powtarzalny (deterministyczny) wynik.
        result.sort(key=lambda p: (p[2], p[1], p[0]))
        return result

    # -- główna pętla -------------------------------------------------------

    def pack_sequence(self, pieces: Sequence[ProductType]) -> list[Placement]:
        """Pakuje sztuki w zadanej kolejności (jedna pozycja listy = 1 sztuka)."""
        placed: list[Placement] = []
        points: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0)]

        for product in pieces:
            best_score = None
            best_point = None
            best_orientation = None

            for point in points:
                for o in product.orientations():
                    if not self._fits(point, o, placed):
                        continue
                    if not self._supported(point, o, placed):
                        continue
                    score = self._score(point, o, placed)
                    if best_score is None or score < best_score:
                        best_score = score
                        best_point = point
                        best_orientation = o

            if best_point is None:            # ta sztuka się nie mieści
                continue

            placement = Placement(
                product=product.name,
                x=best_point[0], y=best_point[1], z=best_point[2],
                dx=best_orientation.dx, dy=best_orientation.dy, dz=best_orientation.dz,
                orientation=best_orientation.label,
            )
            placed.append(placement)

            # zużyty punkt znika, w zamian pojawiają się nowe kandydatury
            remaining = [p for p in points if p != best_point]
            points = self._prune(remaining + self._new_extreme_points(placement, placed),
                                 placed)

        return placed


# ---------------------------------------------------------------------------
# Strategie kolejności + przeszukiwanie wielostartowe
# ---------------------------------------------------------------------------


def _expand(products: Sequence[ProductType]) -> list[ProductType]:
    """Rozwija typy produktów na listę pojedynczych sztuk."""
    pieces: list[ProductType] = []
    for p in products:
        pieces.extend([p] * p.quantity)
    return pieces


def _orderings(products: Sequence[ProductType]) -> list[tuple[str, list[ProductType]]]:
    """Kilka sensownych kolejności wkładania produktów.

    Kolejność ma ogromny wpływ na jakość heurystyki, a policzenie kilku
    wariantów jest tanie - bierzemy więc najlepszy z nich (multi-start).
    """
    def sorted_pieces(key, reverse=True):
        return sorted(_expand(products), key=key, reverse=reverse)

    orders = [
        ("objętość malejąco",
         sorted_pieces(lambda p: (p.volume, max(p.length, p.width, p.height)))),
        ("najdłuższa krawędź malejąco",
         sorted_pieces(lambda p: (max(p.length, p.width, p.height), p.volume))),
        ("pole podstawy malejąco",
         sorted_pieces(lambda p: (p.length * p.width, p.height))),
        ("wysokość malejąco",
         sorted_pieces(lambda p: (p.height, p.volume))),
    ]

    # Warianty "typami": najpierw wszystkie sztuki jednego typu, potem następnego.
    # Zwykle dają ładne, regularne warstwy jednorodnych produktów.
    by_volume_desc = sorted(products, key=lambda p: p.volume, reverse=True)
    orders.append(("typami: od największego", _expand(by_volume_desc)))
    orders.append(("typami: od najmniejszego", _expand(list(reversed(by_volume_desc)))))

    # Produkty bez możliwości obrotu są najtrudniejsze do upchnięcia,
    # więc warto sprawdzić wariant, w którym idą jako pierwsze.
    fixed_first = sorted(products, key=lambda p: (p.rotatable, -p.volume))
    orders.append(("nieobracalne najpierw", _expand(fixed_first)))
    return orders


def pack(
    container: Container,
    products: Sequence[ProductType],
    support_ratio: float = 0.7,
    score_modes: Sequence[str] = ("dblf", "contact"),
    verbose: bool = False,
) -> PackingResult:
    """Pakuje produkty do kartonu, zwracając najlepszy znaleziony wariant.

    Przeszukujemy iloczyn (kolejność produktów x tryb oceny miejsca) i
    wybieramy rozwiązanie o największej zapakowanej objętości.
    """
    best: PackingResult | None = None

    for order_name, pieces in _orderings(products):
        for mode in score_modes:
            packer = ExtremePointPacker(container, support_ratio=support_ratio,
                                        score_mode=mode)
            placements = packer.pack_sequence(pieces)
            result = PackingResult(
                container=container,
                products=products,
                placements=placements,
                strategy=f"{order_name} / ocena: {mode}",
            )
            if verbose:
                print(f"  [strategia] {result.strategy:<45} "
                      f"sztuk: {len(placements):>3}  "
                      f"wypełnienie: {result.fill_ratio * 100:5.2f}%")
            if best is None or result.sort_key() > best.sort_key():
                best = result

            # Nie da się zapakować więcej niż wszystko - kończymy wcześniej.
            if len(placements) == len(pieces):
                return best

    assert best is not None
    return best


def validate(result: PackingResult) -> list[str]:
    """Kontrola poprawności wyniku - zwraca listę wykrytych problemów.

    Sprawdza: mieszczenie się w kartonie, brak przenikania się produktów
    oraz nieprzekroczenie dostępnych ilości sztuk.
    """
    problems: list[str] = []
    c = result.container

    for p in result.placements:
        if (p.x < -EPS or p.y < -EPS or p.z < -EPS
                or p.x + p.dx > c.length + EPS
                or p.y + p.dy > c.width + EPS
                or p.z + p.dz > c.height + EPS):
            problems.append(f"{p.product} @ ({p.x},{p.y},{p.z}) wystaje poza karton")

    for a, b in itertools.combinations(result.placements, 2):
        if (a.x < b.x + b.dx - EPS and b.x < a.x + a.dx - EPS
                and a.y < b.y + b.dy - EPS and b.y < a.y + a.dy - EPS
                and a.z < b.z + b.dz - EPS and b.z < a.z + a.dz - EPS):
            problems.append(
                f"kolizja: {a.product} @ ({a.x},{a.y},{a.z}) "
                f"z {b.product} @ ({b.x},{b.y},{b.z})")

    packed = result.packed_counts
    for prod in result.products:
        if packed.get(prod.name, 0) > prod.quantity:
            problems.append(f"{prod.name}: zapakowano więcej sztuk niż dostępnych")

    return problems
