# -*- coding: utf-8 -*-
"""
Image Editor - Interaktivni editor pro crop, zoom a posun obrazku
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import math


class ImageEditor:
    """Interaktivni editor pro upravu obrazku pred generovanim string art"""

    def __init__(self, parent, image_path, callback):
        """
        Args:
            parent: Rodicovsky widget
            image_path: Cesta k obrazku
            callback: Funkce volana po potvrzeni (dostane PIL Image)
        """
        self.parent = parent
        self.image_path = image_path
        self.callback = callback

        # Nacti obrazek
        self.original_image = Image.open(image_path)
        if self.original_image.mode != 'RGB':
            self.original_image = self.original_image.convert('RGB')

        # Canvas a vystupni rozměry
        self.canvas_size = 600
        self.output_size = 500  # Finalni velikost pro string art

        # Stav editoru - ZJEDNODUŠENÝ
        self.scale = 1.0  # Měřítko zobrazení
        self.pan_x = 0  # Posun v pixelech canvas
        self.pan_y = 0
        self.rotation = 0

        # Vytvor okno
        self.window = tk.Toplevel(parent)
        self.window.title("Úprava obrázku - Crop & Zoom")
        self.window.geometry("850x750")

        self.setup_ui()
        # Auto-fit obrazku do kruhu pri otevreni
        self.auto_fit()
        self.update_preview()

    def auto_fit(self):
        """Automaticky nastav zoom aby obrazek vyplnil kruh"""
        w, h = self.original_image.size
        # Vypocitej scale aby kratsi strana vyplnila canvas
        min_dim = min(w, h)
        self.scale = self.canvas_size / min_dim
        self.scale_var.set(self.scale)

    def setup_ui(self):
        """Vytvori uzivatelske rozhrani"""

        # Hlavni frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instrukce
        instructions = ttk.Label(
            main_frame,
            text="Přiblížte oblast pro string art - myší táhněte, kolečkem zoomujte",
            font=('Arial', 11, 'bold'),
            foreground='#2C3E50'
        )
        instructions.pack(pady=5)

        # Canvas pro nahled
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(pady=10)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg='#ECF0F1',
            highlightthickness=2,
            highlightbackground='#34495E',
            cursor='hand2'
        )
        self.canvas.pack()

        # Bind udalosti mysi
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)
        self.canvas.bind('<Button-4>', self.on_mousewheel)  # Linux
        self.canvas.bind('<Button-5>', self.on_mousewheel)
        self.canvas.bind('<ButtonPress-1>', self.on_mouse_press)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)

        # Bind klavesy
        self.window.bind('<Left>', lambda e: self.rotate(-5))
        self.window.bind('<Right>', lambda e: self.rotate(5))
        self.window.bind('<Up>', lambda e: self.adjust_scale(0.1))
        self.window.bind('<Down>', lambda e: self.adjust_scale(-0.1))

        # Ovladaci panel
        controls_frame = ttk.LabelFrame(main_frame, text="Ovládání", padding="15")
        controls_frame.pack(fill=tk.X, pady=10)

        # Scale slider
        scale_frame = ttk.Frame(controls_frame)
        scale_frame.pack(fill=tk.X, pady=5)

        ttk.Label(scale_frame, text="Přiblížení:", width=12).pack(side=tk.LEFT)
        self.scale_var = tk.DoubleVar(value=1.0)
        scale_slider = ttk.Scale(
            scale_frame,
            from_=0.3,
            to=5.0,
            variable=self.scale_var,
            orient=tk.HORIZONTAL,
            length=400,
            command=self.on_scale_slider
        )
        scale_slider.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.scale_label = ttk.Label(scale_frame, text="100%", width=8)
        self.scale_label.pack(side=tk.LEFT)

        # Rotace slider
        rotation_frame = ttk.Frame(controls_frame)
        rotation_frame.pack(fill=tk.X, pady=5)

        ttk.Label(rotation_frame, text="Otočení:", width=12).pack(side=tk.LEFT)
        self.rotation_var = tk.DoubleVar(value=0)
        rotation_slider = ttk.Scale(
            rotation_frame,
            from_=-180,
            to=180,
            variable=self.rotation_var,
            orient=tk.HORIZONTAL,
            length=400,
            command=self.on_rotation_slider
        )
        rotation_slider.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.rotation_label = ttk.Label(rotation_frame, text="0°", width=8)
        self.rotation_label.pack(side=tk.LEFT)

        # Tlacitka
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(pady=15)

        ttk.Button(buttons_frame, text="🔄 Reset", command=self.reset, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(buttons_frame, text="➕ Přiblížit", command=lambda: self.adjust_scale(0.3), width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(buttons_frame, text="➖ Oddálit", command=lambda: self.adjust_scale(-0.3), width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(buttons_frame, text="↶ -90°", command=lambda: self.rotate(-90), width=10).pack(side=tk.LEFT, padx=3)
        ttk.Button(buttons_frame, text="↷ +90°", command=lambda: self.rotate(90), width=10).pack(side=tk.LEFT, padx=3)

        # Akce
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(pady=15)

        confirm_btn = tk.Button(
            action_frame,
            text="✓ POTVRDIT A GENEROVAT",
            command=self.confirm,
            bg='#27AE60',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            cursor='hand2'
        )
        confirm_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = tk.Button(
            action_frame,
            text="✗ ZRUŠIT",
            command=self.cancel,
            bg='#E74C3C',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

        # Info
        info_text = "💡 Myš: táhněte pro posun, kolečko pro zoom  |  Klávesy: šipky ← → otočení, ↑ ↓ zoom"
        self.info_label = ttk.Label(main_frame, text=info_text, font=('Arial', 9), foreground='#7F8C8D')
        self.info_label.pack(pady=5)

    def on_mousewheel(self, event):
        """Zoom koleckem mysi"""
        if event.num == 4 or event.delta > 0:
            self.adjust_scale(0.15)
        elif event.num == 5 or event.delta < 0:
            self.adjust_scale(-0.15)

    def on_mouse_press(self, event):
        """Zacatek tazeni"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_mouse_drag(self, event):
        """Posun obrazku tazenim - OPRAVENO"""
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        # Primy posun v pixelech canvas
        self.pan_x += dx
        self.pan_y += dy

        self.drag_start_x = event.x
        self.drag_start_y = event.y

        self.update_preview()

    def on_scale_slider(self, value):
        """Zmena scale sliderem"""
        self.scale = float(value)
        self.scale_label.config(text=f"{int(self.scale * 100)}%")
        self.update_preview()

    def on_rotation_slider(self, value):
        """Zmena rotace sliderem"""
        self.rotation = float(value)
        self.rotation_label.config(text=f"{int(self.rotation)}°")
        self.update_preview()

    def adjust_scale(self, delta):
        """Zmena scale"""
        self.scale = max(0.3, min(5.0, self.scale + delta))
        self.scale_var.set(self.scale)
        self.scale_label.config(text=f"{int(self.scale * 100)}%")
        self.update_preview()

    def rotate(self, angle):
        """Rotace obrazku"""
        self.rotation = (self.rotation + angle) % 360
        if self.rotation > 180:
            self.rotation -= 360
        self.rotation_var.set(self.rotation)
        self.rotation_label.config(text=f"{int(self.rotation)}°")
        self.update_preview()

    def reset(self):
        """Reset"""
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.rotation = 0
        self.scale_var.set(1.0)
        self.rotation_var.set(0)
        self.scale_label.config(text="100%")
        self.rotation_label.config(text="0°")
        self.auto_fit()
        self.update_preview()

    def update_preview(self):
        """Aktualizuj nahled - ZJEDNODUŠENO"""
        # Aplikuj rotaci
        if self.rotation != 0:
            img = self.original_image.rotate(-self.rotation, expand=True, resample=Image.BICUBIC)
        else:
            img = self.original_image

        # Aplikuj scale
        w, h = img.size
        new_w = int(w * self.scale)
        new_h = int(h * self.scale)
        if new_w > 0 and new_h > 0:
            img_scaled = img.resize((new_w, new_h), Image.LANCZOS)
        else:
            img_scaled = img

        # Vytvor canvas
        canvas_img = Image.new('RGB', (self.canvas_size, self.canvas_size), '#ECF0F1')

        # Vypocitej pozici paste - stred canvas + pan
        paste_x = (self.canvas_size - new_w) // 2 + int(self.pan_x)
        paste_y = (self.canvas_size - new_h) // 2 + int(self.pan_y)

        # Paste obrazek
        canvas_img.paste(img_scaled, (paste_x, paste_y))

        # Nakresli cerveny kruh
        draw = ImageDraw.Draw(canvas_img)
        margin = 3
        draw.ellipse(
            [margin, margin, self.canvas_size - margin, self.canvas_size - margin],
            outline='#E74C3C',
            width=4
        )

        # Zobraz
        self.photo = ImageTk.PhotoImage(canvas_img)
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

    def get_cropped_image(self):
        """Vrat vyrezany obrazek - OPRAVENO"""
        # Aplikuj rotaci
        if self.rotation != 0:
            img = self.original_image.rotate(-self.rotation, expand=True, resample=Image.BICUBIC)
        else:
            img = self.original_image

        # Aplikuj scale
        w, h = img.size
        new_w = int(w * self.scale)
        new_h = int(h * self.scale)
        img_scaled = img.resize((new_w, new_h), Image.LANCZOS)

        # Vytvor vystupni obrazek
        result = Image.new('RGB', (self.output_size, self.output_size), 'white')

        # Vypocitej pozici paste - proporcionalne k canvas
        scale_ratio = self.output_size / self.canvas_size
        paste_x = int((int((self.canvas_size - new_w) // 2 + self.pan_x)) * scale_ratio)
        paste_y = int((int((self.canvas_size - new_h) // 2 + self.pan_y)) * scale_ratio)

        # Resize obrazek na vystupni velikost
        scaled_w = int(new_w * scale_ratio)
        scaled_h = int(new_h * scale_ratio)
        img_final = img_scaled.resize((scaled_w, scaled_h), Image.LANCZOS)

        # Paste
        result.paste(img_final, (paste_x, paste_y))

        return result

    def confirm(self):
        """Potvrzeni"""
        cropped = self.get_cropped_image()
        self.window.destroy()
        self.callback(cropped)

    def cancel(self):
        """Zruseni"""
        self.window.destroy()
