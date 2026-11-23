"""
Testes automatizados atualizados v0.2.1:
1. Persistência de Configurações (config_manager)
2. OCR Instantâneo com Seleção de Área (ocr_engine e snipper)
3. Lupa Dinâmica com Ancoragem, Régua Guia e Movimento Amortecido (magnifier)
4. Adaptação Cromática Global com 5 Modos de Contraste (contrast_manager)
5. Síntese de Voz (TTS) com Pausa/Retomada e Audiodescrição Blindada (tts_engine)
6. Efeitos Sonoros de Confirmação (sound_effects)
"""

import unittest
import tkinter as tk
from config_manager import cfg
from contrast_manager import contrast_manager
from magnifier import DynamicMagnifier
from ocr_engine import ocr_engine
from snipper import ScreenSnipper
from sound_effects import sounds
from tts_engine import TTSEngine


class TestAssistiveAppV021(unittest.TestCase):
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

    def test_01_config_persistence(self):
        cfg.set("test_key", "valor_teste")
        self.assertEqual(cfg.get("test_key"), "valor_teste")

    def test_02_ocr_and_snipper_ready(self):
        self.assertIsNotNone(ocr_engine)
        snipper = ScreenSnipper(self.root, on_area_selected=lambda l, t, w, h: None)
        self.assertIsNotNone(snipper)

    def test_03_magnifier_advanced_features(self):
        mag = DynamicMagnifier(self.root)
        self.assertEqual(mag.current_preset, "Grande")

        # Régua Guia
        initial_guide = mag.reading_guide
        mag.toggle_reading_guide()
        self.assertNotEqual(mag.reading_guide, initial_guide)

        # Movimento Suave
        initial_smooth = mag.smooth_movement
        mag.toggle_smooth_movement()
        self.assertNotEqual(mag.smooth_movement, initial_smooth)

        # Ancoragem
        initial_dock = mag.is_docked
        mag.toggle_docked()
        self.assertNotEqual(mag.is_docked, initial_dock)

        # Zoom
        mag.zoom_in()
        self.assertGreaterEqual(mag.scale, 2.0)
        mag.zoom_out()
        self.assertGreaterEqual(mag.scale, 1.5)

    def test_04_contrast_manager_5_modes(self):
        cm = contrast_manager
        self.assertEqual(len(cm.MODES), 5)
        for i, name in enumerate(["Normal", "Invertido", "Preto/Amarelo", "Âmbar (Anti-Luz Azul)", "Escala de Cinza"]):
            cm.set_mode(i)
            self.assertEqual(cm.get_current_mode_name(), name)
        cm.set_mode(0)

    def test_05_tts_pause_resume_stop(self):
        tts = TTSEngine()
        tts.set_rate(2)
        self.assertEqual(tts.rate, 2)
        tts._is_speaking = True
        tts.pause()
        self.assertTrue(tts.is_paused())
        tts.resume()
        self.assertFalse(tts.is_paused())
        tts.stop(silent=True)
        self.assertTrue(tts._stop_requested)

    def test_06_sound_effects(self):
        sounds.startup()
        sounds.lens_on()
        sounds.lens_off()
        sounds.filter_change()
        sounds.zoom_in()
        sounds.zoom_out()
        sounds.tts_start()
        sounds.tts_stop()
        sounds.alert_no_text()


if __name__ == "__main__":
    unittest.main()
