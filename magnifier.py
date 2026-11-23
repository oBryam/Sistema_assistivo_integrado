"""
Módulo da Lupa Dinâmica (Lente Virtual) de Área Ampla.
Eixo 2: Lente virtual flutuante com área de visualização ampliada,
acompanhando o cursor em tempo real, independente de outros módulos.

Tamanhos disponíveis:
- Média: 520 x 380 px
- Grande (Padrão): 700 x 500 px
- Panorâmica: 900 x 560 px
"""

import ctypes
import tkinter as tk
from typing import Callable, Optional
import mss
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageTk
import pyautogui
from sound_effects import sounds

# Constantes da API do Windows
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
WDA_EXCLUDEFROMCAPTURE = 0x00000011


class DynamicMagnifier:
    PRESETS = {
        "Média": (520, 380),
        "Grande": (700, 500),
        "Panorâmica": (900, 560)
    }

    def __init__(self, root: tk.Tk, on_update_callback: Optional[Callable] = None):
        self.root = root
        self.on_update_callback = on_update_callback

        self.is_active = False
        self.scale = 2.0  # Faixa: 1.5x a 6.0x
        self.current_preset = "Grande"
        self.win_width, self.win_height = self.PRESETS[self.current_preset]

        self.window: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.header_label: Optional[tk.Label] = None
        self.photo_image: Optional[ImageTk.PhotoImage] = None

        self.sct = mss.MSS()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self._update_job = None

    def toggle(self):
        """Alterna a lupa entre ativa e desativada (Ctrl + Alt + L)."""
        if self.is_active:
            self.stop()
        else:
            self.start()

    def start(self):
        """Ativa a lupa virtual."""
        if self.is_active:
            return

        self.is_active = True
        sounds.lens_on()
        self._create_window()
        self._schedule_update()
        if self.on_update_callback:
            self.on_update_callback()

    def stop(self):
        """Desativa a lupa virtual."""
        if not self.is_active:
            return

        self.is_active = False
        sounds.lens_off()
        if self._update_job:
            self.root.after_cancel(self._update_job)
            self._update_job = None

        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None
            self.canvas = None
            self.header_label = None

        if self.on_update_callback:
            self.on_update_callback()

    def set_size_preset(self, preset_name: str):
        """Altera a dimensão da área ampliada."""
        if preset_name in self.PRESETS:
            self.current_preset = preset_name
            self.win_width, self.win_height = self.PRESETS[preset_name]
            if self.window and self.canvas:
                self.canvas_height = self.win_height - 28
                self.canvas.config(width=self.win_width, height=self.canvas_height)
                self._update_header()

    def _create_window(self):
        """Cria e configura a janela flutuante da lente virtual."""
        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#FFE600", cursor="crosshair")

        container = tk.Frame(self.window, bg="#FFE600", bd=3)
        container.pack(fill=tk.BOTH, expand=True)

        # Barra de status no topo da lente
        self.header_label = tk.Label(
            container,
            text=self.get_status_text(),
            font=("Segoe UI", 11, "bold"),
            bg="#000000",
            fg="#FFE600",
            padx=6,
            pady=3,
            anchor="w"
        )
        self.header_label.pack(fill=tk.X)

        self.canvas_height = self.win_height - 28
        self.canvas = tk.Canvas(
            container,
            width=self.win_width,
            height=self.canvas_height,
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Roda de rolagem do mouse para alterar zoom instantaneamente
        self.window.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        self.window.update_idletasks()
        self._apply_windows_styles()

    def _apply_windows_styles(self):
        """Garante que a lente não capture a si mesma e não roube foco da tarefa do estudante."""
        if not self.window:
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.window.winfo_id())
            if not hwnd:
                hwnd = self.window.winfo_id()

            # Evita efeito espelho infinito
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

            # Evita roubo de foco do teclado/mouse
            cur_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd,
                GWL_EXSTYLE,
                cur_style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
            )
        except Exception as e:
            print(f"[WinStyle Error]: {e}")

    def _on_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        """Aumenta a escala em +0.5x até 6.0x."""
        if self.scale < 6.0:
            self.scale = round(min(6.0, self.scale + 0.5), 2)
            sounds.zoom_in()
            self._update_header()
            if self.on_update_callback:
                self.on_update_callback()

    def zoom_out(self):
        """Diminui a escala em -0.5x até 1.5x."""
        if self.scale > 1.5:
            self.scale = round(max(1.5, self.scale - 0.5), 2)
            sounds.zoom_out()
            self._update_header()
            if self.on_update_callback:
                self.on_update_callback()

    def set_scale(self, new_scale: float):
        self.scale = max(1.5, min(6.0, round(float(new_scale), 2)))
        self._update_header()
        if self.on_update_callback:
            self.on_update_callback()

    def get_status_text(self) -> str:
        return f"🔍 LUPA: {self.scale:.1f}x  |  📐 TAMANHO: {self.current_preset} ({self.win_width}x{self.win_height})  |  Ctrl+- / Ctrl++"

    def _update_header(self):
        if self.header_label:
            try:
                self.header_label.config(text=self.get_status_text())
            except Exception:
                pass

    def _schedule_update(self):
        if not self.is_active or not self.window:
            return
        self._capture_and_render()
        self._update_job = self.root.after(33, self._schedule_update)

    def _capture_and_render(self):
        try:
            mx, my = pyautogui.position()

            # Posicionamento inteligente para acomodar a lente grande sem cobrir o cursor
            offset_x = 35
            offset_y = 35
            win_x = mx + offset_x
            win_y = my + offset_y

            # Se ultrapassar a borda direita da tela, reposiciona à esquerda do cursor
            if win_x + self.win_width > self.screen_width:
                win_x = max(10, mx - self.win_width - offset_x)
            # Se ultrapassar a borda inferior, reposiciona acima do cursor
            if win_y + self.win_height > self.screen_height:
                win_y = max(10, my - self.win_height - offset_y)

            self.window.geometry(f"{self.win_width}x{self.win_height}+{win_x}+{win_y}")

            # Área do desktop a capturar
            cap_w = int(self.win_width / self.scale)
            cap_h = int(self.canvas_height / self.scale)

            left = mx - (cap_w // 2)
            top = my - (cap_h // 2)

            left = max(0, min(self.screen_width - cap_w, left))
            top = max(0, min(self.screen_height - cap_h, top))

            bbox = {
                "left": left,
                "top": top,
                "width": cap_w,
                "height": cap_h
            }

            sct_img = self.sct.grab(bbox)
            raw_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # Redimensionamento bilinear nítido
            scaled_img = raw_img.resize(
                (self.win_width, self.canvas_height),
                Image.Resampling.BILINEAR
            )

            # Mira central destacada
            draw = ImageDraw.Draw(scaled_img)
            cx, cy = self.win_width // 2, self.canvas_height // 2
            draw.line([(cx - 12, cy), (cx + 12, cy)], fill=(255, 0, 0), width=2)
            draw.line([(cx, cy - 12), (cx, cy + 12)], fill=(255, 0, 0), width=2)

            self.photo_image = ImageTk.PhotoImage(scaled_img)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo_image)

        except Exception:
            pass
