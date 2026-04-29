"""カラーテーマ定数 - 全UIモジュール共通"""

# ──────────────────── カラー ────────────────────
COLOR_BG_HEADER = "#003366"
COLOR_BORDER = "#1a6db0"
COLOR_BORDER_DIM = "#0d3b66"
COLOR_UP = "#00e5ff"
COLOR_DOWN = "#ff5252"
# ローソク足チャート専用色（Issue #31: 日本式 上=赤・下=青）
# COLOR_UP/COLOR_DOWN とは独立。PNL や矢印など他の UI には影響させない。
CHART_UP = "#ff5252"
CHART_DOWN = "#4fc3f7"
COLOR_LABEL = "#8899aa"
COLOR_VALUE = "#e0f0ff"
COLOR_ACCENT = "#4fc3f7"
COLOR_MUTED = "#607080"
COLOR_TITLE = "#80d8ff"
COLOR_WARN = "#ffab40"

# ──────────────────── スタイル ────────────────────
STYLE_UP = f"bold {COLOR_UP}"
STYLE_DOWN = f"bold {COLOR_DOWN}"
STYLE_LABEL = COLOR_LABEL
STYLE_VALUE = f"bold {COLOR_VALUE}"
STYLE_BORDER = COLOR_BORDER

# ──────────────────── チャート文字 ────────────────────
CHAR_BODY_UP = "┃"
CHAR_BODY_DOWN = "┃"
CHAR_WICK = "│"
CHAR_BAR_FILL = "█"
CHAR_BAR_EMPTY = "░"
