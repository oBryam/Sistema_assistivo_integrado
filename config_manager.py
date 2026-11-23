"""
Módulo de Persistência de Configurações do Estudante (config.json).
Permite salvar e carregar automaticamente as preferências personalizadas:
- Escala e tamanho da lupa
- Modo de exibição da lupa (Flutuante vs Ancorado)
- Régua de leitura ativa
- Movimento suave ativado
- Modo de contraste para fotofobia
- Velocidade da voz (TTS)
- Audiodescrição operacional das ações
"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "magnifier_scale": 2.0,
    "magnifier_preset": "Grande",
    "magnifier_docked": False,
    "magnifier_dock_position": "Topo",  # "Topo" ou "Base"
    "reading_guide": True,
    "smooth_movement": True,
    "contrast_mode": 0,
    "tts_rate": 1,
    "audiodescription": True,
    "theme": "dark"
}


class ConfigManager:
    def __init__(self):
        self.config = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """Carrega preferências do arquivo config.json se existir."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"[Config Load Error]: {e}")

    def save(self):
        """Salva as preferências atuais no arquivo config.json."""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config Save Error]: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()


# Instância global
cfg = ConfigManager()
