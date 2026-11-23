"""
Módulo de Feedback Sonoro e Confirmação Auditiva para Tecnologia Assistiva.
Gera bipes e tons com frequências e durações distintas para cada ação do sistema,
garantindo retorno auditivo imediato para estudantes com deficiência visual.
"""

import threading
import winsound

class SoundEffects:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def _play(self, freq: int, duration: int):
        if not self.enabled:
            return
        try:
            winsound.Beep(freq, duration)
        except Exception:
            pass

    def play_async(self, freq: int, duration: int):
        """Toca um bipe de forma assíncrona para não travar a interface."""
        threading.Thread(target=self._play, args=(freq, duration), daemon=True).start()

    def startup(self):
        """Som de inicialização da aplicação: sequência ascendente."""
        def _run():
            for f in [523, 659, 784, 1046]:  # C5, E5, G5, C6
                self._play(f, 90)
        threading.Thread(target=_run, daemon=True).start()

    def lens_on(self):
        """Lupa ativada: dois tons agudos ascendentes."""
        def _run():
            self._play(700, 100)
            self._play(950, 130)
        threading.Thread(target=_run, daemon=True).start()

    def lens_off(self):
        """Lupa desativada: dois tons graves descendentes."""
        def _run():
            self._play(950, 100)
            self._play(600, 130)
        threading.Thread(target=_run, daemon=True).start()

    def filter_change(self):
        """Alternância de filtro cromático: tom médio distintivo."""
        self.play_async(850, 120)

    def zoom_in(self):
        """Zoom aumentado: tom agudo breve."""
        self.play_async(1200, 70)

    def zoom_out(self):
        """Zoom reduzido: tom mais grave breve."""
        self.play_async(500, 70)

    def tts_start(self):
        """Leitura TTS iniciada: melodia breve de início."""
        def _run():
            self._play(660, 90)
            self._play(880, 120)
        threading.Thread(target=_run, daemon=True).start()

    def tts_stop(self):
        """Leitura TTS interrompida: bipe grave curto de pausa."""
        self.play_async(400, 110)

    def alert_no_text(self):
        """Alerta de nenhum texto selecionado."""
        def _run():
            self._play(440, 120)
            self._play(330, 180)
        threading.Thread(target=_run, daemon=True).start()


# Instância global para reuso
sounds = SoundEffects()
