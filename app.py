"""
Módulo da Interface Gráfica Principal (GUI) Refinada e Despoluída.
Sistema Assistivo Integrado v0.3
- Design moderno, limpo e sem poluição visual
- Suporte completo a Modo Escuro (Dark) e Modo Claro (Light) com alternância dinâmica
- Lupa Dinâmica, Contraste de Tela, Síntese de Voz (TTS) e OCR com Seleção de Área
- Engrenagem de Configurações (Ajuste de Fonte e Atalhos Personalizáveis)
- Fonte ajustável em toda a interface (acessibilidade para baixa visão)
"""

import tkinter as tk
from tkinter import messagebox
from config_manager import cfg
from contrast_manager import contrast_manager
from magnifier import DynamicMagnifier
from ocr_engine import ocr_engine
from shortcuts import GlobalShortcutManager, SHORTCUT_LABELS
from snipper import ScreenSnipper
from sound_effects import sounds
from tts_engine import TTSEngine

APP_NAME = "Sistema Assistivo Integrado"
APP_VERSION = "0.3"
APP_FULL_TITLE = f"{APP_NAME} v{APP_VERSION}"

THEMES = {
    "dark": {
        "bg": "#121212",
        "card_bg": "#1E1E1E",
        "border": "#333333",
        "text_primary": "#FFFFFF",
        "text_accent": "#FFE600",
        "text_muted": "#A0A0A0",
        "btn_default_bg": "#2B2B2B",
        "btn_default_fg": "#FFFFFF",
        "btn_active_bg": "#FFE600",
        "btn_active_fg": "#000000",
        "btn_read_bg": "#1B5E20",
        "btn_read_fg": "#FFFFFF",
        "btn_ocr_bg": "#E65100",
        "btn_ocr_fg": "#FFFFFF",
        "btn_stop_bg": "#B71C1C",
        "btn_stop_fg": "#FFFFFF",
        "btn_pause_bg": "#0D47A1",
        "btn_pause_fg": "#FFFFFF",
        "input_bg": "#0B0B0B",
        "input_fg": "#FFE600",
        "highlight_bg": "#FFE600",
        "highlight_fg": "#000000",
        "status_green": "#00E676"
    },
    "light": {
        "bg": "#F5F6F8",
        "card_bg": "#FFFFFF",
        "border": "#D8DEE4",
        "text_primary": "#1A1A1A",
        "text_accent": "#0969DA",
        "text_muted": "#57606A",
        "btn_default_bg": "#EAEFF4",
        "btn_default_fg": "#1F2328",
        "btn_active_bg": "#0969DA",
        "btn_active_fg": "#FFFFFF",
        "btn_read_bg": "#2DA44E",
        "btn_read_fg": "#FFFFFF",
        "btn_ocr_bg": "#D97706",
        "btn_ocr_fg": "#FFFFFF",
        "btn_stop_bg": "#CF222E",
        "btn_stop_fg": "#FFFFFF",
        "btn_pause_bg": "#0969DA",
        "btn_pause_fg": "#FFFFFF",
        "input_bg": "#F8FAFC",
        "input_fg": "#0F172A",
        "highlight_bg": "#FEF08A",
        "highlight_fg": "#000000",
        "status_green": "#16A34A"
    }
}

# Limites do tamanho de fonte
FONT_MIN = 8
FONT_MAX = 24


class HighContrastApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_FULL_TITLE)
        self.root.geometry("520x700")
        self.root.resizable(False, False)

        # Captura de exceções global para segurança
        self.root.report_callback_exception = lambda t, v, tb: print(f"[Safe GUI]: {t.__name__}: {v}")

        # Tema atual: "dark" ou "light"
        self.current_theme = cfg.get("theme", "dark")
        self.colors = THEMES.get(self.current_theme, THEMES["dark"])
        self.root.configure(bg=self.colors["bg"])

        # Tamanho de fonte base (configurável pelo usuário)
        self.font_size = int(cfg.get("font_size", 10))

        # 1. TTS com Karaokê
        self.tts = TTSEngine(
            on_status_change=self._on_tts_status_change,
            on_sentence_change=self._on_sentence_highlight
        )

        # 2. Lupa Dinâmica
        self.magnifier = DynamicMagnifier(self.root, on_update_callback=self._update_magnifier_ui)

        # 3. Contraste de Tela para Fotofobia
        self.contrast = contrast_manager
        self.contrast.on_change_callback = self._on_contrast_changed
        initial_contrast = int(cfg.get("contrast_mode", 0))
        if initial_contrast != 0:
            self.contrast.set_mode(initial_contrast)

        # 4. Snipper de OCR integrado com pausa de segurança na lupa
        self.snipper = ScreenSnipper(
            self.root,
            on_area_selected=self._on_ocr_area_selected,
            on_close_callback=lambda: self.magnifier.resume_capture()
        )

        # 5. Atalhos Globais (personalizáveis)
        self.shortcuts = GlobalShortcutManager(
            self.root,
            self.magnifier,
            self.tts,
            self.contrast,
            self.snipper,
            on_text_captured=self._on_external_text_captured
        )
        self.shortcuts.start()

        # Referência à janela de configurações
        self._settings_window = None

        self._build_ui()
        sounds.startup()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # =========================================================
    # Helpers de fonte escalável
    # =========================================================
    def _font(self, delta: int = 0, bold: bool = False) -> tuple:
        """Retorna tupla de fonte com tamanho relativo ao base."""
        style = "bold" if bold else "normal"
        return ("Segoe UI", max(FONT_MIN, self.font_size + delta), style)

    def _on_ocr_area_selected(self, left: int, top: int, width: int, height: int):
        self.shortcuts.handle_snipped_area(left, top, width, height)

    def _toggle_theme(self):
        """Alterna dinamicamente entre Modo Escuro e Modo Claro."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        cfg.set("theme", self.current_theme)
        self.colors = THEMES[self.current_theme]
        self._apply_theme()

    # =========================================================
    # Construção da Interface
    # =========================================================
    def _build_ui(self):
        c = self.colors
        self.container = tk.Frame(self.root, bg=c["bg"], padx=14, pady=10)
        self.container.pack(fill=tk.BOTH, expand=True)

        # -------------------------------------------------------------
        # CABEÇALHO COMPACTO (sem botão minimizar, com engrenagem)
        # -------------------------------------------------------------
        header = tk.Frame(self.container, bg=c["bg"])
        header.pack(fill=tk.X, pady=(0, 8))

        self.lbl_title = tk.Label(
            header,
            text=f"{APP_NAME} v{APP_VERSION}",
            font=self._font(3, bold=True),
            bg=c["bg"],
            fg=c["text_accent"]
        )
        self.lbl_title.pack(side=tk.LEFT)

        controls_right = tk.Frame(header, bg=c["bg"])
        controls_right.pack(side=tk.RIGHT)

        # Botão engrenagem de configurações
        self.btn_settings = tk.Button(
            controls_right,
            text="⚙",
            font=self._font(4, bold=True),
            bg=c["btn_default_bg"],
            fg=c["text_primary"],
            bd=1,
            cursor="hand2",
            padx=6,
            command=self._open_settings
        )
        self.btn_settings.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_theme = tk.Button(
            controls_right,
            text="☀️ Claro" if self.current_theme == "dark" else "🌙 Escuro",
            font=self._font(-1, bold=True),
            bg=c["btn_default_bg"],
            fg=c["btn_default_fg"],
            bd=1,
            cursor="hand2",
            padx=8,
            command=self._toggle_theme
        )
        self.btn_theme.pack(side=tk.LEFT, padx=(0, 4))

        # -------------------------------------------------------------
        # 1. CARD: LUPA DINÂMICA
        # -------------------------------------------------------------
        sc = cfg.get_shortcuts_dict()
        lupa_shortcut = sc.get("toggle_magnifier", "ctrl+alt+l").title()

        self.card_lupa = tk.LabelFrame(
            self.container,
            text=" Lupa Dinâmica ",
            font=self._font(0, bold=True),
            bg=c["card_bg"],
            fg=c["text_accent"],
            bd=1,
            relief="solid",
            padx=10,
            pady=6
        )
        self.card_lupa.pack(fill=tk.X, pady=(0, 6))

        # Linha 1: Botão Liga/Desliga e Zoom
        row1 = tk.Frame(self.card_lupa, bg=c["card_bg"])
        row1.pack(fill=tk.X, pady=(0, 4))

        self.btn_lupa = tk.Button(
            row1,
            text=f"🔍 Ativar Lupa ({lupa_shortcut})",
            font=self._font(0, bold=True),
            bg=c["btn_default_bg"],
            fg=c["text_primary"],
            bd=1,
            cursor="hand2",
            command=self.magnifier.toggle,
            pady=4
        )
        self.btn_lupa.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        tk.Button(row1, text="－", font=self._font(0, bold=True), bg=c["btn_default_bg"], fg=c["text_primary"], width=3, bd=1, cursor="hand2", command=self.magnifier.zoom_out).pack(side=tk.LEFT, padx=1)
        self.lbl_scale = tk.Label(row1, text=f"{self.magnifier.scale:.1f}x", font=self._font(0, bold=True), bg=c["bg"], fg=c["text_accent"], width=5, bd=1, relief="solid")
        self.lbl_scale.pack(side=tk.LEFT, padx=3)
        tk.Button(row1, text="＋", font=self._font(0, bold=True), bg=c["btn_default_bg"], fg=c["text_primary"], width=3, bd=1, cursor="hand2", command=self.magnifier.zoom_in).pack(side=tk.LEFT, padx=1)

        # Linha 2: Ferramentas da Lupa (Tamanho, Guia, Ancoragem)
        row2 = tk.Frame(self.card_lupa, bg=c["card_bg"])
        row2.pack(fill=tk.X, pady=(2, 0))

        self.btn_size_m = tk.Button(row2, text="Média", font=self._font(-2), bg=c["btn_default_bg"], fg=c["text_primary"], bd=1, cursor="hand2", command=lambda: self._select_preset("Média"))
        self.btn_size_m.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        self.btn_size_g = tk.Button(row2, text="Grande", font=self._font(-2, bold=True), bg=c["btn_active_bg"], fg=c["btn_active_fg"], bd=1, cursor="hand2", command=lambda: self._select_preset("Grande"))
        self.btn_size_g.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        self.btn_size_p = tk.Button(row2, text="Panorâmica", font=self._font(-2), bg=c["btn_default_bg"], fg=c["text_primary"], bd=1, cursor="hand2", command=lambda: self._select_preset("Panorâmica"))
        self.btn_size_p.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        self.btn_dock = tk.Button(
            row2,
            text="📌 Ancorar" if not self.magnifier.is_docked else "🔓 Flutuar",
            font=self._font(-2, bold=True),
            bg=c["btn_default_bg"],
            fg=c["text_primary"],
            bd=1,
            cursor="hand2",
            command=self._toggle_dock
        )
        self.btn_dock.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        self.btn_guide = tk.Button(
            row2,
            text="📏 Guia",
            font=self._font(-2, bold=True),
            bg=c["btn_active_bg"] if self.magnifier.reading_guide else c["btn_default_bg"],
            fg=c["btn_active_fg"] if self.magnifier.reading_guide else c["text_primary"],
            bd=1,
            cursor="hand2",
            command=self._toggle_guide
        )
        self.btn_guide.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # -------------------------------------------------------------
        # 2. CARD: CONTRASTE DE TELA (FOTOFOBIA)
        # -------------------------------------------------------------
        contrast_shortcut = sc.get("next_contrast", "ctrl+alt+i").title()

        self.card_contrast = tk.LabelFrame(
            self.container,
            text=f" Filtro de Contraste para Fotofobia ({contrast_shortcut}) ",
            font=self._font(0, bold=True),
            bg=c["card_bg"],
            fg=c["text_accent"],
            bd=1,
            relief="solid",
            padx=10,
            pady=6
        )
        self.card_contrast.pack(fill=tk.X, pady=(0, 6))

        row_cf = tk.Frame(self.card_contrast, bg=c["card_bg"])
        row_cf.pack(fill=tk.X)

        self.cf_btns = []
        labels = ["Normal", "Invertido", "Preto/Amarelo", "Âmbar", "Cinza"]
        for i, name in enumerate(labels):
            is_active = (self.contrast.mode_index == i)
            b = tk.Button(
                row_cf,
                text=name,
                font=self._font(-2, bold=is_active),
                bg=c["btn_active_bg"] if is_active else c["btn_default_bg"],
                fg=c["btn_active_fg"] if is_active else c["text_primary"],
                bd=1,
                cursor="hand2",
                command=lambda idx=i: self._select_contrast_mode(idx)
            )
            b.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
            self.cf_btns.append(b)

        # -------------------------------------------------------------
        # 3. CARD: LEITURA DE TEXTO (TTS & OCR)
        # -------------------------------------------------------------
        self.card_tts = tk.LabelFrame(
            self.container,
            text=" Síntese de Voz (TTS) & Leitura de Imagem (OCR) ",
            font=self._font(0, bold=True),
            bg=c["card_bg"],
            fg=c["text_accent"],
            bd=1,
            relief="solid",
            padx=10,
            pady=6
        )
        self.card_tts.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # Ações Rápidas
        read_shortcut = sc.get("read_selection", "ctrl+alt+r").title()
        ocr_shortcut = sc.get("ocr_selection", "ctrl+alt+o").title()

        row_acts = tk.Frame(self.card_tts, bg=c["card_bg"])
        row_acts.pack(fill=tk.X, pady=(0, 4))

        self.btn_read_sel = tk.Button(
            row_acts,
            text=f"▶ Ler Seleção ({read_shortcut})",
            font=self._font(-1, bold=True),
            bg=c["btn_read_bg"],
            fg=c["btn_read_fg"],
            bd=1,
            cursor="hand2",
            command=self.shortcuts.trigger_read_selection,
            pady=4
        )
        self.btn_read_sel.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))

        self.btn_ocr_sel = tk.Button(
            row_acts,
            text=f"📷 Ler Imagem OCR ({ocr_shortcut})",
            font=self._font(-1, bold=True),
            bg=c["btn_ocr_bg"],
            fg=c["btn_ocr_fg"],
            bd=1,
            cursor="hand2",
            command=self.shortcuts.trigger_ocr_selection,
            pady=4
        )
        self.btn_ocr_sel.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        self.btn_pause = tk.Button(
            row_acts,
            text="⏸",
            font=self._font(0, bold=True),
            bg=c["btn_pause_bg"],
            fg=c["btn_pause_fg"],
            width=3,
            bd=1,
            cursor="hand2",
            command=self.tts.toggle_pause
        )
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_stop = tk.Button(
            row_acts,
            text="⏹",
            font=self._font(0, bold=True),
            bg=c["btn_stop_bg"],
            fg=c["btn_stop_fg"],
            width=3,
            bd=1,
            cursor="hand2",
            command=self.tts.stop
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(2, 0))

        # Caixa de Texto com Karaokê
        self.txt_preview = tk.Text(
            self.card_tts,
            height=5,
            bg=c["input_bg"],
            fg=c["input_fg"],
            font=self._font(-1),
            bd=1,
            relief="solid",
            wrap="word",
            insertbackground=c["input_fg"]
        )
        self.txt_preview.pack(fill=tk.BOTH, expand=True, pady=4)
        self.txt_preview.tag_config("highlight", background=c["highlight_bg"], foreground=c["highlight_fg"])
        self.txt_preview.insert(
            "1.0",
            "Selecione um texto e use o atalho de leitura, ou use o atalho OCR para desenhar um retângulo sobre o texto que deseja ler."
        )

        # Linha de utilitários de texto e velocidade
        row_opts = tk.Frame(self.card_tts, bg=c["card_bg"])
        row_opts.pack(fill=tk.X, pady=(2, 0))

        tk.Button(row_opts, text="▶ Ler Caixa", font=self._font(-2), bg=c["btn_default_bg"], fg=c["text_primary"], bd=1, cursor="hand2", command=self._read_from_text_box).pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(row_opts, text="📋 Colar", font=self._font(-2), bg=c["btn_default_bg"], fg=c["text_primary"], bd=1, cursor="hand2", command=self._read_clipboard_direct).pack(side=tk.LEFT, padx=2)
        tk.Button(row_opts, text="Limpar", font=self._font(-2), bg=c["btn_default_bg"], fg=c["text_muted"], bd=1, cursor="hand2", command=lambda: self.txt_preview.delete("1.0", tk.END)).pack(side=tk.LEFT, padx=2)

        self.lbl_speed_txt = tk.Label(row_opts, text="Velocidade:", font=self._font(-2), bg=c["card_bg"], fg=c["text_muted"])
        self.lbl_speed_txt.pack(side=tk.LEFT, padx=(8, 2))
        self.speed_slider = tk.Scale(
            row_opts,
            from_=-4,
            to=6,
            orient=tk.HORIZONTAL,
            showvalue=False,
            bg=c["card_bg"],
            troughcolor=c["bg"],
            activebackground=c["text_accent"],
            highlightthickness=0,
            command=self._on_speed_changed
        )
        self.speed_slider.set(self.tts.rate)
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # -------------------------------------------------------------
        # RODAPÉ MINIMALISTA COM STATUS E ATALHOS RÁPIDOS
        # -------------------------------------------------------------
        footer = tk.Frame(self.container, bg=c["bg"])
        footer.pack(fill=tk.X, pady=(2, 0))

        self.lbl_status = tk.Label(
            footer,
            text="● Pronto",
            font=self._font(-2, bold=True),
            bg=c["bg"],
            fg=c["status_green"]
        )
        self.lbl_status.pack(side=tk.LEFT)

        self.lbl_footer_shortcuts = tk.Label(
            footer,
            text=self._build_footer_text(),
            font=self._font(-2),
            bg=c["bg"],
            fg=c["text_muted"]
        )
        self.lbl_footer_shortcuts.pack(side=tk.RIGHT)

        self._update_magnifier_ui()

    def _build_footer_text(self) -> str:
        """Gera o texto do rodapé com os atalhos atuais."""
        sc = cfg.get_shortcuts_dict()
        parts = [
            f"L: {sc.get('toggle_magnifier', 'ctrl+alt+l')}",
            f"I: {sc.get('next_contrast', 'ctrl+alt+i')}",
            f"R: {sc.get('read_selection', 'ctrl+alt+r')}",
            f"O: {sc.get('ocr_selection', 'ctrl+alt+o')}",
        ]
        return "Atalhos: " + " | ".join(parts)

    # =========================================================
    # JANELA DE CONFIGURAÇÕES (Engrenagem ⚙)
    # =========================================================
    def _open_settings(self):
        """Abre a janela de configurações com Ajuste de Fonte e Atalhos."""
        if self._settings_window and self._settings_window.winfo_exists():
            self._settings_window.lift()
            self._settings_window.focus_force()
            return

        c = self.colors
        win = tk.Toplevel(self.root)
        win.title("⚙ Configurações")
        win.geometry("520x540")
        win.resizable(False, False)
        win.configure(bg=c["bg"])
        win.attributes("-topmost", True)
        win.transient(self.root)
        self._settings_window = win

        container = tk.Frame(win, bg=c["bg"], padx=16, pady=12)
        container.pack(fill=tk.BOTH, expand=True)

        # Título
        tk.Label(
            container,
            text="⚙ Configurações",
            font=self._font(5, bold=True),
            bg=c["bg"],
            fg=c["text_accent"]
        ).pack(anchor=tk.W, pady=(0, 12))

        # ==== SEÇÃO 1: AJUSTE DE FONTE ====
        font_card = tk.LabelFrame(
            container,
            text=" Tamanho da Fonte da Interface ",
            font=self._font(0, bold=True),
            bg=c["card_bg"],
            fg=c["text_accent"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8
        )
        font_card.pack(fill=tk.X, pady=(0, 10))

        font_row = tk.Frame(font_card, bg=c["card_bg"])
        font_row.pack(fill=tk.X)

        tk.Button(
            font_row,
            text="A−",
            font=self._font(2, bold=True),
            bg=c["btn_default_bg"],
            fg=c["text_primary"],
            width=4,
            bd=1,
            cursor="hand2",
            command=lambda: self._change_font_size(-1, font_lbl)
        ).pack(side=tk.LEFT, padx=(0, 8))

        font_lbl = tk.Label(
            font_row,
            text=f"Tamanho atual: {self.font_size}",
            font=self._font(0, bold=True),
            bg=c["card_bg"],
            fg=c["text_primary"]
        )
        font_lbl.pack(side=tk.LEFT, expand=True)

        tk.Button(
            font_row,
            text="A+",
            font=self._font(2, bold=True),
            bg=c["btn_default_bg"],
            fg=c["text_primary"],
            width=4,
            bd=1,
            cursor="hand2",
            command=lambda: self._change_font_size(+1, font_lbl)
        ).pack(side=tk.LEFT, padx=(8, 0))

        font_hint = tk.Label(
            font_card,
            text=f"Intervalo: {FONT_MIN} (mínimo) a {FONT_MAX} (máximo)",
            font=self._font(-2),
            bg=c["card_bg"],
            fg=c["text_muted"]
        )
        font_hint.pack(anchor=tk.W, pady=(4, 0))

        # ==== SEÇÃO 2: ATALHOS PERSONALIZÁVEIS ====
        shortcut_card = tk.LabelFrame(
            container,
            text=" Atalhos do Teclado (clique para alterar) ",
            font=self._font(0, bold=True),
            bg=c["card_bg"],
            fg=c["text_accent"],
            bd=1,
            relief="solid",
            padx=12,
            pady=8
        )
        shortcut_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Scroll frame para atalhos
        sc_canvas = tk.Canvas(shortcut_card, bg=c["card_bg"], highlightthickness=0)
        sc_scrollbar = tk.Scrollbar(shortcut_card, orient="vertical", command=sc_canvas.yview)
        sc_frame = tk.Frame(sc_canvas, bg=c["card_bg"])

        sc_frame.bind("<Configure>", lambda e: sc_canvas.configure(scrollregion=sc_canvas.bbox("all")))
        sc_canvas.create_window((0, 0), window=sc_frame, anchor="nw")
        sc_canvas.configure(yscrollcommand=sc_scrollbar.set)

        sc_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._shortcut_labels_widgets = {}
        current_shortcuts = cfg.get_shortcuts_dict()

        for action, label in SHORTCUT_LABELS.items():
            row = tk.Frame(sc_frame, bg=c["card_bg"])
            row.pack(fill=tk.X, pady=2)

            tk.Label(
                row,
                text=label,
                font=self._font(-1),
                bg=c["card_bg"],
                fg=c["text_primary"],
                anchor=tk.W,
                width=28
            ).pack(side=tk.LEFT)

            hotkey_text = current_shortcuts.get(action, "")
            hotkey_lbl = tk.Label(
                row,
                text=hotkey_text,
                font=self._font(-1, bold=True),
                bg=c["bg"],
                fg=c["text_accent"],
                bd=1,
                relief="solid",
                padx=6,
                width=20,
                cursor="hand2"
            )
            hotkey_lbl.pack(side=tk.RIGHT)
            hotkey_lbl.bind("<Button-1>", lambda e, a=action, lbl=hotkey_lbl: self._start_hotkey_capture(a, lbl))
            self._shortcut_labels_widgets[action] = hotkey_lbl

        shortcut_hint = tk.Label(
            shortcut_card,
            text="Clique no atalho → pressione a nova combinação de teclas",
            font=self._font(-2),
            bg=c["card_bg"],
            fg=c["text_muted"]
        )
        shortcut_hint.pack(anchor=tk.W, pady=(4, 0))

        # ==== BOTÕES DE AÇÃO ====
        btn_row = tk.Frame(container, bg=c["bg"])
        btn_row.pack(fill=tk.X, pady=(4, 0))

        tk.Button(
            btn_row,
            text="🔄 Restaurar Atalhos Padrão",
            font=self._font(-1, bold=True),
            bg=c["btn_default_bg"],
            fg=c["text_primary"],
            bd=1,
            cursor="hand2",
            command=lambda: self._reset_shortcuts_ui()
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_row,
            text="✖ Fechar",
            font=self._font(-1, bold=True),
            bg=c["btn_stop_bg"],
            fg=c["btn_stop_fg"],
            bd=1,
            cursor="hand2",
            padx=12,
            command=win.destroy
        ).pack(side=tk.RIGHT)

    def _change_font_size(self, delta: int, font_lbl: tk.Label):
        """Altera o tamanho de fonte e recria a interface."""
        new_size = max(FONT_MIN, min(FONT_MAX, self.font_size + delta))
        if new_size == self.font_size:
            return

        self.font_size = new_size
        cfg.set("font_size", new_size)
        font_lbl.config(text=f"Tamanho atual: {self.font_size}")

        # Reconstrói a interface principal com o novo tamanho
        self._rebuild_main_ui()
        sounds.filter_change()

    def _start_hotkey_capture(self, action: str, label_widget: tk.Label):
        """Inicia a captura de um novo atalho do teclado."""
        c = self.colors
        label_widget.config(text="⏳ Pressione as teclas...", bg=c["btn_active_bg"], fg=c["btn_active_fg"])
        label_widget.update()

        import keyboard as kb

        def _on_hotkey(event):
            try:
                # Constrói a string do hotkey a partir das teclas modificadoras + tecla principal
                modifiers = []
                if event.name in ("ctrl", "alt", "shift", "windows"):
                    return  # Espera tecla principal

                # Captura o hotkey completo que está pressionado agora
                hotkey = kb.read_hotkey(suppress=False)
                if hotkey:
                    hotkey = hotkey.lower().strip()
                    cfg.set_shortcut(action, hotkey)
                    label_widget.config(text=hotkey, bg=c["bg"], fg=c["text_accent"])

                    # Recarrega atalhos globais
                    self.shortcuts.reload()
                    # Atualiza rodapé
                    self.lbl_footer_shortcuts.config(text=self._build_footer_text())
                    sounds.filter_change()
            except Exception as e:
                print(f"[Hotkey Capture Error]: {e}")
                label_widget.config(text="Erro", bg=c["btn_stop_bg"], fg=c["btn_stop_fg"])

        # Captura em thread separada para não travar a interface
        import threading

        def _capture():
            try:
                hotkey = kb.read_hotkey(suppress=False)
                if hotkey:
                    hotkey = hotkey.lower().strip()
                    cfg.set_shortcut(action, hotkey)

                    def _update_ui():
                        label_widget.config(text=hotkey, bg=c["bg"], fg=c["text_accent"])
                        self.shortcuts.reload()
                        self.lbl_footer_shortcuts.config(text=self._build_footer_text())
                        sounds.filter_change()

                    self.root.after_idle(_update_ui)
            except Exception as e:
                print(f"[Hotkey Capture Error]: {e}")
                self.root.after_idle(lambda: label_widget.config(text="Erro", bg=c["btn_stop_bg"], fg=c["btn_stop_fg"]))

        threading.Thread(target=_capture, daemon=True).start()

    def _reset_shortcuts_ui(self):
        """Restaura atalhos padrão e atualiza a interface."""
        cfg.reset_shortcuts()
        self.shortcuts.reload()

        from config_manager import DEFAULT_SHORTCUTS
        for action, lbl in self._shortcut_labels_widgets.items():
            lbl.config(text=DEFAULT_SHORTCUTS.get(action, ""))

        self.lbl_footer_shortcuts.config(text=self._build_footer_text())
        sounds.filter_change()

    def _rebuild_main_ui(self):
        """Destrói e reconstrói toda a interface principal com as novas configurações."""
        self.container.destroy()
        self._build_ui()
        self._apply_theme()

    # =========================================================
    # Aplicação de tema
    # =========================================================
    def _apply_theme(self):
        """Aplica as cores do tema selecionado a todos os widgets da interface."""
        c = self.colors
        self.root.configure(bg=c["bg"])
        self.container.configure(bg=c["bg"])
        self.lbl_title.configure(bg=c["bg"], fg=c["text_accent"])
        self.btn_theme.configure(
            text="☀️ Claro" if self.current_theme == "dark" else "🌙 Escuro",
            bg=c["btn_default_bg"],
            fg=c["btn_default_fg"]
        )
        self.btn_settings.configure(bg=c["btn_default_bg"], fg=c["text_primary"])

        # Card Lupa
        self.card_lupa.configure(bg=c["card_bg"], fg=c["text_accent"])
        for child in self.card_lupa.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=c["card_bg"])
        self.lbl_scale.configure(bg=c["bg"], fg=c["text_accent"])

        # Card Contraste
        self.card_contrast.configure(bg=c["card_bg"], fg=c["text_accent"])
        for child in self.card_contrast.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=c["card_bg"])

        # Card TTS
        self.card_tts.configure(bg=c["card_bg"], fg=c["text_accent"])
        for child in self.card_tts.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=c["card_bg"])
        self.txt_preview.configure(
            bg=c["input_bg"],
            fg=c["input_fg"],
            insertbackground=c["input_fg"]
        )
        self.txt_preview.tag_config("highlight", background=c["highlight_bg"], foreground=c["highlight_fg"])
        self.lbl_speed_txt.configure(bg=c["card_bg"], fg=c["text_muted"])
        self.speed_slider.configure(bg=c["card_bg"], troughcolor=c["bg"], activebackground=c["text_accent"])

        # Rodapé
        self.lbl_status.configure(bg=c["bg"], fg=c["status_green"])
        self.lbl_footer_shortcuts.configure(bg=c["bg"], fg=c["text_muted"])

        # Atualiza botões
        self._update_magnifier_ui()
        self._on_contrast_changed(self.contrast.mode_index, self.contrast.get_current_mode_name())

    def _toggle_dock(self):
        self.magnifier.toggle_docked()
        self.btn_dock.config(text="🔓 Flutuar" if self.magnifier.is_docked else "📌 Ancorar")
        self.tts.announce("Modo ancorado" if self.magnifier.is_docked else "Modo flutuante")

    def _toggle_guide(self):
        self.magnifier.toggle_reading_guide()
        c = self.colors
        is_on = self.magnifier.reading_guide
        self.btn_guide.config(
            bg=c["btn_active_bg"] if is_on else c["btn_default_bg"],
            fg=c["btn_active_fg"] if is_on else c["text_primary"]
        )

    def _select_preset(self, preset_name: str):
        self.magnifier.set_size_preset(preset_name)
        c = self.colors
        self.btn_size_m.config(bg=c["btn_active_bg"] if preset_name == "Média" else c["btn_default_bg"], fg=c["btn_active_fg"] if preset_name == "Média" else c["text_primary"])
        self.btn_size_g.config(bg=c["btn_active_bg"] if preset_name == "Grande" else c["btn_default_bg"], fg=c["btn_active_fg"] if preset_name == "Grande" else c["text_primary"])
        self.btn_size_p.config(bg=c["btn_active_bg"] if preset_name == "Panorâmica" else c["btn_default_bg"], fg=c["btn_active_fg"] if preset_name == "Panorâmica" else c["text_primary"])

    def _select_contrast_mode(self, idx: int):
        self.contrast.set_mode(idx)
        cfg.set("contrast_mode", idx)

    def _update_magnifier_ui(self):
        c = self.colors
        sc = cfg.get_shortcuts_dict()
        lupa_shortcut = sc.get("toggle_magnifier", "ctrl+alt+l").title()
        if self.magnifier.is_active:
            self.btn_lupa.config(text=f"✔ Lupa Ativa ({lupa_shortcut})", bg=c["btn_active_bg"], fg=c["btn_active_fg"])
        else:
            self.btn_lupa.config(text=f"🔍 Ativar Lupa ({lupa_shortcut})", bg=c["btn_default_bg"], fg=c["text_primary"])
        self.lbl_scale.config(text=f"{self.magnifier.scale:.1f}x")

    def _on_contrast_changed(self, mode_idx: int, mode_name: str):
        c = self.colors
        for i, b in enumerate(self.cf_btns):
            is_active = (i == mode_idx)
            b.config(
                bg=c["btn_active_bg"] if is_active else c["btn_default_bg"],
                fg=c["btn_active_fg"] if is_active else c["text_primary"],
                font=self._font(-2, bold=is_active)
            )

    def _on_speed_changed(self, val):
        self.tts.set_rate(int(float(val)))

    def _on_external_text_captured(self, text: str):
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
            import pyperclip
            text = pyperclip.paste().strip()
            if text:
                self.txt_preview.delete("1.0", tk.END)
                self.txt_preview.insert("1.0", text)
                self.tts.speak(text)
            else:
                sounds.alert_no_text()
        except Exception:
            sounds.alert_no_text()

    def _on_sentence_highlight(self, sentence: str):
        def _highlight():
            try:
                self.txt_preview.tag_remove("highlight", "1.0", tk.END)
                if not sentence or not sentence.strip():
                    return
                idx = "1.0"
                words = sentence.strip().split()
                if not words:
                    return
                search_chunk = " ".join(words[:min(4, len(words))])
                pos = self.txt_preview.search(search_chunk, idx, stopindex=tk.END, exact=True)
                if pos:
                    end_pos = f"{pos}+{len(sentence)}c"
                    self.txt_preview.tag_add("highlight", pos, end_pos)
                    self.txt_preview.see(pos)
            except Exception:
                pass
        self.root.after_idle(_highlight)

    def _on_tts_status_change(self, status: str):
        def _update():
            c = self.colors
            try:
                if status == "speaking":
                    self.lbl_status.config(text="🔊 Lendo texto...", fg=c["text_accent"])
                    self.btn_pause.config(text="⏸")
                elif status == "paused":
                    self.lbl_status.config(text="⏸ Pausado", fg=c["text_muted"])
                    self.btn_pause.config(text="▶")
                else:
                    self.lbl_status.config(text="● Pronto", fg=c["status_green"])
                    self.btn_pause.config(text="⏸")
            except Exception:
                pass
        self.root.after_idle(_update)

    def _on_close(self):
        try:
            if self._settings_window and self._settings_window.winfo_exists():
                self._settings_window.destroy()
            self.snipper.close()
            self.shortcuts.stop()
            self.tts.stop(silent=True)
            self.magnifier.stop()
            self.contrast.reset_to_normal()
        except Exception:
            pass
        finally:
            self.root.destroy()
