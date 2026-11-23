"""
Módulo de OCR Instantâneo Otimizado para Textos Bloqueados e Imagens.
Utiliza Tesseract com modelo em Português e pré-processamento de imagem
(redimensionamento de alta fidelidade e binarização adaptativa) para máxima acurácia.
"""

import os
import cv2
import mss
import numpy as np
from PIL import Image
import pytesseract

# Configuração dos caminhos do Tesseract e modelos de idioma
TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Tesseract-OCR\tesseract.exe")
]

for p in TESSERACT_PATHS:
    if os.path.exists(p):
        pytesseract.pytesseract.tesseract_cmd = p
        break

# Diretório com modelo em língua portuguesa
LOCAL_TESSDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tessdata")
if os.path.exists(LOCAL_TESSDATA):
    os.environ["TESSDATA_PREFIX"] = LOCAL_TESSDATA


class OCREngine:
    def __init__(self):
        self.sct = mss.MSS()

    def extract_from_region(self, left: int, top: int, width: int, height: int) -> str:
        """
        Captura exatamente a região retangular delimitada pelo usuário e extrai o texto.
        Aplica pré-processamento avançado para garantir altíssima acurácia de leitura.
        """
        try:
            bbox = {
                "left": int(left),
                "top": int(top),
                "width": int(width),
                "height": int(height)
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
            lang = "por" if os.path.exists(os.path.join(LOCAL_TESSDATA, "por.traineddata")) else "eng"
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
            return ""

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Normalização de quebras de linha e remoção de ruídos
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines)


# Instância global
ocr_engine = OCREngine()
