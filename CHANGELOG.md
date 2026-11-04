# Changelog

## [5.0] - 2026-01-19 (E-Shop Edition)

### ✨ Nove funkce pro e-shop

- **Presety pro ruzne typy obrazku**:
  - `portrait` - pro obliceje a portrety
  - `pet` - pro domaci mazlicky
  - `logo` - pro loga a grafiku
  - `landscape` - pro krajiny
  - `high_detail` - maximum detailu
  - `quick` - rychly projekt pro zacatecniky
  - `wedding` - svatebni fotky
  - `minimalist` - abstraktni vzhled
  - `child` - detske portrety

- **Automaticka analyza obrazku**:
  - `analyze_image_suitability()` - hodnoceni vhodnosti pro string art
  - Automaticka detekce optimalniho kontrastu
  - Quality scoring (0-100)
  - Doporuceni pro zlepseni

- **Material Estimator**:
  - Odhad delky nite v metrech
  - Odhad poctu civek
  - Odhadovana cena materialu
  - Odhad casu sestaveni podle urovne dovednosti

- **Image Validator**:
  - Komplexni validace vstupnich obrazku
  - Kontrola formatu, velikosti, rozliseni
  - Varovani a doporuceni

- **Edge Enhancement**:
  - Zesioleni hran pro lepsi detail
  - Sobel operator pro detekci hran
  - Konfigurovatelna sila (0-50%)

### ⚡ Vykonne vylepseni

- **Multi-threading akcelerace**:
  - `generate_string_art_parallel()` - paralelni generovani
  - ThreadPoolExecutor pro vypocet skore
  - 2-4x zrychleni na vicejadrových CPU

- **Presety s optimalizovanym nastavenim**:
  - Kazdy preset ma optimalni parametry
  - `generate_with_preset()` pro snadne pouziti

### 🖥️ GUI vylepseni

- Sekce rychlych presetu s jednim kliknutim
- Tlacitko pro analyzu obrazku
- Zobrazeni kvality obrazku
- Odhad materialu a casu primo v GUI
- Edge enhancement slider
- Aktualizovane labely a informace

### 📄 Dokumentace

- `ESHOP_IMPLEMENTATION_PLAN.md` - kompletni plan implementace e-shopu
- Nove moduly: `presets.py`, `validators.py`, `estimator.py`

---

## [4.0] - 2025-10-12

### ✨ Pridano
- **Opraveny algoritmus podle vyzkumu**:
  - Suma misto prumeru pixelu (lepsi vysledky)
  - Optimalni line weight 30-100
  - Automaticky kontrast +30%
  - Automaticka ostrost +20%

- **Rezimy rychlosti**:
  - `ultra_fast` - ~30s, 92% presnost
  - `fast` - ~1.5min, 97% presnost
  - `precise` - ~3min, 100% presnost

- **Cachovani vypoctu**:
  - Bresenhamuv algoritmus s cache
  - 2-3x zrychleni

- **Nove exporty**:
  - HTML interaktivni tutorial
  - PDF tisknutelny navod
  - Pin diagram SVG
  - High-quality PNG export

- **Vizualizace**:
  - Opacity niti (0.05-0.4)
  - Sirka niti (0.3-2.0)
  - Zobrazeni pinu
  - Antialiasing

- **Image Editor**:
  - Interaktivni crop/zoom/rotate
  - Automaticky fit do kruhu
  - Real-time nahled

### 🔧 Opraveno
- RingString kompatibilita (A/B/C/D kvadranty)
- Vylepseny format instrukci s checkboxy

---

## [3.0] - 2025-10-12

### ✨ Přidáno
- **Různé tvary**: Podpora pro kruh, čtverec a hvězdu
  - `StringArtGenerator(shape='circle')` - klasický kruhový tvar
  - `StringArtGenerator(shape='square')` - čtvercový tvar
  - `StringArtGenerator(shape='star')` - 5-cípá hvězda
  
- **Nové exportní formáty**:
  - CSV export (`export_to_csv()`) - strukturovaná data pro tabulkové zpracování
  - JSON export (`export_to_json()`) - kompletní metadata a souřadnice
  - SVG export (`export_to_svg()`) - vektorová grafika

- **GUI vylepšení**:
  - Dropdown menu pro výběr exportního formátu
  - Combobox pro výběr tvaru
  - Lepší organizace UI

- **Testování**:
  - 13 komplexních unit testů
  - Testy pro všechny tvary
  - Testy pro všechny exportní formáty

### 🔧 Opraveno
- **RuntimeWarning overflow**: Použití float32 místo uint8 při načítání obrázků
- Encoding issues v celém projektu

### ⚡ Optimalizace
- **NumPy vektorizace**: Rychlejší výpočet skóre linií
- Optimalizované výpočty pomocí vektorizovaných operací
- Lepší správa paměti s float32

### 📚 Dokumentace
- Aktualizovaný README.md s novou strukturou
- Rozšířený claude.md s detaily o všech nových funkcích
- Přidán CHANGELOG.md

## [2.0] - 2025-10-11

### ✨ Přidáno
- Inteligentní výběr startovního bodu
- Parametr `min_distance` pro minimální vzdálenost mezi body

### 🔧 Opraveno
- Lepší distribuce linií po celém obraze
- Prevence krátkých spojení mezi sousedními body

## [1.0] - 2025-10-11

### ✨ Přidáno
- První funkční verze
- Základní algoritmus pro generování string art
- GUI rozhraní (Tkinter)
- CLI rozhraní
- Export do TXT formátu
- 240 bodů rozmístěných po kruhu
- Systém kvadrantů (L-H, P-H, D-P, D-L)
