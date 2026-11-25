"""
Módulo de OCR Instantâneo Otimizado para Textos Bloqueados e Imagens.
Utiliza Tesseract com modelo em Português e pré-processamento de imagem
(redimensionamento de alta fidelidade e binarização adaptativa) para máxima acurácia.

Correções v0.3:
- Busca automática do Tesseract no PATH do sistema (resolve falha em PCs sem instalação padrão)
- Suporte a instalação via Chocolatey, Scoop e caminhos personalizados
- Fallback robusto com mensagem de erro clara quando Tesseract não encontrado
- Instanciação preguiçosa do mss.MSS() para evitar erro de DPI em alguns computadores
"""

import os
import shutil
import sys
import cv2
import numpy as np
from PIL import Image
import pytesseract

# ---------------------------------------------------------------
# Busca robusta do executável Tesseract
# ---------------------------------------------------------------
_TESSERACT_FOUND = False

# 1. Caminhos mais comuns de instalação no Windows
TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Tesseract-OCR\tesseract.exe"),
    os.path.join(os.environ.get("PROGRAMDATA", ""), r"chocolatey\bin\tesseract.exe"),
]

# 2. Se o usuário definiu TESSERACT_CMD como variável de ambiente, prioriza
env_tess = os.environ.get("TESSERACT_CMD", "")
if env_tess:
    TESSERACT_PATHS.insert(0, env_tess)

for p in TESSERACT_PATHS:
    if p and os.path.isfile(p):
        pytesseract.pytesseract.tesseract_cmd = p
        _TESSERACT_FOUND = True
        break

# 3. Fallback: procura no PATH do sistema usando shutil.which
if not _TESSERACT_FOUND:
    which_tess = shutil.which("tesseract")
    if which_tess:
        pytesseract.pytesseract.tesseract_cmd = which_tess
        _TESSERACT_FOUND = True

if not _TESSERACT_FOUND:
    print(
        "[OCR Warning] Tesseract não encontrado. OCR não estará disponível.\n"
        "  Instale via: https://github.com/UB-Mannheim/tesseract/wiki\n"
        "  Ou defina a variável de ambiente TESSERACT_CMD com o caminho do executável."
    )

# Diretório com modelo em língua portuguesa
LOCAL_TESSDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tessdata")
if os.path.isdir(LOCAL_TESSDATA):
    os.environ["TESSDATA_PREFIX"] = LOCAL_TESSDATA


class OCREngine:
    def __init__(self):
        # Instanciação preguiçosa: evita falhas de DPI/threading em certos PCs
        self._sct = None

    @property
    def sct(self):
        """Cria instância do mss sob demanda (evita erro em certos PCs)."""
        if self._sct is None:
            try:
                import mss
                self._sct = mss.mss()
            except Exception as e:
                print(f"[OCR Screen Capture Error]: {e}")
                raise
        return self._sct

    def is_available(self) -> bool:
        """Verifica se o Tesseract está acessível."""
        return _TESSERACT_FOUND

    def extract_from_region(self, left: int, top: int, width: int, height: int) -> str:
        """
        Captura exatamente a região retangular delimitada pelo usuário e extrai o texto.
        Aplica pré-processamento avançado para garantir altíssima acurácia de leitura.
        """
        if not _TESSERACT_FOUND:
            print("[OCR Error]: Tesseract não está instalado ou não foi encontrado.")
            return ""

        try:
            bbox = {
                "left": int(left),
                "top": int(top),
                "width": max(1, int(width)),
                "height": max(1, int(height))
            }

            sct_img = self.sct.grab(bbox)
            raw_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            raw_np = np.array(raw_img)

            # 1. Conversão para tons de cinza
            gray = cv2.cvtColor(raw_np, cv2.COLOR_RGB2GRAY)
            h, w = gray.shape

            # 2. Upscaling de alta qualidade (textos na tela se beneficiam de 2x ou 3x)
            scale_factor = 2 if h >= 120 else 3
            gray_up = cv2.resize(gray, (w * scale_factor, h * scale_factor), interpolation=cv2.INTER_CUBIC)

            # 3. Suavização para remoção de artefatos de grade de pixels do monitor
            blurred = cv2.GaussianBlur(gray_up, (3, 3), 0)

            # 4. Verificação de polaridade (fundo escuro vs claro)
            mean_val = np.mean(blurred)
            if mean_val < 110:
                # Fundo escuro: inverte para que o Tesseract processe texto preto sobre fundo branco
                blurred = cv2.bitwise_not(blurred)

            # 5. Binarização adaptativa Otsu
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 6. Execução do Tesseract com idioma português
            lang = "por" if os.path.isfile(os.path.join(LOCAL_TESSDATA, "por.traineddata")) else "eng"
            config = f"-l {lang} --psm 6"

            # Tenta primeiro na imagem binarizada
            text = pytesseract.image_to_string(thresh, config=config)
            clean_text = self._clean_text(text)

            # Se binarização resultar vazia, tenta na imagem em tons de cinza suavizada
            if not clean_text:
                text = pytesseract.image_to_string(blurred, config=config)
                clean_text = self._clean_text(text)

            return clean_text
        except Exception as e:
            print(f"[OCR Error]: {e}")
            # Tenta recriar instância do mss na próxima chamada
            self._sct = None
            return ""

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Normalização de quebras de linha e remoção de ruídos
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines)


# Instância global
ocr_engine = OCREngine()
