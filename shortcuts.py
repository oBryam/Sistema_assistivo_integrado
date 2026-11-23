"""
Módulo de Gerenciamento de Atalhos Globais de Teclado.
Garante a operação 100% independente de cada funcionalidade:
- Ctrl + Alt + L : Alterna Lupa Dinâmica (Lente Virtual)
- Ctrl + Alt + I : Alterna Contraste Global de Tela (Normal / Invertido / Preto e Amarelo)
- Ctrl + Alt + R : Captura e Vocaliza Texto Selecionado na Tela
- Ctrl + Alt + P : Interrupção Imediata da Fala (TTS Stop)
- Ctrl + + / Ctrl + = : Aumenta Zoom da Lupa
- Ctrl + - : Diminui Zoom da Lupa
"""

import threading
import time
import keyboard
import pyautogui
import pyperclip
from sound_effects import sounds


class GlobalShortcutManager:
    def __init__(self, root, magnifier, tts_engine, contrast_manager, on_text_captured=None):
        self.root = root
        self.magnifier = magnifier
        self.tts = tts_engine
        self.contrast = contrast_manager
        self.on_text_captured = on_text_captured
        self.registered = False

    def start(self):
        """Registra os atalhos globais de forma resiliente."""
        if self.registered:
            return

        try:
            # Eixo 2: Lupa Dinâmica
            keyboard.add_hotkey("ctrl+alt+l", self._safe_dispatch(self.magnifier.toggle))
            keyboard.add_hotkey("ctrl+plus", self._safe_dispatch(self.magnifier.zoom_in))
            keyboard.add_hotkey("ctrl+=", self._safe_dispatch(self.magnifier.zoom_in))
            keyboard.add_hotkey("ctrl+-", self._safe_dispatch(self.magnifier.zoom_out))

            # Eixo 3: Adaptação Cromática Independente (Tela Inteira)
            keyboard.add_hotkey("ctrl+alt+i", self._safe_dispatch(self.contrast.next_mode))

            # Eixo 4: TTS Independente (Captura e Parada)
            keyboard.add_hotkey("ctrl+alt+r", self.trigger_read_selection)
            keyboard.add_hotkey("ctrl+alt+p", self._safe_dispatch(self.tts.stop))

            self.registered = True
            print("[Shortcuts] Atalhos globais registrados com sucesso.")
        except Exception as e:
            print(f"[Shortcuts Warning] Erro ao registrar atalhos: {e}")

    def _safe_dispatch(self, callback):
        """Encaminha com segurança para a thread do Tkinter."""
        def _wrapper():
            self.root.after_idle(callback)
        return _wrapper

    def trigger_read_selection(self):
        """Dispara a captura de texto selecionado em thread separada."""
        threading.Thread(target=self._capture_and_speak_worker, daemon=True).start()

    def _capture_and_speak_worker(self):
        try:
            # Aguarda brevemente a liberação física das teclas do atalho
            time.sleep(0.12)
            try:
                pyautogui.keyUp("alt")
                pyautogui.keyUp("ctrl")
                pyautogui.keyUp("r")
            except Exception:
                pass
            time.sleep(0.04)

            # Salva o conteúdo anterior da área de transferência
            prev_clipboard = ""
            try:
                prev_clipboard = pyperclip.paste()
            except Exception:
                pass

            # Envia Ctrl+C para copiar a seleção atual
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.18)  # Tempo para o software de origem (PDF, navegador, etc.) responder

            new_text = ""
            try:
                new_text = pyperclip.paste()
            except Exception:
                pass

            # Determina o texto a vocalizar
            text_to_speak = ""
            if new_text and new_text.strip() and new_text != prev_clipboard:
                text_to_speak = new_text.strip()
            elif new_text and new_text.strip():
                text_to_speak = new_text.strip()
            elif prev_clipboard and prev_clipboard.strip():
                text_to_speak = prev_clipboard.strip()

            if text_to_speak:
                # Notifica a interface visual
                if self.on_text_captured:
                    self.root.after_idle(lambda: self.on_text_captured(text_to_speak))
                # Executa a síntese de voz
                self.tts.speak(text_to_speak)
            else:
                sounds.alert_no_text()

        except Exception as e:
            print(f"[Capture Error]: {e}")
            sounds.alert_no_text()

    def stop(self):
        """Remove todos os atalhos globais ao sair."""
        if self.registered:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass
            self.registered = False
