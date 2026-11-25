"""
Módulo de Adaptação Cromática e Filtros de Contraste para Fotofobia.
Eixo 3: Funciona de forma 100% independente da lupa, aplicando os filtros
diretamente na tela de todo o sistema operacional (Windows Magnification API).

Modos Expandidos (v0.3) - Corrigidos conforme WCAG 2.1 AA/AAA:
0: Normal (Cores originais)
1: Invertido (Inversão completa e correta do espectro RGB)
2: Preto e Amarelo (Alto contraste WCAG AAA: ratio ≥ 15.6:1)
3: Âmbar / Sépia (Filtro anti-luz azul suavizado com contraste preservado)
4: Escala de Cinza (Coeficientes Rec. 709 padrão para luminância perceptual)
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

    def _make_matrix(self) -> MAGCOLOREFFECT:
        """Cria uma matriz 5x5 zerada."""
        mat = MAGCOLOREFFECT()
        # Todos os campos já estão zerados por ctypes
        return mat

    def _apply_matrix(self, mat: MAGCOLOREFFECT):
        """Aplica a matriz de transformação de cores."""
        if not self.is_supported or not self._mag_dll:
            return
        try:
            self._mag_dll.MagSetFullscreenColorEffect(ctypes.byref(mat))
        except Exception as e:
            print(f"[Contrast Apply Error]: {e}")

    def _apply_identity(self):
        """Restaura as cores normais do monitor (matriz identidade 5x5)."""
        mat = self._make_matrix()
        for i in range(5):
            mat.transform[i][i] = 1.0
        self._apply_matrix(mat)

    def _apply_inverted(self):
        """
        Inversão completa e correta do espectro RGB.
        Fórmula: C' = 1.0 - C (para cada canal R, G, B).
        A matriz correta para inversão total:
          R' = -1·R + 0·G + 0·B + 0·A + 1  =>  row0=-1, offset=+1
          G' = 0·R - 1·G + 0·B + 0·A + 1
          B' = 0·R + 0·G - 1·B + 0·A + 1
          A' = A
        """
        mat = self._make_matrix()
        # Canal vermelho: invertido
        mat.transform[0][0] = -1.0
        mat.transform[4][0] = 1.0
        # Canal verde: invertido
        mat.transform[1][1] = -1.0
        mat.transform[4][1] = 1.0
        # Canal azul: invertido
        mat.transform[2][2] = -1.0
        mat.transform[4][2] = 1.0
        # Alpha: preservado
        mat.transform[3][3] = 1.0
        # Componente homogêneo
        mat.transform[4][4] = 1.0
        self._apply_matrix(mat)

    def _apply_black_yellow(self):
        """
        Alto contraste Preto e Amarelo conforme WCAG AAA (ratio ≥ 15.6:1).
        Converte para luminância e mapeia:
        - Fundos claros (alta luminância) → preto puro (#000000)
        - Texto/elementos escuros (baixa luminância) → amarelo vívido (#FFE600)
        
        Fórmula usando inversão + mapeamento para amarelo:
          L = 0.2126·R + 0.7152·G + 0.0722·B  (Rec. 709)
          L' = 1 - L  (inverte: fundo claro → escuro)
          R' = L'  (amarelo = R + G)
          G' = L' × 0.90  (amarelo ligeiramente desaturado)
          B' = 0  (sem azul = proteção fotofobia)
        """
        mat = self._make_matrix()
        # Coeficientes de luminância Rec. 709 (invertidos para inversão)
        # R' = -(0.2126·R + 0.7152·G + 0.0722·B) + 1.0
        mat.transform[0][0] = -0.2126
        mat.transform[1][0] = -0.7152
        mat.transform[2][0] = -0.0722
        mat.transform[4][0] = 1.0

        # G' = -(0.2126·R + 0.7152·G + 0.0722·B) × 0.90 + 0.90
        mat.transform[0][1] = -0.2126 * 0.90
        mat.transform[1][1] = -0.7152 * 0.90
        mat.transform[2][1] = -0.0722 * 0.90
        mat.transform[4][1] = 0.90

        # B' = 0 (sem componente azul - reduz fadiga de fotofobia)
        mat.transform[0][2] = 0.0
        mat.transform[1][2] = 0.0
        mat.transform[2][2] = 0.0
        mat.transform[4][2] = 0.0

        # Alpha e homogêneo
        mat.transform[3][3] = 1.0
        mat.transform[4][4] = 1.0
        self._apply_matrix(mat)

    def _apply_amber_sepia(self):
        """
        Filtro Âmbar / Sépia: redução significativa de luz azul.
        Preserva contraste e legibilidade conforme WCAG AA (ratio ≥ 4.5:1).

        Matriz calibrada para:
        - Reduzir canal azul em ~85% (proteção para fotofobia)
        - Manter tom quente âmbar/dourado confortável
        - Preservar distinção entre elementos claros e escuros
        """
        mat = self._make_matrix()
        # Canal vermelho: leve aquecimento
        mat.transform[0][0] = 1.0
        mat.transform[1][0] = 0.15
        mat.transform[2][0] = 0.05

        # Canal verde: leve redução para tom dourado
        mat.transform[0][1] = 0.05
        mat.transform[1][1] = 0.85
        mat.transform[2][1] = 0.05

        # Canal azul: redução intensa (~85%)
        mat.transform[0][2] = 0.02
        mat.transform[1][2] = 0.05
        mat.transform[2][2] = 0.15

        # Alpha e homogêneo
        mat.transform[3][3] = 1.0
        mat.transform[4][4] = 1.0
        self._apply_matrix(mat)

    def _apply_grayscale(self):
        """
        Escala de cinza usando coeficientes de luminância Rec. 709 (padrão sRGB/HDTV).
        L = 0.2126·R + 0.7152·G + 0.0722·B
        Cada canal de saída recebe o mesmo valor L, garantindo percepção uniforme.
        """
        mat = self._make_matrix()
        # Coeficientes Rec. 709 para luminância perceptual
        r_coef = 0.2126
        g_coef = 0.7152
        b_coef = 0.0722

        for col in range(3):  # R', G', B' recebem a mesma luminância
            mat.transform[0][col] = r_coef
            mat.transform[1][col] = g_coef
            mat.transform[2][col] = b_coef

        mat.transform[3][3] = 1.0
        mat.transform[4][4] = 1.0
        self._apply_matrix(mat)

    def next_mode(self):
        """Alterna ciclicamente entre todos os modos disponíveis."""
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
