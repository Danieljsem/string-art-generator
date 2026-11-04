# -*- coding: utf-8 -*-
"""
Material Estimator - Odhad materialu a casu pro String Art
Dulezite pro e-shop - zakaznici musi vedet, kolik materialu potrebuji
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ThreadType:
    """Typ nite pro string art"""
    name: str
    thickness_mm: float
    weight_per_m_g: float
    spool_length_m: float
    price_per_spool: float  # CZK
    colors_available: int


# Predefinovane typy niti
THREAD_TYPES = {
    'cotton_standard': ThreadType(
        name='Bavlnena nit - standardni',
        thickness_mm=0.5,
        weight_per_m_g=0.002,
        spool_length_m=100,
        price_per_spool=45,
        colors_available=50
    ),
    'polyester': ThreadType(
        name='Polyesterova nit',
        thickness_mm=0.3,
        weight_per_m_g=0.0015,
        spool_length_m=200,
        price_per_spool=65,
        colors_available=100
    ),
    'silk': ThreadType(
        name='Hedvabna nit (premium)',
        thickness_mm=0.2,
        weight_per_m_g=0.001,
        spool_length_m=50,
        price_per_spool=150,
        colors_available=30
    ),
    'nylon': ThreadType(
        name='Nylonova nit',
        thickness_mm=0.4,
        weight_per_m_g=0.0018,
        spool_length_m=150,
        price_per_spool=55,
        colors_available=40
    )
}


@dataclass
class SkillLevel:
    """Uroven dovednosti pro odhad casu"""
    name: str
    seconds_per_line: float
    break_interval_lines: int
    break_duration_min: int
    error_rate: float  # Procento chyb vyzadujicich opravu


SKILL_LEVELS = {
    'beginner': SkillLevel(
        name='Zacatecnik',
        seconds_per_line=12.0,
        break_interval_lines=150,
        break_duration_min=15,
        error_rate=0.05
    ),
    'intermediate': SkillLevel(
        name='Pokrocily',
        seconds_per_line=6.0,
        break_interval_lines=300,
        break_duration_min=10,
        error_rate=0.02
    ),
    'expert': SkillLevel(
        name='Expert',
        seconds_per_line=3.0,
        break_interval_lines=500,
        break_duration_min=5,
        error_rate=0.01
    )
}


class MaterialEstimator:
    """Odhad materialu a casu pro string art projekt"""

    def __init__(self, num_points: int = 240, frame_diameter_cm: float = 40.0):
        """
        Args:
            num_points: Pocet bodu/hrebiku na ramu
            frame_diameter_cm: Prumer ramu v centimetrech
        """
        self.num_points = num_points
        self.frame_diameter_cm = frame_diameter_cm
        self.frame_radius_cm = frame_diameter_cm / 2
        self.points = self._generate_points()

    def _generate_points(self) -> List[Tuple[float, float]]:
        """Vygeneruje pozice bodu na kruhu v cm"""
        points = []
        for i in range(self.num_points):
            angle = 2 * math.pi * i / self.num_points
            x = self.frame_radius_cm * math.cos(angle)
            y = self.frame_radius_cm * math.sin(angle)
            points.append((x, y))
        return points

    def calculate_line_length(self, point_a_idx: int, point_b_idx: int) -> float:
        """
        Vypocita delku jedne linie v cm

        Args:
            point_a_idx: Index prvniho bodu
            point_b_idx: Index druheho bodu

        Returns:
            Delka linie v cm
        """
        p1 = self.points[point_a_idx]
        p2 = self.points[point_b_idx]
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

    def calculate_thread_length(self, lines: List[Tuple[int, int]],
                                 thread_type: str = 'cotton_standard') -> Dict:
        """
        Vypocita celkovou delku nite

        Args:
            lines: Seznam lini [(from_idx, to_idx), ...]
            thread_type: Typ nite z THREAD_TYPES

        Returns:
            {
                'total_length_cm': float,
                'total_length_m': float,
                'thread_weight_g': float,
                'recommended_spools': int,
                'estimated_cost': float
            }
        """
        thread = THREAD_TYPES.get(thread_type, THREAD_TYPES['cotton_standard'])

        total_length_cm = 0
        for from_idx, to_idx in lines:
            total_length_cm += self.calculate_line_length(from_idx, to_idx)

        # Pridej 10% rezervu na obtaceni kolem hrebiku
        total_length_cm *= 1.10

        total_length_m = total_length_cm / 100
        thread_weight = total_length_m * thread.weight_per_m_g
        spools_needed = math.ceil(total_length_m / thread.spool_length_m)
        estimated_cost = spools_needed * thread.price_per_spool

        return {
            'total_length_cm': round(total_length_cm, 1),
            'total_length_m': round(total_length_m, 2),
            'thread_weight_g': round(thread_weight, 2),
            'recommended_spools': spools_needed,
            'estimated_cost_czk': estimated_cost,
            'thread_type': thread.name,
            'includes_reserve': '10%'
        }

    def estimate_thread_from_params(self, num_lines: int,
                                     thread_type: str = 'cotton_standard') -> Dict:
        """
        Odhad delky nite bez znalosti konkretniho rozlozeni lini

        Pouziva prumernou delku linie pro odhad.

        Args:
            num_lines: Pocet lini
            thread_type: Typ nite

        Returns:
            Odhad materialu
        """
        thread = THREAD_TYPES.get(thread_type, THREAD_TYPES['cotton_standard'])

        # Prumerna delka linie je priblizne 0.6-0.8 prumeru
        avg_line_length_cm = self.frame_diameter_cm * 0.7

        total_length_cm = num_lines * avg_line_length_cm * 1.10  # +10% rezerva
        total_length_m = total_length_cm / 100
        thread_weight = total_length_m * thread.weight_per_m_g
        spools_needed = math.ceil(total_length_m / thread.spool_length_m)
        estimated_cost = spools_needed * thread.price_per_spool

        return {
            'total_length_cm': round(total_length_cm, 1),
            'total_length_m': round(total_length_m, 2),
            'thread_weight_g': round(thread_weight, 2),
            'recommended_spools': spools_needed,
            'estimated_cost_czk': estimated_cost,
            'thread_type': thread.name,
            'note': 'Odhad zalozeny na prumerne delce linie'
        }

    def estimate_assembly_time(self, num_lines: int,
                                skill_level: str = 'beginner') -> Dict:
        """
        Odhadne cas potrebny k sestaveni

        Args:
            num_lines: Pocet lini
            skill_level: Uroven dovednosti

        Returns:
            {
                'total_hours': float,
                'work_time_hours': float,
                'break_time_hours': float,
                'sessions': List[Dict],
                'recommended_days': int
            }
        """
        skill = SKILL_LEVELS.get(skill_level, SKILL_LEVELS['beginner'])

        # Zakladni cas prace
        work_seconds = num_lines * skill.seconds_per_line

        # Pridej cas na opravy chyb
        error_lines = int(num_lines * skill.error_rate)
        error_seconds = error_lines * skill.seconds_per_line * 2  # Oprava trva dvojnasobek

        total_work_seconds = work_seconds + error_seconds

        # Pocet prestavek
        num_breaks = num_lines // skill.break_interval_lines
        break_seconds = num_breaks * skill.break_duration_min * 60

        total_seconds = total_work_seconds + break_seconds

        # Vytvor harmonogram sezeni
        sessions = []
        remaining_lines = num_lines
        session_num = 1

        while remaining_lines > 0:
            lines_in_session = min(remaining_lines, skill.break_interval_lines)
            session_minutes = (lines_in_session * skill.seconds_per_line) / 60

            sessions.append({
                'session': session_num,
                'lines': lines_in_session,
                'duration_min': round(session_minutes, 0),
                'break_after_min': skill.break_duration_min if remaining_lines > lines_in_session else 0
            })

            remaining_lines -= lines_in_session
            session_num += 1

        # Doporuceny pocet dni (max 3 hodiny prace denne)
        total_hours = total_seconds / 3600
        recommended_days = math.ceil(total_hours / 3)

        return {
            'total_hours': round(total_hours, 1),
            'work_time_hours': round(total_work_seconds / 3600, 1),
            'break_time_hours': round(break_seconds / 3600, 1),
            'total_sessions': len(sessions),
            'sessions': sessions,
            'recommended_days': recommended_days,
            'skill_level': skill.name,
            'estimated_errors': error_lines,
            'tips': self._get_assembly_tips(skill_level, num_lines)
        }

    def _get_assembly_tips(self, skill_level: str, num_lines: int) -> List[str]:
        """Vraci tipy pro sestaveni"""
        tips = []

        if skill_level == 'beginner':
            tips.append("Zacinejte v klidu a postupne zrychlujte")
            tips.append("Pouzijte pinzetu pro snazsi uchyceni nite")
            tips.append("Oznacte si dokoncene kroky v navodu")

        if num_lines > 3000:
            tips.append("Pro projekty s vice nez 3000 linii doporucujeme rozlozit na vice dni")
            tips.append("Davejte si prestavky kazdych 30-45 minut")

        if num_lines > 5000:
            tips.append("Velmi narocny projekt - zvazujte pomoc druhe osoby")

        tips.append("Ujistete se, ze mate dobre osvetleni pracovni plochy")
        tips.append("Pracujte na rovnem a stabilnim povrchu")

        return tips

    def get_full_estimate(self, num_lines: int,
                          thread_type: str = 'cotton_standard',
                          skill_level: str = 'beginner') -> Dict:
        """
        Kompletni odhad materialu a casu

        Args:
            num_lines: Pocet lini
            thread_type: Typ nite
            skill_level: Uroven dovednosti

        Returns:
            Kompletni odhad
        """
        material = self.estimate_thread_from_params(num_lines, thread_type)
        time = self.estimate_assembly_time(num_lines, skill_level)

        return {
            'summary': {
                'num_lines': num_lines,
                'frame_diameter_cm': self.frame_diameter_cm,
                'num_points': self.num_points
            },
            'material': material,
            'time': time,
            'total_cost_estimate': {
                'thread_czk': material['estimated_cost_czk'],
                'note': 'Nezahrnuje cenu ramu a hrebiku'
            }
        }

    def format_estimate_for_customer(self, num_lines: int,
                                      thread_type: str = 'cotton_standard',
                                      skill_level: str = 'beginner') -> str:
        """
        Formatuje odhad pro zobrazeni zakaznikovi

        Returns:
            Formatovany text
        """
        est = self.get_full_estimate(num_lines, thread_type, skill_level)

        text = f"""
╔══════════════════════════════════════════════════════╗
║          ODHAD MATERIALU A CASU                      ║
╚══════════════════════════════════════════════════════╝

📊 PROJEKT
   Pocet lini: {est['summary']['num_lines']:,}
   Prumer ramu: {est['summary']['frame_diameter_cm']} cm
   Pocet hrebiku: {est['summary']['num_points']}

🧵 MATERIAL ({est['material']['thread_type']})
   Delka nite: {est['material']['total_length_m']:.1f} m
   Vaha nite: {est['material']['thread_weight_g']:.1f} g
   Doporuceny pocet civek: {est['material']['recommended_spools']}
   Odhadovana cena nite: {est['material']['estimated_cost_czk']:.0f} CZK

⏱️  CAS ({est['time']['skill_level']})
   Celkovy cas: {est['time']['total_hours']:.1f} hodin
   Pocet sezeni: {est['time']['total_sessions']}
   Doporuceny pocet dni: {est['time']['recommended_days']}

💡 TIPY
"""
        for tip in est['time']['tips']:
            text += f"   • {tip}\n"

        return text


# Pomocne funkce pro rychly pristup
def quick_estimate(num_lines: int, frame_cm: float = 40) -> Dict:
    """Rychly odhad pro e-shop"""
    estimator = MaterialEstimator(frame_diameter_cm=frame_cm)
    return estimator.get_full_estimate(num_lines)


def estimate_for_product_page(num_lines: int) -> Dict:
    """
    Odhad pro zobrazeni na produktove strance e-shopu

    Returns:
        Zjednoduseny odhad pro zakaznika
    """
    est = quick_estimate(num_lines)
    return {
        'assembly_time': f"{est['time']['total_hours']:.0f}-{est['time']['total_hours']*1.3:.0f} hodin",
        'difficulty': 'Snadny' if num_lines < 2500 else 'Stredni' if num_lines < 4000 else 'Narocny',
        'thread_needed': f"cca {est['material']['total_length_m']:.0f} m",
        'recommended_for': 'Zacatecniky' if num_lines < 2500 else 'Pokrocile' if num_lines < 4500 else 'Zkusene'
    }
