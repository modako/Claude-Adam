# GDOŚ: national parks and nature reserves (downloaded by hand)

The GDOŚ server (`sdi.gdos.gov.pl`) is behind an Incapsula bot filter that returns 403 to
the cloud environment, so these files were downloaded by the project owner in a browser
from https://www.gov.pl/web/gdos/dostep-do-danych-geoprzestrzennych and committed here.

| File | WFS layer | Downloaded | Features | SHA-256 |
|---|---|---|---|---|
| `ParkiNarodowe.zip` | `GDOS:ParkiNarodowe` | 2026-10-05 | 46 (23 parks + 23 buffer zones) | `606142f2c2caeed0b49f086b97443584793130584b2b72e369b7da36afa9f58a` |
| `Rezerwaty.zip` | `GDOS:Rezerwaty` | 2026-10-05 | 2146 (1726 reserves + 420 buffer zones) | `eea203cf23f01bb17ca6db95c4ff8433d4c2fb6ac78caa966632bfb91a471974` |

Original request (from `wfsrequest.txt` inside each zip):
`http://sdi.gdos.gov.pl/wfs?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME=GDOS:<layer>&SRSNAME=EPSG:2180&outputFormat=shape-zip&format_options=charset:windows-1250`

## Reading notes (verified 2026-10-05)

- CRS: EPSG:2180 (PUWG 1992).
- Fields: `gid` (int), `nazwa` (name), `kodinspire` (INSPIRE id, e.g. `PL.ZIPOP.1393.PN.17`).
- **Encoding is windows-1250** and the zip has no `.cpg`: read with
  `gpd.read_file("zip://...!RezerwatyPolygon.shp", encoding="cp1250")`, otherwise Polish letters break.
- **Buffer zones (`otulina`) are in the same layers**, marked only by `" - otulina"` in `nazwa`.
  A buffer zone is NOT a ban on entry or picking and must be excluded from the legal mask.
- One reserve geometry is invalid: run `make_valid()` before overlays.
- GDOŚ states that these boundaries are not a legal determination.

Attribution: "Generalna Dyrekcja Ochrony Środowiska, dane pobrane 2026-10-05".
