"""
Módulo de Seleção Interativa de Área da Tela para OCR (Screen Snipper).
Versão estável e otimizada:
- Pausa a lupa durante a seleção para evitar conflitos de renderização
- Interface translúcida com mira de alta precisão
- Fecha imediatamente ao soltar o mouse ou teclar ESC
"""

import tkinter as tk
from typing import Callable, Optional
import pyautogui

pyautogui.FAILSAFE = False


class ScreenSnipper:
    def __init__(self, root: tk.Tk, on_area_selected: Callable[[int, int, int, int], None], on_close_callback: Optional[Callable] = None):
        self.root = root
        self.on_area_selected = on_area_selected
        self.on_close_callback = on_close_callback

        self.snip_win: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None

        self.start_x = 0
        self.start_y = 0
        self.rect_id = None

    def start_selection(self):
        """Abre a sobreposição translúcida em tela cheia para o estudante desenhar a área."""
        if self.snip_win:
            try:
                self.snip_win.destroy()
            except Exception:
                pass
            self.snip_win = None

        self.snip_win = tk.Toplevel(self.root)
        self.snip_win.overrideredirect(True)
        self.snip_win.attributes("-topmost", True)
        self.snip_win.attributes("-alpha", 0.32)
        self.snip_win.configure(bg="#000000", cursor="crosshair")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.snip_win.geometry(f"{screen_w}x{screen_h}+0+0")

        self.canvas = tk.Canvas(
            self.snip_win,
            width=screen_w,
            height=screen_h,
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Barra instrutiva
        badge_w = 520
        badge_h = 32
        bx = (screen_w - badge_w) // 2
        self.canvas.create_rectangle(bx, 16, bx + badge_w, 16 + badge_h, fill="#FFE600", outline="#000000", width=2)
        self.canvas.create_text(
            screen_w // 2, 32,
            text="🖱 ARRASTE O RETÂNGULO SOBRE O TEXTO A LER | ESC para Cancelar",
            fill="#000000",
            font=("Segoe UI", 10, "bold")
        )

        self.snip_win.bind("<ButtonPress-1>", self._on_button_press)
        self.snip_win.bind("<B1-Motion>", self._on_mouse_drag)
        self.snip_win.bind("<ButtonRelease-1>", self._on_button_release)
        self.snip_win.bind("<Escape>", lambda e: self.close())
        self.snip_win.bind("<Button-3>", lambda e: self.close())

        self.snip_win.focus_force()

    def _on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#FFE600",
            width=3,
            fill="#FFFFFF"
        )

    def _on_mouse_drag(self, event):
        cur_x, cur_y = event.x, event.y
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def _on_button_release(self, event):
        end_x = event.x
        end_y = event.y

        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)

        self.close()

        if width > 15 and height > 15:
            if self.on_area_selected:
                self.on_area_selected(left, top, width, height)

    def close(self):
        if self.snip_win:
            try:
                self.snip_win.destroy()
            except Exception:
                pass
            self.snip_win = None
            self.canvas = None
            self.rect_id = None

        if self.on_close_callback:
            try:
                self.on_close_callback()
            except Exception:
                pass
