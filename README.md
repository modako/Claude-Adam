# 3D bin packing — optymalne pakowanie produktów do kartonu

Program układa wiele różnych typów produktów w jednym kartonie tak, żeby zmieścić
ich jak najwięcej, respektując ograniczenia obrotu poszczególnych produktów,
i rysuje wynik w 3D.

## Uruchomienie

```bash
pip install matplotlib numpy
python3 main.py        # pakowanie + raport + wizualizacje
python3 test_packing.py  # testy poprawności
```

Dane wejściowe (karton, lista produktów, wymagane podparcie) są zwykłymi
zmiennymi na górze `main.py` — tam się je zmienia.

## Struktura

| plik | zawartość |
|---|---|
| `packing.py` | model danych + algorytm pakowania + walidacja wyniku |
| `visualization.py` | rysowanie 3D (matplotlib/mplot3d) |
| `main.py` | dane wejściowe, raport tekstowy, uruchomienie |
| `test_packing.py` | testy poprawności (obroty, kolizje, limity sztuk, podparcie) |

## Dlaczego własny algorytm, a nie py3dbp

Rozważyłem `py3dbp` i wybrałem własną implementację:

* **Ograniczenia obrotu.** Wymagana jest flaga „obracać / nie obracać" per
  produkt. `py3dbp` iteruje po sztywnej liście 6 typów rotacji dla wszystkich
  przedmiotów — żeby zablokować obroty pojedynczego produktu, trzeba i tak
  ingerować w bibliotekę.
* **Utrzymanie.** `py3dbp` jest praktycznie nierozwijane i ma znane błędy w
  wykrywaniu przecięć oraz liczeniu na `Decimal`. Debugowanie cudzego,
  martwego kodu jest droższe niż utrzymanie ~350 linii własnych.
* **Kontrola nad jakością wyniku.** Własna implementacja pozwala dołożyć
  kryterium podparcia podstawy (produkty nie „lewitują"), ocenę ciasnoty
  dopasowania i przeszukiwanie wielu strategii naraz — a to właśnie te rzeczy
  decydują o procencie wypełnienia.
* **Zero zależności** dla samego pakowania (matplotlib potrzebny tylko do
  rysowania).

Koszt: trzeba było napisać algorytm. Zysk: pełna kontrola i wynik 45.83% na
danych testowych, czyli **teoretyczne maksimum** (produkty mają łącznie tyle
objętości, ile ten procent kartonu — nic nie zostało na zewnątrz).

## Jak działa algorytm

Heurystyka **Extreme Points** (Crainic, Perron & Toth 2008) z wyborem
najlepszego miejsca i przeszukiwaniem wielostartowym:

1. **Punkty ekstremalne (EP).** Utrzymujemy zbiór punktów-kandydatów, w których
   może stanąć lewy-przedni-dolny narożnik kolejnego produktu. Na starcie tylko
   `(0,0,0)`.
2. **Best-fit, nie first-fit.** Dla każdej sztuki sprawdzamy *wszystkie* pary
   (punkt × dopuszczalna orientacja) i wybieramy najlepszą, zamiast brać
   pierwszą pasującą.
3. **Ocena miejsca.** Dwa tryby, oba są sprawdzane:
   * `dblf` — najpierw jak najniżej i najbliżej narożnika (buduje równe warstwy),
     remisy rozstrzyga większa powierzchnia styku;
   * `contact` — najpierw maksymalny styk ścianek (upycha w szczeliny),
     remisy rozstrzyga położenie.
4. **Nowe EP z rzutowaniem.** Po wstawieniu produktu dodajemy jego trzy narożniki
   *oraz ich rzuty* na najbliższe napotkane ścianki. Rzutowanie jest kluczowe —
   bez niego algorytm nie potrafiłby wykorzystać szczelin obok i pod już
   ułożonymi produktami.
5. **Podparcie.** Produkt musi opierać się na dnie kartonu albo mieć co najmniej
   `SUPPORT_RATIO` (domyślnie 70%) podstawy podpartej innymi produktami. Dzięki
   temu wynik jest fizycznie możliwy do ułożenia, a nie tylko geometrycznie
   poprawny.
6. **Multi-start.** Kolejność wkładania mocno wpływa na wynik heurystyki, a jest
   tania w policzeniu — sprawdzamy 7 kolejności × 2 tryby oceny i bierzemy
   najlepszy wynik. Przerywamy wcześniej, gdy wszystko już się zmieściło.

Złożoność jednego przebiegu to `O(n² × |EP| × |orientacje|)`; dla 70 sztuk to
ułamek sekundy, dla ~150 sztuk rzędu sekundy.

**Walidacja.** `packing.validate()` niezależnie sprawdza wynik: czy nic nie
wystaje poza karton, czy żadne dwa produkty się nie przenikają i czy nie
zapakowano więcej sztuk, niż jest dostępnych. Raport pokazuje jej wynik.

## Wynik na danych testowych

Karton 40×40×60 cm, Produkt A 10×10×4 cm ×50 (obrót OK), Produkt B 15×10×8 cm
×20 (bez obrotu):

```
Produkt       zapakowano  nie weszło  dostępnych        objętość
Produkt A             50           0          50       20 000 cm3
Produkt B             20           0          20       24 000 cm3
RAZEM                 70           0          70       44 000 cm3

WYKORZYSTANIE OBJĘTOŚCI:      45.83 %      (= teoretyczne maksimum)
Wysokość zajętego stosu:      28 cm z 60 cm
Czas obliczeń:                0.13 s
```

Wszystkie sztuki mieszczą się na 28 cm z 60 cm dostępnej wysokości — zostaje
32 cm wolnego miejsca.

## Wizualizacje

| plik | co pokazuje |
|---|---|
| `packing_3d.png` | główny widok 3D: przezroczysty karton + kolorowe produkty + legenda |
| `packing_views.png` | cztery ujęcia (2 × 3/4, z przodu, z góry) |
| `packing_layers.png` | rzuty z góry dla kolejnych poziomów — pokazują to, co schowane w środku |

## Układ współrzędnych

`x` = długość kartonu, `y` = szerokość, `z` = wysokość. Punkt `(0,0,0)` to
lewy-przedni-dolny narożnik. Pozycja produktu w raporcie to współrzędne jego
lewego-przedniego-dolnego narożnika.

Orientacja opisana jest trzema literami mówiącymi, która **oryginalna** krawędź
produktu leży wzdłuż osi X, Y i Z: `D` = długość, `S` = szerokość, `W` = wysokość.
Np. `DSW` to orientacja oryginalna, `SDW` to obrót o 90° wokół osi pionowej.

## Możliwe rozszerzenia

Świadomie pominięte (nie były w zakresie): eksport do CSV/Excela, interfejs,
wczytywanie danych z pliku, ograniczenia wagowe i „co można postawić na czym",
pakowanie do wielu kartonów naraz oraz dobór najmniejszego pasującego kartonu.
Model danych i podział na moduły są przygotowane pod te rozszerzenia.
