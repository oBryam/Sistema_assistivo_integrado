"""
Sistema Assistivo Integrado v0.2
Ponto de Entrada da Aplicação de Tecnologia Assistiva (TDIC).
Executa o Painel Principal de Alto Contraste, Lupa Dinâmica de Área Ampla,
Adaptação Cromática Global para Fotofobia, Síntese de Voz (TTS) e OCR Instantâneo.
"""

import sys
import tkinter as tk
from app import HighContrastApp, APP_FULL_TITLE


def main():
    try:
        root = tk.Tk()
        app = HighContrastApp(root)
        print(f"[{APP_FULL_TITLE}] Iniciado com sucesso.")
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"[Fatal Error]: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
