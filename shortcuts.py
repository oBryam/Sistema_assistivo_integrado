"""
Módulo de Gerenciamento de Atalhos Globais de Teclado - Versão com Atalhos Personalizáveis.
Garante a operação 100% independente e segura:
- Atalhos configuráveis pelo usuário via tela de configurações
- Fallback para atalhos padrão quando configuração ausente
- Re-registro dinâmico após mudança de atalhos
"""

import threading
import time
import keyboard
import pyautogui
import pyperclip
from config_manager import cfg
from ocr_engine import ocr_engine
from sound_effects import sounds

pyautogui.FAILSAFE = False


# Nomes amigáveis para exibição na interface
SHORTCUT_LABELS = {
    "toggle_magnifier": "Ligar/Desligar Lupa",
    "zoom_in": "Aumentar Zoom",
    "zoom_in_alt": "Aumentar Zoom (Alt)",
    "zoom_out": "Diminuir Zoom",
    "next_contrast": "Alternar Filtro de Contraste",
    "read_selection": "Ler Seleção (TTS)",
    "toggle_pause": "Pausar/Retomar Leitura",
    "stop_speech": "Parar Leitura",
    "ocr_selection": "Ler Imagem (OCR)",
}


class GlobalShortcutManager:
    def __init__(self, root, magnifier, tts_engine, contrast_manager, snipper, on_text_captured=None):
        self.root = root
        self.magnifier = magnifier
        self.tts = tts_engine
        self.contrast = contrast_manager
        self.snipper = snipper
        self.on_text_captured = on_text_captured
        self.registered = False

    def start(self):
        if self.registered:
            return
        self._register_all()

    def _register_all(self):
        """Registra todos os atalhos usando as configurações do usuário."""
        try:
            sc = cfg.get_shortcuts_dict()

            # Eixo 2: Lupa
            keyboard.add_hotkey(sc.get("toggle_magnifier", "ctrl+alt+l"), self._safe_dispatch(self._toggle_magnifier))
            keyboard.add_hotkey(sc.get("zoom_in", "ctrl+plus"), self._safe_dispatch(self.magnifier.zoom_in))
            keyboard.add_hotkey(sc.get("zoom_in_alt", "ctrl+="), self._safe_dispatch(self.magnifier.zoom_in))
            keyboard.add_hotkey(sc.get("zoom_out", "ctrl+-"), self._safe_dispatch(self.magnifier.zoom_out))

            # Eixo 3: Contraste Global
            keyboard.add_hotkey(sc.get("next_contrast", "ctrl+alt+i"), self._safe_dispatch(self._next_contrast))

            # Eixo 4: TTS (Seleção, Pausa, Parada e Seleção Visual de OCR)
            keyboard.add_hotkey(sc.get("read_selection", "ctrl+alt+r"), self.trigger_read_selection)
            keyboard.add_hotkey(sc.get("toggle_pause", "ctrl+alt+space"), self._safe_dispatch(self.tts.toggle_pause))
            keyboard.add_hotkey(sc.get("stop_speech", "ctrl+alt+p"), self._safe_dispatch(self.tts.stop))
            keyboard.add_hotkey(sc.get("ocr_selection", "ctrl+alt+o"), self._safe_dispatch(self.trigger_ocr_selection))

            self.registered = True
            print("[Shortcuts] Atalhos globais registrados com sucesso.")
        except Exception as e:
            print(f"[Shortcuts Warning]: {e}")

    def reload(self):
        """Re-registra todos os atalhos após mudança de configuração."""
        self.stop()
        self._register_all()

    def _safe_dispatch(self, callback):
        def _wrapper():
            try:
                self.root.after_idle(callback)
            except Exception as e:
                print(f"[Dispatch Error]: {e}")
        return _wrapper

    def _toggle_magnifier(self):
        try:
            self.magnifier.toggle()
            msg = f"Lupa ligada, escala {self.magnifier.scale:.1f}" if self.magnifier.is_active else "Lupa desligada"
            self.tts.announce(msg)
        except Exception as e:
            print(f"[Toggle Mag Error]: {e}")

    def _next_contrast(self):
        try:
            self.contrast.next_mode()
            self.tts.announce(f"Filtro: {self.contrast.get_current_mode_name()}")
        except Exception as e:
            print(f"[Contrast Error]: {e}")

    def trigger_ocr_selection(self):
        """Pausa a captura da lupa temporariamente e abre a seleção visual em tela cheia."""
        try:
            if hasattr(self.magnifier, "pause_capture"):
                self.magnifier.pause_capture()
            self.snipper.start_selection()
        except Exception as e:
            print(f"[Snipper Trigger Error]: {e}")

    def handle_snipped_area(self, left: int, top: int, width: int, height: int):
        """Processa a área delimitada pelo aluno em thread separada."""
        def _worker():
            try:
                sounds.filter_change()
                self.tts.announce("Lendo área selecionada")
                text = ocr_engine.extract_from_region(left, top, width, height)
                if text and text.strip():
                    clean = text.strip()
                    if self.on_text_captured:
                        self.root.after_idle(lambda: self.on_text_captured(clean))
                    self.tts.speak(clean)
                else:
                    sounds.alert_no_text()
                    self.tts.announce("Nenhum texto identificado nesta área")
            except Exception as e:
                print(f"[Snipped OCR Error]: {e}")
                sounds.alert_no_text()

        threading.Thread(target=_worker, daemon=True).start()

    def trigger_read_selection(self):
        threading.Thread(target=self._capture_and_speak_worker, daemon=True).start()

    def _capture_and_speak_worker(self):
        try:
            time.sleep(0.12)
            try:
                pyautogui.keyUp("alt")
                pyautogui.keyUp("ctrl")
                pyautogui.keyUp("r")
            except Exception:
                pass
            time.sleep(0.04)

            prev_clipboard = ""
            try:
                prev_clipboard = pyperclip.paste()
            except Exception:
                pass

            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.18)

            new_text = ""
            try:
                new_text = pyperclip.paste()
            except Exception:
                pass

            text_to_speak = ""
            if new_text and new_text.strip() and new_text != prev_clipboard:
                text_to_speak = new_text.strip()
            elif new_text and new_text.strip():
                text_to_speak = new_text.strip()
            elif prev_clipboard and prev_clipboard.strip():
                text_to_speak = prev_clipboard.strip()

            if text_to_speak:
                if self.on_text_captured:
                    self.root.after_idle(lambda: self.on_text_captured(text_to_speak))
                self.tts.speak(text_to_speak)
            else:
                sounds.alert_no_text()
                self.tts.announce("Nenhum texto selecionado")

        except Exception as e:
            print(f"[Capture Error]: {e}")
            sounds.alert_no_text()

    def get_shortcut_display(self, action: str) -> str:
        """Retorna o atalho formatado para exibição na interface."""
        hotkey = cfg.get_shortcut(action)
        return hotkey.replace("+", "+").title().replace("Ctrl", "Ctrl").replace("Alt", "Alt").replace("Space", "Espaço")

    def stop(self):
        if self.registered:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass
            self.registered = False
