"""
Testes automatizados atualizados para validação da independência dos módulos:
- Lupa Dinâmica de Área Ampla (Presets Média, Grande, Panorâmica)
- Contraste Global de Tela Inteira para Fotofobia (Normal, Invertido, Preto/Amarelo)
- Síntese de Voz (TTS) resiliente em Língua Portuguesa
- Confirmações Sonoras de Acessibilidade
"""

import unittest
import tkinter as tk
from contrast_manager import contrast_manager
from magnifier import DynamicMagnifier
from sound_effects import sounds
from tts_engine import TTSEngine


class TestAssistiveAppUpdated(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            contrast_manager.reset_to_normal()
            cls.root.destroy()
        except Exception:
            pass

    def test_eixo_1_sound_effects(self):
        """Valida que todos os efeitos sonoros funcionam assincronamente."""
        sounds.startup()
        sounds.lens_on()
        sounds.lens_off()
        sounds.filter_change()
        sounds.zoom_in()
        sounds.zoom_out()
        sounds.tts_start()
        sounds.tts_stop()
        sounds.alert_no_text()

    def test_eixo_2_magnifier_large_area_presets(self):
        """Valida a ampliação da área da lupa e presets de tamanho."""
        mag = DynamicMagnifier(self.root)
        self.assertEqual(mag.current_preset, "Grande")
        self.assertEqual((mag.win_width, mag.win_height), (700, 500))

        # Testa troca para preset Média
        mag.set_size_preset("Média")
        self.assertEqual((mag.win_width, mag.win_height), (520, 380))

        # Testa troca para preset Panorâmica
        mag.set_size_preset("Panorâmica")
        self.assertEqual((mag.win_width, mag.win_height), (900, 560))

        # Testa limites de zoom (1.5x a 6.0x)
        for _ in range(12):
            mag.zoom_in()
        self.assertEqual(mag.scale, 6.0)

        for _ in range(15):
            mag.zoom_out()
        self.assertEqual(mag.scale, 1.5)

    def test_eixo_3_global_contrast_independence(self):
        """Valida que o contraste global para fotofobia opera independentemente da lupa."""
        cm = contrast_manager
        cm.set_mode(0)
        self.assertEqual(cm.get_current_mode_name(), "Normal")

        # Invertido
        cm.next_mode()
        self.assertEqual(cm.get_current_mode_name(), "Invertido")

        # Preto e Amarelo
        cm.next_mode()
        self.assertEqual(cm.get_current_mode_name(), "Preto/Amarelo")

        # Retorna para Normal
        cm.set_mode(0)
        self.assertEqual(cm.get_current_mode_name(), "Normal")

    def test_eixo_4_tts_engine_resilience(self):
        """Valida os controles do motor TTS."""
        tts = TTSEngine()
        tts.set_rate(3)
        self.assertEqual(tts.rate, 3)

        # Limites seguros de velocidade
        tts.set_rate(15)
        self.assertEqual(tts.rate, 8)
        tts.set_rate(-15)
        self.assertEqual(tts.rate, -5)

        # Interrupção imediata
        tts.stop(silent=True)
        self.assertTrue(tts._stop_requested)


if __name__ == "__main__":
    unittest.main()
