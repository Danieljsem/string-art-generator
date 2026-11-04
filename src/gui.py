# -*- coding: utf-8 -*-
"""
String Art Generator - GUI v5.0 (E-Shop Edition)
Graficke rozhrani pro generovani string art
VYLEPŠENO: Presety, analyza obrazku, odhad materialu, edge enhancement
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import tempfile
import threading
from string_art import StringArtGenerator
from image_editor import ImageEditor
from presets import PRESETS, get_preset, get_preset_names_for_dropdown
from validators import ImageValidator
from estimator import MaterialEstimator, estimate_for_product_page


class StringArtGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("String Art Generator v5.0 - E-Shop Edition")
        self.root.geometry("1200x900")
        self.root.configure(bg='#1a1a2e')

        self.generator = None
        self.image_path = None
        self.generated_lines = None
        self.edited_image = None
        self.is_generating = False
        self.validator = ImageValidator()
        self.estimator = MaterialEstimator()
        self.current_preset = None

        # Styl
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        self.setup_ui()

    def configure_styles(self):
        """Nastaví tmavý moderní styl"""
        bg_dark = '#1a1a2e'
        bg_medium = '#16213e'
        bg_light = '#0f3460'
        accent = '#e94560'
        text_color = '#eaeaea'

        self.style.configure('TFrame', background=bg_dark)
        self.style.configure('TLabelframe', background=bg_dark, foreground=text_color)
        self.style.configure('TLabelframe.Label', background=bg_dark, foreground=accent,
                           font=('Segoe UI', 11, 'bold'))
        self.style.configure('TLabel', background=bg_dark, foreground=text_color,
                           font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10))
        self.style.configure('TEntry', font=('Segoe UI', 10))
        self.style.configure('TCombobox', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 24, 'bold'),
                           foreground=accent, background=bg_dark)
        self.style.configure('SubHeader.TLabel', font=('Segoe UI', 10),
                           foreground='#888888', background=bg_dark)

    def setup_ui(self):
        """Vytvoří uživatelské rozhraní"""

        # Hlavní frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Nadpis
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        title = ttk.Label(header_frame, text="String Art Generator", style='Header.TLabel')
        title.pack()
        subtitle = ttk.Label(header_frame, text="v5.0 E-Shop Edition - Presety, analyza, odhad materialu",
                            style='SubHeader.TLabel')
        subtitle.pack()

        # Levý panel - nastavení
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=1, column=0, sticky=(tk.N, tk.W, tk.E), padx=(0, 10))

        # === PRESETY ===
        preset_frame = ttk.LabelFrame(left_panel, text="Rychle presety", padding="10")
        preset_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(preset_frame, text="Typ obrazku:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.preset_var = tk.StringVar(value='portrait')
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, width=18, state='readonly')
        preset_names = [(p.id, p.name) for p in PRESETS.values()]
        preset_combo['values'] = [f"{name}" for id, name in preset_names]
        preset_combo.current(0)
        preset_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_change)

        self.preset_info_label = ttk.Label(preset_frame, text="Portret - pro obliceje",
                                          font=('Segoe UI', 8, 'italic'), foreground='#888888')
        self.preset_info_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        apply_preset_btn = tk.Button(preset_frame, text="Aplikovat preset",
                                    command=self.apply_preset,
                                    bg='#2ecc71', fg='white', font=('Segoe UI', 9), padx=10, pady=3)
        apply_preset_btn.grid(row=2, column=0, columnspan=2, pady=5)

        # === ZÁKLADNÍ NASTAVENÍ ===
        basic_frame = ttk.LabelFrame(left_panel, text="Manualni nastaveni", padding="10")
        basic_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        # Počet bodů
        ttk.Label(basic_frame, text="Počet bodů:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.num_points_var = tk.IntVar(value=200)
        points_combo = ttk.Combobox(basic_frame, textvariable=self.num_points_var, width=12, state='readonly')
        points_combo['values'] = (120, 160, 200, 240, 288, 360)
        points_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        # Počet linií
        ttk.Label(basic_frame, text="Počet linií:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.num_lines_var = tk.IntVar(value=3500)
        lines_combo = ttk.Combobox(basic_frame, textvariable=self.num_lines_var, width=12, state='readonly')
        lines_combo['values'] = (1500, 2500, 3500, 4500, 5500, 7000)
        lines_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        # Tvar
        ttk.Label(basic_frame, text="Tvar:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.shape_var = tk.StringVar(value='circle')
        shape_combo = ttk.Combobox(basic_frame, textvariable=self.shape_var, width=12, state='readonly')
        shape_combo['values'] = ('circle', 'square', 'star')
        shape_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        # Rychlost
        ttk.Label(basic_frame, text="Kvalita/Rychlost:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.speed_var = tk.StringVar(value='fast')
        speed_combo = ttk.Combobox(basic_frame, textvariable=self.speed_var, width=12, state='readonly')
        speed_combo['values'] = ('ultra_fast', 'fast', 'precise')
        speed_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)

        # === VIZUALIZACE ===
        viz_frame = ttk.LabelFrame(left_panel, text="Vizualizace nití", padding="10")
        viz_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)

        # Průhlednost (KLÍČOVÉ!)
        ttk.Label(viz_frame, text="Průhlednost nití:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.opacity_var = tk.DoubleVar(value=0.12)
        opacity_scale = ttk.Scale(viz_frame, from_=0.05, to=0.4, variable=self.opacity_var,
                                 orient=tk.HORIZONTAL, length=150, command=self.on_opacity_change)
        opacity_scale.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        self.opacity_label = ttk.Label(viz_frame, text="12%", width=5)
        self.opacity_label.grid(row=0, column=2, sticky=tk.W)

        # Šířka nití
        ttk.Label(viz_frame, text="Šířka nití:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.line_width_var = tk.DoubleVar(value=0.5)
        width_scale = ttk.Scale(viz_frame, from_=0.3, to=2.0, variable=self.line_width_var,
                               orient=tk.HORIZONTAL, length=150, command=self.on_width_change)
        width_scale.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.width_label = ttk.Label(viz_frame, text="0.5", width=5)
        self.width_label.grid(row=1, column=2, sticky=tk.W)

        # Kontrast
        ttk.Label(viz_frame, text="Kontrast:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.contrast_var = tk.DoubleVar(value=1.5)
        contrast_scale = ttk.Scale(viz_frame, from_=1.0, to=2.5, variable=self.contrast_var,
                                  orient=tk.HORIZONTAL, length=150, command=self.on_contrast_change)
        contrast_scale.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        self.contrast_label = ttk.Label(viz_frame, text="1.5x", width=5)
        self.contrast_label.grid(row=2, column=2, sticky=tk.W)

        # Zobrazit piny
        self.show_pins_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(viz_frame, text="Zobrazit piny/hřebíky",
                       variable=self.show_pins_var).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=2)

        # Edge Enhancement
        ttk.Label(viz_frame, text="Zesílení hran:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.edge_var = tk.DoubleVar(value=0.0)
        edge_scale = ttk.Scale(viz_frame, from_=0.0, to=0.5, variable=self.edge_var,
                              orient=tk.HORIZONTAL, length=150, command=self.on_edge_change)
        edge_scale.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        self.edge_label = ttk.Label(viz_frame, text="0%", width=5)
        self.edge_label.grid(row=4, column=2, sticky=tk.W)

        # === POKROČILÉ ===
        adv_frame = ttk.LabelFrame(left_panel, text="Pokročilé", padding="10")
        adv_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(adv_frame, text="Váha linie:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.line_weight_var = tk.IntVar(value=35)  # Zvýšeno v5.2 pro lepší kontrast
        ttk.Entry(adv_frame, textvariable=self.line_weight_var, width=8).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(adv_frame, text="Min. vzdálenost:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.min_distance_var = tk.IntVar(value=20)
        ttk.Entry(adv_frame, textvariable=self.min_distance_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=5)

        # === VSTUPNÍ OBRÁZEK ===
        image_frame = ttk.LabelFrame(left_panel, text="Vstupní obrázek", padding="10")
        image_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)

        self.image_path_label = ttk.Label(image_frame, text="Žádný obrázek nevybrán",
                                         font=('Segoe UI', 9, 'italic'))
        self.image_path_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5)

        btn_frame = ttk.Frame(image_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)

        select_btn = tk.Button(btn_frame, text="Vybrat obrázek", command=self.load_image,
                              bg='#0f3460', fg='white', font=('Segoe UI', 10), padx=15, pady=5)
        select_btn.pack(side=tk.LEFT, padx=2)

        analyze_btn = tk.Button(btn_frame, text="Analyzovat", command=self.analyze_image,
                               bg='#f39c12', fg='white', font=('Segoe UI', 10), padx=10, pady=5)
        analyze_btn.pack(side=tk.LEFT, padx=2)

        # Info o kvalite obrazku
        self.quality_label = ttk.Label(image_frame, text="",
                                       font=('Segoe UI', 9), foreground='#888888')
        self.quality_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # === ODHAD MATERIALU ===
        estimate_frame = ttk.LabelFrame(left_panel, text="Odhad materialu a casu", padding="10")
        estimate_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)

        self.estimate_label = ttk.Label(estimate_frame, text="Vyberte preset nebo nastavte linie",
                                        font=('Segoe UI', 9), foreground='#888888')
        self.estimate_label.grid(row=0, column=0, sticky=tk.W, padx=5)

        estimate_btn = tk.Button(estimate_frame, text="Vypocitat odhad", command=self.show_estimate,
                                bg='#9b59b6', fg='white', font=('Segoe UI', 9), padx=10, pady=3)
        estimate_btn.grid(row=1, column=0, pady=5)

        # === AKCE ===
        action_frame = ttk.Frame(left_panel)
        action_frame.grid(row=6, column=0, pady=15)

        self.generate_btn = tk.Button(action_frame, text="GENEROVAT STRING ART",
                                     command=self.generate_art, state=tk.DISABLED,
                                     bg='#e94560', fg='white', font=('Segoe UI', 12, 'bold'),
                                     padx=20, pady=10)
        self.generate_btn.pack(pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(left_panel, mode='determinate', length=300)
        self.progress.grid(row=7, column=0, pady=5)

        self.status_label = ttk.Label(left_panel, text="Připraven", font=('Segoe UI', 10))
        self.status_label.grid(row=8, column=0)

        # Pravý panel - náhled a export
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))

        # Náhled
        preview_frame = ttk.LabelFrame(right_panel, text="Náhled výsledku", padding="10")
        preview_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        self.preview_canvas = tk.Canvas(preview_frame, width=500, height=500, bg='white',
                                        highlightthickness=2, highlightbackground='#0f3460')
        self.preview_canvas.pack(pady=5)

        # Export tlačítka - obrázky
        export_frame1 = ttk.Frame(right_panel)
        export_frame1.grid(row=1, column=0, pady=5)

        ttk.Label(export_frame1, text="Export obrázků:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=5)

        self.export_png_btn = tk.Button(export_frame1, text="PNG", command=self.export_png,
                                       state=tk.DISABLED, bg='#0f3460', fg='white',
                                       font=('Segoe UI', 9), padx=8, pady=3)
        self.export_png_btn.pack(side=tk.LEFT, padx=2)

        self.export_svg_btn = tk.Button(export_frame1, text="SVG", command=self.export_svg,
                                       state=tk.DISABLED, bg='#0f3460', fg='white',
                                       font=('Segoe UI', 9), padx=8, pady=3)
        self.export_svg_btn.pack(side=tk.LEFT, padx=2)

        self.refresh_btn = tk.Button(export_frame1, text="Obnovit náhled",
                                    command=self.refresh_preview, state=tk.DISABLED,
                                    bg='#16213e', fg='white', font=('Segoe UI', 9), padx=8, pady=3)
        self.refresh_btn.pack(side=tk.LEFT, padx=2)

        # Export tlačítka - tutoriály
        export_frame2 = ttk.Frame(right_panel)
        export_frame2.grid(row=2, column=0, pady=5)

        ttk.Label(export_frame2, text="Tutoriály:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=5)

        self.export_html_btn = tk.Button(export_frame2, text="HTML Průvodce",
                                        command=self.export_html_tutorial, state=tk.DISABLED,
                                        bg='#e94560', fg='white', font=('Segoe UI', 9, 'bold'),
                                        padx=8, pady=3)
        self.export_html_btn.pack(side=tk.LEFT, padx=2)

        self.export_pdf_btn = tk.Button(export_frame2, text="PDF Tutorial",
                                       command=self.export_pdf_tutorial, state=tk.DISABLED,
                                       bg='#e94560', fg='white', font=('Segoe UI', 9, 'bold'),
                                       padx=8, pady=3)
        self.export_pdf_btn.pack(side=tk.LEFT, padx=2)

        self.export_diagram_btn = tk.Button(export_frame2, text="Pin Diagram",
                                           command=self.export_pin_diagram, state=tk.DISABLED,
                                           bg='#2ecc71', fg='white', font=('Segoe UI', 9),
                                           padx=8, pady=3)
        self.export_diagram_btn.pack(side=tk.LEFT, padx=2)

        # Export tlačítka - data
        export_frame3 = ttk.Frame(right_panel)
        export_frame3.grid(row=3, column=0, pady=5)

        ttk.Label(export_frame3, text="Data:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=5)

        self.export_txt_btn = tk.Button(export_frame3, text="TXT", command=self.export_txt,
                                       state=tk.DISABLED, bg='#0f3460', fg='white',
                                       font=('Segoe UI', 9), padx=8, pady=3)
        self.export_txt_btn.pack(side=tk.LEFT, padx=2)

        self.export_json_btn = tk.Button(export_frame3, text="JSON", command=self.export_json,
                                        state=tk.DISABLED, bg='#0f3460', fg='white',
                                        font=('Segoe UI', 9), padx=8, pady=3)
        self.export_json_btn.pack(side=tk.LEFT, padx=2)

        self.export_csv_btn = tk.Button(export_frame3, text="CSV", command=self.export_csv,
                                       state=tk.DISABLED, bg='#0f3460', fg='white',
                                       font=('Segoe UI', 9), padx=8, pady=3)
        self.export_csv_btn.pack(side=tk.LEFT, padx=2)

        # Konfigurace gridu
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def on_opacity_change(self, value):
        """Callback pro změnu opacity"""
        self.opacity_label.config(text=f"{int(float(value) * 100)}%")

    def on_width_change(self, value):
        """Callback pro změnu šířky"""
        self.width_label.config(text=f"{float(value):.1f}")

    def on_contrast_change(self, value):
        """Callback pro změnu kontrastu"""
        self.contrast_label.config(text=f"{float(value):.1f}x")

    def on_edge_change(self, value):
        """Callback pro změnu edge enhancement"""
        self.edge_label.config(text=f"{int(float(value) * 100)}%")

    def on_preset_change(self, event):
        """Callback pri zmene presetu"""
        preset_name = self.preset_var.get()
        # Najdi preset podle jmena
        for preset_id, preset in PRESETS.items():
            if preset.name == preset_name:
                self.current_preset = preset
                info = f"{preset.description} ({preset.difficulty})"
                self.preset_info_label.config(text=info[:50] + "..." if len(info) > 50 else info)
                break

    def apply_preset(self):
        """Aplikuje vybrany preset do nastaveni"""
        if self.current_preset is None:
            # Najdi preset podle jmena
            preset_name = self.preset_var.get()
            for preset_id, preset in PRESETS.items():
                if preset.name == preset_name:
                    self.current_preset = preset
                    break

        if self.current_preset is None:
            return

        preset = self.current_preset

        # Nastav hodnoty podle presetu
        self.num_points_var.set(preset.num_points)
        self.num_lines_var.set(preset.num_lines)
        self.speed_var.set(preset.speed_mode)
        self.opacity_var.set(preset.opacity)
        self.line_width_var.set(preset.line_width)
        self.contrast_var.set(preset.contrast_factor)
        self.edge_var.set(preset.edge_enhancement)
        self.line_weight_var.set(preset.line_weight)
        self.min_distance_var.set(preset.min_distance)

        # Aktualizuj labely
        self.opacity_label.config(text=f"{int(preset.opacity * 100)}%")
        self.width_label.config(text=f"{preset.line_width:.1f}")
        self.contrast_label.config(text=f"{preset.contrast_factor:.1f}x")
        self.edge_label.config(text=f"{int(preset.edge_enhancement * 100)}%")

        # Aktualizuj odhad
        self.update_estimate_label()

        self.status_label.config(text=f"Preset '{preset.name}' aplikovan")

    def analyze_image(self):
        """Analyzuje obrazek a zobrazi hodnoceni"""
        if not self.image_path:
            messagebox.showwarning("Upozorneni", "Nejdrive vyberte obrazek!")
            return

        try:
            # Validace
            validation = self.validator.validate(self.image_path)

            if not validation['valid']:
                error_msg = "\n".join(validation['errors'])
                messagebox.showerror("Chyba validace", f"Obrazek neni vhodny:\n\n{error_msg}")
                return

            # Analyza vhodnosti pro string art
            generator = StringArtGenerator()
            analysis = generator.analyze_image_suitability(self.image_path)

            # Zobraz vysledky
            quality_text = f"Kvalita: {analysis['quality_rating']} ({analysis['overall_score']}/100)"
            self.quality_label.config(text=quality_text)

            # Detailni report
            msg = f"""ANALYZA OBRAZKU

Celkove hodnoceni: {analysis['quality_rating']}
Skore: {analysis['overall_score']}/100

Detaily:
- Kontrast: {analysis['contrast_score']}/100
- Detail: {analysis['detail_score']}/100
- Velikost: {analysis['size_score']}/100
- Rozliseni: {analysis['image_size'][0]}x{analysis['image_size'][1]}px

Doporuceny kontrast: {analysis['recommended_contrast_factor']:.1f}x

Vhodny pro string art: {'ANO' if analysis['suitable_for_stringart'] else 'NE'}
"""

            if analysis['recommendations']:
                msg += "\nDoporuceni:\n"
                for rec in analysis['recommendations']:
                    msg += f"- {rec}\n"

            if validation['warnings']:
                msg += "\nUpozorneni:\n"
                for warn in validation['warnings']:
                    msg += f"- {warn}\n"

            messagebox.showinfo("Analyza obrazku", msg)

            # Automaticky nastav doporuceny kontrast
            self.contrast_var.set(analysis['recommended_contrast_factor'])
            self.contrast_label.config(text=f"{analysis['recommended_contrast_factor']:.1f}x")

        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba pri analyze:\n{str(e)}")

    def show_estimate(self):
        """Zobrazi odhad materialu a casu"""
        num_lines = self.num_lines_var.get()

        try:
            estimate = self.estimator.get_full_estimate(num_lines)

            msg = f"""ODHAD MATERIALU A CASU

Projekt: {num_lines:,} linii

MATERIAL:
- Delka nite: {estimate['material']['total_length_m']:.1f} m
- Doporuceno civek: {estimate['material']['recommended_spools']}
- Odhadovana cena: {estimate['material']['estimated_cost_czk']:.0f} CZK

CAS (pro zacatecnika):
- Celkovy cas: {estimate['time']['total_hours']:.1f} hodin
- Pocet sezeni: {estimate['time']['total_sessions']}
- Doporuceny pocet dni: {estimate['time']['recommended_days']}

TIPY:
"""
            for tip in estimate['time']['tips'][:3]:
                msg += f"- {tip}\n"

            messagebox.showinfo("Odhad materialu a casu", msg)

        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba pri vypoctu:\n{str(e)}")

    def update_estimate_label(self):
        """Aktualizuje label s rychlym odhadem"""
        num_lines = self.num_lines_var.get()
        est = estimate_for_product_page(num_lines)
        text = f"~{est['assembly_time']} | {est['difficulty']} | {est['thread_needed']}"
        self.estimate_label.config(text=text)

    def load_image(self):
        """Načte obrázek"""
        file_path = filedialog.askopenfilename(
            title="Vyberte obrázek",
            filetypes=[
                ("Obrázky", "*.png *.PNG *.jpg *.JPG *.jpeg *.JPEG *.bmp *.BMP *.gif *.GIF"),
                ("Všechny soubory", "*.*")
            ]
        )

        if file_path:
            self.image_path = file_path
            self.image_path_label.config(text=os.path.basename(file_path))
            self.status_label.config(text=f"Načten: {os.path.basename(file_path)}")
            self.open_image_editor()

    def open_image_editor(self):
        """Otevře editor pro úpravu obrázku"""
        def on_editor_confirm(edited_img):
            self.edited_image = edited_img
            self.generate_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Obrázek upraven - připraven ke generování")

            # Zobraz náhled vstupního obrázku
            preview = edited_img.copy()
            preview = preview.resize((500, 500), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(preview)
            self.preview_canvas.delete('all')
            self.preview_canvas.create_image(250, 250, image=self.preview_photo)

        ImageEditor(self.root, self.image_path, on_editor_confirm)

    def generate_art(self):
        """Spustí generování string art v novém vlákně"""
        if not self.image_path or not self.edited_image:
            messagebox.showerror("Chyba", "Nejdřív vyberte a upravte obrázek!")
            return

        if self.is_generating:
            return

        self.is_generating = True
        self.generate_btn.config(state=tk.DISABLED, text="Generuji...")
        self.progress['value'] = 0

        # Spusť v novém vlákně
        thread = threading.Thread(target=self._generate_in_thread)
        thread.daemon = True
        thread.start()

    def _generate_in_thread(self):
        """Generování v odděleném vlákně"""
        try:
            # Ulož upravený obrázek do temp souboru
            temp_path = tempfile.mktemp(suffix='.png')
            self.edited_image.save(temp_path)

            # Inicializuj generátor
            num_points = self.num_points_var.get()
            shape = self.shape_var.get()
            self.generator = StringArtGenerator(num_points=num_points, image_size=500, shape=shape)

            self.root.after(0, lambda: self.status_label.config(text="Generuji string art..."))

            # Progress callback
            def progress_callback(lines, percent):
                self.root.after(0, lambda p=percent: self.progress.configure(value=p))
                self.root.after(0, lambda l=len(lines): self.status_label.config(
                    text=f"Generuji... {l} linií ({int(percent)}%)"))

            # Generuj s paralelni verzi a edge enhancement
            num_lines = self.num_lines_var.get()
            line_weight = self.line_weight_var.get()
            speed = self.speed_var.get()
            contrast = self.contrast_var.get()
            edge_enhancement = self.edge_var.get()

            self.generated_lines = self.generator.generate_string_art_parallel(
                temp_path,
                num_lines=num_lines,
                line_weight=line_weight,
                min_distance=self.min_distance_var.get(),
                speed_mode=speed,
                progress_callback=progress_callback,
                contrast_factor=contrast,
                edge_enhancement=edge_enhancement
            )

            # Smaž temp soubor
            if os.path.exists(temp_path):
                os.remove(temp_path)

            # Aktualizuj UI
            self.root.after(0, self._on_generation_complete)

        except Exception as e:
            self.root.after(0, lambda: self._on_generation_error(str(e)))

    def _on_generation_complete(self):
        """Callback po dokončení generování"""
        self.is_generating = False
        self.progress['value'] = 100
        self.status_label.config(text=f"Hotovo! {len(self.generated_lines)} linií")
        self.generate_btn.config(state=tk.NORMAL, text="GENEROVAT STRING ART")

        # Aktivuj export tlačítka
        self.export_png_btn.config(state=tk.NORMAL)
        self.export_svg_btn.config(state=tk.NORMAL)
        self.export_txt_btn.config(state=tk.NORMAL)
        self.export_json_btn.config(state=tk.NORMAL)
        self.export_csv_btn.config(state=tk.NORMAL)
        self.export_html_btn.config(state=tk.NORMAL)
        self.export_pdf_btn.config(state=tk.NORMAL)
        self.export_diagram_btn.config(state=tk.NORMAL)
        self.refresh_btn.config(state=tk.NORMAL)

        # Zobraz náhled
        self.refresh_preview()

        messagebox.showinfo("Hotovo",
                           f"String art byl úspěšně vygenerován!\n\n"
                           f"Počet linií: {len(self.generated_lines)}\n"
                           f"Počet bodů: {self.generator.num_points}")

    def _on_generation_error(self, error_msg):
        """Callback při chybě"""
        self.is_generating = False
        self.progress['value'] = 0
        self.generate_btn.config(state=tk.NORMAL, text="GENEROVAT STRING ART")
        self.status_label.config(text="Chyba při generování")
        messagebox.showerror("Chyba", f"Nastala chyba při generování:\n{error_msg}")

    def refresh_preview(self):
        """Obnoví náhled s aktuálními parametry vizualizace"""
        if not self.generated_lines or not self.generator:
            return

        self.status_label.config(text="Renderuji náhled...")
        self.root.update()

        try:
            # Renderuj s aktuálními parametry
            img = self.generator.render_to_image(
                self.generated_lines,
                size=500,
                line_width=self.line_width_var.get(),
                opacity=self.opacity_var.get(),
                background='white',
                line_color='black',
                show_pins=self.show_pins_var.get()
            )

            self.preview_photo = ImageTk.PhotoImage(img)
            self.preview_canvas.delete('all')
            self.preview_canvas.create_image(250, 250, image=self.preview_photo)

            self.status_label.config(text=f"Hotovo! {len(self.generated_lines)} linií")

        except Exception as e:
            self.status_label.config(text=f"Chyba renderování: {str(e)}")

    def export_png(self):
        """Export do PNG"""
        if not self.generated_lines:
            return

        output_path = filedialog.asksaveasfilename(
            title="Uložit jako PNG",
            defaultextension=".png",
            filetypes=[("PNG soubory", "*.png"), ("Všechny soubory", "*.*")]
        )

        if output_path:
            try:
                self.generator.export_high_quality_image(
                    self.generated_lines,
                    output_path,
                    size=1500,  # Vysoké rozlišení
                    line_width=self.line_width_var.get(),
                    opacity=self.opacity_var.get()
                )
                messagebox.showinfo("Hotovo", f"PNG exportováno do:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba při exportu:\n{str(e)}")

    def export_svg(self):
        """Export do SVG"""
        if not self.generated_lines:
            return

        output_path = filedialog.asksaveasfilename(
            title="Uložit jako SVG",
            defaultextension=".svg",
            filetypes=[("SVG soubory", "*.svg"), ("Všechny soubory", "*.*")]
        )

        if output_path:
            try:
                self.generator.export_to_svg(
                    self.generated_lines,
                    output_path,
                    line_width=self.line_width_var.get(),
                    opacity=self.opacity_var.get()
                )
                messagebox.showinfo("Hotovo", f"SVG exportováno do:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba při exportu:\n{str(e)}")

    def export_txt(self):
        """Export instrukcí do TXT"""
        if not self.generated_lines:
            return

        output_path = filedialog.asksaveasfilename(
            title="Uložit instrukce",
            defaultextension=".txt",
            filetypes=[("Textové soubory", "*.txt"), ("Všechny soubory", "*.*")]
        )

        if output_path:
            try:
                self.generator.export_instructions(self.generated_lines, output_path)
                messagebox.showinfo("Hotovo", f"Instrukce exportovány do:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba při exportu:\n{str(e)}")

    def export_json(self):
        """Export do JSON"""
        if not self.generated_lines:
            return

        output_path = filedialog.asksaveasfilename(
            title="Uložit jako JSON",
            defaultextension=".json",
            filetypes=[("JSON soubory", "*.json"), ("Všechny soubory", "*.*")]
        )

        if output_path:
            try:
                self.generator.export_to_json(self.generated_lines, output_path)
                messagebox.showinfo("Hotovo", f"JSON exportováno do:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba při exportu:\n{str(e)}")

    def export_csv(self):
        """Export do CSV"""
        if not self.generated_lines:
            return

        output_path = filedialog.asksaveasfilename(
            title="Uložit jako CSV",
            defaultextension=".csv",
            filetypes=[("CSV soubory", "*.csv"), ("Všechny soubory", "*.*")]
        )

        if output_path:
            try:
                self.generator.export_to_csv(self.generated_lines, output_path)
                messagebox.showinfo("Hotovo", f"CSV exportováno do:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba při exportu:\n{str(e)}")

    def export_html_tutorial(self):
        """Export interaktivního HTML tutorialu"""
        if not self.generated_lines:
            return

        output_path = filedialog.asksaveasfilename(
            title="Uložit HTML Tutorial",
            defaultextension=".html",
            filetypes=[("HTML soubory", "*.html"), ("Všechny soubory", "*.*")]
        )

        if output_path:
            try:
                self.status_label.config(text="Generuji HTML tutorial...")
                self.root.update()
                self.generator.export_html_tutorial(self.generated_lines, output_path)
                self.status_label.config(text=f"Hotovo! {len(self.generated_lines)} linií")
                messagebox.showinfo("Hotovo",
                    f"HTML tutorial exportován do:\n{output_path}\n\n"
                    "Otevři soubor v prohlížeči pro interaktivní průvodce!")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba při exportu:\n{str(e)}")

    def export_pdf_tutorial(self):
        """Export PDF tutorialu - KOMPLETNI verze s sablonou hrebicku a IRL navodem"""
        if not self.generated_lines:
            return

        output_path = filedialog.asksaveasfilename(
            title="Uložit PDF Tutorial",
            defaultextension=".pdf",
            filetypes=[("PDF soubory", "*.pdf"), ("Všechny soubory", "*.*")]
        )

        if output_path:
            try:
                self.status_label.config(text="Generuji kompletní PDF tutorial...")
                self.root.update()
                # Pouzij kompletni verzi s sablonou hrebicku a IRL navodem
                self.generator.export_pdf_tutorial_complete(
                    self.generated_lines,
                    output_path,
                    frame_size_cm=40  # Defaultni velikost ramu 40x40cm
                )
                self.status_label.config(text=f"Hotovo! {len(self.generated_lines)} linií")
                messagebox.showinfo("Hotovo",
                    f"Kompletní PDF tutorial exportován do:\n{output_path}\n\n"
                    "Obsahuje:\n"
                    "- Šablonu pro rozmístění hřebíčků\n"
                    "- Seznam potřebného materiálu\n"
                    "- Návod na přípravu desky\n"
                    "- Instrukce pro napínání nitě\n"
                    "- Krokový návod s checkboxy")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba při exportu:\n{str(e)}")

    def export_pin_diagram(self):
        """Export SVG diagramu s očíslovanými piny"""
        if not self.generator:
            return

        output_path = filedialog.asksaveasfilename(
            title="Uložit Pin Diagram",
            defaultextension=".svg",
            filetypes=[("SVG soubory", "*.svg"), ("Všechny soubory", "*.*")]
        )

        if output_path:
            try:
                self.generator.export_pin_diagram_svg(output_path)
                messagebox.showinfo("Hotovo",
                    f"Pin diagram exportován do:\n{output_path}\n\n"
                    "Diagram ukazuje rozložení a čísla všech pinů!")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba při exportu:\n{str(e)}")


def main():
    root = tk.Tk()
    app = StringArtGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
