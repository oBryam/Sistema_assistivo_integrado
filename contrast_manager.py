"""
Módulo de Adaptação Cromática e Filtros de Contraste para Fotofobia.
Eixo 3: Funciona de forma 100% independente da lupa, aplicando os filtros
diretamente na tela de todo o sistema operacional (Windows Magnification API)
ou de forma sincronizada na lupa.

Modos:
0: Normal (Cores originais)
1: Cores Invertidas (Inversão global do espectro RGB)
2: Alto Contraste Preto e Amarelo (Fundo preto com caracteres amarelos)
"""

import atexit
import ctypes
from typing import Callable, Optional
from sound_effects import sounds


class MAGCOLOREFFECT(ctypes.Structure):
    _fields_ = [("transform", (ctypes.c_float * 5) * 5)]


class FullscreenContrastManager:
    MODES = ["Normal", "Invertido", "Preto/Amarelo"]

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
                    # Garante que começa normal
                    self._apply_identity()
        except Exception as e:
            print(f"[Contrast API Warning] {e}")
            self.is_supported = False

    def _apply_identity(self):
        """Restaura as cores padrão do sistema operacional."""
        if not self.is_supported or not self._mag_dll:
            return
        try:
            mat = MAGCOLOREFFECT()
            for i in range(5):
                mat.transform[i][i] = 1.0
            self._mag_dll.MagSetFullscreenColorEffect(ctypes.byref(mat))
        except Exception as e:
            print(f"[Contrast Reset Error] {e}")

    def _apply_inverted(self):
        """Aplica inversão de cores em toda a tela do Windows."""
        if not self.is_supported or not self._mag_dll:
            return
        try:
            mat = MAGCOLOREFFECT()
            # Diagonal negativa para inverter R, G, B
            mat.transform[0][0] = -1.0
            mat.transform[1][1] = -1.0
            mat.transform[2][2] = -1.0
            mat.transform[3][3] = 1.0
            # Bias de +1.0 para transformar [0, 1] em [1, 0]
            mat.transform[4][0] = 1.0
            mat.transform[4][1] = 1.0
            mat.transform[4][2] = 1.0
            mat.transform[4][4] = 1.0
            self._mag_dll.MagSetFullscreenColorEffect(ctypes.byref(mat))
        except Exception as e:
            print(f"[Contrast Invert Error] {e}")

    def _apply_black_yellow(self):
        """
        Aplica filtro Preto e Amarelo para fotofobia em toda a tela:
        Fundos brancos/claros tornam-se preto absoluto (0, 0, 0).
        Textos e elementos escuros tornam-se amarelo vívido (255, 230, 0).
        """
        if not self.is_supported or not self._mag_dll:
            return
        try:
            mat = MAGCOLOREFFECT()
            # Coluna 0 (Vermelho): R' = 1.0 - (0.30*R + 0.59*G + 0.11*B)
            mat.transform[0][0] = -0.30
            mat.transform[1][0] = -0.59
            mat.transform[2][0] = -0.11
            mat.transform[4][0] = 1.00

            # Coluna 1 (Verde): G' = 0.90 - (0.27*R + 0.53*G + 0.10*B)
            mat.transform[0][1] = -0.27
            mat.transform[1][1] = -0.53
            mat.transform[2][1] = -0.10
            mat.transform[4][1] = 0.90

            # Coluna 2 (Azul): B' = 0.0 (sem azul para reduzir luz azul e fotofobia)
            mat.transform[0][2] = 0.0
            mat.transform[1][2] = 0.0
            mat.transform[2][2] = 0.0
            mat.transform[4][2] = 0.0

            # Alfa e translação homogênea
            mat.transform[3][3] = 1.0
            mat.transform[4][4] = 1.0

            self._mag_dll.MagSetFullscreenColorEffect(ctypes.byref(mat))
        except Exception as e:
            print(f"[Contrast Black/Yellow Error] {e}")

    def next_mode(self):
        """Alterna ciclicamente entre Normal, Invertido e Preto/Amarelo (Ctrl + Alt + I)."""
        self.set_mode((self.mode_index + 1) % len(self.MODES))

    def set_mode(self, index: int):
        """Define o modo cromático especificado."""
        self.mode_index = index % len(self.MODES)
        sounds.filter_change()

        if self.mode_index == 0:
            self._apply_identity()
        elif self.mode_index == 1:
            self._apply_inverted()
        elif self.mode_index == 2:
            self._apply_black_yellow()

        if self.on_change_callback:
            self.on_change_callback(self.mode_index, self.get_current_mode_name())

    def get_current_mode_name(self) -> str:
        return self.MODES[self.mode_index]

    def reset_to_normal(self):
        """Restaura o monitor ao estado padrão ao sair."""
        self._apply_identity()
        if self.is_supported and self._mag_dll:
            try:
                self._mag_dll.MagUninitialize()
            except Exception:
                pass


# Instância global
contrast_manager = FullscreenContrastManager()
