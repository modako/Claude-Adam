"""
Uzupełnia kolumnę "1 karton paletowy" wyłącznie dla płaskich płatków materiału.

Wchodzi na ORYGINALNY plik od użytkownika i zmienia w nim tylko komórki
kolumny D – operując bezpośrednio na XML-u, żeby nie stracić logo ani
formatowania (openpyxl kasuje osadzone obrazki przy zapisie).

Reguły:
  * zakres  – tylko wyroby będące wykrojonym kawałkiem materiału (plaskie.py),
  * grubość – grubość materiału z kolumny Material razy liczba warstw
              ("2-layer" / "double" = podwójna grubość),
  * układ   – sztuki leżą na płasko, jedna na drugiej.

Uruchomienie:
    python3 fill_plaskie.py WEJSCIE.xlsx WYJSCIE.xlsx
"""

from __future__ import annotations

import collections
import re
import shutil
import sys
import zipfile

import openpyxl

import carton_fit as cf
import plaskie

CARTON_CM = (40.0, 50.0, 60.0)     # wymiary wewnętrzne kartonu paletowego
HEADER_ROW = 13

_s = lambda v: "" if v is None else str(v).strip()
_base = lambda c: c.rsplit("/", 1)[0] if "/" in c else c


def analyse(path: str) -> list[dict]:
    """Zwraca wynik dla każdej pozycji będącej płaskim płatkiem materiału."""
    ws = openpyxl.load_workbook(path, data_only=True)["Arkusz1"]
    rows = [(r, [ws.cell(row=r, column=c + 1).value for c in range(6)])
            for r in range(HEADER_ROW + 1, ws.max_row + 1)]
    prods = [(r, v) for r, v in rows if _s(v[4])]

    # warianty kolorystyczne dzielą nazwę, opis, rozmiar i materiał
    groups = collections.defaultdict(list)
    for _, v in prods:
        groups[_base(_s(v[4]))].append(v)

    out = []
    for row, v in prods:
        grp = groups[_base(_s(v[4]))]
        pick = lambda i: _s(v[i]) or next((_s(x[i]) for x in grp if _s(x[i])), "")
        size, material = pick(2), pick(5)

        flat = cf.parse_flat_size(size)
        if not flat:
            continue
        # o kwalifikacji decyduje opis całej rodziny, nie pojedynczego wiersza
        text = " ".join(_s(x[0]) + " " + _s(x[1]) for x in grp)
        if not plaskie.is_flat_sheet(text):
            continue

        mm, layers = plaskie.piece_thickness_mm(material, text)
        rec = {"row": row, "code": _s(v[4]),
               "name": pick(0), "desc": pick(1), "size": size,
               "material": material, "layers": layers, "mm": mm,
               "count": None, "per_layer": None, "stack": None, "why": ""}

        if mm is None:
            rec["why"] = "materiał bez podanej grubości"
            out.append(rec)
            continue

        fit = cf.fit_in_carton(CARTON_CM, (flat[0], flat[1], mm / 10.0),
                               flat_only=True)
        rec.update(count=fit.count or None, per_layer=fit.per_layer,
                   stack=fit.layers)
        if not fit.count:
            rec["why"] = "nie mieści się na dnie kartonu"
        out.append(rec)
    return out


def write_column_d(src: str, dst: str, results: list[dict]) -> int:
    """Wpisuje liczby do kolumny D, nie ruszając reszty pliku."""
    values = {r["row"]: r["count"] for r in results if r["count"]}
    with zipfile.ZipFile(src) as z:
        names = z.namelist()
        payload = {n: z.read(n) for n in names}
    sheet = payload["xl/worksheets/sheet1.xml"].decode("utf-8")

    written = 0

    def patch(m: re.Match) -> str:
        nonlocal written
        row = int(m.group("row"))
        if row not in values:
            return m.group(0)
        written += 1
        return f'<c r="D{row}"{m.group("style") or ""}><v>{values[row]}</v></c>'

    sheet = re.sub(r'<c r="D(?P<row>\d+)"(?P<style>[^>/]*)/>', patch, sheet)
    if written != len(values):
        raise RuntimeError(f"wpisano {written} z {len(values)} wartości")

    payload["xl/worksheets/sheet1.xml"] = sheet.encode("utf-8")
    shutil.copyfile(src, dst)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        for n in names:
            out.writestr(n, payload[n])
    return written


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    results = analyse(src)
    written = write_column_d(src, dst, results)

    done = [r for r in results if r["count"]]
    skipped = [r for r in results if not r["count"]]
    print(f"pozycji w zakresie (płatki materiału): {len(results)}")
    print(f"  policzonych i wpisanych:             {written}")
    print(f"  bez wyniku:                          {len(skipped)}")
    for r in skipped:
        print(f"     w.{r['row']:<5} {r['name'][:22]:<22} {r['size'][:16]:<16} "
              f"{r['material'][:26]:<26} – {r['why']}")

    print(f"\n{'nazwa':<22}{'opis':<28}{'rozmiar':<16}{'gr.':>7}{'w':>3}"
          f"{'/warstwę':>9}{'warstw':>8}{'SZTUK':>8}")
    print("-" * 101)
    seen = set()
    for r in sorted(done, key=lambda x: x["row"]):
        key = (r["name"], r["size"], r["mm"])
        if key in seen:
            continue
        seen.add(key)
        print(f"{r['name'][:21]:<22}{r['desc'][:27]:<28}{r['size'][:15]:<16}"
              f"{r['mm']:>5g}mm{r['layers']:>3}{r['per_layer']:>9}"
              f"{r['stack']:>8}{r['count']:>8}")


if __name__ == "__main__":
    main()
