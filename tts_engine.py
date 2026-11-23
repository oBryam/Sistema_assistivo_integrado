"""
Módulo de Síntese de Voz (TTS) em Língua Portuguesa - Versão Definitiva sem Deadlocks.
Eixo 4: Leitura de Textos Extensos e OCR.
Garantias de Estabilidade:
- Fila de execução dedicada sem concorrência de threads
- Zero bloqueios (locks) na thread de interface gráfica (Tkinter)
- Notificação de status desacoplada (idle, speaking, paused)
- Liberação segura de recursos sem travamento de áudio ou COM
"""

import queue
import re
import threading
import time
from typing import Callable, Optional
import pythoncom
import win32com.client
from config_manager import cfg
from sound_effects import sounds


class TTSEngine:
    def __init__(self, on_status_change: Optional[Callable[[str], None]] = None, on_sentence_change: Optional[Callable[[str], None]] = None):
        self.on_status_change = on_status_change      # Recebe "speaking", "paused" ou "idle"
        self.on_sentence_change = on_sentence_change  # Recebe a sentença atual ou ""

        self.rate = cfg.get("tts_rate", 1)
        self.active_voice_name = "Microsoft Maria (pt-BR)"

        # Estados atômicos (sem locks bloqueantes para a GUI)
        self._is_speaking = False
        self._is_paused = False
        self._stop_requested = False

        self._queue = queue.Queue()
        self._current_voice = None

        # Thread persistente de áudio para evitar criação e destruição repetitiva de COM
        self._worker_thread = threading.Thread(target=self._audio_loop, daemon=True)
        self._worker_thread.start()

    def speak(self, text: str) -> bool:
        """Enfileira o texto para vocalização assíncrona imediata."""
        if not text or not text.strip():
            sounds.alert_no_text()
            return False

        # Interrompe qualquer fala anterior
        self.stop(silent=True)

        self._stop_requested = False
        self._is_paused = False

        sounds.tts_start()
        self._queue.put(("speak", text.strip()))
        return True

    def toggle_pause(self):
        """Alterna pausa/retomada."""
        if not self._is_speaking:
            return
        if self._is_paused:
            self.resume()
        else:
            self.pause()

    def pause(self):
        if not self._is_speaking or self._is_paused:
            return
        self._is_paused = True
        if self._current_voice:
            try:
                self._current_voice.Pause()
            except Exception:
                pass
        sounds.tts_stop()
        self._notify_status("paused")

    def resume(self):
        if not self._is_speaking or not self._is_paused:
            return
        self._is_paused = False
        if self._current_voice:
            try:
                self._current_voice.Resume()
            except Exception:
                pass
        sounds.tts_start()
        self._notify_status("speaking")

    def stop(self, silent: bool = False):
        """Interrupção imediata da fala."""
        self._stop_requested = True
        self._is_paused = False

        if self._current_voice:
            try:
                self._current_voice.Speak("", 2)  # SVSFPurgeBeforeSpeak
            except Exception:
                pass

        if not silent:
            sounds.tts_stop()

        self._is_speaking = False
        self._notify_status("idle")
        self._notify_sentence("")

    def announce(self, message: str):
        """Audiodescrição curta enfileirada sem colidir com leitura longa."""
        if not cfg.get("audiodescription", True):
            return
        if self._is_speaking:
            return  # Não interrompe se o usuário estiver ouvindo um texto
        self._queue.put(("announce", message))

    def set_rate(self, rate_val: int):
        self.rate = max(-5, min(8, int(rate_val)))
        cfg.set("tts_rate", self.rate)
        if self._current_voice:
            try:
                self._current_voice.Rate = self.rate
            except Exception:
                pass

    def is_speaking(self) -> bool:
        return self._is_speaking and not self._is_paused

    def is_paused(self) -> bool:
        return self._is_paused

    def _notify_status(self, status: str):
        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception:
                pass

    def _notify_sentence(self, sentence: str):
        if self.on_sentence_change:
            try:
                self.on_sentence_change(sentence)
            except Exception:
                pass

    def _audio_loop(self):
        """Loop contínuo de processamento de áudio com COM persistente."""
        try:
            pythoncom.CoInitialize()
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            self._current_voice = voice

            # Configura voz em português
            for v in voice.GetVoices():
                desc = v.GetDescription().lower()
                if "maria" in desc or "portuguese" in desc or "brazil" in desc or "pt-br" in desc:
                    voice.Voice = v
                    self.active_voice_name = v.GetDescription()
                    break

            voice.Rate = self.rate
            voice.Volume = 100
        except Exception as e:
            print(f"[TTS Init Error]: {e}")
            return

        while True:
            try:
                task_type, payload = self._queue.get()
                if task_type == "speak":
                    self._process_speak(voice, payload)
                elif task_type == "announce":
                    self._process_announce(voice, payload)
                self._queue.task_done()
            except Exception as e:
                print(f"[TTS Queue Loop Error]: {e}")
                time.sleep(0.1)

    def _process_speak(self, voice, text: str):
        self._is_speaking = True
        self._is_paused = False
        self._stop_requested = False
        self._notify_status("speaking")

        # Quebra em sentenças para acompanhamento do Karaokê
        sentences = [s.strip() for s in re.split(r'(?<=[.!?;\n])\s+', text) if s.strip()]
        if not sentences:
            sentences = [text]

        voice.Rate = self.rate

        try:
            for sentence in sentences:
                if self._stop_requested:
                    break

                self._notify_sentence(sentence)
                voice.Speak(sentence, 1)  # SVSFlagsAsync = 1

                time.sleep(0.04)
                while not self._stop_requested:
                    if self._is_paused:
                        time.sleep(0.08)
                        continue
                    if voice.WaitUntilDone(60):
                        break

            if self._stop_requested:
                try:
                    voice.Speak("", 2)
                except Exception:
                    pass

        except Exception as e:
            print(f"[TTS Speak Error]: {e}")
        finally:
            self._is_speaking = False
            self._is_paused = False
            self._notify_sentence("")
            self._notify_status("idle")

    def _process_announce(self, voice, message: str):
        if self._is_speaking:
            return
        try:
            prev_rate = voice.Rate
            voice.Rate = min(6, self.rate + 3)
            voice.Speak(message, 1)
            voice.WaitUntilDone(2000)
            voice.Rate = prev_rate
        except Exception:
            pass
