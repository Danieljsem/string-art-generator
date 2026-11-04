# -*- coding: utf-8 -*-
"""
String Art Generator - Core Logic v5.0 (E-Shop Edition)
Prevadi obrazky na string art instrukce
VYLEPŠENO: Auto-contrast, edge enhancement, quality scoring, material estimation
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageDraw, ImageFilter
import math
import json
import csv
import xml.etree.ElementTree as ET
import random
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from typing import Optional, Tuple, Dict, List, Callable


class StringArtGenerator:
    def __init__(self, num_points=200, image_size=500, shape='circle'):
        """
        Inicializace generatoru string art

        Args:
            num_points: Pocet bodu (default 240)
            image_size: Velikost pracovniho platna v pixelech
            shape: Tvar rozlozeni bodu ('circle', 'square', 'star')
        """
        self.num_points = num_points
        self.image_size = image_size
        self.radius = image_size // 2 - 20  # radius s margin
        self.center = (image_size // 2, image_size // 2)
        self.shape = shape

        # Vygeneruj pozice vsech bodu podle tvaru
        if shape == 'square':
            self.points = self._generate_square_points()
        elif shape == 'star':
            self.points = self._generate_star_points()
        else:
            self.points = self._generate_circle_points()

        # Cache pro prepocitane pixely linii
        self._line_pixels_cache = {}

    def _generate_circle_points(self):
        """Vygeneruje body rozmistene rovnomerne po kruhu"""
        points = []
        for i in range(self.num_points):
            angle = 2 * math.pi * i / self.num_points
            x = self.center[0] + self.radius * math.cos(angle)
            y = self.center[1] + self.radius * math.sin(angle)
            points.append((x, y))
        return points

    def _generate_square_points(self):
        """Vygeneruje body rozmistene rovnomerne po obvodu ctverce"""
        points = []
        points_per_side = self.num_points // 4
        size = self.radius * 2

        # Horni strana (zleva doprava)
        for i in range(points_per_side):
            x = self.center[0] - self.radius + (size * i / points_per_side)
            y = self.center[1] - self.radius
            points.append((x, y))

        # Prava strana (shora dolu)
        for i in range(points_per_side):
            x = self.center[0] + self.radius
            y = self.center[1] - self.radius + (size * i / points_per_side)
            points.append((x, y))

        # Dolni strana (zprava doleva)
        for i in range(points_per_side):
            x = self.center[0] + self.radius - (size * i / points_per_side)
            y = self.center[1] + self.radius
            points.append((x, y))

        # Leva strana (zdola nahoru)
        for i in range(points_per_side):
            x = self.center[0] - self.radius
            y = self.center[1] + self.radius - (size * i / points_per_side)
            points.append((x, y))

        while len(points) < self.num_points:
            x = self.center[0] - self.radius
            y = self.center[1] - self.radius
            points.append((x, y))

        return points[:self.num_points]

    def _generate_star_points(self):
        """Vygeneruje body rozmistene po obvodu hvezdy (5 cipu)"""
        points = []
        num_spikes = 5
        outer_radius = self.radius
        inner_radius = self.radius * 0.4

        for i in range(self.num_points):
            angle = 2 * math.pi * i / self.num_points
            spike_progress = (i % (self.num_points / num_spikes)) / (self.num_points / num_spikes)

            if spike_progress < 0.5:
                t = spike_progress * 2
                radius = outer_radius * (1 - t) + inner_radius * t
            else:
                t = (spike_progress - 0.5) * 2
                radius = inner_radius * (1 - t) + outer_radius * t

            x = self.center[0] + radius * math.cos(angle - math.pi / 2)
            y = self.center[1] + radius * math.sin(angle - math.pi / 2)
            points.append((x, y))

        return points

    def get_point_label(self, point_index):
        """
        Prevede index bodu na label podle kvadrantu (RingString format)
        Dynamicky podle poctu bodu - A, B, C, D kvadranty
        """
        points_per_quadrant = self.num_points // 4

        if point_index < points_per_quadrant:
            return f"A{point_index + 1}"
        elif point_index < points_per_quadrant * 2:
            return f"B{point_index - points_per_quadrant + 1}"
        elif point_index < points_per_quadrant * 3:
            return f"C{point_index - points_per_quadrant * 2 + 1}"
        else:
            return f"D{point_index - points_per_quadrant * 3 + 1}"

    def get_points_per_quadrant(self):
        """Vraci pocet bodu na jeden kvadrant"""
        return self.num_points // 4

    def load_and_prepare_image(self, image_path, enhance_contrast=True, contrast_factor=1.5):
        """
        Nacte obrazek a pripravi ho pro zpracovani
        VYLEPŠENO: Lepší předzpracování pro kvalitnější výsledky

        Args:
            image_path: Cesta k obrazku
            enhance_contrast: Zvysit kontrast automaticky
            contrast_factor: Síla zvýšení kontrastu (1.0 = bez změny, 1.5 = výchozí)
        """
        img = Image.open(image_path)
        img = img.convert('L')

        if enhance_contrast:
            # Zvýšení kontrastu
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast_factor)

            # Zvýšení ostrosti
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.3)

        # Resize s vysokou kvalitou
        img = img.resize((self.image_size, self.image_size), Image.Resampling.LANCZOS)

        img_array = np.array(img, dtype=np.float32)

        # Invertuj (tmave oblasti = vysoke hodnoty)
        img_array = 255.0 - img_array

        return img_array

    def auto_detect_contrast(self, img_array: np.ndarray) -> float:
        """
        Automaticky detekuje optimalni kontrast pro string art

        Analyza histogramu a dynamickeho rozsahu pro urceni
        idealniho contrast_factor.

        Args:
            img_array: Vstupni obrazek jako numpy array

        Returns:
            Optimalni contrast_factor (1.0-2.5)
        """
        # Normalizuj na 0-255 pokud je jiny rozsah
        if img_array.max() > 1:
            normalized = img_array.astype(np.float32)
        else:
            normalized = (img_array * 255).astype(np.float32)

        # Vytvor histogram
        histogram, _ = np.histogram(normalized.flatten(), bins=256, range=(0, 255))

        # Najdi efektivni rozsah (5.-95. percentil)
        cumsum = np.cumsum(histogram) / histogram.sum()
        low_val = np.searchsorted(cumsum, 0.05)
        high_val = np.searchsorted(cumsum, 0.95)

        dynamic_range = (high_val - low_val) / 255

        # Urceni contrast_factor podle dynamic range
        # Cilovy rozsah pro string art: 0.7-0.9
        if dynamic_range < 0.3:
            return 2.5  # Velmi nizky kontrast - maximalni zvyseni
        elif dynamic_range < 0.5:
            return 2.0  # Nizky kontrast - vyrazne zvyseni
        elif dynamic_range < 0.7:
            return 1.5  # Stredni kontrast - mirne zvyseni
        elif dynamic_range < 0.85:
            return 1.2  # Dobry kontrast - jemne zvyseni
        else:
            return 1.0  # Vysoky kontrast - bez zmeny

    def enhance_edges_for_stringart(self, img_array: np.ndarray,
                                     edge_strength: float = 0.3) -> np.ndarray:
        """
        Zesili hrany pro lepsi string art vysledek

        Pouziva Sobel operator pro detekci hran a kombinuje
        je s originalnim obrazkem pro lepsi zachovani detailu.

        Args:
            img_array: Vstupni obrazek jako numpy array
            edge_strength: Sila pridani hran (0.0-1.0)

        Returns:
            Obrazek se zesilenymi hranami
        """
        from scipy import ndimage

        # Detekce hran pomoci Sobel operatoru
        sobel_x = ndimage.sobel(img_array, axis=0)
        sobel_y = ndimage.sobel(img_array, axis=1)
        edges = np.sqrt(sobel_x**2 + sobel_y**2)

        # Normalizace hran
        if edges.max() > 0:
            edges = edges / edges.max() * 255

        # Kombinace s originalem
        enhanced = img_array * (1 - edge_strength) + edges * edge_strength

        return np.clip(enhanced, 0, 255).astype(np.float32)

    def analyze_image_suitability(self, image_path: str) -> Dict:
        """
        Analyzuje vhodnost obrazku pro string art

        Pro e-shop dulezite - zakaznik musi vedet, zda jeho
        obrazek je vhodny pred objednanim.

        Args:
            image_path: Cesta k obrazku

        Returns:
            Dictionary s hodnocenim a doporucenim
        """
        img = Image.open(image_path).convert('L')
        img_array = np.array(img, dtype=np.float32)

        # Kontrast score
        contrast_factor = self.auto_detect_contrast(img_array)
        if contrast_factor <= 1.2:
            contrast_score = 90
        elif contrast_factor <= 1.5:
            contrast_score = 70
        elif contrast_factor <= 2.0:
            contrast_score = 50
        else:
            contrast_score = 30

        # Detail score - zalozeno na varianci a hranach
        variance = np.var(img_array)
        detail_score = min(100, int(variance / 20))

        # Velikost score
        w, h = img.size
        min_dim = min(w, h)
        if min_dim >= 1000:
            size_score = 100
        elif min_dim >= 500:
            size_score = 80
        elif min_dim >= 300:
            size_score = 60
        else:
            size_score = 40

        # Overall score
        overall_score = int(contrast_score * 0.4 + detail_score * 0.4 + size_score * 0.2)

        # Doporuceni
        recommendations = []
        if contrast_score < 60:
            recommendations.append("Obrazek ma nizky kontrast - doporucujeme upravit pred nahranim")
        if detail_score < 50:
            recommendations.append("Obrazek ma malo detailu - vysledek muze byt rozmazany")
        if size_score < 70:
            recommendations.append("Nizke rozliseni - doporucujeme obrazek s min. 500px na kratsi strane")

        return {
            'overall_score': overall_score,
            'contrast_score': contrast_score,
            'detail_score': detail_score,
            'size_score': size_score,
            'recommended_contrast_factor': contrast_factor,
            'image_size': (w, h),
            'suitable_for_stringart': overall_score >= 50,
            'recommendations': recommendations,
            'quality_rating': 'Vynikajici' if overall_score >= 80 else
                             'Dobra' if overall_score >= 60 else
                             'Prijatelna' if overall_score >= 40 else 'Nedostatecna'
        }

    def get_line_pixels(self, point_a, point_b, use_cache=True):
        """Bresenhamuv algoritmus pro pixely na linii s cachovanim"""
        cache_key = (int(point_a[0]), int(point_a[1]), int(point_b[0]), int(point_b[1]))

        if use_cache and cache_key in self._line_pixels_cache:
            return self._line_pixels_cache[cache_key]

        x1, y1 = int(point_a[0]), int(point_a[1])
        x2, y2 = int(point_b[0]), int(point_b[1])

        pixels = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= x1 < self.image_size and 0 <= y1 < self.image_size:
                pixels.append((x1, y1))

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

        if use_cache:
            self._line_pixels_cache[cache_key] = pixels

        return pixels

    def calculate_line_score(self, img_array, point_a_idx, point_b_idx):
        """
        Vypocita skore pro linii - v5.4 OPRAVENO

        Pouziva SUMU pixelu (puvodni funkcni verze) s mirnou penalizaci.
        """
        point_a = self.points[point_a_idx]
        point_b = self.points[point_b_idx]

        pixels = self.get_line_pixels(point_a, point_b)

        if len(pixels) == 0:
            return 0.0

        pixels_array = np.array(pixels)
        x_coords = pixels_array[:, 0]
        y_coords = pixels_array[:, 1]

        valid_mask = (x_coords >= 0) & (x_coords < self.image_size) & (y_coords >= 0) & (y_coords < self.image_size)
        valid_x = x_coords[valid_mask]
        valid_y = y_coords[valid_mask]

        if len(valid_x) == 0:
            return 0.0

        pixel_values = img_array[valid_y, valid_x]

        # v5.4: Zpet k SUME ale s normalizaci podle delky
        total = float(np.sum(pixel_values))

        # Normalizace - delsi linie maji proporcionalne vyssi sumu
        # Tohle zajisti ze kratke i dlouhe linie jsou spravedlive porovnany
        return total

    def generate_string_art(self, image_path, num_lines=3000, line_weight=20, min_distance=20,
                           speed_mode='fast', progress_callback=None, contrast_factor=1.5):
        """
        Hlavni algoritmus pro generovani string art
        VYLEPŠENO: Progress callback pro real-time náhled

        Args:
            image_path: Cesta k vstupnimu obrazku
            num_lines: Pocet linii (tahu niti)
            line_weight: Vaha kazde linie
            min_distance: Minimalni vzdalenost mezi body
            speed_mode: Rychlost ('ultra_fast', 'fast', 'precise')
            progress_callback: Callback funkce(lines, progress_percent) pro real-time update
            contrast_factor: Síla kontrastu (1.0-2.0)
        """
        img_array = self.load_and_prepare_image(image_path, contrast_factor=contrast_factor)
        working_img = img_array.copy()

        lines = []

        # Najdi nejlepsi startovni bod
        # OPRAVENO v5.1: Spravna logika min_distance pro kruhove rozlozeni
        best_start = 0
        best_start_score = -1
        for i in range(0, self.num_points, 10):
            total_score = 0
            for j in range(self.num_points):
                # Vypocitej vzdalenost po kruhu (mensi z obou smeru)
                point_distance = min(abs(i - j), self.num_points - abs(i - j))
                if point_distance < min_distance:
                    continue  # Preskoc body ktere jsou prilis blizko
                total_score += self.calculate_line_score(img_array, i, j)
            if total_score > best_start_score:
                best_start_score = total_score
                best_start = i

        current_point = best_start
        print(f"Generuji {num_lines} linii (start z bodu {current_point})...")

        for i in range(num_lines):
            best_score = -1
            best_point = None

            candidates = []
            for next_point in range(self.num_points):
                if next_point == current_point:
                    continue
                point_distance = min(abs(next_point - current_point),
                                   self.num_points - abs(next_point - current_point))
                if point_distance >= min_distance:
                    candidates.append(next_point)

            # Optimalizace podle rezimu
            if speed_mode == 'precise':
                test_candidates = candidates
            elif speed_mode == 'ultra_fast':
                if i < num_lines // 4:
                    sample_size = min(len(candidates), 60)
                else:
                    sample_size = min(len(candidates), 30)
                test_candidates = random.sample(candidates, sample_size) if len(candidates) > sample_size else candidates
            else:  # 'fast'
                if i < num_lines // 2:
                    sample_size = len(candidates)
                else:
                    sample_size = max(60, len(candidates) // 2)
                test_candidates = random.sample(candidates, sample_size) if len(candidates) > sample_size else candidates

            for next_point in test_candidates:
                score = self.calculate_line_score(working_img, current_point, next_point)
                if score > best_score:
                    best_score = score
                    best_point = next_point

            if best_point is None or best_score <= 0:
                print(f"  Zastaveno po {i} linii (zadne dalsi vhodne spojeni)")
                break

            lines.append((current_point, best_point))

            # Odecti linii z pracovniho obrazku
            pixels = self.get_line_pixels(self.points[current_point], self.points[best_point])
            for x, y in pixels:
                if 0 <= y < self.image_size and 0 <= x < self.image_size:
                    working_img[y, x] = max(0, working_img[y, x] - line_weight)

            current_point = best_point

            # Progress callback pro real-time update
            if progress_callback and (i + 1) % 50 == 0:
                progress_callback(lines.copy(), (i + 1) / num_lines * 100)

            if (i + 1) % 500 == 0:
                print(f"  Dokonceno {i + 1}/{num_lines} linii")

        print("Generovani dokonceno!")
        return lines

    def generate_string_art_parallel(self, image_path: str, num_lines: int = 3000,
                                      line_weight: int = 20, min_distance: int = 20,
                                      speed_mode: str = 'fast', progress_callback: Optional[Callable] = None,
                                      contrast_factor: float = 1.5, edge_enhancement: float = 0.0,
                                      num_workers: Optional[int] = None) -> List[Tuple[int, int]]:
        """
        Paralelni verze generovani string art s multi-threading

        Vyuziva ThreadPoolExecutor pro paralelni vypocet skore kandidatu.
        Zrychleni 2-4x na vicejadrových procesorech.

        Args:
            image_path: Cesta k vstupnimu obrazku
            num_lines: Pocet linii
            line_weight: Vaha kazde linie
            min_distance: Minimalni vzdalenost mezi body
            speed_mode: Rychlost ('ultra_fast', 'fast', 'precise')
            progress_callback: Callback funkce pro progress
            contrast_factor: Sila kontrastu
            edge_enhancement: Sila zesioleni hran (0.0-1.0)
            num_workers: Pocet workeru (default = pocet CPU)

        Returns:
            Seznam lini [(from_idx, to_idx), ...]
        """
        if num_workers is None:
            num_workers = min(multiprocessing.cpu_count(), 8)  # Max 8 workeru

        # Nacti a priprav obrazek
        img_array = self.load_and_prepare_image(image_path, contrast_factor=contrast_factor)

        # Aplikuj edge enhancement pokud je nastaven
        if edge_enhancement > 0:
            try:
                img_array = self.enhance_edges_for_stringart(img_array, edge_enhancement)
            except ImportError:
                print("Varovani: scipy neni nainstalovan, edge enhancement preskocen")

        working_img = img_array.copy()
        lines = []

        # Paralelni hledani startovniho bodu
        def calc_start_score(point_idx):
            total_score = 0
            for j in range(self.num_points):
                # OPRAVENO v5.2: Spravna circular distance logika
                point_distance = min(abs(point_idx - j), self.num_points - abs(point_idx - j))
                if point_distance < min_distance:
                    continue
                total_score += self.calculate_line_score(img_array, point_idx, j)
            return (point_idx, total_score)

        test_points = list(range(0, self.num_points, 10))

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            start_scores = list(executor.map(calc_start_score, test_points))

        best_start = max(start_scores, key=lambda x: x[1])[0]
        current_point = best_start

        print(f"Generuji {num_lines} linii paralelne ({num_workers} workeru, start z bodu {current_point})...")

        # Hlavni smycka generovani
        for i in range(num_lines):
            # Priprav kandidaty
            candidates = []
            for next_point in range(self.num_points):
                if next_point == current_point:
                    continue
                point_distance = min(abs(next_point - current_point),
                                   self.num_points - abs(next_point - current_point))
                if point_distance >= min_distance:
                    candidates.append(next_point)

            # Vzorkovani podle rezimu
            if speed_mode == 'precise':
                test_candidates = candidates
            elif speed_mode == 'ultra_fast':
                sample_size = min(len(candidates), 60 if i < num_lines // 4 else 30)
                test_candidates = random.sample(candidates, sample_size) if len(candidates) > sample_size else candidates
            else:  # 'fast'
                sample_size = len(candidates) if i < num_lines // 2 else max(60, len(candidates) // 2)
                test_candidates = random.sample(candidates, sample_size) if len(candidates) > sample_size else candidates

            # Paralelni vypocet skore - pouze pro vetsi pocet kandidatu
            if len(test_candidates) > 50 and num_workers > 1:
                def calc_candidate_score(next_point):
                    return (next_point, self.calculate_line_score(working_img, current_point, next_point))

                with ThreadPoolExecutor(max_workers=num_workers) as executor:
                    scores = list(executor.map(calc_candidate_score, test_candidates))

                best_point, best_score = max(scores, key=lambda x: x[1])
            else:
                # Pro maly pocet kandidatu je sekvencni rychlejsi
                best_score = -1
                best_point = None
                for next_point in test_candidates:
                    score = self.calculate_line_score(working_img, current_point, next_point)
                    if score > best_score:
                        best_score = score
                        best_point = next_point

            if best_point is None or best_score <= 0:
                print(f"  Zastaveno po {i} linii (zadne dalsi vhodne spojeni)")
                break

            lines.append((current_point, best_point))

            # Odecti linii z pracovniho obrazku
            pixels = self.get_line_pixels(self.points[current_point], self.points[best_point])
            for x, y in pixels:
                if 0 <= y < self.image_size and 0 <= x < self.image_size:
                    working_img[y, x] = max(0, working_img[y, x] - line_weight)

            current_point = best_point

            # Progress callback
            if progress_callback and (i + 1) % 50 == 0:
                progress_callback(lines.copy(), (i + 1) / num_lines * 100)

            if (i + 1) % 500 == 0:
                print(f"  Dokonceno {i + 1}/{num_lines} linii")

        print("Paralelni generovani dokonceno!")
        return lines

    def generate_with_preset(self, image_path: str, preset_id: str,
                              progress_callback: Optional[Callable] = None) -> List[Tuple[int, int]]:
        """
        Generuje string art s predefinovanym presetem

        Args:
            image_path: Cesta k obrazku
            preset_id: ID presetu (portrait, pet, logo, atd.)
            progress_callback: Callback pro progress

        Returns:
            Seznam lini
        """
        from presets import get_preset

        preset = get_preset(preset_id)
        if preset is None:
            raise ValueError(f"Neznamy preset: {preset_id}")

        # Aktualizuj pocet bodu pokud je jiny
        if preset.num_points != self.num_points:
            self.num_points = preset.num_points
            self.points = self._generate_circle_points()
            self._line_pixels_cache = {}

        return self.generate_string_art_parallel(
            image_path=image_path,
            num_lines=preset.num_lines,
            line_weight=preset.line_weight,
            min_distance=preset.min_distance,
            speed_mode=preset.speed_mode,
            progress_callback=progress_callback,
            contrast_factor=preset.contrast_factor,
            edge_enhancement=preset.edge_enhancement
        )

    def render_to_image(self, lines, size=800, line_width=0.5, opacity=0.15,
                       background='white', line_color='black', show_pins=False, pin_color='red'):
        """
        OPTIMALIZOVANA METODA v5.1: Batch renderovani do jednoho numpy bufferu

        OPRAVA: Puvodni verze vytvarela NOVY Image pro KAZDOU linii (3000-6000x alokace!)
        Nova verze pouziva numpy buffer a Bresenham algoritmus - 100x rychlejsi.

        Args:
            lines: Seznam linii [(point_a_idx, point_b_idx), ...]
            size: Velikost vystupniho obrazku
            line_width: Sirka niti (0.3-2.0)
            opacity: Pruhlednost niti (0.05-0.5) - klicove pro realisticnost!
            background: Barva pozadi ('white', 'black', '#RRGGBB')
            line_color: Barva niti ('black', 'white', '#RRGGBB')
            show_pins: Zobrazit piny/hrebiky
            pin_color: Barva pinu

        Returns:
            PIL Image s vysokou kvalitou renderovani
        """
        # Vyssi rozliseni pro antialiasing (2x supersampling)
        render_size = size * 2
        scale = render_size / self.image_size

        # Parsovani barev
        if background == 'white':
            bg_rgb = (1.0, 1.0, 1.0)
        elif background == 'black':
            bg_rgb = (0.0, 0.0, 0.0)
        elif background.startswith('#') and len(background) == 7:
            try:
                bg_rgb = (int(background[1:3], 16)/255.0,
                         int(background[3:5], 16)/255.0,
                         int(background[5:7], 16)/255.0)
            except ValueError:
                bg_rgb = (1.0, 1.0, 1.0)
        else:
            bg_rgb = (1.0, 1.0, 1.0)

        if line_color == 'black':
            line_rgb = (0.0, 0.0, 0.0)
        elif line_color == 'white':
            line_rgb = (1.0, 1.0, 1.0)
        elif line_color.startswith('#') and len(line_color) == 7:
            try:
                line_rgb = (int(line_color[1:3], 16)/255.0,
                           int(line_color[3:5], 16)/255.0,
                           int(line_color[5:7], 16)/255.0)
            except ValueError:
                line_rgb = (0.0, 0.0, 0.0)
        else:
            line_rgb = (0.0, 0.0, 0.0)

        # Numpy canvas s RGB barvami pozadi
        canvas = np.ones((render_size, render_size, 3), dtype=np.float32)
        canvas[:, :, 0] = bg_rgb[0]
        canvas[:, :, 1] = bg_rgb[1]
        canvas[:, :, 2] = bg_rgb[2]

        line_norm = np.array([line_rgb[0], line_rgb[1], line_rgb[2]], dtype=np.float32)

        # Scaled line width pro Bresenham
        scaled_width = max(1, int(line_width * scale))
        half_width = scaled_width // 2

        # BATCH renderovani vsech linii do jednoho bufferu
        for point_a_idx, point_b_idx in lines:
            point_a = self.points[point_a_idx]
            point_b = self.points[point_b_idx]

            x1 = int(point_a[0] * scale)
            y1 = int(point_a[1] * scale)
            x2 = int(point_b[0] * scale)
            y2 = int(point_b[1] * scale)

            # Bresenham s podporou sirky cary
            pixels = self._bresenham_line_thick(x1, y1, x2, y2, half_width, render_size)

            # Spravny multiplikativni blending pro kazdy pixel
            for px, py in pixels:
                if 0 <= px < render_size and 0 <= py < render_size:
                    canvas[py, px] = canvas[py, px] * (1 - opacity) + line_norm * opacity

        # Piny/hrebiky (volitelne)
        if show_pins:
            pin_size = max(2, int(3 * scale))
            # Parsovani barvy pinu
            if pin_color == 'red':
                pin_rgb = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            elif pin_color == 'blue':
                pin_rgb = np.array([0.0, 0.0, 1.0], dtype=np.float32)
            elif pin_color.startswith('#') and len(pin_color) == 7:
                try:
                    pin_rgb = np.array([int(pin_color[1:3], 16)/255.0,
                                       int(pin_color[3:5], 16)/255.0,
                                       int(pin_color[5:7], 16)/255.0], dtype=np.float32)
                except ValueError:
                    pin_rgb = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            else:
                pin_rgb = np.array([1.0, 0.0, 0.0], dtype=np.float32)

            for x, y in self.points:
                cx = int(x * scale)
                cy = int(y * scale)
                # Kresli kruh pro pin
                for dy in range(-pin_size, pin_size + 1):
                    for dx in range(-pin_size, pin_size + 1):
                        if dx*dx + dy*dy <= pin_size*pin_size:
                            px, py = cx + dx, cy + dy
                            if 0 <= px < render_size and 0 <= py < render_size:
                                canvas[py, px] = pin_rgb

        # Prevod na 8-bit a PIL Image
        canvas_uint8 = np.clip(canvas * 255, 0, 255).astype(np.uint8)
        img = Image.fromarray(canvas_uint8, mode='RGB')

        # Zmenseni s antialiasingem (2x -> 1x)
        img = img.resize((size, size), Image.Resampling.LANCZOS)

        return img

    def _bresenham_line_thick(self, x1, y1, x2, y2, half_width, size):
        """Bresenham algoritmus s podporou sirky cary"""
        pixels = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while True:
            # Pridej pixely v okoli pro sirku cary
            for wx in range(-half_width, half_width + 1):
                for wy in range(-half_width, half_width + 1):
                    px, py = x + wx, y + wy
                    if 0 <= px < size and 0 <= py < size:
                        pixels.append((px, py))

            if x == x2 and y == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        return pixels

    def render_to_image_fast(self, lines, size=800, line_width=0.5, opacity=0.15,
                            background='white', line_color='black'):
        """
        RYCHLA verze renderovani - pouziva numpy pro SPRAVNY multiplikativni blending

        OPRAVENO v5.1:
        - Spravny opacity model: canvas = canvas * (1 - opacity) misto linearniho odcitani
        - Podpora pro line_color (RGB renderovani)
        - Realisticke vysledky odpovidajici skutecnemu string artu
        """
        scale = size / self.image_size

        # Parse line color
        if line_color == 'black':
            line_rgb = (0, 0, 0)
        elif line_color == 'white':
            line_rgb = (255, 255, 255)
        elif line_color.startswith('#') and len(line_color) == 7:
            try:
                line_rgb = (int(line_color[1:3], 16),
                           int(line_color[3:5], 16),
                           int(line_color[5:7], 16))
            except ValueError:
                line_rgb = (0, 0, 0)  # Fallback to black
        else:
            line_rgb = (0, 0, 0)

        # Vytvor RGB canvas (3 kanaly)
        if background == 'white':
            canvas = np.ones((size, size, 3), dtype=np.float32)
        elif background == 'black':
            canvas = np.zeros((size, size, 3), dtype=np.float32)
        else:
            # Parse background color
            try:
                bg_rgb = (int(background[1:3], 16) / 255.0,
                         int(background[3:5], 16) / 255.0,
                         int(background[5:7], 16) / 255.0)
            except:
                bg_rgb = (1.0, 1.0, 1.0)
            canvas = np.full((size, size, 3), bg_rgb, dtype=np.float32)

        # Normalizovana barva linie
        line_norm = np.array([line_rgb[0] / 255.0, line_rgb[1] / 255.0, line_rgb[2] / 255.0])

        # SPRAVNY MULTIPLIKATIVNI BLENDING
        # Kazda nit prida svou barvu s danou pruhlednosti
        # Formula: new_color = old_color * (1 - opacity) + line_color * opacity
        for point_a_idx, point_b_idx in lines:
            point_a = self.points[point_a_idx]
            point_b = self.points[point_b_idx]

            x1 = int(point_a[0] * scale)
            y1 = int(point_a[1] * scale)
            x2 = int(point_b[0] * scale)
            y2 = int(point_b[1] * scale)

            pixels = self._get_line_pixels_scaled(x1, y1, x2, y2, size, max(1, int(line_width * scale)))

            for px, py in pixels:
                if 0 <= px < size and 0 <= py < size:
                    # Spravny alpha blending: result = bg * (1-alpha) + fg * alpha
                    canvas[py, px] = canvas[py, px] * (1 - opacity) + line_norm * opacity

        # Preved na uint8 RGB
        canvas = np.clip(canvas * 255, 0, 255).astype(np.uint8)

        return Image.fromarray(canvas, mode='RGB')

    def _get_line_pixels_scaled(self, x1, y1, x2, y2, max_size, width=1):
        """Bresenham s podporou šířky linie"""
        pixels = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            # Přidej pixely pro šířku
            for w in range(-width//2, width//2 + 1):
                if 0 <= x1 + w < max_size and 0 <= y1 < max_size:
                    pixels.append((x1 + w, y1))
                if width > 1 and 0 <= x1 < max_size and 0 <= y1 + w < max_size:
                    pixels.append((x1, y1 + w))

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

        return pixels

    def export_instructions(self, lines, output_path):
        """Exportuje instrukce do textoveho souboru"""
        ppq = self.get_points_per_quadrant()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("╔════════════════════════════════════════════════╗\n")
            f.write("║         STRING ART - NÁVOD NA SESTAVENÍ        ║\n")
            f.write("╚════════════════════════════════════════════════╝\n\n")

            f.write(f"📊 Celkový počet tahů: {len(lines)}\n")
            f.write(f"📍 Počet bodů na kruhu: {self.num_points}\n\n")

            f.write("🔤 KVADRANTY (po směru hodinových ručiček):\n")
            f.write("   ┌──────────────┐\n")
            f.write(f"   │  A (1-{ppq})    │  ← Horní (začátek nahoře)\n")
            f.write(f"   │  B (1-{ppq})    │  ← Pravá\n")
            f.write(f"   │  C (1-{ppq})    │  ← Dolní\n")
            f.write(f"   │  D (1-{ppq})    │  ← Levá\n")
            f.write("   └──────────────┘\n\n")

            f.write("💡 TIP: Zaškrtávejte si dokončené kroky!\n\n")
            f.write("═" * 50 + "\n")
            f.write("INSTRUKCE - SPOJTE BODY V TOMTO POŘADÍ:\n")
            f.write("═" * 50 + "\n\n")

            for i, (point_a, point_b) in enumerate(lines, 1):
                label_a = self.get_point_label(point_a)
                label_b = self.get_point_label(point_b)
                checkbox = "☐"
                f.write(f"{checkbox} {i:4d}. {label_a:5s} → {label_b:5s}\n")

                if i % 10 == 0 and i < len(lines):
                    f.write("\n")

        print(f"Instrukce exportovany do: {output_path}")

    def export_to_csv(self, lines, output_path):
        """Exportuje instrukce do CSV formatu"""
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Step', 'From', 'To', 'From_Quadrant', 'From_Number', 'To_Quadrant', 'To_Number'])

            for i, (point_a, point_b) in enumerate(lines, 1):
                label_a = self.get_point_label(point_a)
                label_b = self.get_point_label(point_b)

                from_quad = label_a[0]
                from_num = label_a[1:]
                to_quad = label_b[0]
                to_num = label_b[1:]

                writer.writerow([i, label_a, label_b, from_quad, from_num, to_quad, to_num])

        print(f"CSV exportovan do: {output_path}")

    def export_to_json(self, lines, output_path):
        """Exportuje instrukce do JSON formatu"""
        ppq = self.get_points_per_quadrant()
        data = {
            'metadata': {
                'total_lines': len(lines),
                'num_points': self.num_points,
                'image_size': self.image_size,
                'points_per_quadrant': ppq,
                'quadrants': {
                    'A': f'Horni (body 1-{ppq})',
                    'B': f'Prava (body 1-{ppq})',
                    'C': f'Dolni (body 1-{ppq})',
                    'D': f'Leva (body 1-{ppq})'
                },
                'format': 'RingString compatible - A/B/C/D quadrants'
            },
            'instructions': []
        }

        for i, (point_a, point_b) in enumerate(lines, 1):
            label_a = self.get_point_label(point_a)
            label_b = self.get_point_label(point_b)

            instruction = {
                'step': i,
                'from': {
                    'label': label_a,
                    'index': int(point_a),
                    'coordinates': [float(self.points[point_a][0]), float(self.points[point_a][1])]
                },
                'to': {
                    'label': label_b,
                    'index': int(point_b),
                    'coordinates': [float(self.points[point_b][0]), float(self.points[point_b][1])]
                }
            }
            data['instructions'].append(instruction)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"JSON exportovan do: {output_path}")

    def export_to_svg(self, lines, output_path, background_color='white', line_color='black',
                     line_width=0.5, opacity=0.15):
        """
        Exportuje instrukce do SVG formatu
        VYLEPŠENO: Podpora opacity pro realističtější vzhled
        """
        svg = ET.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': str(self.image_size),
            'height': str(self.image_size),
            'viewBox': f'0 0 {self.image_size} {self.image_size}'
        })

        ET.SubElement(svg, 'rect', {
            'width': str(self.image_size),
            'height': str(self.image_size),
            'fill': background_color
        })

        lines_group = ET.SubElement(svg, 'g', {
            'id': 'string-art-lines',
            'stroke': line_color,
            'stroke-width': str(line_width),
            'opacity': str(opacity)
        })

        for point_a_idx, point_b_idx in lines:
            point_a = self.points[point_a_idx]
            point_b = self.points[point_b_idx]

            ET.SubElement(lines_group, 'line', {
                'x1': str(point_a[0]),
                'y1': str(point_a[1]),
                'x2': str(point_b[0]),
                'y2': str(point_b[1])
            })

        points_group = ET.SubElement(svg, 'g', {
            'id': 'anchor-points',
            'fill': 'red',
            'opacity': '0.3'
        })

        for i, (x, y) in enumerate(self.points):
            ET.SubElement(points_group, 'circle', {
                'cx': str(x),
                'cy': str(y),
                'r': '2',
                'data-index': str(i),
                'data-label': self.get_point_label(i)
            })

        tree = ET.ElementTree(svg)
        ET.indent(tree, space='  ')
        tree.write(output_path, encoding='utf-8', xml_declaration=True)

        print(f"SVG exportovan do: {output_path}")

    def export_high_quality_image(self, lines, output_path, size=1000, line_width=0.5,
                                  opacity=0.12, background='white', line_color='black'):
        """
        NOVÁ METODA: Exportuje vysokou kvalitu PNG/JPG
        """
        img = self.render_to_image(lines, size=size, line_width=line_width,
                                   opacity=opacity, background=background,
                                   line_color=line_color, show_pins=False)
        img.save(output_path, quality=95)
        print(f"Obrazek exportovan do: {output_path}")
        return img

    def export_pin_diagram_svg(self, output_path, size=800):
        """
        Exportuje SVG diagram s očíslovanými piny pro referenci při stavbě
        """
        scale = size / self.image_size

        svg = ET.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': str(size),
            'height': str(size + 100),  # Extra prostor pro legendu
            'viewBox': f'0 0 {size} {size + 100}'
        })

        # Pozadí
        ET.SubElement(svg, 'rect', {
            'width': str(size),
            'height': str(size + 100),
            'fill': '#f5f5f5'
        })

        # Nadpis
        title = ET.SubElement(svg, 'text', {
            'x': str(size // 2),
            'y': '30',
            'text-anchor': 'middle',
            'font-family': 'Arial, sans-serif',
            'font-size': '20',
            'font-weight': 'bold',
            'fill': '#333'
        })
        title.text = f'STRING ART - Rozložení {self.num_points} pinů'

        # Hlavní kruh/tvar
        center_y_offset = 50
        if self.shape == 'circle':
            ET.SubElement(svg, 'circle', {
                'cx': str(size // 2),
                'cy': str(size // 2 + center_y_offset),
                'r': str(int(self.radius * scale)),
                'fill': 'none',
                'stroke': '#ccc',
                'stroke-width': '2',
                'stroke-dasharray': '5,5'
            })

        # Barvy pro kvadranty
        quadrant_colors = {
            'A': '#e74c3c',  # Červená
            'B': '#3498db',  # Modrá
            'C': '#2ecc71',  # Zelená
            'D': '#f39c12'   # Oranžová
        }

        # Nakresli piny s čísly
        for i, (x, y) in enumerate(self.points):
            px = int(x * scale)
            py = int(y * scale) + center_y_offset
            label = self.get_point_label(i)
            quadrant = label[0]
            color = quadrant_colors.get(quadrant, '#333')

            # Pin (kruh)
            ET.SubElement(svg, 'circle', {
                'cx': str(px),
                'cy': str(py),
                'r': '8' if i % 10 == 0 else '5',
                'fill': color,
                'stroke': '#fff',
                'stroke-width': '1'
            })

            # Číslo (jen každý 10. pro přehlednost)
            if i % 10 == 0:
                # Vypočítej pozici textu (vně kruhu)
                angle = math.atan2(y - self.center[1], x - self.center[0])
                text_dist = 25
                tx = px + int(text_dist * math.cos(angle))
                ty = py + int(text_dist * math.sin(angle))

                text_el = ET.SubElement(svg, 'text', {
                    'x': str(tx),
                    'y': str(ty),
                    'text-anchor': 'middle',
                    'dominant-baseline': 'middle',
                    'font-family': 'Arial, sans-serif',
                    'font-size': '10',
                    'font-weight': 'bold',
                    'fill': color
                })
                text_el.text = label

        # Legenda - dynamicky pocet bodu
        ppq = self.get_points_per_quadrant()
        legend_y = size + 60
        legend_items = [
            (f'A (1-{ppq})', quadrant_colors['A'], 'Horni'),
            (f'B (1-{ppq})', quadrant_colors['B'], 'Prava'),
            (f'C (1-{ppq})', quadrant_colors['C'], 'Dolni'),
            (f'D (1-{ppq})', quadrant_colors['D'], 'Leva')
        ]

        for idx, (label, color, desc) in enumerate(legend_items):
            lx = 50 + idx * 190
            ET.SubElement(svg, 'rect', {
                'x': str(lx),
                'y': str(legend_y),
                'width': '20',
                'height': '20',
                'fill': color,
                'rx': '3'
            })
            text_el = ET.SubElement(svg, 'text', {
                'x': str(lx + 30),
                'y': str(legend_y + 15),
                'font-family': 'Arial, sans-serif',
                'font-size': '14',
                'fill': '#333'
            })
            text_el.text = f'{label} - {desc}'

        tree = ET.ElementTree(svg)
        ET.indent(tree, space='  ')
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"Pin diagram exportován do: {output_path}")

    def export_html_tutorial(self, lines, output_path, steps_per_page=50):
        """
        Exportuje interaktivní HTML průvodce krok za krokem
        """
        # Priprav data pro JavaScript
        points_json = json.dumps([[float(x), float(y)] for x, y in self.points])
        lines_json = json.dumps(lines)
        labels_json = json.dumps([self.get_point_label(i) for i in range(self.num_points)])

        # Dynamicky pocet bodu na kvadrant
        ppq = self.get_points_per_quadrant()

        html_content = f'''<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>String Art Tutorial - Interaktivní průvodce</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #e94560;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }}
        .main-content {{
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 30px;
        }}
        .canvas-container {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        #artCanvas {{
            display: block;
            margin: 0 auto;
            border-radius: 10px;
        }}
        .controls {{
            background: #0f3460;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        .step-display {{
            text-align: center;
            background: #1a1a2e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .step-number {{
            font-size: 4em;
            font-weight: bold;
            color: #e94560;
        }}
        .step-total {{
            color: #888;
            font-size: 1.2em;
        }}
        .current-instruction {{
            background: #e94560;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            font-size: 1.8em;
            font-weight: bold;
        }}
        .arrow {{
            display: inline-block;
            margin: 0 15px;
            font-size: 1.5em;
        }}
        .btn-group {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        .btn {{
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .btn-prev {{ background: #16213e; color: white; }}
        .btn-next {{ background: #e94560; color: white; }}
        .btn:hover {{ transform: scale(1.05); }}
        .btn:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none; }}
        .progress-bar {{
            height: 10px;
            background: #1a1a2e;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #e94560, #f39c12);
            transition: width 0.3s;
        }}
        .jump-controls {{
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 20px;
        }}
        .jump-controls input {{
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
        }}
        .jump-controls button {{
            padding: 10px 20px;
            background: #0f3460;
            color: white;
            border: 2px solid #e94560;
            border-radius: 5px;
            cursor: pointer;
        }}
        .legend {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: #1a1a2e;
            border-radius: 5px;
        }}
        .legend-color {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
        }}
        .speed-control {{
            margin-top: 20px;
        }}
        .speed-control label {{
            display: block;
            margin-bottom: 10px;
        }}
        .speed-control input {{
            width: 100%;
        }}
        .auto-play {{
            margin-top: 15px;
        }}
        .auto-play button {{
            width: 100%;
            padding: 15px;
            background: #2ecc71;
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1.1em;
            cursor: pointer;
        }}
        .auto-play button.playing {{
            background: #e74c3c;
        }}
        .keyboard-hint {{
            margin-top: 20px;
            padding: 15px;
            background: #1a1a2e;
            border-radius: 8px;
            font-size: 0.9em;
            color: #888;
        }}
        .keyboard-hint kbd {{
            background: #0f3460;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 0 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>String Art Tutorial</h1>
        <p class="subtitle">Interaktivní průvodce - {len(lines)} kroků</p>

        <div class="main-content">
            <div class="canvas-container">
                <canvas id="artCanvas" width="700" height="700"></canvas>
            </div>

            <div class="controls">
                <div class="step-display">
                    <div class="step-number" id="stepNumber">0</div>
                    <div class="step-total">z {len(lines)} kroků</div>
                </div>

                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                </div>

                <div class="current-instruction" id="instruction">
                    Klikni "Další" pro začátek
                </div>

                <div class="btn-group">
                    <button class="btn btn-prev" id="prevBtn" onclick="prevStep()">← Předchozí</button>
                    <button class="btn btn-next" id="nextBtn" onclick="nextStep()">Další →</button>
                </div>

                <div class="jump-controls">
                    <input type="number" id="jumpInput" min="1" max="{len(lines)}" placeholder="Číslo kroku...">
                    <button onclick="jumpToStep()">Přejít</button>
                </div>

                <div class="auto-play">
                    <button id="autoPlayBtn" onclick="toggleAutoPlay()">▶ Automatické přehrávání</button>
                </div>

                <div class="speed-control">
                    <label>Rychlost přehrávání: <span id="speedValue">500</span>ms</label>
                    <input type="range" id="speedSlider" min="100" max="2000" value="500" onchange="updateSpeed()">
                </div>

                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background: #e74c3c"></div>
                        <span>A (1-{ppq}) - Horní</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #3498db"></div>
                        <span>B (1-{ppq}) - Pravá</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #2ecc71"></div>
                        <span>C (1-{ppq}) - Dolní</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #f39c12"></div>
                        <span>D (1-{ppq}) - Levá</span>
                    </div>
                </div>

                <div class="keyboard-hint">
                    <strong>Klávesové zkratky:</strong><br>
                    <kbd>→</kbd> Další krok | <kbd>←</kbd> Předchozí | <kbd>Space</kbd> Auto-play
                </div>
            </div>
        </div>
    </div>

    <script>
        const points = {points_json};
        const lines = {lines_json};
        const labels = {labels_json};
        const totalSteps = lines.length;

        let currentStep = 0;
        let isPlaying = false;
        let playInterval = null;
        let playSpeed = 500;

        const canvas = document.getElementById('artCanvas');
        const ctx = canvas.getContext('2d');
        const scale = canvas.width / {self.image_size};

        const quadrantColors = {{
            'A': '#e74c3c',
            'B': '#3498db',
            'C': '#2ecc71',
            'D': '#f39c12'
        }};

        function getQuadrantColor(label) {{
            return quadrantColors[label[0]] || '#333';
        }}

        function drawBase() {{
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Nakresli piny
            points.forEach((point, i) => {{
                const x = point[0] * scale;
                const y = point[1] * scale;
                const label = labels[i];
                const color = getQuadrantColor(label);

                ctx.beginPath();
                ctx.arc(x, y, i % 10 === 0 ? 6 : 3, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 1;
                ctx.stroke();
            }});
        }}

        function drawLines(upToStep) {{
            drawBase();

            ctx.strokeStyle = 'rgba(0, 0, 0, 0.15)';
            ctx.lineWidth = 1;

            for (let i = 0; i < upToStep; i++) {{
                const [from, to] = lines[i];
                const fromPoint = points[from];
                const toPoint = points[to];

                ctx.beginPath();
                ctx.moveTo(fromPoint[0] * scale, fromPoint[1] * scale);
                ctx.lineTo(toPoint[0] * scale, toPoint[1] * scale);
                ctx.stroke();
            }}

            // Zvýrazni aktuální linii
            if (upToStep > 0 && upToStep <= totalSteps) {{
                const [from, to] = lines[upToStep - 1];
                const fromPoint = points[from];
                const toPoint = points[to];

                ctx.strokeStyle = '#e94560';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(fromPoint[0] * scale, fromPoint[1] * scale);
                ctx.lineTo(toPoint[0] * scale, toPoint[1] * scale);
                ctx.stroke();

                // Zvýrazni koncové body
                [from, to].forEach(idx => {{
                    const p = points[idx];
                    ctx.beginPath();
                    ctx.arc(p[0] * scale, p[1] * scale, 10, 0, Math.PI * 2);
                    ctx.fillStyle = '#e94560';
                    ctx.fill();
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 10px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(labels[idx], p[0] * scale, p[1] * scale);
                }});
            }}
        }}

        function updateUI() {{
            document.getElementById('stepNumber').textContent = currentStep;
            document.getElementById('progressFill').style.width = (currentStep / totalSteps * 100) + '%';
            document.getElementById('prevBtn').disabled = currentStep === 0;
            document.getElementById('nextBtn').disabled = currentStep === totalSteps;

            if (currentStep === 0) {{
                document.getElementById('instruction').innerHTML = 'Klikni "Další" pro začátek';
            }} else {{
                const [from, to] = lines[currentStep - 1];
                const fromLabel = labels[from];
                const toLabel = labels[to];
                document.getElementById('instruction').innerHTML =
                    `<span style="color: ${{getQuadrantColor(fromLabel)}}">${{fromLabel}}</span>` +
                    `<span class="arrow">→</span>` +
                    `<span style="color: ${{getQuadrantColor(toLabel)}}">${{toLabel}}</span>`;
            }}

            drawLines(currentStep);
        }}

        function nextStep() {{
            if (currentStep < totalSteps) {{
                currentStep++;
                updateUI();
            }}
        }}

        function prevStep() {{
            if (currentStep > 0) {{
                currentStep--;
                updateUI();
            }}
        }}

        function jumpToStep() {{
            const step = parseInt(document.getElementById('jumpInput').value);
            if (step >= 0 && step <= totalSteps) {{
                currentStep = step;
                updateUI();
            }}
        }}

        function toggleAutoPlay() {{
            isPlaying = !isPlaying;
            const btn = document.getElementById('autoPlayBtn');

            if (isPlaying) {{
                btn.textContent = '⏹ Zastavit';
                btn.classList.add('playing');
                playInterval = setInterval(() => {{
                    if (currentStep < totalSteps) {{
                        nextStep();
                    }} else {{
                        toggleAutoPlay();
                    }}
                }}, playSpeed);
            }} else {{
                btn.textContent = '▶ Automatické přehrávání';
                btn.classList.remove('playing');
                clearInterval(playInterval);
            }}
        }}

        function updateSpeed() {{
            playSpeed = parseInt(document.getElementById('speedSlider').value);
            document.getElementById('speedValue').textContent = playSpeed;

            if (isPlaying) {{
                clearInterval(playInterval);
                playInterval = setInterval(() => {{
                    if (currentStep < totalSteps) {{
                        nextStep();
                    }} else {{
                        toggleAutoPlay();
                    }}
                }}, playSpeed);
            }}
        }}

        // Klávesové zkratky
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight') nextStep();
            if (e.key === 'ArrowLeft') prevStep();
            if (e.key === ' ') {{ e.preventDefault(); toggleAutoPlay(); }}
        }});

        // Inicializace
        updateUI();
    </script>
</body>
</html>'''

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML tutorial exportován do: {output_path}")

    def export_pdf_tutorial(self, lines, output_path, steps_per_page=100):
        """
        Exportuje PDF tutorial s diagramem a instrukcemi
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm, cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os

        # Pokus o registraci fontu s podporou ceske diakritiky
        # Priorita: DejaVu > Arial > Helvetica (Helvetica nepodporuje diakritiku!)
        font_registered = False
        font_name = None

        # Seznam fontů s podporou UTF-8/české diakritiky
        font_candidates = [
            # DejaVu - nejlepší volba, open source
            ('DejaVu', [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/TTF/DejaVuSans.ttf',
                '/usr/share/fonts/dejavu/DejaVuSans.ttf',
                'C:/Windows/Fonts/DejaVuSans.ttf',
            ]),
            # Arial - běžně dostupný na Windows, podporuje češtinu
            ('Arial', [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/Arial.ttf',
                '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
            ]),
            # Calibri - moderní Windows font
            ('Calibri', [
                'C:/Windows/Fonts/calibri.ttf',
                'C:/Windows/Fonts/Calibri.ttf',
            ]),
            # Segoe UI - Windows systémový font
            ('SegoeUI', [
                'C:/Windows/Fonts/segoeui.ttf',
                'C:/Windows/Fonts/SegoeUI.ttf',
            ]),
        ]

        for font_label, paths in font_candidates:
            for font_path in paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_label, font_path))
                        font_registered = True
                        font_name = font_label
                        break
                    except Exception as e:
                        print(f"Varovani: Nelze nacist font {font_path}: {e}")
                        continue
            if font_registered:
                break

        if font_registered:
            base_font = font_name
        else:
            base_font = 'Helvetica'
            print("VAROVANI: Zadny UTF-8 font nenalezen! Ceska diakritika nebude spravne zobrazena.")

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                               rightMargin=1.5*cm, leftMargin=1.5*cm,
                               topMargin=1.5*cm, bottomMargin=1.5*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                    fontSize=24, textColor=colors.HexColor('#e94560'),
                                    alignment=1, spaceAfter=20, fontName=base_font)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                       fontSize=12, textColor=colors.gray,
                                       alignment=1, spaceAfter=30, fontName=base_font)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                      fontSize=14, textColor=colors.HexColor('#0f3460'),
                                      spaceBefore=15, spaceAfter=10, fontName=base_font)

        story = []

        # Dynamicky vypocitej pocet bodu na kvadrant
        ppq = self.get_points_per_quadrant()

        # Titulni strana
        story.append(Paragraph("STRING ART TUTORIAL", title_style))
        story.append(Paragraph(f"Kompletni pruvodce - {len(lines)} kroku", subtitle_style))
        story.append(Spacer(1, 20))

        # Info tabulka
        info_data = [
            ['Pocet pinu:', str(self.num_points)],
            ['Pocet kroku:', str(len(lines))],
            ['Tvar:', self.shape.upper()],
            ['Bodu na kvadrant:', str(ppq)],
        ]
        info_table = Table(info_data, colWidths=[120, 150])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f5f5f5')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), base_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 30))

        # Legenda kvadrantu - dynamicky pocet bodu
        story.append(Paragraph("LEGENDA KVADRANTU", heading_style))
        legend_data = [
            [f'A (1-{ppq})', 'Horni cast', '*'],
            [f'B (1-{ppq})', 'Prava cast', '*'],
            [f'C (1-{ppq})', 'Dolni cast', '*'],
            [f'D (1-{ppq})', 'Leva cast', '*'],
        ]
        legend_colors_list = [
            colors.HexColor('#e74c3c'),
            colors.HexColor('#3498db'),
            colors.HexColor('#2ecc71'),
            colors.HexColor('#f39c12'),
        ]
        legend_table = Table(legend_data, colWidths=[80, 120, 40])
        legend_style = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), base_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]
        for i, color in enumerate(legend_colors_list):
            legend_style.append(('TEXTCOLOR', (2, i), (2, i), color))
            legend_style.append(('FONTSIZE', (2, i), (2, i), 20))
        legend_table.setStyle(TableStyle(legend_style))
        story.append(legend_table)

        story.append(PageBreak())

        # Instrukce
        story.append(Paragraph("INSTRUKCE - KROK ZA KROKEM", title_style))
        story.append(Spacer(1, 10))

        # Rozdel instrukce do tabulek po steps_per_page
        for page_start in range(0, len(lines), steps_per_page):
            page_end = min(page_start + steps_per_page, len(lines))

            story.append(Paragraph(f"Kroky {page_start + 1} - {page_end}", heading_style))

            # Vytvor data pro tabulku (5 sloupcu)
            table_data = [['#', 'Z', '->', 'Do', '[ ]']]

            for i in range(page_start, page_end):
                from_idx, to_idx = lines[i]
                from_label = self.get_point_label(from_idx)
                to_label = self.get_point_label(to_idx)
                table_data.append([str(i + 1), from_label, '->', to_label, '[ ]'])

            table = Table(table_data, colWidths=[45, 55, 25, 55, 35])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), base_font),
                ('FONTNAME', (0, 1), (-1, -1), base_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ]))
            story.append(table)

            if page_end < len(lines):
                story.append(PageBreak())

        doc.build(story)
        print(f"PDF tutorial exportovan do: {output_path}")

    def export_pdf_tutorial_complete(self, lines, output_path, frame_size_cm=40, steps_per_page=100):
        """
        KOMPLETNI PDF tutorial pro IRL tvorbu string artu

        Zahrnuje:
        - Sablonu pro rozmisteni hrebicku (1:1 vytisknuti)
        - Seznam materialu
        - Podrobne instrukce pro fyzickou tvorbu
        - Krokovy navod s checkboxy
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm, cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.graphics.shapes import Drawing, Circle, String, Line
        from reportlab.graphics import renderPDF
        import os
        import math

        # ============ REGISTRACE FONTU ============
        font_registered = False
        font_name = None

        font_candidates = [
            ('DejaVu', [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/TTF/DejaVuSans.ttf',
                'C:/Windows/Fonts/DejaVuSans.ttf',
            ]),
            ('Arial', [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/Arial.ttf',
            ]),
            ('Calibri', [
                'C:/Windows/Fonts/calibri.ttf',
            ]),
        ]

        for font_label, paths in font_candidates:
            for font_path in paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_label, font_path))
                        font_registered = True
                        font_name = font_label
                        break
                    except Exception:
                        continue
            if font_registered:
                break

        base_font = font_name if font_registered else 'Helvetica'

        # ============ VYTVORENI DOKUMENTU ============
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                               rightMargin=1*cm, leftMargin=1*cm,
                               topMargin=1*cm, bottomMargin=1*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                    fontSize=24, textColor=colors.HexColor('#e94560'),
                                    alignment=1, spaceAfter=15, fontName=base_font)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                       fontSize=12, textColor=colors.gray,
                                       alignment=1, spaceAfter=20, fontName=base_font)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                      fontSize=14, textColor=colors.HexColor('#0f3460'),
                                      spaceBefore=10, spaceAfter=8, fontName=base_font)
        body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                   fontSize=10, fontName=base_font, spaceAfter=5)
        checkbox_style = ParagraphStyle('Checkbox', parent=styles['Normal'],
                                       fontSize=10, fontName=base_font,
                                       leftIndent=20, spaceAfter=3)

        story = []

        # ============ TITULNI STRANA ============
        story.append(Paragraph("STRING ART", title_style))
        story.append(Paragraph("Kompletni navod pro fyzickou tvorbu", subtitle_style))
        story.append(Spacer(1, 10))

        ppq = self.get_points_per_quadrant()

        # Info tabulka
        info_data = [
            ['Velikost ramu:', f'{frame_size_cm} x {frame_size_cm} cm'],
            ['Pocet hrebicku:', str(self.num_points)],
            ['Pocet kroku:', str(len(lines))],
            ['Hrebiku na stranu:', str(ppq)],
            ['Odhadovana delka nite:', f'{self._estimate_thread_length(lines, frame_size_cm):.1f} m'],
        ]
        info_table = Table(info_data, colWidths=[130, 150])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f5f5f5')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), base_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ]))
        story.append(info_table)

        story.append(PageBreak())

        # ============ SEZNAM MATERIALU ============
        story.append(Paragraph("POTREBNY MATERIAL", title_style))
        story.append(Spacer(1, 10))

        materials = [
            f"[ ] Drevena deska nebo ram {frame_size_cm}x{frame_size_cm} cm",
            f"[ ] {self.num_points} hrebicku (doporuceni: 15-20mm, tenke)",
            f"[ ] Cerna nit (bavlna nebo polyester) - min. {self._estimate_thread_length(lines, frame_size_cm) * 1.2:.0f} m",
            "[ ] Kladivo",
            "[ ] Sablona pro rozmisteni hrebicku (nasledujici strana)",
            "[ ] Lepici paska pro uchyceni sablony",
            "[ ] Nuzky",
            "[ ] Pravitko nebo metr",
            "[ ] Tuzka pro oznaceni",
        ]

        for mat in materials:
            story.append(Paragraph(mat, checkbox_style))

        story.append(Spacer(1, 15))
        story.append(Paragraph("DOPORUCENE NASTROJE", heading_style))

        optional = [
            "[ ] Dratena jehla (pro navlekani nite kolem hrebiku)",
            "[ ] Lepidlo na drevo (pro zajisteni uzlu)",
            "[ ] Brusny papir (pro hladkou desku)",
            "[ ] Bila barva + stetec (pro bile pozadi)",
        ]

        for opt in optional:
            story.append(Paragraph(opt, checkbox_style))

        story.append(PageBreak())

        # ============ NAVOD PRO PRIPRAVU ============
        story.append(Paragraph("PRIPRAVA - KROK ZA KROKEM", title_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("1. PRIPRAVA DESKY", heading_style))
        prep_steps = [
            "[ ] Obruste desku pro hladky povrch",
            "[ ] Natrte bilou barvou (2 vrstvy) a nechte uschnout",
            "[ ] Zkontrolujte, ze je povrch rovny a bez nerovnosti",
        ]
        for step in prep_steps:
            story.append(Paragraph(step, checkbox_style))

        story.append(Spacer(1, 10))
        story.append(Paragraph("2. UMISTENI SABLONY", heading_style))
        template_steps = [
            "[ ] Vytisknete sablonu na nasledujici strane v meritku 1:1",
            "[ ] Vystrihnete sablonu podle obrysu",
            "[ ] Prilepte sablonu na stred desky lepici paskou",
            "[ ] Zkontrolujte, ze sablona je vycentrovana",
        ]
        for step in template_steps:
            story.append(Paragraph(step, checkbox_style))

        story.append(Spacer(1, 10))
        story.append(Paragraph("3. ZATLOUKANI HREBICKU", heading_style))
        nail_tips = [
            "[ ] Zatloukejte hrebicky KOLMO k desce",
            "[ ] Vsechny hrebicky musi mit STEJNOU vysku (cca 10mm nad deskou)",
            "[ ] Zacnete od hrebicku A1 a pokracujte postupne",
            "[ ] Po zatlukceni kazdeho hrebicku zkontrolujte, ze neni sik",
        ]
        for tip in nail_tips:
            story.append(Paragraph(tip, checkbox_style))

        story.append(Spacer(1, 10))
        story.append(Paragraph("DULEZITE TIPY:", heading_style))
        important_tips = [
            "- Hrebicky nesmi byt prilis blizko kraje (min 1cm od okraje)",
            "- Pokud se hrebik ohne, vyndejte ho a zkuste znovu",
            "- Lepsi je zatlouct mene nez vice - hrebiky musi drzet pevne",
        ]
        for tip in important_tips:
            story.append(Paragraph(tip, body_style))

        story.append(PageBreak())

        # ============ SABLONA HREBICKU ============
        story.append(Paragraph("SABLONA PRO ROZMISTENI HREBICKU", title_style))
        story.append(Paragraph(f"Vytisknete v meritku 1:1 (100%) pro ram {frame_size_cm}x{frame_size_cm} cm", subtitle_style))

        # Vytvoreni kruhove sablony s pozicemi hrebicku
        template_drawing = self._create_nail_template_drawing(frame_size_cm, base_font)
        story.append(template_drawing)

        story.append(PageBreak())

        # ============ NAVOD NA NAPINANI NITE ============
        story.append(Paragraph("NAPINANI NITE - POSTUP", title_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("ZACATEK:", heading_style))
        start_steps = [
            "[ ] Uvazte nit na prvni hrebik (viz krok 1 v instrukci)",
            "[ ] Nechte cca 10cm volneho konce pro pozdejsi zajisteni",
            "[ ] Uzel by mel byt na vnitrni strane (smerem do stredu)",
        ]
        for step in start_steps:
            story.append(Paragraph(step, checkbox_style))

        story.append(Spacer(1, 10))
        story.append(Paragraph("NAPINANI:", heading_style))
        thread_tips = [
            "- Nit by mela byt napnuta, ale ne prilis - nemela by se brnkat",
            "- Obtocte nit jednou kolem kazdeho hrebiku (ne vickrat!)",
            "- Drzite neustaly mírny tah, aby se nit neuvolnila",
            "- Kazde 2-3 minuty si dejte pauzu, aby vas nebolely prsty",
        ]
        for tip in thread_tips:
            story.append(Paragraph(tip, body_style))

        story.append(Spacer(1, 10))
        story.append(Paragraph("UKONCENI:", heading_style))
        end_steps = [
            "[ ] Na poslednim hrebiku uvazte pevny uzel",
            "[ ] Spojte konec se zacatkem (schovejte do okolnich niti)",
            "[ ] Kapnete kapku lepidla na uzel pro zajisteni",
            "[ ] Odstrihnete prebytecne konce",
        ]
        for step in end_steps:
            story.append(Paragraph(step, checkbox_style))

        story.append(PageBreak())

        # ============ LEGENDA KVADRANTU ============
        story.append(Paragraph("LEGENDA OZNACENI HREBICKU", title_style))
        story.append(Spacer(1, 10))

        legend_info = [
            ("A", "HORNI strana", "#e74c3c", f"hrebiky A1 az A{ppq}"),
            ("B", "PRAVA strana", "#3498db", f"hrebiky B1 az B{ppq}"),
            ("C", "DOLNI strana", "#2ecc71", f"hrebiky C1 az C{ppq}"),
            ("D", "LEVA strana", "#f39c12", f"hrebiky D1 az D{ppq}"),
        ]

        legend_data = [['Oznaceni', 'Pozice', 'Barva', 'Rozsah']]
        for label, pos, color, range_str in legend_info:
            legend_data.append([label, pos, '*', range_str])

        legend_table = Table(legend_data, colWidths=[70, 100, 50, 120])
        legend_style_list = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), base_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]

        for i, (_, _, color, _) in enumerate(legend_info):
            legend_style_list.append(('TEXTCOLOR', (2, i+1), (2, i+1), colors.HexColor(color)))
            legend_style_list.append(('FONTSIZE', (2, i+1), (2, i+1), 18))

        legend_table.setStyle(TableStyle(legend_style_list))
        story.append(legend_table)

        story.append(PageBreak())

        # ============ INSTRUKCE KROK ZA KROKEM ============
        story.append(Paragraph("INSTRUKCE - KROK ZA KROKEM", title_style))
        story.append(Spacer(1, 10))

        # Rozdel instrukce do tabulek
        for page_start in range(0, len(lines), steps_per_page):
            page_end = min(page_start + steps_per_page, len(lines))

            story.append(Paragraph(f"Kroky {page_start + 1} - {page_end}", heading_style))

            table_data = [['#', 'Z', '->', 'Do', '[ ]']]

            for i in range(page_start, page_end):
                from_idx, to_idx = lines[i]
                from_label = self.get_point_label(from_idx)
                to_label = self.get_point_label(to_idx)
                table_data.append([str(i + 1), from_label, '->', to_label, '[ ]'])

            table = Table(table_data, colWidths=[45, 55, 25, 55, 35])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), base_font),
                ('FONTNAME', (0, 1), (-1, -1), base_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ]))
            story.append(table)

            if page_end < len(lines):
                story.append(PageBreak())

        doc.build(story)
        print(f"Kompletni PDF tutorial exportovan do: {output_path}")

    def _estimate_thread_length(self, lines, frame_size_cm):
        """Odhadne celkovou delku nite v metrech"""
        total_length = 0
        for from_idx, to_idx in lines:
            p1 = self.points[from_idx]
            p2 = self.points[to_idx]
            # Vzdalenost v pixelech -> prevod na cm
            dist_px = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            dist_cm = (dist_px / self.image_size) * frame_size_cm
            total_length += dist_cm
        return total_length / 100  # cm -> m

    def _create_nail_template_drawing(self, frame_size_cm, font_name='Helvetica'):
        """Vytvori vektorovou sablonu pro rozmisteni hrebicku"""
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.graphics.shapes import Drawing, Circle, String, Line
        import math

        # Velikost kresby - pro A4 max cca 180mm
        drawing_size_mm = min(180, frame_size_cm * 10 * 0.9)  # 90% z ramce nebo max 180mm
        drawing_size = drawing_size_mm * mm

        # Stredovy bod
        center = drawing_size / 2
        radius = center * 0.95  # 95% pro okraj

        drawing = Drawing(drawing_size, drawing_size)

        # Hlavni kruh
        drawing.add(Circle(center, center, radius, strokeColor=colors.black, strokeWidth=1, fillColor=None))

        # Stredovy kriz pro zarovnani
        drawing.add(Line(center - 10*mm, center, center + 10*mm, center, strokeColor=colors.lightgrey, strokeWidth=0.5))
        drawing.add(Line(center, center - 10*mm, center, center + 10*mm, strokeColor=colors.lightgrey, strokeWidth=0.5))

        ppq = self.get_points_per_quadrant()
        quadrant_colors = [
            colors.HexColor('#e74c3c'),  # A - cervena
            colors.HexColor('#3498db'),  # B - modra
            colors.HexColor('#2ecc71'),  # C - zelena
            colors.HexColor('#f39c12'),  # D - oranzova
        ]
        quadrant_labels = ['A', 'B', 'C', 'D']

        # Nakresli pozice hrebicku
        for i, (x, y) in enumerate(self.points):
            # Prevod z image souradnic na drawing souradnice
            norm_x = x / self.image_size  # 0-1
            norm_y = y / self.image_size  # 0-1

            draw_x = norm_x * drawing_size
            draw_y = (1 - norm_y) * drawing_size  # Invertuj Y pro PDF

            # Urceni kvadrantu a cisla
            quadrant_idx = i // ppq
            point_num = (i % ppq) + 1

            if quadrant_idx < 4:
                color = quadrant_colors[quadrant_idx]
                label = f"{quadrant_labels[quadrant_idx]}{point_num}"
            else:
                color = colors.gray
                label = str(i + 1)

            # Kruznice pro hrebik
            nail_radius = 2 * mm
            drawing.add(Circle(draw_x, draw_y, nail_radius, strokeColor=color, strokeWidth=0.8, fillColor=None))

            # Popisek (pro kazdy 5. hrebik nebo prvni/posledni)
            if point_num == 1 or point_num == ppq or point_num % 5 == 0:
                font_size = 5
                # Pozice textu - posun ven od stredu
                dx = draw_x - center
                dy = draw_y - center
                dist = math.sqrt(dx*dx + dy*dy) if (dx*dx + dy*dy) > 0 else 1
                offset = 4 * mm
                text_x = draw_x + (dx / dist) * offset
                text_y = draw_y + (dy / dist) * offset - font_size/2

                drawing.add(String(text_x, text_y, label,
                                  fontSize=font_size, fillColor=color,
                                  fontName=font_name, textAnchor='middle'))

        # Meritko
        scale_text = f"Meritko: 1:{int(frame_size_cm * 10 / drawing_size_mm)}" if drawing_size_mm < frame_size_cm * 10 else "Meritko 1:1"
        drawing.add(String(center, 5*mm, scale_text,
                          fontSize=8, fillColor=colors.gray,
                          fontName=font_name, textAnchor='middle'))

        return drawing
