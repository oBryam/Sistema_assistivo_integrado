"""
Módulo de Adaptação Cromática e Filtros de Contraste para Fotofobia.
Eixo 3: Funciona de forma 100% independente da lupa, aplicando os filtros
diretamente na tela de todo o sistema operacional (Windows Magnification API).

Modos Expandidos (v0.2):
0: Normal (Cores originais)
1: Invertido (Inversão global do espectro RGB - Fundo Escuro)
2: Preto e Amarelo (Fundo preto absoluto com caracteres amarelo vívido)
3: Âmbar / Sépia (Filtro anti-luz azul para redução da fadiga ocular)
4: Escala de Cinza (Alto contraste monocromático para daltonismo)
"""

import atexit
import ctypes
from typing import Callable, Optional
from sound_effects import sounds


class MAGCOLOREFFECT(ctypes.Structure):
    _fields_ = [("transform", (ctypes.c_float * 5) * 5)]


class FullscreenContrastManager:
    MODES = [
        "Normal",
        "Invertido",
        "Preto/Amarelo",
        "Âmbar (Anti-Luz Azul)",
        "Escala de Cinza"
    ]

    def __init__(self, on_change_callback: Optional[Callable] = None):
        self.mode_index = 0
        self.on_change_callback = on_change_callback
        self.is_supported = False
        self._mag_dll = None

        self._init_api()
        atexit.register(self.reset_to_normal)

    def _init_api(self):
        try:
            self._mag_dll = ctypes.windll.LoadLibrary("Magnification.dll")
            if hasattr(self._mag_dll, "MagInitialize") and hasattr(self._mag_dll, "MagSetFullscreenColorEffect"):
                res = self._mag_dll.MagInitialize()
                if res:
                    self.is_supported = True
                    self._apply_identity()
        except Exception as e:
            print(f"[Contrast API Warning]: {e}")
            self.is_supported = False

    def _apply_identity(self):
        """Restaura as cores normais do monitor."""
        if not self.is_supported or not self._mag_dll:
            return
        try:
            mat = MAGCOLOREFFECT()
            for i in range(5):
                mat.transform[i][i] = 1.0
            self._mag_dll.MagSetFullscreenColorEffect(ctypes.byref(mat))
        except Exception as e:
            print(f"[Contrast Reset Error]: {e}")

    def _apply_inverted(self):
        """Inversão global do espectro RGB (fundos brancos viram pretos)."""
        if not self.is_supported or not self._mag_dll:
            return
        try:
            mat = MAGCOLOREFFECT()
            mat.transform[0][0] = -1.0
            mat.transform[1][1] = -1.0
            mat.transform[2][2] = -1.0
            mat.transform[3][3] = 1.0
            mat.transform[4][0] = 1.0
            mat.transform[4][1] = 1.0
            mat.transform[4][2] = 1.0
            mat.transform[4][4] = 1.0
            self._mag_dll.MagSetFullscreenColorEffect(ctypes.byref(mat))
        except Exception as e:
            print(f"[Contrast Invert Error]: {e}")

    def _apply_black_yellow(self):
        """Alto contraste: fundos claros viram preto e texto vira amarelo vívido."""
        if not self.is_supported or not self._mag_dll:
            return
        try:
            mat = MAGCOLOREFFECT()
            # R' = 1.0 - (0.30*R + 0.59*G + 0.11*B)
            mat.transform[0][0] = -0.30
            mat.transform[1][0] = -0.59
            mat.transform[2][0] = -0.11
            mat.transform[4][0] = 1.00

            # G' = 0.90 - (0.27*R + 0.53*G + 0.10*B)
            mat.transform[0][1] = -0.27
            mat.transform[1][1] = -0.53
            mat.transform[2][1] = -0.10
            mat.transform[4][1] = 0.90

            # B' = 0.0 (sem azul para fotofobia)
            mat.transform[0][2] = 0.0
            mat.transform[1][2] = 0.0
            mat.transform[2][2] = 0.0
            mat.transform[4][2] = 0.0

            mat.transform[3][3] = 1.0
            mat.transform[4][4] = 1.0
            self._mag_dll.MagSetFullscreenColorEffect(ctypes.byref(mat))
        except Exception as e:
            print(f"[Contrast Black/Yellow Error]: {e}")

    def _apply_amber_sepia(self):
        """Filtro Âmbar / Sépia: atenuação drástica de luz azul e calor visual."""
        if not self.is_supported or not self._mag_dll:
            return
        try:
            mat = MAGCOLOREFFECT()
            # Tom avermelhado/dourado
            mat.transform[0][0] = 0.45; mat.transform[1][0] = 0.65; mat.transform[2][0] = 0.15
            # Tom verde aconchegante
            mat.transform[0][1] = 0.35; mat.transform[1][1] = 0.55; mat.transform[2][1] = 0.10
            # Redução intensa do canal azul
            mat.transform[0][2] = 0.05; mat.transform[1][2] = 0.10; mat.transform[2][2] = 0.05
            mat.transform[3][3] = 1.0
            mat.transform[4][4] = 1.0
            self._mag_dll.MagSetFullscreenColorEffect(ctypes.byref(mat))
        except Exception as e:
            print(f"[Contrast Amber Error]: {e}")

    def _apply_grayscale(self):
        """Escala de cinza de alto contraste para neutralidade e daltonismo."""
        if not self.is_supported or not self._mag_dll:
            return
        try:
            mat = MAGCOLOREFFECT()
            for col in range(3):
                mat.transform[0][col] = 0.299
                mat.transform[1][col] = 0.587
                mat.transform[2][col] = 0.114
            mat.transform[3][3] = 1.0
            mat.transform[4][4] = 1.0
            self._mag_dll.MagSetFullscreenColorEffect(ctypes.byref(mat))
        except Exception as e:
            print(f"[Contrast Grayscale Error]: {e}")

    def next_mode(self):
        """Alterna ciclicamente entre todos os modos disponíveis (Ctrl + Alt + I)."""
        self.set_mode((self.mode_index + 1) % len(self.MODES))

    def set_mode(self, index: int):
        self.mode_index = index % len(self.MODES)
        sounds.filter_change()

        if self.mode_index == 0:
            self._apply_identity()
        elif self.mode_index == 1:
            self._apply_inverted()
        elif self.mode_index == 2:
            self._apply_black_yellow()
        elif self.mode_index == 3:
            self._apply_amber_sepia()
        elif self.mode_index == 4:
            self._apply_grayscale()

        if self.on_change_callback:
            self.on_change_callback(self.mode_index, self.get_current_mode_name())

    def get_current_mode_name(self) -> str:
        return self.MODES[self.mode_index]

    def reset_to_normal(self):
        self._apply_identity()
        if self.is_supported and self._mag_dll:
            try:
                self._mag_dll.MagUninitialize()
            except Exception:
                pass


# Instância global
contrast_manager = FullscreenContrastManager()
