"""
Módulo da Lupa Dinâmica (Lente Virtual) - Versão Otimizada de Alta Performance.
Eixo 2: Acessibilidade Visual e Ampliação Ergonômica.
Correções críticas:
- Elimina vazamento de memória Tcl (reutiliza PhotoImage.paste em vez de criar novas imagens)
- Elimina recriação contínua de itens no Canvas (zero Canvas.delete("all"))
- Reposicionamento via SetWindowPos da API do Windows (zero reflow de geometria no Tkinter)
- Taxa de atualização estável (40ms = 25 FPS) sem sobrecarregar a fila de mensagens do sistema
"""

import ctypes
import tkinter as tk
from typing import Callable, Optional
import mss
import numpy as np
from PIL import Image, ImageDraw, ImageTk
import pyautogui
from config_manager import cfg
from sound_effects import sounds

pyautogui.FAILSAFE = False

# Constantes da API Win32
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
WDA_EXCLUDEFROMCAPTURE = 0x00000011

SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010


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
        self.scale = float(cfg.get("magnifier_scale", 2.0))
        self.current_preset = cfg.get("magnifier_preset", "Grande")
        self.is_docked = bool(cfg.get("magnifier_docked", False))
        self.dock_position = cfg.get("magnifier_dock_position", "Topo")
        self.reading_guide = bool(cfg.get("reading_guide", True))
        self.smooth_movement = bool(cfg.get("smooth_movement", True))

        self.win_width, self.win_height = self.PRESETS.get(self.current_preset, (700, 500))

        self.window: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.header_label: Optional[tk.Label] = None

        # Reutilização única de objeto de imagem e item do canvas
        self.photo_image: Optional[ImageTk.PhotoImage] = None
        self.canvas_image_id = None
        self.hwnd = None

        self.sct = mss.MSS()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.current_win_x = 0
        self.current_win_y = 0
        self.last_pos_x = -9999
        self.last_pos_y = -9999

        self._update_job = None
        self._is_paused_for_snipping = False

    def toggle(self):
        if self.is_active:
            self.stop()
        else:
            self.start()

    def start(self):
        if self.is_active:
            return

        self.is_active = True
        sounds.lens_on()
        self._create_window()
        self._schedule_update()
        if self.on_update_callback:
            self.on_update_callback()

    def stop(self):
        if not self.is_active:
            return

        self.is_active = False
        sounds.lens_off()

        if self._update_job:
            try:
                self.root.after_cancel(self._update_job)
            except Exception:
                pass
            self._update_job = None

        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None
            self.canvas = None
            self.header_label = None
            self.photo_image = None
            self.canvas_image_id = None
            self.hwnd = None

        if self.on_update_callback:
            self.on_update_callback()

    def pause_capture(self):
        self._is_paused_for_snipping = True

    def resume_capture(self):
        self._is_paused_for_snipping = False

    def toggle_docked(self):
        self.is_docked = not self.is_docked
        cfg.set("magnifier_docked", self.is_docked)
        if self.is_active and self.window:
            self.stop()
            self.start()
        elif self.on_update_callback:
            self.on_update_callback()

    def toggle_reading_guide(self):
        self.reading_guide = not self.reading_guide
        cfg.set("reading_guide", self.reading_guide)
        if self.on_update_callback:
            self.on_update_callback()

    def toggle_smooth_movement(self):
        self.smooth_movement = not self.smooth_movement
        cfg.set("smooth_movement", self.smooth_movement)
        if self.on_update_callback:
            self.on_update_callback()

    def set_size_preset(self, preset_name: str):
        if preset_name in self.PRESETS:
            self.current_preset = preset_name
            cfg.set("magnifier_preset", preset_name)
            self.win_width, self.win_height = self.PRESETS[preset_name]
            if self.is_active and self.window:
                self.stop()
                self.start()

    def _create_window(self):
        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#FFE600", cursor="crosshair")

        container = tk.Frame(self.window, bg="#FFE600", bd=2)
        container.pack(fill=tk.BOTH, expand=True)

        self.header_label = tk.Label(
            container,
            text=self.get_status_text(),
            font=("Segoe UI", 9, "bold"),
            bg="#000000",
            fg="#FFE600",
            padx=4,
            pady=2,
            anchor="w"
        )
        self.header_label.pack(fill=tk.X)

        if self.is_docked:
            dock_h = 280
            self.canvas_width = max(100, self.screen_width - 4)
            self.canvas_height = max(100, dock_h - 26)
            dock_y = 0 if self.dock_position == "Topo" else (self.screen_height - dock_h)
            self.window.geometry(f"{self.screen_width}x{dock_h}+0+{dock_y}")
        else:
            self.canvas_width = self.win_width
            self.canvas_height = max(100, self.win_height - 26)
            self.window.geometry(f"{self.win_width}x{self.win_height}+100+100")

        self.canvas = tk.Canvas(
            container,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Imagem base inicial (reutilizada perpetuamente via paste)
        blank = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        self.photo_image = ImageTk.PhotoImage(blank)
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.photo_image)

        self.window.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        self.window.update_idletasks()
        self._apply_windows_styles()

        try:
            mx, my = pyautogui.position()
            self.current_win_x, self.current_win_y = mx, my
        except Exception:
            self.current_win_x, self.current_win_y = 100, 100

    def _apply_windows_styles(self):
        if not self.window:
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.window.winfo_id())
            if not hwnd:
                hwnd = self.window.winfo_id()
            self.hwnd = hwnd

            ctypes.windll.user32.SetWindowDisplayAffinity(self.hwnd, WDA_EXCLUDEFROMCAPTURE)

            cur_style = ctypes.windll.user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                self.hwnd,
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
        if self.scale < 6.0:
            self.scale = round(min(6.0, self.scale + 0.5), 2)
            cfg.set("magnifier_scale", self.scale)
            sounds.zoom_in()
            self._update_header()
            if self.on_update_callback:
                self.on_update_callback()

    def zoom_out(self):
        if self.scale > 1.5:
            self.scale = round(max(1.5, self.scale - 0.5), 2)
            cfg.set("magnifier_scale", self.scale)
            sounds.zoom_out()
            self._update_header()
            if self.on_update_callback:
                self.on_update_callback()

    def get_status_text(self) -> str:
        mode_str = f"Ancorada ({self.dock_position})" if self.is_docked else f"Flutuante ({self.current_preset})"
        guide_str = " | Guia On" if self.reading_guide else ""
        return f"🔍 {self.scale:.1f}x  |  {mode_str}{guide_str}"

    def _update_header(self):
        if self.header_label:
            try:
                self.header_label.config(text=self.get_status_text())
            except Exception:
                pass

    def _schedule_update(self):
        """Loop de atualização de 25 FPS (40ms) sem travar a interface."""
        if not self.is_active or not self.window or not self.canvas:
            return

        if not self._is_paused_for_snipping:
            try:
                self._capture_and_render()
            except Exception:
                pass

        if self.is_active and self.window:
            self._update_job = self.root.after(40, self._schedule_update)

    def _capture_and_render(self):
        if not self.window or not self.canvas or not self.photo_image:
            return

        try:
            mx, my = pyautogui.position()
        except Exception:
            return

        render_w = self.canvas_width
        render_h = self.canvas_height

        # Reposicionamento suave via SetWindowPos (ultra-rápido, sem reflow do Tkinter)
        if not self.is_docked and self.hwnd:
            target_x = mx + 30
            target_y = my + 30

            if target_x + self.win_width > self.screen_width:
                target_x = max(5, mx - self.win_width - 30)
            if target_y + self.win_height > self.screen_height:
                target_y = max(5, my - self.win_height - 30)

            if self.smooth_movement:
                self.current_win_x += int((target_x - self.current_win_x) * 0.5)
                self.current_win_y += int((target_y - self.current_win_y) * 0.5)
            else:
                self.current_win_x, self.current_win_y = target_x, target_y

            # Chama a API nativa somente se a posição se moveu pelo menos 2 pixels
            if abs(self.current_win_x - self.last_pos_x) >= 2 or abs(self.current_win_y - self.last_pos_y) >= 2:
                self.last_pos_x = self.current_win_x
                self.last_pos_y = self.current_win_y
                ctypes.windll.user32.SetWindowPos(
                    self.hwnd, 0,
                    self.current_win_x, self.current_win_y, 0, 0,
                    SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE
                )

        # Coordenadas da área a capturar
        cap_w = max(20, min(self.screen_width, int(render_w / self.scale)))
        cap_h = max(20, min(self.screen_height, int(render_h / self.scale)))

        left = max(0, min(self.screen_width - cap_w, mx - (cap_w // 2)))
        top = max(0, min(self.screen_height - cap_h, my - (cap_h // 2)))

        bbox = {
            "left": left,
            "top": top,
            "width": cap_w,
            "height": cap_h
        }

        try:
            sct_img = self.sct.grab(bbox)
            raw_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            scaled_img = raw_img.resize((render_w, render_h), Image.Resampling.BILINEAR)

            # Régua Guia de Leitura
            if self.reading_guide:
                overlay = Image.new("RGBA", (render_w, render_h), (0, 0, 0, 0))
                draw_ov = ImageDraw.Draw(overlay)
                cy = render_h // 2
                guide_height = 40

                draw_ov.rectangle([0, 0, render_w, cy - guide_height // 2], fill=(0, 0, 0, 75))
                draw_ov.rectangle([0, cy + guide_height // 2, render_w, render_h], fill=(0, 0, 0, 75))
                draw_ov.line([(0, cy - guide_height // 2), (render_w, cy - guide_height // 2)], fill=(255, 230, 0, 220), width=2)
                draw_ov.line([(0, cy + guide_height // 2), (render_w, cy + guide_height // 2)], fill=(255, 230, 0, 220), width=2)

                scaled_img.paste(overlay, (0, 0), overlay)

            # Mira central sutil
            draw = ImageDraw.Draw(scaled_img)
            cx, cy = render_w // 2, render_h // 2
            draw.line([(cx - 8, cy), (cx + 8, cy)], fill=(255, 0, 0), width=2)
            draw.line([(cx, cy - 8), (cx, cy + 8)], fill=(255, 0, 0), width=2)

            # Atualização in-place na mesma PhotoImage existente (Zero vazamento Tcl)
            self.photo_image.paste(scaled_img)
        except Exception:
            pass
