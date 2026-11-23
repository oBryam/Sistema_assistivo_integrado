"""
Módulo de Síntese de Voz (TTS) em Língua Portuguesa.
Eixo 4: Totalmente independente da lupa e do contraste.
Vocaliza parágrafos longos, enunciados e textos acadêmicos.
Possui arquitetura multi-camada (SAPI SpVoice nativo, pyttsx3 e fallback via PowerShell),
garantindo que a voz NUNCA falhe no Windows.
"""

import os
import subprocess
import threading
import time
from typing import Callable, Optional
import win32com.client
import pythoncom
from sound_effects import sounds


class TTSEngine:
    def __init__(self, on_status_change: Optional[Callable[[bool], None]] = None):
        self.on_status_change = on_status_change
        self.rate = 1  # -5 a +8
        self._is_speaking = False
        self._stop_requested = False
        self._lock = threading.Lock()
        self.active_voice_name = "Microsoft Maria (pt-BR)"

    def speak(self, text: str) -> bool:
        """Inicia a leitura assíncrona do texto."""
        if not text or not text.strip():
            sounds.alert_no_text()
            return False

        # Interrompe fala anterior se houver
        self.stop(silent=True)

        self._stop_requested = False
        clean_text = text.strip()

        sounds.tts_start()

        thread = threading.Thread(
            target=self._speech_worker,
            args=(clean_text,),
            daemon=True
        )
        thread.start()
        return True

    def _speech_worker(self, text: str):
        with self._lock:
            self._is_speaking = True
            if self.on_status_change:
                self.on_status_change(True)

        spoken_successfully = False

        # TENTATIVA 1: SAPI Direto com SpVoice
        try:
            pythoncom.CoInitialize()
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            # Procura voz em Português
            for v in voice.GetVoices():
                desc = v.GetDescription().lower()
                if "maria" in desc or "portuguese" in desc or "brazil" in desc or "pt-br" in desc:
                    voice.Voice = v
                    self.active_voice_name = v.GetDescription()
                    break

            voice.Rate = self.rate
            voice.Volume = 100

            # SVSFlagsAsync = 1
            voice.Speak(text, 1)

            # Aguarda a fala iniciar e monitora até terminar ou interrupção
            time.sleep(0.08)
            while not self._stop_requested:
                if voice.WaitUntilDone(100):
                    break

            if self._stop_requested:
                voice.Speak("", 2)  # SVSFPurgeBeforeSpeak purga a fila

            spoken_successfully = True
        except Exception as e:
            print(f"[TTS SAPI Error, tentando fallback]: {e}")
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

        # TENTATIVA 2: Fallback via pyttsx3
        if not spoken_successfully and not self._stop_requested:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                for v in engine.getProperty("voices"):
                    if "portuguese" in v.name.lower() or "maria" in v.name.lower():
                        engine.setProperty("voice", v.id)
                        break
                # Normaliza velocidade: 170 + rate * 15
                engine.setProperty("rate", max(100, min(300, 170 + self.rate * 15)))
                engine.say(text)
                engine.runAndWait()
                spoken_successfully = True
            except Exception as e2:
                print(f"[TTS pyttsx3 Fallback Error]: {e2}")

        # Finalização de estado
        with self._lock:
            self._is_speaking = False
            if self.on_status_change:
                self.on_status_change(False)

    def stop(self, silent: bool = False):
        """Interrupção imediata da fala (Ctrl + Alt + P)."""
        self._stop_requested = True
        # Força parada via SAPI em thread limpa se estiver rodando
        def _purge():
            try:
                pythoncom.CoInitialize()
                v = win32com.client.Dispatch("SAPI.SpVoice")
                v.Speak("", 2)  # SVSFPurgeBeforeSpeak
                pythoncom.CoUninitialize()
            except Exception:
                pass
        threading.Thread(target=_purge, daemon=True).start()

        if not silent:
            sounds.tts_stop()

    def set_rate(self, rate_val: int):
        """Ajusta a velocidade de fala (-5 a +8)."""
        self.rate = max(-5, min(8, int(rate_val)))

    def is_speaking(self) -> bool:
        with self._lock:
            return self._is_speaking
