# -*- coding: utf-8 -*-
"""
Testy pro String Art Generator
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import numpy as np
from string_art import StringArtGenerator
from PIL import Image
import tempfile
import json


class TestStringArtGenerator(unittest.TestCase):
    """Testovaci trida pro StringArtGenerator"""

    def setUp(self):
        """Priprava pro testy"""
        self.generator_circle = StringArtGenerator(num_points=240, image_size=500, shape='circle')
        self.generator_square = StringArtGenerator(num_points=240, image_size=500, shape='square')
        self.generator_star = StringArtGenerator(num_points=240, image_size=500, shape='star')

        # Vytvor testovaci obrazek
        self.test_image_path = tempfile.mktemp(suffix='.png')
        img = Image.new('L', (100, 100), color=255)
        # Nakresli jednoduchy ctverec
        for x in range(30, 70):
            for y in range(30, 70):
                img.putpixel((x, y), 0)
        img.save(self.test_image_path)

    def tearDown(self):
        """Uklid po testech"""
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def test_initialization(self):
        """Test inicializace generatoru"""
        self.assertEqual(self.generator_circle.num_points, 240)
        self.assertEqual(self.generator_circle.image_size, 500)
        self.assertEqual(len(self.generator_circle.points), 240)

    def test_circle_points_generation(self):
        """Test generovani bodu na kruhu"""
        points = self.generator_circle.points
        self.assertEqual(len(points), 240)

        # Kontrola, ze jsou body na kruhu
        center_x, center_y = self.generator_circle.center
        radius = self.generator_circle.radius

        for x, y in points:
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            self.assertAlmostEqual(distance, radius, delta=1.0)

    def test_square_points_generation(self):
        """Test generovani bodu na ctverci"""
        points = self.generator_square.points
        self.assertEqual(len(points), 240)

        # Kontrola, ze jsou body na obvodu ctverce
        center_x, center_y = self.generator_square.center
        radius = self.generator_square.radius

        for x, y in points:
            # Body musi byt na jedne ze stran ctverce
            on_edge = (
                abs(x - (center_x - radius)) < 1.0 or  # leva strana
                abs(x - (center_x + radius)) < 1.0 or  # prava strana
                abs(y - (center_y - radius)) < 1.0 or  # horni strana
                abs(y - (center_y + radius)) < 1.0     # dolni strana
            )
            self.assertTrue(on_edge)

    def test_star_points_generation(self):
        """Test generovani bodu na hvezde"""
        points = self.generator_star.points
        self.assertEqual(len(points), 240)

    def test_point_label(self):
        """Test prekladu indexu bodu na label"""
        # L-H kvadrant (0-59)
        self.assertEqual(self.generator_circle.get_point_label(0), "L-H 1")
        self.assertEqual(self.generator_circle.get_point_label(30), "L-H 31")
        self.assertEqual(self.generator_circle.get_point_label(59), "L-H 60")

        # P-H kvadrant (60-119)
        self.assertEqual(self.generator_circle.get_point_label(60), "P-H 1")
        self.assertEqual(self.generator_circle.get_point_label(90), "P-H 31")

        # D-P kvadrant (120-179)
        self.assertEqual(self.generator_circle.get_point_label(120), "D-P 1")

        # D-L kvadrant (180-239)
        self.assertEqual(self.generator_circle.get_point_label(180), "D-L 1")

    def test_load_and_prepare_image(self):
        """Test nacteni a pripravy obrazku"""
        img_array = self.generator_circle.load_and_prepare_image(self.test_image_path)

        # Kontrola typu a velikosti
        self.assertIsInstance(img_array, np.ndarray)
        self.assertEqual(img_array.shape, (500, 500))
        self.assertEqual(img_array.dtype, np.float32)

        # Kontrola rozsahu hodnot
        self.assertTrue(np.all(img_array >= 0))
        self.assertTrue(np.all(img_array <= 255))

    def test_get_line_pixels(self):
        """Test ziskani pixelu na linii"""
        point_a = (10, 10)
        point_b = (20, 20)

        pixels = self.generator_circle.get_line_pixels(point_a, point_b)

        # Kontrola, ze linie obsahuje oba koncove body
        self.assertIn((10, 10), pixels)
        self.assertIn((20, 20), pixels)

        # Kontrola, ze linie ma rozumnou delku
        self.assertGreater(len(pixels), 0)
        self.assertLess(len(pixels), 20)

    def test_calculate_line_score(self):
        """Test vypoctu skore linie"""
        img_array = self.generator_circle.load_and_prepare_image(self.test_image_path)

        # Vypocitej skore mezi dvema body
        score = self.generator_circle.calculate_line_score(img_array, 0, 100)

        # Skore by melo byt float
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)

    def test_generate_string_art(self):
        """Test generovani string art"""
        lines = self.generator_circle.generate_string_art(
            self.test_image_path,
            num_lines=50,  # Malo linii pro rychly test
            line_weight=25,
            min_distance=20
        )

        # Kontrola vysledku
        self.assertIsInstance(lines, list)
        self.assertGreater(len(lines), 0)
        self.assertLessEqual(len(lines), 50)

        # Kontrola formatu linii
        for line in lines:
            self.assertIsInstance(line, tuple)
            self.assertEqual(len(line), 2)
            point_a, point_b = line
            self.assertGreaterEqual(point_a, 0)
            self.assertLess(point_a, 240)
            self.assertGreaterEqual(point_b, 0)
            self.assertLess(point_b, 240)
            self.assertNotEqual(point_a, point_b)

    def test_export_instructions(self):
        """Test exportu do TXT"""
        lines = [(0, 100), (100, 50), (50, 150)]
        output_path = tempfile.mktemp(suffix='.txt')

        try:
            self.generator_circle.export_instructions(lines, output_path)

            # Kontrola, ze soubor existuje
            self.assertTrue(os.path.exists(output_path))

            # Kontrola obsahu
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("STRING ART TUTORIAL", content)
                self.assertIn("Celkovy pocet tahu: 3", content)
                self.assertIn("L-H", content)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_export_to_csv(self):
        """Test exportu do CSV"""
        lines = [(0, 100), (100, 50), (50, 150)]
        output_path = tempfile.mktemp(suffix='.csv')

        try:
            self.generator_circle.export_to_csv(lines, output_path)

            # Kontrola, ze soubor existuje
            self.assertTrue(os.path.exists(output_path))

            # Kontrola obsahu
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("Step", content)
                self.assertIn("From_Quadrant", content)
                self.assertIn("To_Quadrant", content)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_export_to_json(self):
        """Test exportu do JSON"""
        lines = [(0, 100), (100, 50), (50, 150)]
        output_path = tempfile.mktemp(suffix='.json')

        try:
            self.generator_circle.export_to_json(lines, output_path)

            # Kontrola, ze soubor existuje
            self.assertTrue(os.path.exists(output_path))

            # Kontrola obsahu
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assertIn('metadata', data)
                self.assertIn('instructions', data)
                self.assertEqual(data['metadata']['total_lines'], 3)
                self.assertEqual(len(data['instructions']), 3)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_export_to_svg(self):
        """Test exportu do SVG"""
        lines = [(0, 100), (100, 50), (50, 150)]
        output_path = tempfile.mktemp(suffix='.svg')

        try:
            self.generator_circle.export_to_svg(lines, output_path)

            # Kontrola, ze soubor existuje
            self.assertTrue(os.path.exists(output_path))

            # Kontrola obsahu
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('<svg', content)
                self.assertIn('xmlns', content)
                self.assertIn('<line', content)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


if __name__ == '__main__':
    unittest.main()
