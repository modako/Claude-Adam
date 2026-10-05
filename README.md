# Grzyby: prognoza dla grzybiarzy

Prywatna aplikacja mobilna (Android + iOS), która pokazuje na mapie lasy w Polsce pokolorowane według **Indeksu Grzybowego** (0–100):

- 🟢 **≥ 60**: jedź,
- 🟡 **35–59**: warto, jeśli blisko,
- 🔴 **< 35**: nie warto,
- ⬜ **szary**: brak wstępu lub zakaz zbioru (park narodowy, rezerwat, poligon, uprawa leśna).

Indeks łączy **potencjał lasu** (gatunek, wiek i siedlisko drzewostanu z Banku Danych o Lasach) z **pogodą** z ostatnich tygodni i prognozą na 14 dni (Open-Meteo). Region startowy: lubuskie i wielkopolskie.

> Aplikacja **nie rozpoznaje grzybów i nie ocenia ich jadalności**. W razie wątpliwości skonsultuj się z grzyboznawcą.

## Co gdzie jest

| Folder | Zawartość |
|---|---|
| `docs/research.md` | raport z researchu (lasy, model, dane, prawo, konkurencja) |
| `docs/research_z_przypisami.md` | ten sam raport z przypisami i listą źródeł |
| `docs/SPEC.md` | specyfikacja modelu prognozy i wszystkie parametry |
| `docs/PROMPTY.md` | plan pracy: prompty dla kolejnych etapów |
| `CLAUDE.md` | zasady projektu dla Claude Code |
| `pipeline/` | obliczenia w Pythonie (od etapu 1) |
| `app/` | aplikacja mobilna Expo (od etapu 3) |
| `data/` | wygenerowane dane (nie trafiają do repozytorium, poza `data/samples/`) |

## Status

Etap 0 (setup i specyfikacja) zrobiony. Plan wszystkich etapów jest w `CLAUDE.md`.

## Źródła danych i atrybucje

Open-Meteo (CC BY 4.0), © autorzy OpenStreetMap (ODbL), Bank Danych o Lasach (Lasy Państwowe), Generalna Dyrekcja Ochrony Środowiska. Szczegóły i daty pobrania pojawią się w `data/static/attribution.json` (etap 1).
