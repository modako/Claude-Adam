"""
Wybór produktów będących płaskim płatkiem materiału + reguła grubości warstw.

Zakres uzgodniony z użytkownikiem: tylko wyroby, które są po prostu wykrojonym
kawałkiem materiału – podkładki, zawieszki, zakładki, maty, breloki bez okuć.
Wszystko, co ma ringi, śrubki, klips, rzep, gumkę, karabińczyk albo jest uszyte
w etui/torbę, zostaje poza zakresem: tam grubości nie da się wyliczyć z
katalogu, bo decyduje o niej konstrukcja, a nie materiał.
"""

from __future__ import annotations

import re

# Produkt JEST płatkiem materiału – rozpoznanie po nazwie i opisie.
INCLUDE = re.compile(r"""
    coaster | doorhanger | door\s?hanger | bookmark
  | mouse\s?-?\s?(pad|mat) | desk\s?mat | table\s?mat | placemat
  | seat\s?pad | seatpad
  | luggage\s?/?\s?id\s?tag | luggage\s?tag | id\s?tag
  | key\s?fob
  | christmas\s?decoration | easter\s?decoration | decorative\s?banderolle
  | gingerbread | cutlery\s?coaster
""", re.I | re.X)

# ...chyba że ma okucia, zapięcie, wypełnienie albo jest uszyte w pojemnik.
# Ta lista ma pierwszeństwo przed INCLUDE.
EXCLUDE = re.compile(r"""
    \bcase\b | cover | \bbag\b | folder | notebook | wallet | apron
  | pen\s?box | pencil | sack | briefcase | clipboard | menu | guest\s?book
  | card\s?holder | envelope | pocket | organizer | lanyard | carabiner
  | keychain | \bring | screw | \bclip | velcro | elastic | magnet
  | press\s?stud | buckle | strap | handle | \bsock\b | warmer | \bpin\b
  | address\s?card | 2in1 | \brope\b | \bhook\b | \bband\b | ribbon | rivet
  | foam | filled | eyelet | embossing | basket | container | \bbelt\b
""", re.I | re.X)

# Etui na tablety i laptopy – druga grupa liczona w tej rundzie.
# Świadomie NIE obejmuje etui na telefon, wizytowników, piórników, okładek
# na menu ani etui na paszport: to inna konstrukcja i inny rozmiar.
ETUI = re.compile(r"""
    tablet\s?case | laptop\s?case | tablet\s?cover | notebook\s?cover
  | ^\s*case\s+a[45]\b | \bcase\s+a[45]\s
""", re.I | re.X)

# Etui z kieszenią albo klapą ma jeden panel materiału więcej.
# Dopuszczamy słowa pośrednie: "with pocket", "with flap", "with leather flap",
# "with front pocket".
ETUI_EXTRA_PANEL = re.compile(r'with\s+(?:\w+\s+){0,2}(pocket|flap)', re.I)


def is_case(text: str) -> bool:
    """Czy opis wskazuje na etui na tablet albo laptop."""
    return bool(ETUI.search(text or ""))


def case_panels(text: str) -> int:
    """Ile warstw materiału ma ścianka etui.

    Pusty pokrowiec jest uszyty z dwóch paneli. Wersje "with pocket" albo
    "with flap" mają trzeci panel, więc leżą grubiej.
    """
    return 3 if ETUI_EXTRA_PANEL.search(text or "") else 2


# --- Teczki: dossiery i foldery -------------------------------------------
# Rozpoznajemy je po NAZWIE, nie po opisie: w kolumnie Description praktycznie
# każda teczka jest opisana jako "folder A4/A5", więc opis nie odróżnia
# dossieru od folderu z ringami.
FOLDER_NAME = re.compile(r'\bFOLDER\b', re.I)
DOSSIER_NAME = re.compile(r'\bDOSSIER\b', re.I)

# Folder ma metalowe ringi i to one decydują o grubości – wartość podana
# przez użytkownika, niezależna od rodzaju filcu.
FOLDER_THICKNESS_MM = 25.0

# Dossier nie ma ringów, jest tylko składany, więc grubość bierze się z
# materiału: dwa panele złożonej teczki, trzeci przy przegródkach i kieszeniach.
DOSSIER_EXTRA_PANEL = re.compile(r'compartment|pocket', re.I)


def is_folder(name: str) -> bool:
    """Teczka z ringami – liczona stałą grubością."""
    return bool(FOLDER_NAME.search(name or ""))


def is_dossier(name: str) -> bool:
    """Teczka składana, bez ringów – grubość liczona z materiału."""
    return bool(DOSSIER_NAME.search(name or ""))


def dossier_panels(text: str) -> int:
    """Ile warstw materiału leży na sobie w złożonym dossierze."""
    return 3 if DOSSIER_EXTRA_PANEL.search(text or "") else 2


# Ile warstw materiału ma jedna sztuka.
_LAYERS = [
    (re.compile(r'\b3\s*-?\s*layers?\b|\bsandwich\b', re.I), 3),
    (re.compile(r'\b2\s*-?\s*layers?\b|\bdouble\b|\bdoubble\b', re.I), 2),
    (re.compile(r'\b1\s*-?\s*layers?\b|\bsingle\b', re.I), 1),
]


def is_flat_sheet(text: str) -> bool:
    """Czy opis produktu wskazuje na płaski płatek materiału."""
    if EXCLUDE.search(text):
        return False
    return bool(INCLUDE.search(text))


def layer_count(text: str) -> int:
    """Liczba warstw materiału w jednej sztuce (domyślnie 1).

    Reguła uzgodniona z użytkownikiem: jeśli w opisie jest napisane, że wyrób
    jest dwuwarstwowy, jedna sztuka liczy się jako podwójna grubość materiału.
    """
    for pattern, n in _LAYERS:
        if pattern.search(text):
            return n
    return 1


_RE_MM = re.compile(r'(\d+(?:[.,]\d+)?)\s*mm', re.I)

# Grubości materiałów, których arkusz nie podaje liczbowo, oraz liczba warstw,
# w jakiej dany materiał występuje w wyrobie. Ustalone z użytkownikiem na
# podstawie tego, jak te wyroby są faktycznie zbudowane.
#
#   washable paper – oklejka po OBU stronach rdzenia z filcu, czyli 2 warstwy
#                    po 1 mm (tak jest zbudowana zarówno wersja "2-layer",
#                    jak i "sandwich / washable paper + felt + washable paper"),
#   recycled leather – naszyta z jednej strony, 1 warstwa 0,6 mm
#                    (opis "2-layer coaster" = skóra + filc).
# Kolejność ma znaczenie: dopasowanie idzie po pierwszym trafieniu, więc
# zapisy bardziej szczegółowe ("hard tyvek") muszą stać przed ogólnymi.
COMPONENTS = {
    "washable paper": {"mm": 1.0, "layers": 2},   # oklejka po obu stronach rdzenia
    "recycled leather": {"mm": 0.6, "layers": 1}, # naszyta z jednej strony
    "wp/rl": {"mm": 0.6, "layers": 1},            # wariant liczony jako RL
    "pu- leather": {"mm": 1.0, "layers": 1},
    "pu-leather": {"mm": 1.0, "layers": 1},
    "press board": {"mm": 1.0, "layers": 1},      # usztywnienie z jednej strony
    "pressboard": {"mm": 1.0, "layers": 1},
    "hard tyvek": {"mm": 0.3, "layers": 1},
    "tyvek": {"mm": 0.1, "layers": 1},
}

# Materiały bez znanej grubości – pozycja zostaje bez wyniku zamiast zgadywania.
NO_THICKNESS = ["cotton", "neoprene", "polyester band"]


def _felt_mm(material: str) -> float | None:
    """Grubość rdzenia – jedyna liczba podana wprost w kolumnie Material."""
    found = _RE_MM.findall(material or "")
    if not found:
        return None
    return sum(float(x.replace(",", ".")) for x in found)


def piece_thickness_mm(material: str, text: str,
                       panels: int | None = None) -> tuple[float | None, str]:
    """Grubość jednej sztuki wraz z opisem, z czego się składa.

    panels=None – płatek materiału: liczbę warstw bierzemy z opisu
        ("2-layer" / "double" = podwójna, "3-layer" / "sandwich" = potrójna).
    panels=2/3  – etui: liczba paneli wynika z konstrukcji pokrowca, nie z opisu.

    Doklejone lub naszyte składniki (skóra, press board, oklejka z papieru)
    doliczamy raz, wg tabeli COMPONENTS – niezależnie od liczby paneli.
    """
    mat = (material or "").lower()
    core = _felt_mm(material)

    # materiał jednorodny bez liczby w opisie, ale o znanej grubości
    # (np. sam "washable paper") – rdzeniem jest ten materiał
    if core is None and "+" not in (material or ""):
        hit = next((k for k in COMPONENTS if k in mat), None)
        if hit:
            n = panels if panels else layer_count(text)
            mm = COMPONENTS[hit]["mm"] * n
            return mm, (f"{hit} {COMPONENTS[hit]['mm']:g} mm x {n} warstw"
                        if n > 1 else f"{hit} {COMPONENTS[hit]['mm']:g} mm")
    if core is None:
        return None, "brak grubości rdzenia"

    # wyrób złożony rozpoznajemy po zapisie "A + B"; materiał jednorodny
    # (np. sama "recycled leather 0,6mm") ma już swoją grubość w liczbie
    composite = "+" in (material or "")
    extras, parts = 0.0, [f"rdzeń {core:g} mm"]
    if composite:
        for name, spec in COMPONENTS.items():
            if name in mat:
                extras += spec["mm"] * spec["layers"]
                parts.append(f"{name} {spec['layers']}x{spec['mm']:g} mm")

    # składnik o nieznanej grubości dyskwalifikuje pozycję
    for unknown in NO_THICKNESS:
        if unknown in mat:
            return None, f"nieznana grubość: {unknown}"

    n = panels if panels else (1 if extras > 0 else layer_count(text))
    body = core * n
    if n > 1:
        parts[0] = f"rdzeń {core:g} mm x {n}"
    if extras > 0:
        return body + extras, " + ".join(parts)
    return body, (f"{core:g} mm x {n} warstw" if n > 1 else f"{core:g} mm")
