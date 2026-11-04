#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rychly test s novymi parametry
"""
from src.string_art import StringArtGenerator
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

# Vytvor generator
print("=== STRING ART GENERATOR - Test ===\n")
print("Inicializuji...")
generator = StringArtGenerator(num_points=240, image_size=500, shape='circle')

# Nacti obrazek
image_path = "test.JPEG"
print(f"Načítám: {image_path}")

# Generuj s novymi parametry
print("\nGeneruji string art...")
print("Parametry:")
print("  - Počet linií: 1000 (zkráceno pro test)")
print("  - Váha linie: 15")
print("  - Min. vzdálenost: 20")

lines = generator.generate_string_art(
    image_path,
    num_lines=1000,  # Zkraceno pro rychly test
    line_weight=15,
    min_distance=20
)

print(f"\n✅ Vygenerováno {len(lines)} linií!")

# Vytvor vizualizaci
print("Vytvářím vizualizaci...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

# Original
original = Image.open(image_path).convert('L')
original = original.resize((500, 500), Image.Resampling.LANCZOS)
ax1.imshow(original, cmap='gray')
ax1.set_title('Originál')
ax1.axis('off')

# String art
ax2.set_xlim(0, 500)
ax2.set_ylim(0, 500)
ax2.set_aspect('equal')
ax2.invert_yaxis()
ax2.set_title(f'String Art ({len(lines)} linií)')
ax2.axis('off')
ax2.set_facecolor('white')

for point_a_idx, point_b_idx in lines:
    point_a = generator.points[point_a_idx]
    point_b = generator.points[point_b_idx]
    ax2.plot([point_a[0], point_b[0]], [point_a[1], point_b[1]],
             'k-', linewidth=0.15, alpha=0.3)

plt.tight_layout()
plt.savefig('output/quick_test_result.png', dpi=150, bbox_inches='tight')
print("✅ Uloženo: output/quick_test_result.png")
print("\n=== Test dokončen! ===")
