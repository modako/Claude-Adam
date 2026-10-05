# Aplikacja dla grzybiarzy w Polsce: research do specyfikacji (lasy, model prognozy, dane, prawo, konkurencja)

Najskuteczniejsza będzie aplikacja, która łączy dwie warstwy: **statyczny potencjał lasu** (gatunek panujący, wiek i siedlisko drzewostanu z Banku Danych o Lasach) oraz **dynamiczny indeks pogodowy** (bilans wilgoci z ostatnich 2–4 tygodni, temperatura z ostatnich 5–7 dni, opóźnienie 7–14 dni po opadzie). Do tego dochodzi twarda maska prawna (parki narodowe, rezerwaty, zakazy wstępu, poligony). Lista "znanych regionów" jest tu mniej ważna. Wszyscy polscy konkurenci robią dziś jakąś wersję tego samego, ale żaden nie publikuje walidacji. Przewagę da więc jakość danych o drzewostanach na poziomie wydzielenia, uczciwa kalibracja na własnych zbiorach i miara "presji grzybiarzy". Lista lasów "o których nikt nie wie" może być tylko hipotezą wyliczoną z danych, a nie wiedzą z internetu.

## TL;DR

- **Gdzie:** najlepszy potencjał mają duże, słabo zaludnione kompleksy borów sosnowych i mieszanych: Bory Dolnośląskie (ok. 160–165 tys. ha), Puszcza Notecka (LKP 137 tys. ha), Bory Tucholskie, Lasy Mazurskie/Puszcza Piska, Puszcza Augustowska i Knyszyńska oraz Puszcza Solska z Lasami Janowskimi. Mniej znane kandydatury (np. Bory Stobrawskie, Lasy Lublinieckie, Puszcza Barlinecka i Gorzowska, Lasy Sobiborsko-Włodawskie, Puszcza Sandomierska) to wnioski z przesłanek, nie potwierdzone fakty. Aplikacja powinna je wyliczać sama z BDL i danych o zaludnieniu.
- **Kiedy:** wysyp grzybów mikoryzowych pojawia się zwykle ok. 7–14 dni po obfitym opadzie, jeśli potem jest ciepło, ale nie upalnie. Czeski ČHMÚ liczy to z nasycenia gleby opadami z 30 dni (API30) skorygowanego średnią temperaturą z 7 dni. W pierwszej wersji (v1) preprintu z 10-letniego badania borowika szlachetnego pod Bielefeld optimum wynosiło ok. 13 °C dla średniej z 5 dni. Nie znaleziono tam też owocników przy średniej >17,5 °C połączonej z opadem <1 mm/dobę. Nowsza wersja preprintu wiąże szczyt owocnikowania z temperaturą ok. 13 °C uśrednioną z 20 dni i z opadem sumowanym w oknie 26 dni.
- **Jak zbudować:** Open-Meteo (prognoza do 16 dni, wilgotność i temperatura gleby, za darmo do 10 000 wywołań/dobę do użytku niekomercyjnego; płatny plan Standard daje 1 mln wywołań/mies., ale według cennika nie obejmuje API historycznych ani ansambli), BDL (WMS/WFS + SHP na wniosek), GDOŚ (WMS/WFS/SHP form ochrony przyrody),\[1\] MapLibre + kafelki PMTiles offline. Indeks 0–100 z progami ≥60 zielony, 35–59 żółty, <35 czerwony. Rozpoznawania grzybów ze zdjęcia nie należy oferować jako oceny jadalności. W badaniu Greene i in. (Clinical Toxicology 2023) Picture Mushroom poprawnie rozpoznał 44% trujących okazów, iNaturalist 40%, a Mushroom Identificator 30%.

## Key Findings

1. **Sosna to fundament.** Według Wielkoobszarowej Inwentaryzacji Stanu Lasu (Raport o stanie lasów 2022) sosna zajmuje 58,7% powierzchni lasów Polski, a gatunki iglaste 68,7%.\[2\] Lasy Państwowe (RDLP Szczecinek) piszą wprost, że "największa liczba gatunków grzybów jadalnych związana jest z sosną zwyczajną", a występowanie części gatunków zależy od "stadium rozwoju i wieku drzewostanu".\[3\] Gatunek panujący i wiek drzewostanu z BDL są więc najważniejszymi zmiennymi statycznymi.
2. **Lesistość:** według GUS ("Leśnictwo w 2025 r.") lasy zajmowały na koniec 2025 r. 9290,8 tys. ha, czyli 29,6% powierzchni kraju. Według raportu za 2024 r. najbardziej lesiste jest województwo lubuskie (49,5%), a najmniej łódzkie (21,4%). Lubuskie i zachodniopomorskie (35,9%) to statystycznie najlepsze tereny do szukania mniej obleganych lasów.\[4\]
3. **Pogoda działa z opóźnieniem.** ČHMÚ: grzyby "začínají nejvíce růst po vydatných deštích (cca 10 dní po nich)" i następnie przy ciepłej, ale nie upalnej pogodzie. Model ČHMÚ (współtworzony z Czeskim Towarzystwem Mykologicznym) używa API30 + średniej temperatury z 7 dni + współczynnika sezonowego.\[5\]
4. **Temperatura ma optimum, opad działa raczej liniowo.** Badanie populacji borowika szlachetnego pod Bielefeld (2015–2024, 1905 owocników, preprint bioRxiv bez recenzji) w wersji v1 wskazało optimum 13,2 °C dla średniej z 5 dni i dodatni, liniowy wpływ opadu. Nowsza wersja preprintu podaje inne okna: szczyt przy ok. 13 °C uśrednionych z 20 dni i liniowy wzrost z opadem sumowanym z 26 dni. Większość owocników pojawiała się przy średniej 7–19 °C. Przy średniej >17,5 °C i opadzie <1 mm/dobę nie pojawił się żaden owocnik. W suchym 2016 r. znaleziono tylko 4 owocniki.
5. **Wilgotność gleby jest lepszym predyktorem niż sam opad.** W 22–24-letnich seriach z borów sosnowych środkowej Hiszpanii (Agricultural and Forest Meteorology, 2020) wilgotność gleby z satelitów dorównywała opadowi siłą predykcji (r = 0,63–0,72). NDVI z poprzedniego roku korelował z plonami na poziomie r = 0,41–0,6, a modele łączące oba źródła osiągały średnie R² adj do 0,629. Autorzy z Bielefeld zauważają, że wpływ opadu na wilgotność gleby może się opóźniać nawet o miesiąc.\[6\]
6. **Konkurencja w Polsce jest już gęsta**, ale opiera się na marketingu, a nie na walidacji. Grzyby.pl to raporty grzybiarzy w "grzybach na osobogodzinę", częściowo płatne.\[7\]\[8\] Sezonnagrzyby.pl agreguje zgłoszenia do kwadratów ok. 7×7 km.\[9\] GrzyboRadar daje indeks 0–100 dla 230 punktów z OpenWeather.\[10\] GrzybMappka daje skalę 1–10 dla "każdego lasu" i bierze gatunek panujący z rządowej bazy.\[11\] FungiRadar korzysta z ERA5 i ESA WorldCover 10 m, a mapy gatunkowe są płatne.\[12\]\[13\] Żaden z tych serwisów nie publikuje miar trafności.
7. **Prawo jest liberalne, ale ze stałymi wyłączeniami.** W lasach Skarbu Państwa zbiór na własne potrzeby jest bezpłatny.\[14\] Stały zakaz wstępu obejmuje m.in. uprawy leśne do 4 m wysokości (także bez tablicy), drzewostany nasienne, ostoje zwierząt i źródliska (art. 26 ustawy o lasach).\[15\] Nadleśniczy wprowadza okresowy zakaz wstępu m.in. przy dużym zagrożeniu pożarowym.\[16\]
8. **AI do rozpoznawania grzybów jest niebezpieczne.** W badaniu Greene i in. (Clinical Toxicology 61(3), 2023, Victorian Poisons Information Centre, 78 okazów z lat 2020–2021) Picture Mushroom poprawnie rozpoznał 44% trujących okazów, Mushroom Identificator 30%, a iNaturalist 40%. Muchomor zielonawy był też błędnie przypisywany innym gatunkom: dwa razy przez Picture Mushroom i raz przez iNaturalist.

## Details

### 1. Lasy i regiony grzybowe

#### 1.1 Duże kompleksy: co potwierdzają źródła

- **Bory Dolnośląskie:** Nadleśnictwo Pieńsk (LP) podaje powierzchnię >165 tys. ha z dominacją sosny.\[17\] Encyklopedia Leśna mówi o "największym w Polsce zwartym kompleksie leśnym o pow. ok. 160 tys. ha" z udziałem sosny ok. 93%.\[18\]
- **Puszcza Notecka:** RDLP Piła podaje, że LKP "Puszcza Notecka" ma 137 229 ha i jest "największym leśnym kompleksem promocyjnym w kraju".\[19\] To głównie bory sosnowe na piaszczystych glebach sandrowych, z dużymi obszarami odległymi od miejscowości. Typowe grzyby: podgrzybki, maślaki, kurki, borowiki.\[20\] Często wymieniane okolice: Skwierzyna, Międzychód, Sieraków, Chojno, Lewice, Łowyń.\[21\]
- **Bory Tucholskie:** RDLP Toruń opisuje LKP (84 141 ha) jako część "największego zwartego obszaru leśnego w naszym kraju", z ok. 94% siedlisk borowych.\[22\] Źródła lokalne wymieniają okolice Chojnic, Czerska, Krzywogońca i Śliwic.\[23\]\[24\]\[25\] Uwaga na konflikt: jednostki LP nazywają "największym" zarówno Bory Tucholskie, jak i Bory Dolnośląskie.\[17\]\[22\] Prawdopodobnie jedne liczą cały region, a drugie zwarty kompleks.
- **Lasy Mazurskie / Puszcza Piska:** oficjalna jednostka LKP "Lasy Mazurskie" (nadleśnictwa Strzałowo, Spychowo, Mrągowo, Pisz, Maskulińskie) ma 118 216 ha.\[26\] Wartość ok. 100 tys. ha dla samej Puszczy Piskiej pochodzi tylko ze źródeł wtórnych.\[27\] Dominują bory sosnowe i sosnowo-świerkowe z borowikami, kurkami, podgrzybkami i koźlarzami.\[24\]\[28\]
- **Puszcza Augustowska:** łącznie ok. 160 tys. ha, w Polsce ok. 100–114 tys. ha.\[29\]\[30\] Brak tu oficjalnej liczby LP, więc dane są wtórne.
- **Puszcza Knyszyńska:** LKP 62 319 ha (LP).\[31\] To bory sosnowe z domieszką świerka, dębu i brzozy; serwisy turystyczne wskazują borowiki, podgrzybki i maślaki.\[21\]
- **Puszcza Solska:** ok. 1240 km² (źródła wtórne), w sąsiedztwie Lasów Janowskich i Roztocza.\[32\]
- **Inne regiony wymieniane w mediach i przez grzybiarzy:** Puszcza Zielonka, Puszcza Drawska, Lasy nad Górną Liswartą (pow. lubliniecki), okolice Jeziora Chechło-Nakło, Kaszuby (Kościerzyna, Kartuz, Bytów), Nadleśnictwo Manowo, okolice Gorzowa (Jastrzębsko Stare), Bieszczady, Beskid Niski, Kotlina Jeleniogórska.\[21\]\[23\]\[24\]\[25\]\[28\]\[33\]\[34\] Puszcza Kampinoska to w dużej części park narodowy, a w parkach narodowych i rezerwatach zbiór grzybów jest zakazany.\[35\] Aplikacja musi to wyciąć maską prawną.

Ocena źródeł: większość rankingów "gdzie na grzyby" pochodzi z portali lifestyle'owych i turystycznych (np. kobietamag, travelist, emoti, triverna). Są wtórne, kopiują się nawzajem i nie podają danych. Traktuj je jako wskaźnik **popularności**, a nie obfitości.

#### 1.2 Mniej znane kompleksy o wysokim potencjale (HIPOTEZY)

Poniższe propozycje są **wnioskiem**, a nie potwierdzonym faktem. Nie zmierzyłem liczby wzmianek online. Oparłem się na przesłankach: duży udział boru sosnowego lub mieszanego, wysoka lesistość województwa, oddalenie od aglomeracji i rzadkie występowanie w popularnych rankingach, które przejrzałem.

| Kandydat (hipoteza) | Przesłanki | Co sprawdzić w danych |
|---|---|---|
| Bory Stobrawskie (opolskie) | rozległe bory sosnowe, z dala od dużych miast, rzadko w rankingach | udział So >60%, klasy wieku III–V w BDL |
| Lasy Lublinieckie (śląskie) | lesistość śląskiego 32,1%; pojedyncze wzmianki o borowikach w okolicach Liswarty\[4\]\[21\] | presja z konurbacji śląskiej (to może być raczej las "popularny lokalnie") |
| Puszcza Barlinecka i Gorzowska (lubuskie/zach.-pom.) | najwyższa lesistość w kraju (lubuskie 49,5%), niska gęstość zaludnienia\[4\] | siedliska Bśw/BMśw, wiek >60 lat |
| Bory Lubuskie / okolice Krzeszyc i Rudnicy | raporty o złotoborowikach i koźlarzach w lubuskim\[25\] | lokalne raporty sezonowe |
| Lasy Sobiborskie i Włodawskie (lubelskie) | duże bory na piaskach, peryferyjne położenie, mała gęstość zaludnienia | zakazy wstępu, strefa przygraniczna |
| Puszcza Sandomierska (podkarpackie) | podkarpackie ma 38,4% lesistości; ok. 1100 km² (dane wtórne)\[4\]\[36\] | udział sosny i jodły |
| Puszcza Romincka i Borecka (warm.-maz.) | świerk i sosna, peryferyjne, mała presja | dostęp drogowy, strefa przygraniczna |
| Puszcza Pilicka i Lasy Spalskie (łódzkie/maz.) | bory sosnowe w regionie o niskiej lesistości | presja z Łodzi i Warszawy |

Zalecenie: zamiast utrzymywać ręczną listę, aplikacja powinna liczyć ranking "ukrytych perełek" automatycznie: **wysoki potencjał siedliskowy z BDL × niska presja** (mała liczba mieszkańców w zasięgu 60 min jazdy, mała liczba obserwacji GBIF/iNaturalist i zgłoszeń, brak w rankingach).

#### 1.3 Gatunki a drzewa, siedliska i wiek drzewostanu

| Gatunek | Drzewa żywicielskie / siedlisko | Wiek drzewostanu | Typowe miesiące w Polsce |
|---|---|---|---|
| Borowik szlachetny (*Boletus edulis*) | wiele gatunków iglastych i liściastych (sosna, świerk, buk, dąb); unika gleb wapiennych | wg LP Szczecinek "woli drzewostany młodsze"\[3\] | VI–XI, szczyt VIII–IX |
| Podgrzybek brunatny (*Imleria badia*) | sosna, świerk; lasy iglaste i mieszane, często mszyste runo | "starsze, dojrzewające i dojrzałe drzewostany" (LP)\[3\] | VI–XI, szczyt IX–X |
| Koźlarze (*Leccinum* spp.) | mikoryza z brzozą; także topola, osika, grab\[3\]\[37\] | skraje lasów, młodsze brzeziny | VI–X |
| Maślak zwyczajny (*Suillus luteus*) | sosna | "młode sośniny" (LP)\[3\] | V–XI |
| Maślak żółty (*Suillus grevillei*) | wyłącznie modrzew | — | VI–X (źródła wtórne)\[38\] |
| Kurka (*Cantharellus cibarius*) | sosna, świerk, także dąb i grab; mech lub iglasta ściółka\[3\] | wysokie bory | VI–X |
| Rydz (*Lactarius deliciosus*) | sosna, gleby piaszczyste; mleczaj świerkowy – świerk | często młodsze sośniny | VIII–XI (źródła wtórne)\[39\] |
| Kania (*Macrolepiota procera*) | polany, prześwietlone i trawiaste miejsca; unika wilgotnych i zakwaszonych gleb (LP)\[3\] | luki i skraje | VII–X |
| Opieńki (*Armillaria* spp.) | pniaki, martwe i osłabione drzewa (saprotrof/pasożyt) | zręby, drzewostany po szkodach | IX–XI, szczyt X; jadalne warunkowo, wymagają obgotowania\[40\]\[41\] |
| Gąska zielonka (*Tricholoma equestre*) | bory sosnowe na piaskach | — | IX–XI (Encyklopedia Leśna)\[42\] |
| Gąska niekształtna (*T. portentosum*) | bory iglaste, gleby kwaśne i piaszczyste, sosna i świerk | — | IX–XI\[43\] |

Uwaga dotycząca bezpieczeństwa gąski zielonki: NEJM (Bedry i in., 2001) opisał 12 przypadków opóźnionej rabdomiolizy po spożyciu dużych ilości tego grzyba (według źródeł wtórnych 3 zgony).\[44\]\[45\] Przegląd Klimaszyk i Rzymski (Toxins 2018) uznaje ją za jadalną w rozsądnych ilościach.\[46\] W aplikacji warto napisać: "jadalność sporna, powiązana z rabdomiolizą po wielokrotnym spożyciu dużych ilości". Formalnie gatunek jest na polskiej liście grzybów dopuszczonych do obrotu (Dz.U. 2022 poz. 2365).\[47\]

Wniosek dla modelu: dla każdego wydzielenia z BDL liczymy **wektor przydatności per gatunek**, np. borowik = f(So/Św/Bk/Db, wiek 30–80 lat), podgrzybek = f(So/Św, wiek >50 lat), maślak = f(So, wiek 5–25 lat), koźlarz = f(udział Brz), maślak żółty = f(udział Md). Progi wiekowe są heurystyką do kalibracji. Źródła LP podają kierunek (młodsze/starsze), nie liczby. Hiszpańskie modele dla borowika w borach sosnowych wskazują optimum pierśnicowego pola przekroju ok. 40 m²/ha (Pinar Grande),\[48\] co sugeruje, że liczy się też zwarcie i zasobność drzewostanu.

### 2. Nauka o owocnikowaniu i model prognozy

#### 2.1 Co mówią badania

- **Bielefeld, buczyny (borowik szlachetny):** dzienne zliczenia przez 10 lat, model GLMM. W wersji v1 preprintu (okna 5-dniowe) optimum temperatury wynosiło 13,2 °C (szczyt gęstości obserwacji ok. 15 °C), a wpływ opadu był dodatni i liniowy. Nowsza wersja podaje optimum ok. 13 °C dla średniej z 20 dni i liniowy wzrost z opadem z 26 dni. Sezon owocnikowania trwał łącznie 86 dni (5 VIII–21 XI). Owocniki często pojawiały się bez bieżącego opadu, czyli temperatura ograniczała silniej niż krótkoterminowy deszcz. Wyniki pojawiały się w kilku odrębnych falach w sezonie. Status: preprint bez recenzji.
- **Hiszpania, bory sosnowe:** jesienne opady (IX–XI) korelowały dodatnio z plonem borowika, a wpływu temperatury nie wykryto.\[49\] Plony rydza korelowały dodatnio z opadem i wilgotnością powietrza, a ujemnie z temperaturą maksymalną i minimalną.\[50\] Opady z przełomu lata i jesieni były najważniejszym czynnikiem ekstremalnych wysypów.\[49\] W pracy z Agricultural and Forest Meteorology (2020) wilgotność gleby z satelitów osiągała r = 0,63–0,72, czyli tyle co opad, a połączenie danych klimatycznych z satelitarnymi dało modele ze średnim R² adj do 0,629.
- **Szwajcaria (WSL, rezerwat La Chanéaz, 75 ha):** wieloletnie zliczenia owocników grzybów mikoryzowych korelowały dodatnio z opadami letnimi (VI–X) i z przyrostem drzew.\[51\] Zbiory grzybów mikoryzowych miały szczyty w sierpniu i październiku przy ciepłej i wilgotnej pogodzie (Büntgen i in.).\[52\]
- **Japonia (Sato i in. 2012, 30 lat):** u grzybów mikoryzowych kluczowe były wysoka temperatura i odpowiednia skumulowana suma opadów (miesięczna i tygodniowa). U saprotrofów te zależności nie były tak silne.\[53\]
- **Norwegia (Kauserud i in. 2008, PNAS):** owocnikowanie jesienne przesunęło się później o ok. 13 dni na 60 lat.\[54\] Ciepła jesień i zima opóźniają owocnikowanie także w kolejnym roku.\[55\]
- **Węgry (Scientific Reports 2023, sieci neuronowe):** dla *Russula* i *Amanita* predyktorami były suma temperatur z 3 tygodni, różnice ciśnienia i średnia wilgotność względna z 3 dni.\[56\]
- **Jukon (Krebs i in. 2008):** regresja plonów grzybów na średnich miesięcznych temperaturach i sumach opadów.\[56\]

#### 2.2 Progi praktyczne (heurystyki do kalibracji)

Badania podają kierunki, ale **nie dają jednego uniwersalnego progu mm** dla Polski. Poniższe wartości to moja propozycja startowa, wyprowadzona z powyższych badań i metodologii ČHMÚ. Trzeba ją skalibrować na własnych danych.

- **Wyzwalacz:** opad ≥20 mm w ciągu 1–3 dni lub ≥30–40 mm w 14 dni, przy wilgotności gleby 0–28 cm powyżej mediany sezonowej.
- **Opóźnienie:** odpowiedź zaczyna się w 5.–7. dniu, szczyt przypada na 8.–14. dzień, a wygasanie na 15.–21. dzień. ČHMÚ podaje ok. 10 dni, a mykolog cytowany przez czeskie media "týden až deset dní".\[5\]\[57\]
- **Temperatura:** optimum średniej 5-dniowej ok. 12–16 °C. Poniżej ok. 5 °C i powyżej ok. 20 °C wzrost jest silnie ograniczony. Twardy zakaz: średnia 5-dniowa >17,5 °C przy opadzie <1 mm/dobę.\[6\]
- **Przymrozek:** Tmin < 0 °C przez ≥2 noce wygasza owocnikowanie grzybów mikoryzowych (w Bielefeld monitoring kończono po pierwszym silnym mrozie).\[6\] Opieńki i gąski są odporniejsze, więc dla nich kara powinna być mniejsza.
- **Susza i parowanie:** ten sam opad jest mniej skuteczny w gorącym okresie. ČHMÚ koryguje API30 średnią temperaturą z 7 dni.\[58\] Zamiast samego opadu lepiej liczyć bilans P − ET₀ (Open-Meteo udostępnia ewapotranspirację ET₀).
- **Wiatr i nasłonecznienie:** silny wiatr i pełne słońce przyspieszają wysychanie ściółki. Brak tu ilościowych badań, więc wystarczy mały wpływ przez ET₀.

#### 2.3 Istniejące serwisy prognostyczne

| Serwis | Metoda (wg deklaracji) | Mocne strony | Słabe strony |
|---|---|---|---|
| ČHMÚ – Pravděpodobnost růstu hub (CZ) | API30 + średnia temp. 7 dni + współczynnik sezonowy; z Czeskim Tow. Mykologicznym; codzienna aktualizacja | przejrzysta, instytucjonalna metodologia | brak rozróżnienia gatunków i typu lasu; ČHMÚ sam zaznacza, że kolor nie oznacza grzybów w danym miejscu\[5\]\[59\] |
| HoubyMapa.cz | bilans wodny, wilgotność i temp. gleby, wyzwalacz z opóźnieniem ok. 10 dni, "szok termiczny", anomalia klimatyczna + zgłoszenia | łączy model ze zgłoszeniami\[60\] | brak publicznej walidacji |
| Houbařská mapa (CZ) | ponad 40 zmiennych: las, geologia, pH, wysokość + pogoda; trend na 7 dni, alerty | model per gatunek i sektor\[61\] | marketing, brak walidacji |
| grzyby.pl (PL, M. Snowarski) | raporty grzybiarzy w "grzybach na osobogodzinę"; mapa prognozy oparta na ocenie suchości ściółki | najdłuższa historia, moderacja zgłoszeń | precyzyjne lokalizacje i duża mapa tylko dla płacących; autor przyznaje, że wilgotność ściółki "cechuje się inną dynamiką niż pojaw owocników"\[7\]\[62\]\[63\] |
| sezonnagrzyby.pl | zgłoszenia zaokrąglane do ok. 7×7 km, aktualizacja 8:00/14:00/20:00\[9\] | dobry wzorzec prywatności | sama aktywność, bez modelu |
| GrzyboRadar | OpenWeather, 230 punktów, 0–100, prognoza na 5 dni; ≥60 wysoka, ≥80 bardzo wysoka szansa\[10\] | czytelna skala | punkty, nie poligony; nie uwzględnia typu lasu |
| GrzybMappka | skala 1–10 dla każdego lasu; gatunek panujący z rządowej bazy + pogoda; borowik i podgrzybek\[11\] | idzie w stronę poligonów i drzewostanów | brak walidacji |
| FungiRadar | ERA5 + ESA WorldCover 10 m, "dane z ponad 400 nadleśnictw", AI na 7 dni | bogate dane | kluczowe funkcje płatne; "95% przedział ufności" bez opisu metody\[12\]\[13\] |
| KrainaGrzybow, mapagrzybów.pl | warstwy satelitarne, glebowe, pogodowe | zasięg UE (KrainaGrzybow), iOS | deklaracje marketingowe ("150+ gatunków")\[64\]\[65\] |

Wniosek: rynek jest zatłoczony, ale **nikt nie publikuje trafności** (np. korelacji ze zgłoszeniami). Dla aplikacji prywatnej to nie problem. Dla publicznej transparentna walidacja byłaby wyróżnikiem.

#### 2.4 Proponowany algorytm "Indeksu Grzybowego" (IG 0–100)

Obliczamy osobno dla każdej komórki siatki pogodowej (ok. 0,05–0,1°) i każdego dnia d (od −30 do +14). Następnie łączymy z wydzieleniami z BDL.

**A. Potencjał siedliskowy H ∈ [0,1]** (statyczny, liczony raz w roku):
- H_gat = max po gatunkach grzybów z [przydatność(gatunek panujący, domieszki) × przydatność(wiek) × przydatność(siedlisko)]
- przykład dla borowika: So/Św/Bk/Db = 1,0, Brz = 0,6, Ol = 0,1; wiek 30–80 lat = 1,0, 15–30 = 0,6, >120 = 0,7, uprawa <4 m = 0 (i tak zakaz wstępu); siedliska Bśw/BMśw/LMśw = 1,0, Bb/Ol (bagienne) = 0,2.

**B. Wilgoć M ∈ [0,1]:**
- API_d = Σ_{i=1..30} P_{d−i} · 0,9^i (indeks opadu poprzedzającego, analogia do API30 ČHMÚ)
- Bilans_14 = Σ_{14 dni}(P − ET₀)
- SM = wilgotność gleby 0–28 cm z Open-Meteo, przeliczona na percentyl względem tej samej komórki i miesiąca (z archiwum ERA5-Land)
- M = 0,4·sigmoid((API_d − 25)/8) + 0,3·sigmoid(Bilans_14/10) + 0,3·percentyl(SM)

**C. Wyzwalacz z opóźnieniem L ∈ [0,1]:**
- dla każdego dnia d−k z opadem ≥10 mm: wkład = min(1, P/25) · K(k), gdzie K(k) to jądro gamma ze szczytem w k ≈ 10 dni (k=5→0,3; 8→0,8; 10→1,0; 14→0,7; 21→0,2)
- L = min(1, Σ wkładów)

**D. Temperatura T ∈ [0,1]:**
- T5 = średnia temperatura dobowa z 5 dni; T = exp(−((T5 − 14)/5)²)
- jeśli T5 > 17,5 i średni opad 5-dniowy < 1 mm → T = 0
- jeśli Tmin < 0 °C przez ≥2 z ostatnich 3 nocy → T × 0,3 (dla opieniek i gąsek × 0,7)

**E. Sezon S(miesiąc):** IV 0,1; V 0,3; VI 0,5; VII 0,7; VIII 1,0; IX 1,0; X 0,9; XI 0,4 (do skalibrowania, analogia do współczynnika ČHMÚ).

**F. Wynik:**
- W = 100 · S · T · (0,5·M + 0,5·L)
- **IG = W · (0,4 + 0,6·H)** (słaby las nie dostanie zielonego, ale bardzo dobry las przy złej pogodzie też nie)
- Kolory: **≥60 zielony "jedź"**, **35–59 żółty "warto, jeśli blisko"**, **<35 czerwony "nie warto"**. Szary = brak wstępu (maska prawna).
- **"Kiedy jechać":** dla dni +1…+14 liczymy IG z prognozy, a aplikacja pokazuje dzień maksimum i okno IG ≥60. Niepewność prognozy rośnie z horyzontem, więc dni +8…+14 trzeba wyświetlać jako przedział (min–max z modeli ICON/ECMWF/GFS albo z ansambli Open-Meteo).

**G. Kalibracja (kluczowe dla skuteczności):** zapisuj każdy własny wypad (data, poligon, liczba grzybów na godzinę dla gatunku). Po 30–50 wypadach dopasuj wagi regresją Poissona lub ujemną dwumianową (jak w badaniu z Bielefeld). Uzupełniająco możesz użyć dat obserwacji z GBIF/iNaturalist w Polsce jako sygnału fenologii, nie obfitości.

### 3. Źródła danych

| Dane | Źródło / dostęp | Format | Licencja / koszt | Uwagi |
|---|---|---|---|---|
| Prognoza pogody | Open-Meteo `/v1/forecast` | JSON, wiele współrzędnych w jednym zapytaniu | darmowo niekomercyjnie: 600/min, 5000/h, 10 000/dobę, 300 000/mies.; dane CC BY 4.0 (wymagana atrybucja)\[66\]\[67\] | do 16 dni; wilgotność gleby 0–1, 1–3, 3–9, 9–27, 27–81 cm; temperatura gleby 0/6/18/54 cm; ET₀\[68\]\[69\]\[70\] |
| Pogoda historyczna | Open-Meteo Historical Weather API (ERA5, ERA5-Land) i Historical Forecast API (od 2021) | JSON | jw. | ERA5-Land: wilgotność i temperatura gleby 0–7, 7–28, 28–100 cm; do percentyli i kalibracji\[70\]\[71\] |
| Wersja komercyjna | Open-Meteo API Standard (1 mln wywołań/mies.) i Professional (5 mln/mies.) | — | według cennika open-meteo.com plan Standard nie obejmuje Historical Weather, Historical Forecast ani Ensemble API, które są dopiero w planie Professional; kwoty w USD niepotwierdzone na stronie; serwer open source AGPLv3 (self-hosting) | — |
| Obserwacje IMGW | danepubliczne.imgw.pl: `/api/data/synop`, `/api/data/meteo`, `/api/data/hydro`, ostrzeżenia `/api/data/warningsmeteo`; archiwum CSV od lat 50. | JSON/XML/CSV (CP1250) | dane publiczne wg regulaminu IMGW-PIB | API synop nie zwraca współrzędnych stacji; przydatne do weryfikacji opadów\[72\]\[73\]\[74\] |
| Drzewostany (BDL) | WMS `https://mapserver.bdl.lasy.gov.pl/arcgis/services/WMS_BDL_mapa_drzewostanow/MapServer/WMSServer`; WMS siedlisk `.../WMS_BDL_mapa_siedlisk/...`; WFS `https://wfs.bdl.lasy.gov.pl/geoserver/BDL/ows` (wydzielenia per RDLP); SHP na wniosek per nadleśnictwo (bdl.lasy.gov.pl/portal/wniosek) | WMS/WMTS/WFS/SHP | informacja publiczna; obowiązek podania źródła i czasu pozyskania\[75\] | gatunek panujący, wiek, siedlisko, opis taksacyjny; obejmuje też lasy poza LP (wg PUL)\[76\]\[77\]\[78\]\[79\]\[80\] |
| Zakazy wstępu, zagrożenie pożarowe | WMS BDL `WMS_zakazy_wstepu_do_lasu` i warstwa zagrożenia pożarowego | WMS\[81\]\[82\] | jw. | metoda IBL: pomiary o 9:00 i 13:00, sezon 1 III–30 IX, stopnie 0–3\[83\] |
| Formy ochrony przyrody | GDOŚ: `sdi.gdos.gov.pl/wms`, `sdi.gdos.gov.pl/wfs`, SHP (gov.pl/web/gdos/dostep-do-danych-geoprzestrzennych)\[84\] | WMS/WFS/SHP\[1\] | publiczne | GDOŚ zastrzega, że granice nie stanowią prawnego ustalenia\[85\] |
| Poligony lasów, drogi, parkingi | OpenStreetMap (Geofabrik, extract Polski) | PBF | ODbL (atrybucja, udostępnianie bazy na tej samej licencji) | `landuse=forest`, `natural=wood`, `military=*`, `landuse=military` dla poligonów wojskowych |
| Pokrycie terenu | CORINE Land Cover (Copernicus), ESA WorldCover 10 m | raster/wektor | otwarte | do lasów niepokrytych przez BDL |
| Obserwacje grzybów | GBIF (zbiory polskie, m.in. Rejestr grzybów chronionych i zagrożonych GREJ, 7668 rekordów),\[86\] iNaturalist | Darwin Core Archive / API | rekordy CC0, CC BY lub CC BY-NC; pobranie mieszane dziedziczy CC BY-NC (blokada komercyjna)\[86\]\[87\] | dobre do fenologii i siedlisk; obciążone bliskością miast |

### 4. Popularność lasu ("presja grzybiarzy")

Nie ma publicznego API z liczbą grzybiarzy. Facebook nie udostępnia treści grup, regulamin Google Maps/Places zabrania masowego przechowywania danych, a grzyby.pl i sezonnagrzyby.pl nie mają otwartych API (scraping może naruszać regulaminy). Proponuję więc **indeks presji P (0–100)** z danych otwartych:

- liczba mieszkańców w zasięgu 30 i 60 min jazdy (siatka ludności GUS 1 km + sieć dróg OSM): waga 40%
- dostępność: parkingi leśne, drogi publiczne, infrastruktura turystyczna z WFS BDL (w tym "Zanocuj w lesie", ścieżki): 25%\[77\]
- gęstość obserwacji grzybów GBIF/iNaturalist na km² lasu: 15%
- obecność w popularnych rankingach mediów i liczba zgłoszeń widocznych publicznie (ręczna adnotacja): 20%

Prezentacja: "popularny" (P ≥ 60), "umiarkowany", "mało znany" (P < 30). Ranking "ukryte perełki" = wysokie H, niskie P. W wersji publicznej własne zgłoszenia użytkowników (zagregowane) staną się najlepszym sygnałem presji.

### 5. Prawo i bezpieczeństwo

- **Lasy Skarbu Państwa** są udostępnione ludności, a zbiór grzybów na własne potrzeby jest bezpłatny.\[14\]
- **Stały zakaz wstępu** (art. 26 ustawy o lasach): uprawy leśne do 4 m wysokości, powierzchnie doświadczalne i drzewostany nasienne, ostoje zwierząt, źródliska rzek i potoków, obszary zagrożone erozją.\[88\] Na uprawach do 4 m zakaz obowiązuje nawet bez tablicy.\[15\]
- **Okresowy zakaz** wprowadza nadleśniczy przy zniszczeniu drzewostanów lub degradacji runa, dużym zagrożeniu pożarowym oraz pracach gospodarczych.\[16\] Według LP okresowy zakaz z powodu pożarów wprowadza się, gdy wilgotność ściółki o 9:00 przez 5 kolejnych dni spada poniżej 10%.\[89\]
- **Parki narodowe i rezerwaty:** zbiór zakazany poza miejscami wyznaczonymi przez zarządcę. **Tereny wojskowe:** bezwzględny zakaz.\[35\]
- **Lasy prywatne:** właściciel może wprowadzić zakaz wstępu (oznaczony tablicami).\[88\] Aplikacja powinna rozróżniać formę własności (osobny WMS BDL "kategorie własności") i pokazywać ostrzeżenie.\[90\]
- **Kary:** za zbieranie grzybów w miejscu zakazanym lub w niedozwolony sposób grozi grzywna do 250 zł albo nagana.\[15\] Za naruszenie ochrony gatunkowej media podają kwoty do 5000 zł;\[14\] to informacja wtórna do weryfikacji w Kodeksie wykroczeń.
- **Gatunki chronione:** rozporządzenie Ministra Środowiska z 9 października 2014 r. w sprawie ochrony gatunkowej grzybów (Dz.U. 2014 poz. 1408).\[15\] Pod ochroną ścisłą są m.in. borowik szatański, borowik korzeniasty, borowik królewski, dwupierścieniak cesarski, soplówka jeżowata, żyłkowiec różowawy, opieńka torfowiskowa, koronica ozdobna, trufla wgłębiona i maślak trydencki.\[91\]\[92\]\[93\]\[94\] Pod ochroną częściową są m.in. gąska pomarańczowa i kilka gatunków wodnich.\[95\] Aplikacja powinna mieć listę "nie zbieraj" z tego aktu.
- **Rozpoznawanie ze zdjęcia:** w badaniu Clinical Toxicology (2023, 78 okazów z przypadków zatruć) najlepsza aplikacja rozpoznała 44% trujących. Muchomor zielonawy (*Amanita phalloides*) był też błędnie identyfikowany.\[96\]\[97\] Rekomendacja: **nie implementować oceny jadalności**. Jeśli już pokazywać identyfikację, to tylko jako "podobne gatunki do porównania" z czerwonym ostrzeżeniem i odesłaniem do grzyboznawcy (sanepid) lub ośrodka toksykologicznego. Dla wersji publicznej to również kwestia odpowiedzialności prawnej.

### 6. Konkurencja: luki do wypełnienia

1. **Dokładność przestrzenna:** większość serwisów działa na punktach (230 punktów GrzyboRadaru) lub siatce.\[10\] Indeks liczony na poziomie wydzielenia BDL (las sosnowy 40–80 lat vs uprawa obok) to realna przewaga.
2. **Maska legalności:** połączenie zakazów wstępu, zagrożenia pożarowego, GDOŚ, poligonów i własności prywatnej w jednym widoku "czy mogę tu zbierać dziś".
3. **Miara presji i "ukryte perełki"**, opisane powyżej.
4. **Uczciwa niepewność:** przedziały prognozy na dni 8–14 i publikowana walidacja.
5. **Dziennik prywatny i kalibracja osobista:** model uczy się na Twoich lasach.
6. **Prywatność:** zapis miejscówek lokalnie i agregacja publicznych zgłoszeń do kwadratów ok. 7×7 km (wzorzec sezonnagrzyby.pl).\[9\]

### 7. Rekomendacje techniczne

- **Mapa:** MapLibre GL (JS lub React Native / MapLibre Native) z wektorowymi kafelkami. Podkład z własnego extraktu OSM w formacie **PMTiles** (Protomaps): jeden plik na S3/R2 bez serwera kafelków, a pobranie regionu umożliwia tryb offline. Nie używaj publicznych kafelków tile.openstreetmap.org do aplikacji publicznej, bo polityka OSMF ogranicza intensywne użycie. Warstwy WMS (BDL, GDOŚ) traktuj tylko jako podgląd. Do obliczeń pobierz wektory (WFS/SHP) i zaimportuj do PostGIS.
- **Architektura MVP (prywatnie):**
  1. Jednorazowy ETL: SHP/WFS z BDL (wydzielenia: gatunek panujący, wiek, siedlisko, własność) + GDOŚ + OSM do PostGIS, potem obliczenie H dla każdego wydzielenia i agregacja do "lasów" (np. oddział lub kompleks).
  2. Codzienny cron (np. 05:00): Open-Meteo dla siatki ok. 0,1° nad lasami Polski (rzędu kilku tysięcy punktów, co mieści się w darmowym limicie 10 000 wywołań/dobę).\[70\] Zapis do tabeli `weather_daily(cell_id, date, p, tmean, tmin, et0, sm_0_28)`, a następnie obliczenie IG na dni −30…+14.
  3. Generowanie kafelków z wynikami (np. `tippecanoe` do PMTiles) albo API (FastAPI) zwracające GeoJSON dla widocznego zakresu mapy.
  4. Aplikacja: PWA lub Expo (React Native) + MapLibre; widoki: mapa kolorów na dziś, suwak dni +1…+14, karta lasu (gatunki, H, P, legalność, wykres IG), dziennik wypadów.
- **Ścieżka do wersji publicznej:** licencja komercyjna Open-Meteo albo self-hosting serwera AGPLv3. Plan Standard (1 mln wywołań/mies.) wystarczy do samej prognozy, ale według cennika dostęp do API historycznych i ansambli (potrzebnych do percentyli i kalibracji) daje dopiero plan Professional (5 mln/mies.). Atrybucje: CC BY 4.0 (Open-Meteo), ODbL (OSM), źródło i data pozyskania (BDL), GDOŚ. Unikaj danych CC BY-NC (część GBIF/iNaturalist) w produkcie płatnym albo używaj ich tylko jako filtrów wewnętrznych po analizie prawnej. Prywatność (RODO): lokalizacje zgłoszeń domyślnie prywatne, publicznie tylko zaokrąglone do siatki ok. 7 km i z opóźnieniem 24–48 h; bez śledzenia GPS na serwerze; jasna polityka prywatności. Funkcję "bezpieczny powrót" (ślad GPS) trzymaj lokalnie na urządzeniu.

## Recommendations

1. **Zacznij od 1–2 województw** (np. lubuskie + wielkopolskie: Puszcza Notecka, Barlinecka, Gorzowska) i pełnych danych BDL na poziomie wydzielenia. Nie zaczynaj od punktów dla całej Polski.
2. **Wdrażaj indeks IG etapami:** najpierw W (pogoda), potem H (BDL), potem P (presja), a na końcu kalibracja na własnych wypadach. Bez kalibracji traktuj progi jako hipotezę.
3. **Maska prawna musi być twarda (szary kolor)**, a nie ostrzeżeniem w tekście.
4. **Nie dodawaj rozpoznawania jadalności ze zdjęcia.**
5. **Mierz skuteczność:** dla każdej prognozy zapisuj wynik terenowy i licz korelację rang IG z liczbą grzybów na godzinę.

## Caveats

- Progi w mm i stopniach w algorytmie to propozycje wyprowadzone z badań zagranicznych (Niemcy, Hiszpania, Szwajcaria, Japonia) i metodologii ČHMÚ. Nie ma opublikowanego, zwalidowanego modelu dla Polski. Kluczowe badanie borowika z Bielefeld to preprint bez recenzji.
- Listy "najlepszych lasów" w mediach są wtórne i wzajemnie się kopiują. Mówią więcej o popularności niż o obfitości.
- Sekcja "mało znane kompleksy" to hipoteza, a nie wynik pomiaru liczby wzmianek.
- Powierzchnie Puszczy Piskiej, Augustowskiej i Solskiej pochodzą ze źródeł wtórnych. Liczba stref prognozy pożarowej różni się w źródłach (42 vs 60), więc trzeba ją sprawdzić bezpośrednio w IBL/LP.\[98\]\[99\]
- Deklaracje konkurentów ("AI", "dokładność 10 m", "150+ gatunków") to marketing niezweryfikowany niezależnie.
- Cennik open-meteo.com/en/pricing podaje limity planów (Standard 1 mln, Professional 5 mln wywołań/mies.), ale kwot w USD nie udało się na nim potwierdzić. Plan Standard według tej tabeli nie obejmuje API historycznych ani ansambli, więc przed wdrożeniem sprawdź cenę i zakres planu.

## Tabela podsumowująca regiony

| Region / kompleks | Dominujące grzyby | Drzewostan | Szczyt sezonu | Popularny vs mało znany | Status informacji |
|---|---|---|---|---|---|
| Bory Tucholskie | podgrzybki, maślaki, borowiki, kurki, koźlarze | bór sosnowy\[24\]\[28\]\[100\] | VIII–X | bardzo popularny | potwierdzone (LP, media) |
| Puszcza Notecka | podgrzybki, maślaki, kurki, borowiki | bór sosnowy na piaskach sandrowych\[20\] | IX–X | popularny (rozległy, więc są ciche zakątki) | potwierdzone (LP Piła) |
| Bory Dolnośląskie | borowiki, kurki, koźlarze, podgrzybki | bór sosnowy (ok. 93% So)\[18\]\[28\] | VIII–X | średnio popularny | potwierdzone (LP Pieńsk, Encyklopedia Leśna) |
| Lasy Mazurskie / Puszcza Piska | borowiki, kurki, podgrzybki, koźlarze | bór sosnowo-świerkowy\[26\]\[28\] | VIII–IX | bardzo popularny (turystyka) | potwierdzone (LP: LKP 118 216 ha) |
| Puszcza Augustowska | borowiki, kurki, podgrzybki, rydze | bory i lasy mieszane\[28\] | VIII–X | popularny | częściowo wtórne |
| Puszcza Knyszyńska | borowiki, podgrzybki, maślaki | bór sosnowy z domieszką Św, Db, Brz\[21\]\[31\] | VIII–X | średnio popularny | potwierdzone (LP: LKP 62 319 ha) |
| Puszcza Białowieska | borowiki, koźlarze, rydze, kurki | las mieszany / grąd\[28\] | VIII–X | popularny; duża część to park narodowy i rezerwaty (zakaz) | media |
| Puszcza Solska / Lasy Janowskie / Roztocze | borowiki, podgrzybki, kurki | bory sosnowe i jodłowe | VIII–X | średnio popularny | media |
| Puszcza Kampinoska | kurki, maślaki, podgrzybki | bór sosnowy / mieszany\[28\] | VIII–IX | bardzo popularny; w dużej części park narodowy (zakaz) | media |
| Kaszuby (Kościerzyna, Kartuzy, Bytów) | borowiki, podgrzybki, koźlarze\[25\] | bory i lasy mieszane | VIII–IX | popularny | media (raporty grzyby.pl) |
| Bieszczady / Beskid Niski | borowiki, kurki, opieńki | buczyny, jedlina | VIII–X | średnio popularny | media |
| Lasy nad Górną Liswartą (Lubliniec) | borowiki\[21\] | bory sosnowe | VIII–IX | lokalnie popularny | media |
| Bory Stobrawskie | (oczekiwane) podgrzybki, maślaki, borowiki | bór sosnowy | IX–X | mało znany | HIPOTEZA |
| Puszcza Barlinecka / Gorzowska | (oczekiwane) podgrzybki, borowiki, kurki | bory i lasy mieszane | IX–X | mało znany | HIPOTEZA |
| Lasy Sobiborskie / Włodawskie | (oczekiwane) podgrzybki, maślaki, kurki | bór sosnowy | IX–X | mało znany | HIPOTEZA |
| Puszcza Sandomierska | (oczekiwane) borowiki, podgrzybki | bory sosnowe, jodła | VIII–X | mało znany | HIPOTEZA |
| Puszcza Romincka / Borecka | (oczekiwane) borowiki, kurki, koźlarze | świerk, sosna | VIII–IX | mało znany | HIPOTEZA |

## Sources

1. [GIS Support Dane środowiskowe - GIS Support](https://gis-support.pl/baza-wiedzy-2/dane-do-pobrania/dane-srodowiskowe/)
2. [PAŃSTWOWE GOSPODARSTWO LEŚNE LASY PAŃSTWOWE RAPORT O STANIE LASÓW W POLSCE 2022](https://www.bdl.lasy.gov.pl/portal/Media/Default/Publikacje/raport_o_stanie_lasow_2022.pdf)
3. [Polskie lasy](https://www.szczecinek.lasy.gov.pl/polskie-lasy/-/asset_publisher/x9eK/content/dokad-na-grzyby-poradnik)
4. [RAPORT O STANIE LASÓW W POLSCE 20 24 PAŃSTWOWE GOSPODARSTWO LEŚNE](https://www.lasy.gov.pl/pl/informacje/publikacje/informacje-statystyczne-i-raporty/raport-o-stanie-lasow/raport-o-stanie-lasow-w-polsce-2024.pdf/@@download/file/Raport%20o%20stanie%20las%C3%B3w%20w%20Polsce%202024.pdf)
5. [Biometeorologická předpověď Českého hydrometeorologického ústavu](https://info.chmi.cz/bio/mapy.php?type=houby)
6. <https://www.biorxiv.org/content/10.64898/2025.12.12.693895v1.full.pdf>
7. [Gdzie rosną grzyby? Mapa, która wszystko wyjaśnia](https://www.dobreprogramy.pl/gdzie-rosna-grzyby-mapa-ktora-wszystko-wyjasnia,7012928543697472a)
8. [Gdzie są grzyby? Mapa występowania grzybów w Polsce](https://cafesenior.pl/artykuly/gdzie-sa-grzyby-mapa-wystepowania-grzybow-w-polsce,72309.html)
9. [Mapa grzybów w Polsce](https://sezonnagrzyby.pl/)
10. [Gdzie i kiedy na grzyby? Mapa prawdopodobieństwa występowania grzybów dla całej Polski — dziś i prognoza na 5 dni](https://grzyboradar.pl/)
11. [Mapa wysypu grzybów](https://grzybmappka.pl/)
12. [FungiRadar - Gdzie teraz rosną grzyby?](https://fungiradar.pl/pulpit)
13. [Gdzie na grzyby? Interaktywna Mapa i Prognoza Grzybowa](https://fungiradar.pl/)
14. [Nawet 5 tys. zł grzywny za zbieranie grzybów w tych miejscach. Wielu grzybiarzy popełnia ten błąd](https://www.biznesinfo.pl/nawet-5-tys-zl-grzywny-za-zbieranie-grzybow-w-tych-miejscach-wielu-grzybiarzy-popelnia-ten-blad-jb-wksw-080926)
15. [Nie każdy las jest dla grzybiarzy. Gdzie nie wolno zbierać grzybów? - Zielona w INTERIA.PL](https://zielona.interia.pl/przyroda/news-gdzie-w-polsce-nie-wolno-zbierac-grzybow-miejsca-zakazane-dl,nId,23544002)
16. [Art. 26. lasy - Zakazy wstępu do lasu - Ustawa o lasach](https://arslege.pl/zakazy-wstepu-do-lasu/k110/a18994/)
17. [Bory Dolnośląskie - Nadleśnictwo Pieńsk - Lasy Państwowe](https://piensk.wroclaw.lasy.gov.pl/bory-dolnoslaskie)
18. [Bory Dolnośląskie, Puszcza Zgorzelecka, Puszcza Bolesławicka - Encyklopedia Leśna](https://encyklopedialesna.com/haslo/bory-dolnoslaskie-puszcza-zgorzelecka-puszcza-boleslawicka/)
19. [Leśny Kompleks Promocyjny "Puszcza Notecka" - Leśny Kompleks Promocyjny "Puszcza Notecka" - Regionalna Dyrekcja Lasów Państwowych w Pile - Lasy Państwowe](https://www.pila.lasy.gov.pl/lesny-kompleks-promocyjny/-/asset_publisher/1M8a/content/lesny-kompleks-promocyjny-puszcza-notecka-)
20. [Puszcza Notecka (woj. Wielkopolskie) — szansa na grzyby w lesie](https://grzyboradar.pl/punkty/puszcza-notecka)
21. [Gdzie na grzyby w Polsce? Najlepsze miejsca na grzybobranie](https://travelist.pl/magazyn/gdzie-na-grzyby-w-tym-sezonie)
22. [LKP Bory Tucholskie - Regionalna Dyrekcja Lasów Państwowych w Toruniu - Lasy Państwowe](https://www.torun.lasy.gov.pl/lkp-bory-tucholskie)
23. [Gdzie są grzyby? Najlepsze miejsca w Polsce w 2025 roku - KobietaMag.pl](https://kobietamag.pl/gdzie-na-grzyby-najlepsze-miejsca/)
24. [Kiedy i gdzie na grzyby? Najlepsze miejsca na grzybobranie](https://triverna.pl/blog/gdzie-na-grzyby-w-polsce)
25. [Wrześniowy wysyp grzybów trwa. W tych miejscach borowiki można ścinać kosą. Rosną jak na drożdżach - Kuchnia Mojegotowanie.pl](https://kuchnia.mojegotowanie.pl/artykul/wrzesniowy-wysyp-grzybow-trwa-w-tych-miejscach-borowiki-mozna-scinac-kosa-rosna-jak-na-drozdzach2608)
26. [Leśny Kompleks Promocyjny - Nadleśnictwo Wejherowo - Lasy Państwowe](https://wejherowo.gdansk.lasy.gov.pl/lesny-kompleks-promocyjny-xxxxxxxx-)
27. [Puszcze leśne w Polsce. - Leśne forum dyskusyjne](https://www.lasypolskie.pl/viewtopic.php?t=45418)
28. [Gdzie na grzyby w wakacje 2026? 12 najlepszych regionów + mapa \[+ KALENDARZ\] — KrainaGrzybow.pl](https://krainagrzybow.pl/blog/gdzie-na-grzyby-w-wakacje.html)
29. [Puszcza Augustowska](https://www.splywy.pl/atrakcje-rospuda/puszcza-augustowska.html)
30. [Przyroda](http://www.augustowski.home.pl/przyroda/)
31. [Leśne kompleksy promocyjne — Lasy Państwowe](https://www.lasy.gov.pl/pl/nasze-lasy/lesne-kompleksy-promocyjne)
32. [Puszcza Solska](https://hub.pl/nauka/news-puszcza-solska-zielona-perla-lubelszczyzny-odkryj-jej-najwie,nId,23474189)
33. [Najlepsze lasy w Polsce na jesienne grzybobranie - Emoti.pl](https://www.emoti.pl/pl/artykul/gdzie-na-jesienne-grzybobranie-najlepsze-lasy-w-polsce)
34. [Gdzie szukać borowików i podgrzybków? Te lasy są ich pełne - Kobieta w INTERIA.PL](https://kobieta.interia.pl/porady/news-te-lasy-w-polsce-slyna-z-prawdziwkow-i-podgrzybkow-szukaj-ic,nId,23541662)
35. [UWAGA! ZAKAZ WSTĘPU DO LASU - Grzyby - Nadleśnictwo Gostynin - Lasy Państwowe](https://gostynin.lodz.lasy.gov.pl/grzyby/-/asset_publisher/x9eK/content/uwaga-zakaz-wstepu-do-lasu)
36. [Największe kompleksy leśne w Polsce](https://okiemprzyrodnika.wordpress.com/2016/11/26/najwieksze-kompleksy-lesne-w-polsce/)
37. [ABC grzybobrania — Lasy Państwowe](https://www.lasy.gov.pl/pl/informacje/aktualnosci/abc-grzybobrania)
38. [Maślak żółty / modrzewiowy - jak rozpoznać i gdzie szukać](https://www.grzyby.edu.pl/maslak-zolty/)
39. [Grzyby jadalne - atlas gatunków i trujące sobowtóry](https://au.poznan.pl/grzyby-jadalne/)
40. [Rodzaje grzybów - atlas gatunków polskich](https://www.grzyby.edu.pl/grzyby/)
41. [Kalendarz grzybiarza - Kiedy na grzyby? Zaplanuj grzybobranie](https://rzeszowpodkarpackie.com/kiedy-na-grzyby/)
42. [gąska zielonka (g. żółta) - Encyklopedia Leśna](https://encyklopedialesna.com/haslo/gaska-zielonka-g-zolta/)
43. [Dział Uboczne użytkowanie lasu - Encyklopedia Leśna](https://encyklopedialesna.com/dzialy/uboczne-uzytkowanie-lasu/?strona=2)
44. [Brief Report 798 · N Engl J Med, Vol. 345, No. 11 · September 13, 2001 ·](https://www.nejm.org/doi/pdf/10.1056/nejmoa010581)
45. [Search Results for “search this site …”](https://blog.mycology.cornell.edu/search/search+this+site+.../feed/rss2)
46. [The Yellow Knight Fights Back: Toxicological, Epidemiological, and Survey Studies Defend Edibility of Tricholoma equestre](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6267205/)
47. [Wykaz grzybów dopuszczonych do obrotu lub produkcji ...](https://eli.gov.pl/api/acts/DU/2022/2365/text.html)
48. [Boletus edulis yields are influenced by the basal area of the forest stand](https://interlace-hub.com/casestudy/20556)
49. [Insights into the dynamics of Boletus edulis mycelium and fruiting after fire prevention management](https://www.researchgate.net/publication/319663689_Insights_into_the_dynamics_of_Boletus_edulis_mycelium_and_fruiting_after_fire_prevention_management)
50. [Seasonal dynamics of Boletus edulis and Lactarius deliciosus extraradical mycelium in pine forests of central Spain](https://link.springer.com/article/10.1007/s00572-013-0481-3)
51. [Climate variation effects on fungal fruiting](https://www.mn.uio.no/ibv/english/people/aca/haavarka/boddy-et-al-2014.pdf)
52. [(PDF) Linking climate variability to mushroom productivity and phenology](https://researchgate.net/publication/261976600_Linking_climate_variability_to_mushroom_productivity_and_phenology)
53. [A Thirty-Year Survey Reveals That Ecosystem Function of Fungi Predicts Phenology of Mushroom Fruiting - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3507881/)
54. [Mushroom fruiting and climate change](https://www.pnas.org/doi/pdf/10.1073/pnas.0709037105)
55. [Effects of forest management and climatic variables on the mycelium dynamics and sporocarp production of the ectomycorrhizal fungus Boletus edulis](https://www.researchgate.net/publication/315732864_Effects_of_forest_management_and_climatic_variables_on_the_mycelium_dynamics_and_sporocarp_production_of_the_ectomycorrhizal_fungus_Boletus_edulis)
56. [Verification study on how macrofungal fruitbody formation can be predicted by artificial neural network](https://www.nature.com/articles/s41598-023-50638-8)
57. [Aktuální mapa růstu hub 2026: Houbaři si ještě počkají, příznivé podmínky hlásí jen část Moravy](https://www.kupi.cz/magazin/clanek/45090-mapa-rustu-hub-2026)
58. [Meteorologové spustili mapu předpovědi růstu hub. V části země jsou už podmínky dobré](https://ct24.ceskatelevize.cz/clanek/veda/meteorologove-spustili-mapu-predpovedi-rustu-hub-v-casti-zeme-jsou-uz-podminky-dobre-349638)
59. [Houbaři mají žně. Mapa růstu hub ČHMÚ ukazuje místa s největší šancí na úlovek](https://www.kupi.cz/magazin/clanek/48291-kam-na-houby-zari-2026-mapa)
60. [Houbová mapa](https://houbymapa.cz/)
61. [Houbařská mapa](https://houbarskamapa.cz/)
62. [małopolskie - aktualne doniesienia z grzybobrań](https://www.grzyby.pl/raporty/wystepowanie-MP.htm)
63. [Objaśnienie map występowania grzybów](https://www.grzyby.pl/wystepowanie-objasnienie-map.htm)
64. [Na Grzyby — mapa grzybów i aplikacja na iPhone’a](https://about.mapagrzybow.pl/)
65. [Mapa grzybów — gdzie na grzyby?](https://krainagrzybow.pl/)
66. [🧑‍⚖️ Licence](https://open-meteo.com/en/licence)
67. [Open-Meteo: review, pricing & ABI score · APIbenchmarks](https://apibenchmarks.com/weather/open-meteo)
68. [🌦️ Docs](https://open-meteo.com/en/docs)
69. [💰 Pricing](https://open-meteo.com/en/pricing)
70. [🌤️ Free Open-Source Weather API](https://open-meteo.com/)
71. [🏛️ Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
72. [imgwtools · PyPI](https://pypi.org/project/imgwtools/)
73. [regulamin udostępniania danych - Dane publiczne IMGW-PIB](https://danepubliczne.imgw.pl/apiinfo)
74. [GitHub - abnvle/ha-imgw-pib-monitor: Integracja kompleksowo integrująca dane z API IMGW-PIB · GitHub](https://github.com/abnvle/ha-imgw-pib-monitor)
75. [Witamy w Banku Danych o Lasach - Testowe udostępnianie](https://www.bdl.lasy.gov.pl/portal/wniosek)
76. [Bank Danych o Lasach - BULiGL PL](https://buligl.pl/en/w/projekt-bdl)
77. [Witamy w Banku Danych o Lasach - Usługi OGC](https://www.bdl.lasy.gov.pl/portal/uslugi-ogc?v=4)
78. [Witamy w Banku Danych o Lasach - Usługi OGC](https://www9.bdl.lasy.gov.pl/portal/uslugi-ogc?v=1)
79. [Bez tytułu](https://api.dane.gov.pl/1.4/catalog/dataset/629.rdf?lang=pl)
80. [DARMOWE ŹRÓDŁA DANYCH PRZESTRZENNYCH |](https://geoportal.um.gorzow.pl/darmowe-zrodla-danych_przestrzennych/)
81. [Nowe usługi OGC w Banku Danych o Lasach](https://www.gisplay.pl/gis/11033-nowe-uslugi-ogc-w-banku-danych-o-lasach.html)
82. [Witamy w Banku Danych o Lasach - Usługi OGC](https://www4.bdl.lasy.gov.pl/portal/uslugi-ogc-en?v=4)
83. [stopień zagrożenia pożarowego lasu (metoda IBL) - Encyklopedia Leśna](https://encyklopedialesna.com/haslo/stopien-zagrozenia-pozarowego-lasu-metoda-ibl/)
84. [Nowe dane przestrzenne GDOŚ](https://kp.org.pl/pl/informacje/1164-nowe_dane_przestrzenne_gdos)
85. [Dostęp do danych geoprzestrzennych - Generalna Dyrekcja Ochrony Środowiska - Portal Gov.pl](https://www.gov.pl/web/gdos/dostep-do-danych-geoprzestrzennych)
86. [9364686 occurrences included in download](https://gbif.org/occurrence/download/0224653-200613084148143)
87. [USDA United States National Fungus Collections](https://www.gbif.org/dataset/d1a3b128-b406-46bb-a6d1-f3591dcc8a7b)
88. [Art. 26. Zakazy wstępu do lasu Ustawa o lasach](https://prawnik.cc/laws/ustawa-o-lasach/rozdzial-5-zasady-udostepniania-lasow-art-26-zakazy-wstepu-do)
89. [Zagrożenie pożarowe - Nadleśnictwo Nowa Dęba - Lasy Państwowe](https://nowadeba.lublin.lasy.gov.pl/zagrozenie-pozarowe)
90. [Usługi - WMS - Bank Danych o Lasach](https://www9.bdl.lasy.gov.pl/portal/uslugi-mapowe-ogc)
91. [ROZPORZĄDZENIE MINISTRA ŚRODOWISKA z dnia 9 października 2014 r. w sprawie ochrony gatunkowej grzybów - Tekst pierwotny - Baza aktów prawnych - INFOR.pl - portal księgowych](https://www.infor.pl/akt-prawny/DZU.2014.197.0001408,rozporzadzenie-ministra-srodowiska-w-sprawie-ochrony-gatunkowej-grzybow.html)
92. [Rozporządzenie - DZIENNIK USTAW](https://eli.gov.pl/api/acts/DU/2014/1408/text/I/D20141408.pdf)
93. [DZIENNIK USTAW RZECZYPOSPOLITEJ POLSKIEJ](https://dziennikustaw.gov.pl/D2014000140801.pdf)
94. [DZIENNIK USTAW RZECZYPOSPOLITEJ POLSKIEJ](https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20140001408/O/D20141408.pdf)
95. [grzyby chronione](https://www.grzyby.pl/lista-chronionych.htm)
96. [A comparison of the accuracy of mushroom identification applications using digital photographs: Clinical Toxicology: Vol 61, No 3](https://www.tandfonline.com/doi/abs/10.1080/15563650.2022.2162917)
97. [Mushrooming Risk: Unreliable A.I. Tools Generate Mushroom Misinformation - Public Citizen](https://www.citizen.org/article/mushroom-risk-ai-app-misinformation/)
98. [Najwyższy stopień zagrożenia pożarowego w lasach w niemal całym kraju](https://www.teraz-srodowisko.pl/aktualnosci/najwyzszy0stopien-zagrozenia-pozarowego-w-lasach-8586.html)
99. [Zagrożenie pożarowe](https://starogard.gdansk.lasy.gov.pl/aktualnosci/-/asset_publisher/1M8a/content/zagrozenie-pozarowe-wazne-informacje/pop_up)
100. [Leśne skarby](https://www.chaberapart.pl/atrakcje/szczegoly-atrakcji?RecordID=85605)
