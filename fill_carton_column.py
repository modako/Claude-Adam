"""
Uzupełnia w arkuszu BOOGIE kolumnę "1 karton paletowy" dla produktów płaskich.

Co robi:
  1. czyta arkusz, rozpoznaje produkty płaskie (rozmiar zapisany jako "dł x szer"),
  2. wylicza grubość jednej sztuki z kolumny Material,
  3. liczy, ile sztuk wejdzie do kartonu (carton_fit.py),
  4. wpisuje wynik do kolumny D **operując bezpośrednio na XML-u pliku xlsx**,
     żeby nie stracić formatowania ani osadzonego logo (openpyxl kasuje obrazki
     przy zapisie),
  5. zapisuje osobny plik z pełnym uzasadnieniem każdej liczby.

Uruchomienie:
    python3 fill_carton_column.py WEJSCIE.xlsx WYJSCIE.xlsx AUDYT.xlsx
"""

from __future__ import annotations

import collections
import re
import shutil
import sys
import zipfile

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

import carton_fit as cf

# --- parametry uzgodnione z użytkownikiem ---------------------------------
CARTON_CM = (40.0, 50.0, 60.0)   # wymiary WEWNĘTRZNE kartonu paletowego
FLAT_ONLY = True                 # produkty leżą na płasko, nie na sztorc
HEADER_ROW = 13                  # wiersz nagłówka w arkuszu
COL = {"name": 0, "desc": 1, "size": 2, "count": 3, "code": 4, "material": 5}
BIG_COUNT_WARNING = 1000         # od tylu sztuk sygnalizujemy limit wagi

_s = lambda v: "" if v is None else str(v).strip()
_base = lambda code: code.rsplit("/", 1)[0] if "/" in code else code


# ---------------------------------------------------------------------------
# Odczyt i przygotowanie danych
# ---------------------------------------------------------------------------

def read_products(path: str):
    """Zwraca listę (numer_wiersza, wartości) dla wierszy będących produktami.

    Warianty kolorystyczne (ten sam rdzeń kodu artykułu, inna końcówka po "/")
    mają rozmiar i materiał wpisane tylko przy pierwszym wariancie, więc
    brakujące wartości dobieramy z grupy.
    """
    ws = openpyxl.load_workbook(path, data_only=True)["Arkusz1"]
    rows = []
    for r in range(HEADER_ROW + 1, ws.max_row + 1):
        vals = [ws.cell(row=r, column=c + 1).value for c in range(6)]
        if _s(vals[COL["code"]]):
            rows.append((r, vals))

    groups = collections.defaultdict(list)
    for _, v in rows:
        groups[_base(_s(v[COL["code"]]))].append(v)

    def inherited(vals, key):
        own = _s(vals[COL[key]])
        if own:
            return own
        g = groups[_base(_s(vals[COL["code"]]))]
        return next((_s(x[COL[key]]) for x in g if _s(x[COL[key]])), "")

    return [(r, v, inherited(v, "size"), inherited(v, "material")) for r, v in rows]


def compute(path: str):
    """Liczy wynik dla każdego produktu płaskiego."""
    results = []
    for row, vals, size, material in read_products(path):
        flat = cf.parse_flat_size(size)
        if not flat:
            continue                       # nie jest płaski – poza zakresem

        th = cf.parse_thickness(material)
        rec = {
            "row": row,
            "code": _s(vals[COL["code"]]),
            "name": _s(vals[COL["name"]]),
            "desc": _s(vals[COL["desc"]]),
            "size": size,
            "material": material,
            "L": flat[0], "W": flat[1],
            "thickness_mm": th.mm,
            "basis": th.basis,
            "unknown": th.unknown_parts,
            "count": None, "per_layer": None, "layers": None,
            "layout": "", "fill": None, "status": "", "note": "",
        }

        if th.mm is None:
            rec["status"] = "brak grubości materiału – nie policzono"
            results.append(rec)
            continue

        fit = cf.fit_in_carton(CARTON_CM, (flat[0], flat[1], th.mm / 10.0),
                               flat_only=FLAT_ONLY)
        rec.update(count=fit.count, per_layer=fit.per_layer, layers=fit.layers,
                   layout=fit.layout)
        if fit.count == 0:
            rec["status"] = "produkt nie mieści się w kartonie"
        elif th.unknown_parts:
            rec["status"] = ("oszacowane – nieznana grubość składnika: "
                             + ", ".join(th.unknown_parts))
        else:
            rec["status"] = "policzone"

        item_v = flat[0] * flat[1] * (th.mm / 10.0)
        carton_v = CARTON_CM[0] * CARTON_CM[1] * CARTON_CM[2]
        rec["fill"] = item_v * fit.count / carton_v
        if fit.count >= BIG_COUNT_WARNING:
            rec["note"] = "sprawdzić limit wagi kartonu"
        results.append(rec)
    return results


# ---------------------------------------------------------------------------
# Zapis do oryginalnego pliku – operacja na XML, bez utraty formatowania
# ---------------------------------------------------------------------------

def write_counts(src: str, dst: str, results) -> int:
    """Wpisuje liczby do kolumny D, przepisując tylko arkusz wewnątrz xlsx.

    openpyxl przy zapisie gubi osadzone obrazki (w tym pliku jest logo), więc
    zamiast niego podmieniamy pojedyncze komórki bezpośrednio w XML-u i
    przepakowujemy archiwum bez ruszania czegokolwiek innego.
    """
    values = {r["row"]: r["count"] for r in results
              if r["count"] not in (None, 0)}

    with zipfile.ZipFile(src) as z:
        sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        names = z.namelist()
        payload = {n: z.read(n) for n in names}

    written = 0

    def patch(m: re.Match) -> str:
        nonlocal written
        row = int(m.group("row"))
        if row not in values:
            return m.group(0)
        written += 1
        style = m.group("style") or ""
        return f'<c r="D{row}"{style}><v>{values[row]}</v></c>'

    # puste komórki kolumny D są w XML-u zapisane jako <c r="D15" s="227"/>
    sheet = re.sub(r'<c r="D(?P<row>\d+)"(?P<style>[^>/]*)/>', patch, sheet)

    if written != len(values):
        missing = len(values) - written
        raise RuntimeError(f"nie udało się wpisać {missing} wartości – "
                           "komórki kolumny D mają inną postać niż oczekiwana")

    payload["xl/worksheets/sheet1.xml"] = sheet.encode("utf-8")
    shutil.copyfile(src, dst)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        for n in names:
            out.writestr(n, payload[n])
    return written


# ---------------------------------------------------------------------------
# Plik z uzasadnieniem każdej liczby
# ---------------------------------------------------------------------------

def write_audit(path: str, results) -> None:
    """Osobny arkusz: skąd wzięła się każda liczba i co jest niepewne."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Wyliczenia"

    head = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    body = Font(name="Arial", size=10)
    fill = PatternFill("solid", start_color="FF44607A")
    warn = PatternFill("solid", start_color="FFFFF2CC")

    note = [
        "Jak policzono liczbę sztuk w kolumnie „1 karton paletowy”",
        f"Karton (wymiary wewnętrzne): {CARTON_CM[0]:g} x {CARTON_CM[1]:g} x {CARTON_CM[2]:g} cm"
        f" = {CARTON_CM[0]*CARTON_CM[1]*CARTON_CM[2]/1000:g} litrów.",
        "Zakres: wyłącznie produkty płaskie, czyli te z rozmiarem zapisanym jako "
        "„dł x szer”. Produkty z trzecim wymiarem (torby z fałdą) pominięto.",
        "Grubość jednej sztuki: suma grubości materiałów wymienionych w kolumnie "
        "Material. Zapis „A + B” to laminat dwóch warstw, więc grubości się dodaje "
        "(np. recycled leather 0,6 mm + wool felt 3 mm = 3,6 mm). Grubość skóry "
        "z recyklingu wzięta z pozycji „recycled leather 0,6mm” w tym samym arkuszu.",
        "Układ: produkty leżą na płasko, jeden na drugim. Liczba sztuk = ile sztuk "
        "mieści się na dnie kartonu (z obrotem o 90 stopni, układ blokowy) "
        "razy ile warstw wchodzi na wysokość.",
        "UWAGA: to wynik czysto geometryczny. Nie uwzględnia wagi kartonu, "
        "przekładek, opakowań jednostkowych ani zapasu na zamknięcie klapy. "
        "Wiersze oznaczone w kolumnie „Uwagi” prawie na pewno ograniczy waga.",
        "Warianty kolorystyczne (ta sama pozycja, inna końcówka kodu po „/”) "
        "dziedziczą rozmiar i materiał po pierwszym wariancie w grupie.",
    ]
    for i, line in enumerate(note, start=1):
        c = ws.cell(row=i, column=1, value=line)
        c.font = Font(name="Arial", size=10, bold=(i == 1))
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=12)
    for i in range(2, len(note) + 1):
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=12)
        ws.row_dimensions[i].height = 28

    hdr = len(note) + 2
    cols = ["Wiersz w arkuszu", "Article code", "Article name", "Description",
            "Size", "Material", "Grubość szt. [mm]", "Podstawa grubości",
            "Szt. na warstwie", "Warstw", "SZTUK W KARTONIE",
            "Wykorzystanie objętości", "Status", "Uwagi"]
    for j, name in enumerate(cols, start=1):
        c = ws.cell(row=hdr, column=j, value=name)
        c.font, c.fill = head, fill
        c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[hdr].height = 32

    for i, r in enumerate(sorted(results, key=lambda x: x["row"]), start=hdr + 1):
        vals = [r["row"], r["code"], r["name"], r["desc"], r["size"], r["material"],
                r["thickness_mm"], r["basis"], r["per_layer"], r["layers"],
                r["count"], r["fill"], r["status"], r["note"]]
        for j, v in enumerate(vals, start=1):
            c = ws.cell(row=i, column=j, value=v)
            c.font = body
            if j == 12 and v is not None:
                c.number_format = "0.0%"
            if j == 11:
                c.font = Font(name="Arial", size=10, bold=True)
            if r["note"]:
                c.fill = warn

    widths = [9, 16, 22, 30, 18, 34, 12, 40, 10, 9, 13, 12, 40, 22]
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = w
    ws.freeze_panes = ws.cell(row=hdr + 1, column=1)
    ws.auto_filter.ref = f"A{hdr}:N{hdr + len(results)}"
    wb.save(path)


def main() -> None:
    src, dst, audit = sys.argv[1], sys.argv[2], sys.argv[3]
    results = compute(src)
    written = write_counts(src, dst, results)
    write_audit(audit, results)

    ok = [r for r in results if r["status"] == "policzone"]
    est = [r for r in results if r["status"].startswith("oszacowane")]
    none = [r for r in results if r["count"] in (None, 0)]
    big = [r for r in results if r["note"]]
    print(f"produktów płaskich w zakresie:        {len(results)}")
    print(f"  policzone bez zastrzeżeń:           {len(ok)}")
    print(f"  oszacowane (niepełna grubość):      {len(est)}")
    print(f"  bez wyniku (brak grubości):         {len(none)}")
    print(f"  oznaczone „sprawdzić wagę”:         {len(big)}")
    print(f"wpisano wartości do kolumny D:        {written}")


if __name__ == "__main__":
    main()
