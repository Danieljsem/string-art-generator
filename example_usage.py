"""
Příklad použití String Art Generatoru bez GUI
"""

from src.string_art import StringArtGenerator
import sys

def main():
    # Vytvoř generátor
    print("Inicializuji String Art Generator...")
    generator = StringArtGenerator(num_points=240, image_size=500)

    # Zadej cestu k obrázku
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = input("Zadej cestu k obrázku: ")

    print(f"\nNačítám obrázek: {image_path}")

    # Generuj string art
    print("\nGeneruji string art...")
    print("Toto může trvat několik minut...\n")

    lines = generator.generate_string_art(
        image_path,
        num_lines=2000,      # Počet linií
        line_weight=25       # Váha každé linie
    )

    # Exportuj instrukce
    output_path = "output/instructions.txt"
    print(f"\nExportuji instrukce do: {output_path}")
    generator.export_instructions(lines, output_path)

    print("\n" + "="*50)
    print("HOTOVO!")
    print("="*50)
    print(f"Vygenerováno {len(lines)} linií")
    print(f"Instrukce uloženy v: {output_path}")
    print("\nPrvních 10 tahů:")
    for i, (point_a, point_b) in enumerate(lines[:10], 1):
        label_a = generator.get_point_label(point_a)
        label_b = generator.get_point_label(point_b)
        print(f"  {i}. Spojit: {label_a} -> {label_b}")

if __name__ == "__main__":
    main()
