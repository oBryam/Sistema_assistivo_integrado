"""
Módulo da Interface Gráfica Principal (GUI) de Alto Contraste.
Eixo 1: Painel Principal de Alto Contraste
- Total independência entre a Lupa, a Adaptação Cromática e a Síntese de Voz (TTS).
- Lupa com área ampla configurável (Média 520x380, Grande 700x500, Panorâmica 900x560).
- Contraste para fotofobia global (tela inteira).
- TTS resiliente com leitura de seleção, área de transferência e caixa de texto direta.
"""

import tkinter as tk
from tkinter import ttk
import pyperclip
from contrast_manager import contrast_manager
from magnifier import DynamicMagnifier
from shortcuts import GlobalShortcutManager
from sound_effects import sounds
from tts_engine import TTSEngine


APP_NAME = "Sistema Assistivo Integrado"
APP_VERSION = "0.1"
APP_FULL_TITLE = f"{APP_NAME} v{APP_VERSION}"


class HighContrastApp:
    BG_DARK = "#0A0A0A"
    BG_CARD = "#161616"
    COLOR_YELLOW = "#FFE600"
    COLOR_WHITE = "#FFFFFF"
    COLOR_GREEN = "#00E676"
    COLOR_RED = "#FF3333"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_FULL_TITLE)
        self.root.configure(bg=self.BG_DARK)
        self.root.geometry("540x820")
        self.root.resizable(True, True)

        # 1. Eixo 4: TTS Independente
        self.tts = TTSEngine(on_status_change=self._on_tts_status_change)

        # 2. Eixo 2: Lupa Dinâmica Independente com Área Ampla
        self.magnifier = DynamicMagnifier(self.root, on_update_callback=self._update_magnifier_ui)

        # 3. Eixo 3: Contraste para Fotofobia Independente (Global)
        self.contrast = contrast_manager
        self.contrast.on_change_callback = self._on_contrast_changed

        # 4. Atalhos Globais Integrados
        self.shortcuts = GlobalShortcutManager(
            self.root,
            self.magnifier,
            self.tts,
            self.contrast,
            on_text_captured=self._on_external_text_captured
        )
        self.shortcuts.start()

        # Constrói a interface visual de alto contraste
        self._build_ui()

        # Bipes de boas-vindas
        sounds.startup()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Canvas com Scrollbar para garantir usabilidade em qualquer resolução
        main_canvas = tk.Canvas(self.root, bg=self.BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.BG_DARK, padx=14, pady=10)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=515)
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Cabeçalho
        header_frame = tk.Frame(scrollable_frame, bg=self.BG_DARK)
        header_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            header_frame,
            text=f"{APP_NAME.upper()} v{APP_VERSION}",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_DARK,
            fg=self.COLOR_YELLOW
        ).pack(anchor="w")

        tk.Label(
            header_frame,
            text="Acessibilidade Visual, Fotofobia e Apoio Pedagógico",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_DARK,
            fg=self.COLOR_WHITE
        ).pack(anchor="w")

        tk.Frame(scrollable_frame, bg=self.COLOR_YELLOW, height=2).pack(fill=tk.X, pady=(4, 10))

        # =============================================================
        # SEÇÃO 1: LUPA DINÂMICA DE ÁREA AMPLA (EIXO 2)
        # =============================================================
        lupa_box = tk.LabelFrame(
            scrollable_frame,
            text=" 🔍 1. LUPA DINÂMICA (ÁREA AMPLA) ",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_CARD,
            fg=self.COLOR_YELLOW,
            bd=2,
            relief="solid",
            padx=10,
            pady=8
        )
        lupa_box.pack(fill=tk.X, pady=5)

        self.btn_lupa = tk.Button(
            lupa_box,
            text="LIGAR LUPA VIRTUAL (Ctrl + Alt + L)",
            font=("Segoe UI", 12, "bold"),
            bg="#2B2B2B",
            fg=self.COLOR_YELLOW,
            activebackground=self.COLOR_YELLOW,
            activeforeground="#000000",
            bd=2,
            cursor="hand2",
            command=self.magnifier.toggle,
            pady=6
        )
        self.btn_lupa.pack(fill=tk.X, pady=(0, 8))

        # Controles de Zoom
        zoom_row = tk.Frame(lupa_box, bg=self.BG_CARD)
        zoom_row.pack(fill=tk.X, pady=2)

        tk.Label(
            zoom_row,
            text="Nível de Zoom:",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_CARD,
            fg=self.COLOR_WHITE
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            zoom_row,
            text="－ (Ctrl -)",
            font=("Segoe UI", 10, "bold"),
            bg="#333333",
            fg=self.COLOR_WHITE,
            width=9,
            cursor="hand2",
            command=self.magnifier.zoom_out
        ).pack(side=tk.LEFT, padx=3)

        self.lbl_scale = tk.Label(
            zoom_row,
            text="2.0x",
            font=("Segoe UI", 12, "bold"),
            bg="#000000",
            fg=self.COLOR_YELLOW,
            width=6,
            bd=1,
            relief="solid"
        )
        self.lbl_scale.pack(side=tk.LEFT, padx=4)

        tk.Button(
            zoom_row,
            text="＋ (Ctrl +)",
            font=("Segoe UI", 10, "bold"),
            bg="#333333",
            fg=self.COLOR_WHITE,
            width=9,
            cursor="hand2",
            command=self.magnifier.zoom_in
        ).pack(side=tk.LEFT, padx=3)

        # Seletor de Tamanho da Lente (Área Ampla)
        size_row = tk.Frame(lupa_box, bg=self.BG_CARD)
        size_row.pack(fill=tk.X, pady=(8, 2))

        tk.Label(
            size_row,
            text="Área da Lente:",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_CARD,
            fg=self.COLOR_WHITE
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.btn_size_m = tk.Button(
            size_row,
            text="Média (520x380)",
            font=("Segoe UI", 9, "bold"),
            bg="#333333",
            fg=self.COLOR_WHITE,
            cursor="hand2",
            command=lambda: self._select_preset("Média")
        )
        self.btn_size_m.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.btn_size_g = tk.Button(
            size_row,
            text="Grande (700x500)",
            font=("Segoe UI", 9, "bold"),
            bg=self.COLOR_YELLOW,
            fg="#000000",
            cursor="hand2",
            command=lambda: self._select_preset("Grande")
        )
        self.btn_size_g.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.btn_size_p = tk.Button(
            size_row,
            text="Panorâmica (900x560)",
            font=("Segoe UI", 9, "bold"),
            bg="#333333",
            fg=self.COLOR_WHITE,
            cursor="hand2",
            command=lambda: self._select_preset("Panorâmica")
        )
        self.btn_size_p.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # =============================================================
        # SEÇÃO 2: CONTRASTE GLOBAL PARA FOTOFOBIA (EIXO 3)
        # =============================================================
        filter_box = tk.LabelFrame(
            scrollable_frame,
            text=" 🎨 2. CONTRASTE GLOBAL PARA FOTOFOBIA (TELA INTEIRA) ",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_CARD,
            fg=self.COLOR_YELLOW,
            bd=2,
            relief="solid",
            padx=10,
            pady=8
        )
        filter_box.pack(fill=tk.X, pady=6)

        filter_btn_row = tk.Frame(filter_box, bg=self.BG_CARD)
        filter_btn_row.pack(fill=tk.X, pady=(0, 6))

        self.btn_cf_normal = tk.Button(
            filter_btn_row,
            text="Normal",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_YELLOW,
            fg="#000000",
            cursor="hand2",
            command=lambda: self.contrast.set_mode(0)
        )
        self.btn_cf_normal.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.btn_cf_invert = tk.Button(
            filter_btn_row,
            text="Invertido (Anti-Brilho)",
            font=("Segoe UI", 10, "bold"),
            bg="#333333",
            fg=self.COLOR_WHITE,
            cursor="hand2",
            command=lambda: self.contrast.set_mode(1)
        )
        self.btn_cf_invert.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.btn_cf_by = tk.Button(
            filter_btn_row,
            text="Preto / Amarelo",
            font=("Segoe UI", 10, "bold"),
            bg="#333333",
            fg=self.COLOR_WHITE,
            cursor="hand2",
            command=lambda: self.contrast.set_mode(2)
        )
        self.btn_cf_by.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.lbl_contrast_desc = tk.Label(
            filter_box,
            text="Modo Atual: Normal (Pressione Ctrl + Alt + I para alternar em toda a tela)",
            font=("Segoe UI", 9, "bold"),
            bg=self.BG_CARD,
            fg=self.COLOR_YELLOW,
            wraplength=480,
            justify=tk.LEFT
        )
        self.lbl_contrast_desc.pack(anchor="w")

        # =============================================================
        # SEÇÃO 3: LEITURA AUDITIVA DE TEXTOS (TTS) (EIXO 4)
        # =============================================================
        tts_box = tk.LabelFrame(
            scrollable_frame,
            text=" 🔊 3. SÍNTESE DE VOZ - TTS (INDEPENDENTE) ",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_CARD,
            fg=self.COLOR_YELLOW,
            bd=2,
            relief="solid",
            padx=10,
            pady=8
        )
        tts_box.pack(fill=tk.X, pady=6)

        tts_actions_row = tk.Frame(tts_box, bg=self.BG_CARD)
        tts_actions_row.pack(fill=tk.X, pady=(0, 6))

        btn_read_sel = tk.Button(
            tts_actions_row,
            text="▶ LER SELEÇÃO (Ctrl+Alt+R)",
            font=("Segoe UI", 11, "bold"),
            bg="#1B5E20",
            fg=self.COLOR_WHITE,
            activebackground="#2E7D32",
            activeforeground=self.COLOR_WHITE,
            cursor="hand2",
            command=self.shortcuts.trigger_read_selection,
            pady=4
        )
        btn_read_sel.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))

        btn_read_clip = tk.Button(
            tts_actions_row,
            text="📋 COLAR E LER",
            font=("Segoe UI", 11, "bold"),
            bg="#0D47A1",
            fg=self.COLOR_WHITE,
            activebackground="#1565C0",
            activeforeground=self.COLOR_WHITE,
            cursor="hand2",
            command=self._read_clipboard_direct,
            pady=4
        )
        btn_read_clip.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        self.btn_stop = tk.Button(
            tts_actions_row,
            text="⏹ PARAR (Ctrl+Alt+P)",
            font=("Segoe UI", 11, "bold"),
            bg="#B71C1C",
            fg=self.COLOR_WHITE,
            activebackground="#C62828",
            activeforeground=self.COLOR_WHITE,
            cursor="hand2",
            command=self.tts.stop,
            pady=4
        )
        self.btn_stop.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(3, 0))

        # Área de Texto / Visualização e Digitação Direta
        tk.Label(
            tts_box,
            text="Texto a vocalizar (capturado automaticamente ou editável):",
            font=("Segoe UI", 9, "bold"),
            bg=self.BG_CARD,
            fg=self.COLOR_WHITE
        ).pack(anchor="w", pady=(4, 2))

        self.txt_preview = tk.Text(
            tts_box,
            height=4,
            bg="#000000",
            fg=self.COLOR_YELLOW,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            wrap="word",
            insertbackground=self.COLOR_YELLOW
        )
        self.txt_preview.pack(fill=tk.X, pady=(0, 6))
        self.txt_preview.insert(
            "1.0",
            "Selecione um texto em qualquer aplicativo e pressione Ctrl+Alt+R, ou digite/cole seu texto aqui e clique em Ler."
        )

        txt_controls = tk.Frame(tts_box, bg=self.BG_CARD)
        txt_controls.pack(fill=tk.X, pady=(0, 6))

        tk.Button(
            txt_controls,
            text="▶ Ler Texto da Caixa Acima",
            font=("Segoe UI", 10, "bold"),
            bg="#333333",
            fg=self.COLOR_YELLOW,
            cursor="hand2",
            command=self._read_from_text_box
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            txt_controls,
            text="Limpar Caixa",
            font=("Segoe UI", 9),
            bg="#222222",
            fg=self.COLOR_WHITE,
            cursor="hand2",
            command=lambda: self.txt_preview.delete("1.0", tk.END)
        ).pack(side=tk.LEFT)

        # Velocidade da Voz
        speed_row = tk.Frame(tts_box, bg=self.BG_CARD)
        speed_row.pack(fill=tk.X, pady=(4, 4))

        tk.Label(
            speed_row,
            text="Velocidade da Voz:",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_CARD,
            fg=self.COLOR_WHITE
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.speed_slider = tk.Scale(
            speed_row,
            from_=-4,
            to=6,
            orient=tk.HORIZONTAL,
            showvalue=False,
            bg=self.BG_CARD,
            troughcolor="#000000",
            activebackground=self.COLOR_YELLOW,
            highlightthickness=0,
            command=self._on_speed_changed
        )
        self.speed_slider.set(self.tts.rate)
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        self.lbl_speed_val = tk.Label(
            speed_row,
            text="Normal (+1)",
            font=("Segoe UI", 10, "bold"),
            bg="#000000",
            fg=self.COLOR_YELLOW,
            width=11,
            bd=1,
            relief="solid"
        )
        self.lbl_speed_val.pack(side=tk.RIGHT, padx=(4, 0))

        # Status TTS
        self.lbl_tts_status = tk.Label(
            tts_box,
            text="● Voz Pronta: Microsoft Maria (pt-BR)",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_CARD,
            fg=self.COLOR_GREEN
        )
        self.lbl_tts_status.pack(anchor="w", pady=(2, 0))

        # =============================================================
        # SEÇÃO 4: RESUMO DE ATALHOS GLOBAIS
        # =============================================================
        guide_box = tk.LabelFrame(
            scrollable_frame,
            text=" ⌨ ATALHOS GLOBAIS (FUNCIONAM EM QUALQUER APLICATIVO) ",
            font=("Segoe UI", 10, "bold"),
            bg="#111111",
            fg=self.COLOR_WHITE,
            bd=1,
            relief="solid",
            padx=8,
            pady=6
        )
        guide_box.pack(fill=tk.X, pady=(6, 0))

        shortcuts_guide = (
            "• Ctrl + Alt + L  : Liga / Desliga a Lupa Dinâmica\n"
            "• Ctrl + + / -    : Aumenta / Diminui o Zoom (ou Roda do Mouse)\n"
            "• Ctrl + Alt + I  : Alterna Contraste Global de Toda a Tela\n"
            "• Ctrl + Alt + R  : Vocaliza o Texto Selecionado na Tela\n"
            "• Ctrl + Alt + P  : Interrompe Imediatamente a Leitura"
        )
        tk.Label(
            guide_box,
            text=shortcuts_guide,
            font=("Consolas", 9, "bold"),
            bg="#111111",
            fg=self.COLOR_YELLOW,
            justify=tk.LEFT
        ).pack(anchor="w")

        self._update_magnifier_ui()

    def _select_preset(self, preset_name: str):
        self.magnifier.set_size_preset(preset_name)
        self.btn_size_m.config(
            bg=self.COLOR_YELLOW if preset_name == "Média" else "#333333",
            fg="#000000" if preset_name == "Média" else self.COLOR_WHITE
        )
        self.btn_size_g.config(
            bg=self.COLOR_YELLOW if preset_name == "Grande" else "#333333",
            fg="#000000" if preset_name == "Grande" else self.COLOR_WHITE
        )
        self.btn_size_p.config(
            bg=self.COLOR_YELLOW if preset_name == "Panorâmica" else "#333333",
            fg="#000000" if preset_name == "Panorâmica" else self.COLOR_WHITE
        )

    def _update_magnifier_ui(self):
        if self.magnifier.is_active:
            self.btn_lupa.config(
                text="✔ LUPA ATIVA (Ctrl + Alt + L)",
                bg=self.COLOR_YELLOW,
                fg="#000000"
            )
        else:
            self.btn_lupa.config(
                text="🔍 LIGAR LUPA VIRTUAL (Ctrl + Alt + L)",
                bg="#2B2B2B",
                fg=self.COLOR_YELLOW
            )
        self.lbl_scale.config(text=f"{self.magnifier.scale:.1f}x")

    def _on_contrast_changed(self, mode_idx: int, mode_name: str):
        self.btn_cf_normal.config(
            bg=self.COLOR_YELLOW if mode_idx == 0 else "#333333",
            fg="#000000" if mode_idx == 0 else self.COLOR_WHITE
        )
        self.btn_cf_invert.config(
            bg=self.COLOR_YELLOW if mode_idx == 1 else "#333333",
            fg="#000000" if mode_idx == 1 else self.COLOR_WHITE
        )
        self.btn_cf_by.config(
            bg=self.COLOR_YELLOW if mode_idx == 2 else "#333333",
            fg="#000000" if mode_idx == 2 else self.COLOR_WHITE
        )
        self.lbl_contrast_desc.config(
            text=f"Modo Atual: {mode_name} (Ativo em todo o Windows. Alternar via Ctrl + Alt + I)"
        )

    def _on_speed_changed(self, val):
        rate = int(float(val))
        self.tts.set_rate(rate)
        if rate < 0:
            desc = f"Lenta ({rate})"
        elif rate in (0, 1):
            desc = f"Normal ({rate})"
        else:
            desc = f"Rápida (+{rate})"
        self.lbl_speed_val.config(text=desc)

    def _on_external_text_captured(self, text: str):
        """Atualiza a caixa de texto quando um texto é capturado via Ctrl+Alt+R."""
        self.txt_preview.delete("1.0", tk.END)
        self.txt_preview.insert("1.0", text)

    def _read_from_text_box(self):
        text = self.txt_preview.get("1.0", tk.END).strip()
        if text:
            self.tts.speak(text)
        else:
            sounds.alert_no_text()

    def _read_clipboard_direct(self):
        try:
            text = pyperclip.paste().strip()
            if text:
                self.txt_preview.delete("1.0", tk.END)
                self.txt_preview.insert("1.0", text)
                self.tts.speak(text)
            else:
                sounds.alert_no_text()
        except Exception:
            sounds.alert_no_text()

    def _on_tts_status_change(self, is_speaking: bool):
        def _update():
            if is_speaking:
                self.lbl_tts_status.config(
                    text="🔊 Lendo texto selecionado...",
                    fg=self.COLOR_YELLOW
                )
            else:
                self.lbl_tts_status.config(
                    text="● Voz Pronta: Microsoft Maria (pt-BR)",
                    fg=self.COLOR_GREEN
                )
        self.root.after_idle(_update)

    def _on_close(self):
        self.shortcuts.stop()
        self.tts.stop(silent=True)
        self.magnifier.stop()
        self.contrast.reset_to_normal()
        self.root.destroy()
