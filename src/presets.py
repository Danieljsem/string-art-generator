# -*- coding: utf-8 -*-
"""
Presety pro String Art Generator
Optimalizovane nastaveni pro ruzne typy obrazku
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class StringArtPreset:
    """Preset pro generovani string art"""
    id: str
    name: str
    name_en: str
    description: str
    description_en: str

    # Zakladni parametry
    num_lines: int
    num_points: int
    line_weight: int
    min_distance: int

    # Kvalita a rychlost
    speed_mode: str  # 'ultra_fast', 'fast', 'precise'

    # Obrazove upravy
    contrast_factor: float
    edge_enhancement: float  # 0.0-1.0
    sharpness_factor: float

    # Vizualizace
    opacity: float
    line_width: float

    # Metadata
    difficulty: str  # 'easy', 'medium', 'hard'
    assembly_hours_min: float
    assembly_hours_max: float
    recommended_frame_cm: int
    tags: List[str]


# Definice presetu
PRESETS: Dict[str, StringArtPreset] = {
    'portrait': StringArtPreset(
        id='portrait',
        name='Portret',
        name_en='Portrait',
        description='Optimalizovano pro obliceje a portretni fotografie',
        description_en='Optimized for faces and portrait photography',
        num_lines=4500,
        num_points=240,
        line_weight=35,
        min_distance=15,
        speed_mode='precise',
        contrast_factor=1.6,
        edge_enhancement=0.2,
        sharpness_factor=1.4,
        opacity=0.12,
        line_width=0.5,
        difficulty='medium',
        assembly_hours_min=8,
        assembly_hours_max=12,
        recommended_frame_cm=40,
        tags=['portret', 'oblicej', 'osoba', 'detail']
    ),

    'pet': StringArtPreset(
        id='pet',
        name='Domaci mazlicek',
        name_en='Pet',
        description='Pro fotky psu, kocek a jinych zvirat',
        description_en='For photos of dogs, cats and other animals',
        num_lines=4000,
        num_points=240,
        line_weight=40,
        min_distance=18,
        speed_mode='fast',
        contrast_factor=1.5,
        edge_enhancement=0.15,
        sharpness_factor=1.3,
        opacity=0.12,
        line_width=0.5,
        difficulty='medium',
        assembly_hours_min=7,
        assembly_hours_max=10,
        recommended_frame_cm=40,
        tags=['pes', 'kocka', 'zvire', 'mazlicek']
    ),

    'logo': StringArtPreset(
        id='logo',
        name='Logo / Grafika',
        name_en='Logo / Graphics',
        description='Pro jednoducha loga, ikony a grafiku s ostrymi hranami',
        description_en='For simple logos, icons and graphics with sharp edges',
        num_lines=2500,
        num_points=200,
        line_weight=50,
        min_distance=25,
        speed_mode='fast',
        contrast_factor=2.0,
        edge_enhancement=0.0,
        sharpness_factor=1.5,
        opacity=0.15,
        line_width=0.6,
        difficulty='easy',
        assembly_hours_min=4,
        assembly_hours_max=6,
        recommended_frame_cm=35,
        tags=['logo', 'grafika', 'ikona', 'jednoduchy']
    ),

    'landscape': StringArtPreset(
        id='landscape',
        name='Krajina',
        name_en='Landscape',
        description='Pro fotky krajin, prirody a architektury',
        description_en='For photos of landscapes, nature and architecture',
        num_lines=5000,
        num_points=240,
        line_weight=38,  # Zvyseno v5.2 pro lepsi kontrast
        min_distance=12,
        speed_mode='precise',
        contrast_factor=1.4,
        edge_enhancement=0.25,
        sharpness_factor=1.2,
        opacity=0.10,
        line_width=0.4,
        difficulty='hard',
        assembly_hours_min=10,
        assembly_hours_max=15,
        recommended_frame_cm=50,
        tags=['krajina', 'priroda', 'architektura', 'siroke']
    ),

    'high_detail': StringArtPreset(
        id='high_detail',
        name='Vysoky detail',
        name_en='High Detail',
        description='Maximum detailu pro narocne projekty (delsi generovani)',
        description_en='Maximum detail for demanding projects (longer generation)',
        num_lines=6000,
        num_points=288,
        line_weight=35,  # Zvyseno v5.2 pro lepsi kontrast
        min_distance=10,
        speed_mode='precise',
        contrast_factor=1.5,
        edge_enhancement=0.3,
        sharpness_factor=1.4,
        opacity=0.10,
        line_width=0.4,
        difficulty='hard',
        assembly_hours_min=12,
        assembly_hours_max=18,
        recommended_frame_cm=50,
        tags=['detail', 'slozity', 'premium', 'narocny']
    ),

    'quick': StringArtPreset(
        id='quick',
        name='Rychly projekt',
        name_en='Quick Project',
        description='Pro zacatecniky a rychle projekty',
        description_en='For beginners and quick projects',
        num_lines=2000,
        num_points=160,
        line_weight=45,
        min_distance=20,
        speed_mode='ultra_fast',
        contrast_factor=1.7,
        edge_enhancement=0.1,
        sharpness_factor=1.3,
        opacity=0.15,
        line_width=0.6,
        difficulty='easy',
        assembly_hours_min=3,
        assembly_hours_max=5,
        recommended_frame_cm=30,
        tags=['rychly', 'jednoduchy', 'zacatecnik', 'maly']
    ),

    'wedding': StringArtPreset(
        id='wedding',
        name='Svatebni',
        name_en='Wedding',
        description='Pro svatebni fotky a romanticke portety',
        description_en='For wedding photos and romantic portraits',
        num_lines=5000,
        num_points=240,
        line_weight=32,
        min_distance=14,
        speed_mode='precise',
        contrast_factor=1.5,
        edge_enhancement=0.18,
        sharpness_factor=1.35,
        opacity=0.11,
        line_width=0.45,
        difficulty='hard',
        assembly_hours_min=10,
        assembly_hours_max=14,
        recommended_frame_cm=45,
        tags=['svatba', 'par', 'romanticky', 'darek']
    ),

    'minimalist': StringArtPreset(
        id='minimalist',
        name='Minimalisticky',
        name_en='Minimalist',
        description='Menej niti pro abstraktnejsi vzhled',
        description_en='Fewer lines for more abstract look',
        num_lines=1500,
        num_points=120,
        line_weight=55,
        min_distance=30,
        speed_mode='fast',
        contrast_factor=1.8,
        edge_enhancement=0.0,
        sharpness_factor=1.2,
        opacity=0.18,
        line_width=0.7,
        difficulty='easy',
        assembly_hours_min=2,
        assembly_hours_max=4,
        recommended_frame_cm=30,
        tags=['minimalisticky', 'abstraktni', 'jednoduchy', 'moderni']
    ),

    'child': StringArtPreset(
        id='child',
        name='Detsky portret',
        name_en='Child Portrait',
        description='Optimalizovano pro detske tvare',
        description_en='Optimized for children faces',
        num_lines=4000,
        num_points=240,
        line_weight=38,
        min_distance=16,
        speed_mode='precise',
        contrast_factor=1.55,
        edge_enhancement=0.22,
        sharpness_factor=1.35,
        opacity=0.11,
        line_width=0.5,
        difficulty='medium',
        assembly_hours_min=7,
        assembly_hours_max=10,
        recommended_frame_cm=40,
        tags=['dite', 'rodina', 'portret', 'mimino']
    )
}


def get_preset(preset_id: str) -> Optional[StringArtPreset]:
    """Ziska preset podle ID"""
    return PRESETS.get(preset_id)


def get_all_presets() -> Dict[str, StringArtPreset]:
    """Ziska vsechny presety"""
    return PRESETS


def get_presets_by_difficulty(difficulty: str) -> List[StringArtPreset]:
    """Ziska presety podle obtiznosti"""
    return [p for p in PRESETS.values() if p.difficulty == difficulty]


def get_presets_by_tag(tag: str) -> List[StringArtPreset]:
    """Ziska presety podle tagu"""
    return [p for p in PRESETS.values() if tag.lower() in [t.lower() for t in p.tags]]


def suggest_preset(image_analysis: Dict) -> StringArtPreset:
    """
    Navrhne vhodny preset na zaklade analyzy obrazku

    Args:
        image_analysis: Vysledek z analyze_image_suitability()

    Returns:
        Doporuceny preset
    """
    score = image_analysis.get('overall_score', 50)
    contrast = image_analysis.get('contrast_score', 50)
    detail = image_analysis.get('detail_score', 50)

    # Nizka kvalita -> jednoduchy preset
    if score < 50:
        return PRESETS['quick']

    # Vysoky detail -> high_detail nebo portrait
    if detail > 70 and contrast > 60:
        if score > 80:
            return PRESETS['high_detail']
        return PRESETS['portrait']

    # Stredni kvalita -> standard portrait nebo pet
    if score >= 60:
        return PRESETS['portrait']

    # Default
    return PRESETS['pet']


def preset_to_dict(preset: StringArtPreset) -> Dict:
    """Prevede preset na dictionary pro JSON export"""
    return {
        'id': preset.id,
        'name': preset.name,
        'name_en': preset.name_en,
        'description': preset.description,
        'description_en': preset.description_en,
        'settings': {
            'num_lines': preset.num_lines,
            'num_points': preset.num_points,
            'line_weight': preset.line_weight,
            'min_distance': preset.min_distance,
            'speed_mode': preset.speed_mode,
            'contrast_factor': preset.contrast_factor,
            'edge_enhancement': preset.edge_enhancement,
            'sharpness_factor': preset.sharpness_factor,
            'opacity': preset.opacity,
            'line_width': preset.line_width
        },
        'metadata': {
            'difficulty': preset.difficulty,
            'assembly_time': f"{preset.assembly_hours_min}-{preset.assembly_hours_max} hodin",
            'recommended_frame_cm': preset.recommended_frame_cm,
            'tags': preset.tags
        }
    }


def get_presets_for_eshop() -> List[Dict]:
    """Vraci seznam presetu formatovany pro e-shop"""
    return [preset_to_dict(p) for p in PRESETS.values()]


# Pomocna funkce pro GUI
def get_preset_names_for_dropdown() -> List[tuple]:
    """Vraci seznam (id, name) pro dropdown v GUI"""
    return [(p.id, p.name) for p in PRESETS.values()]
