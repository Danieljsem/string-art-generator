# -*- coding: utf-8 -*-
"""
Image Validator - Validace vstupnich obrazku pro String Art
Pro e-shop kriticky dulezite - ochrana pred nevhodnymi soubory
"""

import os
from PIL import Image
from typing import Dict, List, Tuple, Optional
import hashlib


class ImageValidator:
    """Kompletni validace vstupnich obrazku pro string art"""

    # Konfigurace limitu
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MIN_RESOLUTION = 200
    MAX_RESOLUTION = 8000
    OPTIMAL_MIN_RESOLUTION = 500
    ALLOWED_FORMATS = ['JPEG', 'PNG', 'WEBP', 'BMP', 'GIF', 'TIFF']
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif']

    def __init__(self):
        self.last_validation_result = None

    def validate(self, image_path: str) -> Dict:
        """
        Kompletni validace obrazku

        Args:
            image_path: Cesta k obrazku

        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'metadata': Dict
            }
        """
        errors = []
        warnings = []
        metadata = {}

        # Kontrola existence souboru
        if not os.path.exists(image_path):
            return {
                'valid': False,
                'errors': ['Soubor neexistuje'],
                'warnings': [],
                'metadata': {}
            }

        # Kontrola pripony
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            errors.append(f'Nepodporovana pripona: {ext}. Povolene: {", ".join(self.ALLOWED_EXTENSIONS)}')

        # Kontrola velikosti souboru
        try:
            file_size = os.path.getsize(image_path)
            metadata['file_size_bytes'] = file_size
            metadata['file_size_mb'] = round(file_size / (1024 * 1024), 2)

            if file_size > self.MAX_FILE_SIZE:
                errors.append(f'Soubor je prilis velky ({metadata["file_size_mb"]}MB). Maximum: {self.MAX_FILE_SIZE // (1024*1024)}MB')
            elif file_size > self.MAX_FILE_SIZE * 0.8:
                warnings.append(f'Soubor je velky ({metadata["file_size_mb"]}MB)')
        except Exception as e:
            errors.append(f'Nelze zjistit velikost souboru: {str(e)}')

        # Nacteni a kontrola obrazku
        try:
            img = Image.open(image_path)
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['size'] = img.size
            metadata['width'] = img.size[0]
            metadata['height'] = img.size[1]
            metadata['aspect_ratio'] = round(max(img.size) / min(img.size), 2)

            # Kontrola formatu
            if img.format not in self.ALLOWED_FORMATS:
                errors.append(f'Nepodporovany format: {img.format}')

            # Kontrola rozliseni
            w, h = img.size
            min_dim = min(w, h)
            max_dim = max(w, h)

            if min_dim < self.MIN_RESOLUTION:
                errors.append(f'Prilis nizke rozliseni ({w}x{h}). Minimum: {self.MIN_RESOLUTION}px')
            elif min_dim < self.OPTIMAL_MIN_RESOLUTION:
                warnings.append(f'Nizsi rozliseni ({w}x{h}). Pro lepsi vysledky doporucujeme min. {self.OPTIMAL_MIN_RESOLUTION}px')

            if max_dim > self.MAX_RESOLUTION:
                warnings.append(f'Vysoke rozliseni ({w}x{h}) - obrazek bude zmensen')

            # Kontrola pomeru stran
            aspect = max(w, h) / min(w, h)
            if aspect > 3:
                warnings.append(f'Extremni pomer stran ({aspect:.1f}:1). Doporucujeme oriznout na ctvercovy format.')
            elif aspect > 2:
                warnings.append(f'Siroky pomer stran ({aspect:.1f}:1). Cast obrazku bude orezana.')

            # Kontrola barevneho modu
            if img.mode == 'CMYK':
                warnings.append('Obrazek je v CMYK - bude preveden na RGB')
            elif img.mode == 'P':
                warnings.append('Obrazek ma paletu barev - bude preveden na RGB')
            elif img.mode == 'LA' or img.mode == 'PA':
                warnings.append('Obrazek ma alfa kanal - bude ignorovan')

            # Kontrola pruhednosti (pro PNG)
            if img.mode in ('RGBA', 'LA', 'PA'):
                # Zkontroluj, zda neni prilis pruhledny
                if img.mode == 'RGBA':
                    alpha = img.split()[3]
                    alpha_array = list(alpha.getdata())
                    transparent_pixels = sum(1 for a in alpha_array if a < 128)
                    transparency_ratio = transparent_pixels / len(alpha_array)
                    metadata['transparency_ratio'] = round(transparency_ratio, 2)

                    if transparency_ratio > 0.5:
                        warnings.append(f'Obrazek je z {int(transparency_ratio*100)}% pruhledny - pruhledne oblasti budou bile')

            # Hash souboru pro deduplikaci
            with open(image_path, 'rb') as f:
                metadata['file_hash'] = hashlib.md5(f.read()).hexdigest()

        except Exception as e:
            errors.append(f'Nelze nacist obrazek: {str(e)}')

        result = {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'metadata': metadata
        }

        self.last_validation_result = result
        return result

    def quick_validate(self, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        Rychla validace - vraci jen bool a prvni chybu

        Args:
            image_path: Cesta k obrazku

        Returns:
            (valid, error_message or None)
        """
        result = self.validate(image_path)
        if result['valid']:
            return True, None
        return False, result['errors'][0] if result['errors'] else 'Neznama chyba'

    def get_optimization_suggestions(self, image_path: str) -> List[str]:
        """
        Vraci doporuceni pro optimalizaci obrazku

        Args:
            image_path: Cesta k obrazku

        Returns:
            Seznam doporuceni
        """
        result = self.validate(image_path)
        suggestions = []

        if not result['valid']:
            suggestions.append("Obrazek nesplnuje zakladni pozadavky - opravte chyby.")
            return suggestions

        metadata = result['metadata']

        # Doporuceni podle velikosti
        if metadata.get('file_size_mb', 0) > 5:
            suggestions.append("Zvazujte komprimaci obrazku pro rychlejsi nahrani.")

        # Doporuceni podle rozliseni
        min_dim = min(metadata.get('width', 0), metadata.get('height', 0))
        if min_dim < 800:
            suggestions.append("Vyssi rozliseni (min. 800px) poskytne detailnejsi vysledek.")
        elif min_dim > 3000:
            suggestions.append("Obrazek je zbytecne velky - 1000-2000px je optimalni.")

        # Doporuceni podle pomeru stran
        if metadata.get('aspect_ratio', 1) > 1.5:
            suggestions.append("Orezani na ctvercovy format zajisti lepsi vyuziti plochy.")

        # Doporuceni podle formatu
        if metadata.get('format') == 'GIF':
            suggestions.append("Pro lepsi kvalitu pouzijte PNG nebo JPEG format.")

        return suggestions


class BatchValidator:
    """Validace vice obrazku najednou"""

    def __init__(self):
        self.validator = ImageValidator()

    def validate_batch(self, image_paths: List[str]) -> Dict:
        """
        Validuje seznam obrazku

        Args:
            image_paths: Seznam cest k obrazkum

        Returns:
            {
                'total': int,
                'valid': int,
                'invalid': int,
                'results': List[Dict]
            }
        """
        results = []
        valid_count = 0
        invalid_count = 0

        for path in image_paths:
            result = self.validator.validate(path)
            result['path'] = path
            results.append(result)

            if result['valid']:
                valid_count += 1
            else:
                invalid_count += 1

        return {
            'total': len(image_paths),
            'valid': valid_count,
            'invalid': invalid_count,
            'results': results
        }

    def filter_valid(self, image_paths: List[str]) -> Tuple[List[str], List[str]]:
        """
        Rozdeli obrazky na validni a nevalidni

        Returns:
            (valid_paths, invalid_paths)
        """
        valid = []
        invalid = []

        for path in image_paths:
            is_valid, _ = self.validator.quick_validate(path)
            if is_valid:
                valid.append(path)
            else:
                invalid.append(path)

        return valid, invalid
