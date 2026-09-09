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

# Wiersze o konstrukcji ustalonej ręcznie z użytkownikiem, bo nie da się jej
# wyprowadzić z ogólnych reguł tekstowych: papp+ TAB 8", papp+ PHONE i
# papp+ SEAL card to nie "etui" ani "card holder" w sensie ogólnej reguły,
# tylko płaski laminat - dwie warstwy filcu (dowolnego rodzaju) oklejone
# jedną warstwą papieru z jednej strony.
PAPP_FLAT_ROWS = set(range(210, 222))

# Torby laptopowe FORMAT (I/II/III/IV) - ustalone z użytkownikiem: całkowita
# grubość sztuki to stałe 2,5 cm, niezależnie od materiału i rodzaju rączek
# (filc/taśma/skóra) - rączki nie wliczają się do grubości.
FORMAT_FLAT_ROWS = set(range(535, 547)) | {1177, 1178}
FORMAT_THICKNESS_MM = 25.0

_s = lambda v: "" if v is None else str(v).strip()
_base = lambda c: c.rsplit("/", 1)[0] if "/" in c else c


def read_blocks(path: str) -> list[dict]:
    """Rozkłada arkusz na bloki produktowe.

    Arkusz jest zbudowany blokowo: wiersz z wypełnioną kolumną Size otwiera
    nowy produkt i niesie nazwę, opis i wymiary. Kolejne wiersze bez rozmiaru
    to warianty tego samego produktu – dzielą z nim nazwę, opis i wymiary,
    ale KAŻDY MA WŁASNY MATERIAŁ, a więc i własną grubość. Opis produktu bywa
    dopisany w kolejnych wierszach bloku ("2-layer sewn"), więc do rozpoznania
    konstrukcji bierzemy tekst z całego bloku.

    Wiersz bez kodu artykułu (nagłówek sekcji, notka) zamyka bieżący blok.
    """
    ws = openpyxl.load_workbook(path, data_only=True)["Arkusz1"]
    blocks, cur = [], None

    for r in range(HEADER_ROW + 1, ws.max_row + 1):
        v = [ws.cell(row=r, column=c + 1).value for c in range(6)]
        name, desc, size, code, material = (_s(v[0]), _s(v[1]), _s(v[2]),
                                            _s(v[4]), _s(v[5]))

        if not code:                       # nagłówek sekcji albo pusty wiersz
            if not (name or desc):
                cur = None
            elif cur is not None:
                cur = None                 # notka między produktami kończy blok
            continue

        if size or cur is None:            # rozmiar otwiera nowy produkt
            cur = {"size": size, "text": "", "rows": []}
            blocks.append(cur)

        cur["text"] += " " + name + " " + desc
        cur["rows"].append({"row": r, "code": code, "material": material,
                            "name": name, "desc": desc})

    return blocks


def analyse(path: str) -> list[dict]:
    """Wynik dla każdego wariantu w policzonych dotąd grupach.

    Grupa 1 – płaski płatek materiału (podkładki, zawieszki, zakładki, maty):
              grubość = materiał razy liczba warstw z opisu.
    Grupa 2 – etui na tablety i laptopy: grubość = materiał razy liczba paneli
              (2 dla pustego pokrowca, 3 dla wersji z kieszenią albo klapą).
    """
    out = []
    for block in read_blocks(path):
        rows_in_block = {r["row"] for r in block["rows"]}
        is_papp_flat = bool(rows_in_block & PAPP_FLAT_ROWS)
        is_format_flat = bool(rows_in_block & FORMAT_FLAT_ROWS)

        flat = cf.parse_flat_size(block["size"])
        if not flat and is_format_flat:
            # rozmiar zapisany trójwymiarowo (np. "30x40x5 cm") - bierzemy
            # tylko długość i szerokość, bo głębokość zastępujemy ustaloną
            # stałą grubością torby
            m = re.match(r'\s*(?:ca\.?|c\.)?\s*(\d+(?:[.,]\d+)?)\s*[x×]\s*'
                        r'(\d+(?:[.,]\d+)?)', block["size"], re.I)
            if m:
                flat = (float(m.group(1).replace(",", ".")),
                        float(m.group(2).replace(",", ".")))
        if not flat:
            continue

        # teczki rozpoznajemy po nazwie – opis nie odróżnia dossieru od folderu
        names = " ".join(r["name"] for r in block["rows"])
        if is_papp_flat or is_format_flat:
            kind, panels = "płatek", None
        elif plaskie.is_folder(names):
            kind, panels = "folder", None
        elif plaskie.is_dossier(names):
            kind, panels = "dossier", None
        elif plaskie.is_flat_sheet(block["text"]):
            kind, panels = "płatek", None
        elif plaskie.is_case(block["text"]):
            kind, panels = "etui", plaskie.case_panels(block["text"], names)
        else:
            continue

        # materiał wariantu; gdy pusty, bierzemy z pierwszego wiersza bloku
        default_mat = next((r["material"] for r in block["rows"] if r["material"]), "")
        header = block["rows"][0]

        for item in block["rows"]:
            material = item["material"] or default_mat
            if kind in ("folder", "dossier"):
                # teczki mają ustaloną grubość, niezależną od rodzaju filcu:
                # dossier to cztery warstwy złożonego materiału, folder to
                # te same cztery warstwy plus metalowe ringi
                mm = (plaskie.FOLDER_THICKNESS_MM if kind == "folder"
                      else plaskie.DOSSIER_THICKNESS_MM)
                basis = ("4 warstwy + ringi – stała grubość" if kind == "folder"
                         else "4 warstwy – stała grubość") + f" {mm / 10:g} cm"
            elif is_papp_flat:
                # ustalone z użytkownikiem: 2 warstwy filcu (dowolny rodzaj)
                # + 1 warstwa papieru, niezależnie od tego, który wariant
                # filcu jest w tym konkretnym wierszu
                mm = 2 * plaskie.FELT_LAYER_MM + 1.0
                basis = (f"2 x filc {plaskie.FELT_LAYER_MM:g} mm + papier 1 mm "
                        "(ustalone przez użytkownika)")
            elif is_format_flat:
                # ustalone z użytkownikiem: stała grubość 2,5 cm dla całej
                # torby, niezależnie od materiału i rodzaju rączek
                mm = FORMAT_THICKNESS_MM
                basis = "stała grubość 2,5 cm (ustalone przez użytkownika)"
            else:
                mm, basis = plaskie.piece_thickness_mm(material, block["text"],
                                                       panels)
            rec = {"row": item["row"], "code": item["code"],
                   "name": item["name"] or header["name"],
                   "desc": item["desc"] or header["desc"],
                   "size": block["size"], "material": material,
                   "kind": kind, "panels": panels, "basis": basis, "mm": mm,
                   "count": None, "per_layer": None, "stack": None, "why": ""}

            if mm is None:
                rec["why"] = basis
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
    """Wpisuje liczby do kolumny D, nie ruszając reszty pliku.

    Obsługuje oba zapisy komórki w XML-u: pustą samozamykającą
    (`<c r="D15" s="227"/>`) oraz już zawierającą wartość
    (`<c r="D15" s="227"><v>123</v></c>`) - to drugie zdarza się, gdy plik
    wejściowy ma już wcześniej wpisane liczby (własne albo z poprzedniego
    przebiegu tego skryptu), które teraz aktualizujemy.
    """
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

    # jeden wzorzec na oba warianty zapisu komórki - pusta samozamykająca
    # (<c r="D15" s="227"/>) albo już z wartością (<c ...><v>123</v></c>).
    # Osobne dwa re.sub dopasowałyby tę samą komórkę dwa razy: po pierwszym
    # podstawieniu pusta komórka zamienia się w postać z wartością i druga
    # runda złapałaby ją ponownie, podwajając licznik `written`.
    pattern = (r'<c r="D(?P<row>\d+)"(?P<style>[^>/]*)(?:/>'
              r'|>\s*<v>[^<]*</v>\s*</c>)')
    sheet = re.sub(pattern, patch, sheet)
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
    for kind in ("płatek", "etui", "dossier", "folder"):
        grp = [r for r in results if r["kind"] == kind]
        ok = [r for r in grp if r["count"]]
        print(f"{kind:<8} pozycji: {len(grp):>4}   policzonych: {len(ok):>4}   "
              f"bez wyniku: {len(grp) - len(ok):>3}")
    print(f"RAZEM    pozycji: {len(results):>4}   wpisanych:   {written:>4}   "
          f"bez wyniku: {len(skipped):>3}")
    for r in skipped:
        print(f"     w.{r['row']:<5} {r['name'][:22]:<22} {r['size'][:16]:<16} "
              f"{r['material'][:26]:<26} – {r['why']}")

    print(f"\n{'grupa':<8}{'nazwa':<19}{'opis':<26}{'rozmiar':<15}{'gr.':>7}"
          f"{'/warstwę':>9}{'warstw':>8}{'SZTUK':>8}   z czego")
    print("-" * 136)
    seen = set()
    for r in sorted(done, key=lambda x: x["row"]):
        key = (r["name"], r["size"], r["mm"])
        if key in seen:
            continue
        seen.add(key)
        print(f"{r['kind']:<8}{r['name'][:18]:<19}{r['desc'][:25]:<26}{r['size'][:14]:<15}"
              f"{r['mm']:>5g}mm{r['per_layer']:>9}"
              f"{r['stack']:>8}{r['count']:>8}   {r['basis']}")


if __name__ == "__main__":
    main()
