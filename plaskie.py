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


def material_mm(material: str) -> float | None:
    """Grubość materiału w mm, odczytana wprost z kolumny Material.

    Sumujemy wszystkie liczby zapisane w mm (zwykle jest jedna). Materiały bez
    podanej grubości – washable paper, tyvek, press board – dają None i taka
    pozycja zostaje bez wyniku, zamiast dostać liczbę wziętą z sufitu.
    """
    if not material:
        return None
    found = _RE_MM.findall(material)
    if not found:
        return None
    return sum(float(x.replace(",", ".")) for x in found)


def piece_thickness_mm(material: str, text: str) -> tuple[float | None, int]:
    """Grubość jednej sztuki = grubość materiału x liczba warstw."""
    mm = material_mm(material)
    layers = layer_count(text)
    return (None if mm is None else mm * layers), layers
