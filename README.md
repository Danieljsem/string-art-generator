# String Art Generator

Generate string-art (thread-art) instructions from any image. The algorithm places
pins around a shape and greedily picks the chord (thread) that best reduces the
difference to the target image, repeating until the picture emerges. Includes a GUI
and CLI, multiple shapes, and several export formats.

**Tech:** Python · NumPy (vectorized core) · Tkinter GUI · 13 unit tests

| | |
|---|---|
| Shapes | circle, square, 5-point star |
| Export | TXT (manual instructions), CSV, JSON, SVG |
| Interfaces | GUI (Tkinter) and CLI |

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
sudo apt-get install python3-tk      # GUI only

./venv/bin/python src/main.py                     # GUI
./venv/bin/python example_usage.py path/to/image.png   # CLI
./venv/bin/python -m unittest tests.test_string_art    # tests
```

---

# String Art Generator v3.0 (CZ)

Pokročilý generátor instrukcí pro vytváření string art z obrázků s podporou různých tvarů a exportních formátů.

## ✨ Funkce

- 🎨 **Různé tvary**: Kruh, čtverec, hvězda
- 📊 **Více exportních formátů**: TXT, CSV, JSON, SVG
- 🚀 **Optimalizovaný algoritmus**: NumPy vektorizace pro rychlost
- 🖥️ **GUI i CLI rozhraní**: Pro všechny typy použití
- ✅ **Komplexně otestováno**: 13 unit testů

## Použití

### GUI verze (doporučeno)
```bash
./venv/bin/python src/main.py
```
- Výběr tvaru (kruh/čtverec/hvězda)
- Export do 4 formátů (TXT/CSV/JSON/SVG)
- Vizualizace výsledku a přizpůsobitelné parametry

### CLI verze
```bash
./venv/bin/python example_usage.py cesta/k/obrazku.png
```

## Exportní formáty
- **TXT** – instrukce pro ruční vytvoření (`1. Spojit: L-H 31 -> D-L 30`)
- **CSV** – pro tabulkové zpracování
- **JSON** – s kompletními metadaty
- **SVG** – vektorová grafika (prohlížeč, Illustrator, Inkscape)

## Tvary
- **Kruh** – 240 bodů rovnoměrně po kružnici
- **Čtverec** – 60 bodů na každé straně
- **Hvězda** – 5-cípá, plynulý přechod vnějšího/vnitřního poloměru

## Verze
- **v3.0** – NumPy optimalizace, 3 tvary, 4 exportní formáty, 13 testů
- **v2.0** – inteligentní výběr startu, minimální vzdálenost bodů
- **v1.0** – první funkční verze (algoritmus, GUI + CLI)

## License

MIT — see [LICENSE](LICENSE). Free for personal and commercial use.
