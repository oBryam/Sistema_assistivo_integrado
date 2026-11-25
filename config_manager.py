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
- Tamanho de fonte da interface
- Atalhos personalizados
"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_SHORTCUTS = {
    "toggle_magnifier": "ctrl+alt+l",
    "zoom_in": "ctrl+plus",
    "zoom_in_alt": "ctrl+=",
    "zoom_out": "ctrl+-",
    "next_contrast": "ctrl+alt+i",
    "read_selection": "ctrl+alt+r",
    "toggle_pause": "ctrl+alt+space",
    "stop_speech": "ctrl+alt+p",
    "ocr_selection": "ctrl+alt+o",
}

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
    "theme": "dark",
    "font_size": 10,         # Tamanho base de fonte da interface (8-24)
    "shortcuts": dict(DEFAULT_SHORTCUTS),
}


class ConfigManager:
    def __init__(self):
        self.config = dict(DEFAULT_CONFIG)
        # Deep-copy do dicionário de atalhos para evitar mutação
        self.config["shortcuts"] = dict(DEFAULT_SHORTCUTS)
        self.load()

    def load(self):
        """Carrega preferências do arquivo config.json se existir."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
                    # Garante que atalhos faltantes tenham valor padrão
                    if "shortcuts" in self.config and isinstance(self.config["shortcuts"], dict):
                        merged = dict(DEFAULT_SHORTCUTS)
                        merged.update(self.config["shortcuts"])
                        self.config["shortcuts"] = merged
                    else:
                        self.config["shortcuts"] = dict(DEFAULT_SHORTCUTS)
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

    def get_shortcut(self, action: str) -> str:
        """Retorna o atalho configurado para uma ação específica."""
        shortcuts = self.config.get("shortcuts", DEFAULT_SHORTCUTS)
        return shortcuts.get(action, DEFAULT_SHORTCUTS.get(action, ""))

    def set_shortcut(self, action: str, hotkey: str):
        """Define um novo atalho para uma ação e salva."""
        if "shortcuts" not in self.config or not isinstance(self.config["shortcuts"], dict):
            self.config["shortcuts"] = dict(DEFAULT_SHORTCUTS)
        self.config["shortcuts"][action] = hotkey.lower().strip()
        self.save()

    def get_shortcuts_dict(self) -> dict:
        """Retorna uma cópia do dicionário completo de atalhos."""
        return dict(self.config.get("shortcuts", DEFAULT_SHORTCUTS))

    def reset_shortcuts(self):
        """Restaura os atalhos padrão."""
        self.config["shortcuts"] = dict(DEFAULT_SHORTCUTS)
        self.save()


# Instância global
cfg = ConfigManager()
