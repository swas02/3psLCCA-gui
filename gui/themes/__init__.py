"""
gui/themes/__init__.py — Theme registry.

Directory layout
----------------
gui/themes/
    light/
        default.yml     Bootstrap light  (built-in)
        soft_light.yml  Catppuccin Latte (built-in)
        <custom>.yml    drop any .yml here to add your own light theme
        <custom>.py     legacy .py themes still work as a fallback
    dark/
        default.yml     Default dark     (built-in)
        dracula.yml     Dracula          (built-in)
        <custom>.yml    drop any .yml here to add your own dark theme
        <custom>.py     legacy .py themes still work as a fallback

Each theme YAML must contain:
    name: str                        — human-readable display name
    palette: map[role, hex]          — QPalette role → hex colour
    qss_tokens: map[token, hex]      — token → hex map for main.qss substitution

If a YAML file is missing, corrupt, or has a schema mismatch the system
silently falls back to the hardcoded defaults below — the app never crashes.

Selecting active themes
-----------------------
Change via the Settings panel in the app sidebar (persisted to user prefs).
Fallback defaults are ACTIVE_LIGHT / ACTIVE_DARK below.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
from pathlib import Path

import yaml
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
import sys

# ── Fallback defaults (used if no user pref is saved) ────────────────────
ACTIVE_LIGHT: str = "soft_light"  # built-in: "default" | "soft_light"
ACTIVE_DARK: str = "dracula"      # built-in: "default" | "dracula"
APPEARANCE_MODE: str = "auto"     # "auto" | "light" | "dark"
# ──────────────────────────────────────────────────────────────────────────

_PKG = "gui.themes"
_THEMES_DIR = Path(__file__).parent
# Absolute path — works regardless of working directory (e.g. when a project is open)
_QSS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))),
    "gui",
    "assets",
    "themes",
    "main.qss",
)
_prefs_loaded = False
_current_is_dark: bool = False  # last-known resolved is_dark; set by track_mode()
# populated by get_light/dark_theme(); read via get_token()
_active_tokens: dict[str, str] = {}

# ── Hardcoded fallback themes — system NEVER fails even if all YAMLs are gone ──
#
# Light fallback: brand green palette (matches gui/theme.py constants)
_FALLBACK_LIGHT: dict = {
    "name": "Default Light",
    "palette": {
        "accent":           "#90af13",
        "window":           "#f8f9fa",
        "alternate_base":   "#ffffff",
        "base":             "#ffffff",
        "button":           "#ffffff",
        "mid":              "#e9ecef",
        "midlight":         "#ced4da",
        "light":            "#dee2e6",
        "highlight":        "#90af13",
        "highlighted_text": "#000000",
        "text":             "#212529",
        "window_text":      "#212529",
        "button_text":      "#212529",
        "placeholder_text": "#6c757d",
    },
    "qss_tokens": {
        # ── Core (longest prefix first to avoid partial substitution in QSS) ──
        "$primary-hover":      "#7c9811",
        "$primary-active":     "#6c830e",
        "$border-subtle":      "#ced4da",
        "$surface-active":     "#dee2e6",
        "$body-color":         "#212529",
        "$secondary":          "#6c757d",
        "$primary":            "#90af13",
        "$body-bg":            "#f8f9fa",
        "$border":             "#dee2e6",
        "$surface":            "#e9ecef",
        "$muted":              "#adb5bd",
        "$white":              "#fafafa",
        # ── Semantic status ────────────────────────────────────────────────
        # gui/assets/themes/main.qss QComboBox selector
        "$validation-error":   "#dc3545",
        "$danger":             "#ef4444",   # gui/theme.py DANGER
        # soft red tint (matches your system)
        "$danger-bg": "rgba(239,68,68,0.08)",
        "$danger-bg-pressed": "rgba(239,68,68,0.18)",
        # matches SECONDARY (Bootstrap-consistent)
        "$placeholder-text": "#6c757d",
        "$success":            "#22c55e",   # gui/theme.py SUCCESS
        "$warning":            "#f97316",   # gui/theme.py WARNING_COLOR
        "$info":               "#3b82f6",   # gui/theme.py INFO
        "$placeholder":        "#888888",   # gui/theme.py PLACEHOLDER
        "$card-bg":            "#fafafa",   # gui/theme.py CARD_BG
        # ── Sidebar chrome ──────────────────────────────────────────────────
        "$sidebar-hover":      "#ecf0de",   # gui/theme.py SIDEBAR_HOVER
        "$sidebar-sel":        "#dee7c0",   # gui/theme.py SIDEBAR_SEL
        # ── Splash screen ───────────────────────────────────────────────────
        "$splash-progress":    "#2ecc71",   # gui/main.py splash message colour
        "$splash-bg":          "#1a1a2e",   # gui/main.py _px.fill()
        # ── Brand icon ──────────────────────────────────────────────────────
        "$icon-brand":         "#2ecc71",   # gui/project_window.py window icon
        # ── Log viewer ──────────────────────────────────────────────────────
        "$log-success":        "#b5cea8",   # gui/components/logs.py green
        "$log-default":        "#d4d4d4",   # gui/components/logs.py default
        "$log-warning":        "#dcdcaa",   # gui/components/logs.py yellow
        "$log-error":          "#f48771",   # gui/components/logs.py red
        "$log-info":           "#4ec9b0",   # gui/components/logs.py teal
        # ── Action icons ────────────────────────────────────────────────────
        # include buttons (recycling, carbon, structure)
        "$icon-success":       "#2ecc71",
        # matches SECONDARY (Bootstrap-consistent)
        "$placeholder-text": "#6c757d",
        "$icon-danger":        "#e74c3c",   # trash/delete icons everywhere
        "$icon-muted":         "#aaaaaa",   # disabled/muted icon fallback
        # ── Table cell validation states ────────────────────────────────────
        # gui/components/carbon_emission/.../transport_emissions.py
        "$cell-warn-row-bg":   "#fff1f0",
        # gui/components/carbon_emission/.../material_emissions.py
        "$cell-disabled-bg":   "#e9ecef",
        # material_emissions BG_INVALID, excel_importer ERROR_COLOR
        "$cell-invalid-bg":    "#f8d7da",
        # material_emissions BG_SUSPICIOUS, excel_importer WARN_COLOR
        "$cell-warn-bg":       "#fff3cd",
        # gui/components/carbon_emission/.../transport_emissions.py
        "$cell-warn-fg":       "#cf1322",
        # ── Integrity states ────────────────────────────────────────────────
        # gui/components/traffic_data/wpi_selector.py MISMATCH
        "$integrity-mismatch": "#b71c1c",
        # gui/components/traffic_data/wpi_selector.py MISSING
        "$integrity-missing":  "#e65100",
        # gui/components/traffic_data/wpi_selector.py OK
        "$integrity-ok":       "#2e7d32",
        # ── LCC Plot chart bands ─────────────────────────────────────────────
        # gui/components/outputs/lcc_plot.py Initial Stage tick
        "$chart-initial-tick": "#2c4a75",
        # gui/components/outputs/lcc_plot.py Initial Stage band
        "$chart-initial-bg":   "#cfd9e8",
        "$chart-use-tick":     "#1f6f66",   # Use Stage tick
        "$chart-use-bg":       "#cfe8e2",   # Use Stage band
        "$chart-recon-tick":   "#5a3270",   # Reconstruction Stage tick
        "$chart-recon-bg":     "#e8d5f0",   # Reconstruction Stage band
        "$chart-eol-tick":     "#7a3b3b",   # End-of-Life Stage tick
        "$chart-eol-bg":       "#edd5d5",   # End-of-Life Stage band
        "$chart-bar-positive": "#8b1a1a",   # positive cost bars
        "$chart-bar-negative": "#2e7d32",   # negative / savings bars + table text
    },
}

# Dark fallback: matches palette_manager.py + theme.py DARK_QSS_TOKENS
_FALLBACK_DARK: dict = {
    "name": "Default Dark",
    "palette": {
        "accent":           "#6B7D20",
        "window":           "#282828",
        "alternate_base":   "#333333",
        "base":             "#3a3a3a",
        "button":           "#3a3a3a",
        "mid":              "#505050",
        "midlight":         "#484848",
        "light":            "#555555",
        "highlight":        "#6B7D20",
        "highlighted_text": "#ffffff",
        "text":             "#e2e2e2",
        "window_text":      "#e2e2e2",
        "button_text":      "#e2e2e2",
        "placeholder_text": "#888888",
    },
    "qss_tokens": {
        # ── Core ────────────────────────────────────────────────────────────
        "$primary-hover":      "#7c9811",
        "$primary-active":     "#6c830e",
        "$border-subtle":      "#5a5a5a",
        "$surface-active":     "#525252",
        "$body-color":         "#e2e2e2",
        "$secondary":          "#a0a0a0",
        "$primary":            "#90af13",
        "$body-bg":            "#282828",
        "$border":             "#505050",
        "$surface":            "#4a4a4a",
        "$muted":              "#686868",
        "$white":              "#3a3a3a",
        # ── Semantic status ────────────────────────────────────────────────
        "$validation-error":   "#f87171",
        "$danger":             "#f87171",
        # based on dark danger (#f87171)
        "$danger-bg": "rgba(248,113,113,0.10)",
        "$danger-bg-pressed": "rgba(248,113,113,0.20)",
        "$placeholder-text": "#a0a0a0",               # matches your $secondary
        "$success":            "#4ade80",
        "$warning":            "#fb923c",
        "$info":               "#60a5fa",
        "$placeholder":        "#888888",
        "$card-bg":            "#3a3a3a",
        # ── Sidebar chrome ──────────────────────────────────────────────────
        "$sidebar-hover":      "#2e3424",
        "$sidebar-sel":        "#3a4a25",
        # ── Splash screen ───────────────────────────────────────────────────
        "$splash-progress":    "#2ecc71",
        "$splash-bg":          "#1a1a2e",
        # ── Brand icon ──────────────────────────────────────────────────────
        "$icon-brand":         "#2ecc71",
        # ── Log viewer ──────────────────────────────────────────────────────
        "$log-success":        "#b5cea8",
        "$log-default":        "#d4d4d4",
        "$log-warning":        "#dcdcaa",
        "$log-error":          "#f48771",
        "$log-info":           "#4ec9b0",
        # ── Action icons ────────────────────────────────────────────────────
        "$icon-success":       "#2ecc71",
        "$icon-danger":        "#e74c3c",
        "$icon-muted":         "#888888",
        # ── Table cell validation states ────────────────────────────────────
        "$cell-warn-row-bg":   "#2a1515",
        "$cell-disabled-bg":   "#3a3a3a",
        "$cell-invalid-bg":    "#4a1f22",
        "$cell-warn-bg":       "#3d3000",
        "$cell-warn-fg":       "#ff4d4f",
        # ── Integrity states ────────────────────────────────────────────────
        "$integrity-mismatch": "#f44336",
        "$integrity-missing":  "#ff9800",
        "$integrity-ok":       "#4caf50",
        # ── LCC Plot chart bands ─────────────────────────────────────────────
        "$chart-initial-tick": "#6699cc",
        "$chart-initial-bg":   "#1e2a38",
        "$chart-use-tick":     "#44aa99",
        "$chart-use-bg":       "#1a2e28",
        "$chart-recon-tick":   "#9966cc",
        "$chart-recon-bg":     "#2a1c35",
        "$chart-eol-tick":     "#cc6666",
        "$chart-eol-bg":       "#2e1a1a",
        "$chart-bar-positive": "#c94040",
        "$chart-bar-negative": "#4caf50",
    },
}

# Required keys for schema validation
_REQUIRED_KEYS = {"palette", "qss_tokens"}

# ── QPalette role name → attribute map ───────────────────────────────────
_PALETTE_ROLES: dict[str, QPalette.ColorRole] = {
    "accent":           QPalette.Accent,
    "window":           QPalette.Window,
    "alternate_base":   QPalette.AlternateBase,
    "base":             QPalette.Base,
    "button":           QPalette.Button,
    "mid":              QPalette.Mid,
    "midlight":         QPalette.Midlight,
    "light":            QPalette.Light,
    "highlight":        QPalette.Highlight,
    "highlighted_text": QPalette.HighlightedText,
    "text":             QPalette.Text,
    "window_text":      QPalette.WindowText,
    "button_text":      QPalette.ButtonText,
    "placeholder_text": QPalette.PlaceholderText,
}


def _ensure_tokens() -> None:
    """Bootstrap _active_tokens from fallback if not yet loaded."""
    global _active_tokens
    if not _active_tokens:
        data = _FALLBACK_DARK if _current_is_dark else _FALLBACK_LIGHT
        _active_tokens = {str(k): str(v)
                          for k, v in data["qss_tokens"].items()}


_missing_token_cache = set()


def get_token(name: str, fallback: str = "") -> str:
    _ensure_tokens()
    value = _active_tokens.get(name)
    if value is not None:
        return value
    if name not in _missing_token_cache:
        _missing_token_cache.add(name)
        print(
            f"[THEME WARN] Missing token: {name} → using fallback '{fallback}'", file=sys.stderr)
    return fallback


def get_active_theme() -> dict[str, str]:
    _ensure_tokens()
    return _active_tokens


def _build_theme(data: dict) -> tuple[QPalette, dict[str, str]]:
    """Build (QPalette, qss_tokens) from a raw theme dict.

    Validates schema — raises ValueError on mismatch so callers can fall back.
    """
    if not isinstance(data, dict):
        raise ValueError("Theme data is not a mapping")
    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"Theme missing required keys: {missing}")
    if not isinstance(data["palette"], dict):
        raise ValueError("'palette' must be a mapping")
    if not isinstance(data["qss_tokens"], dict):
        raise ValueError("'qss_tokens' must be a mapping")

    palette = QPalette()
    for role_name, hex_color in data["palette"].items():
        role = _PALETTE_ROLES.get(role_name)
        if role is not None:
            palette.setColor(role, QColor(str(hex_color)))

    qss_tokens: dict[str, str] = {
        str(k): str(v) for k, v in data["qss_tokens"].items()
    }
    return palette, qss_tokens


def _fallback(variant: str) -> tuple[QPalette, dict[str, str]]:
    """Return the hardcoded fallback theme — guaranteed to never fail."""
    data = _FALLBACK_DARK if variant == "dark" else _FALLBACK_LIGHT
    return _build_theme(data)


def _ensure_prefs() -> None:
    """Load persisted theme choices from user prefs (once, lazily)."""
    global ACTIVE_LIGHT, ACTIVE_DARK, APPEARANCE_MODE, _prefs_loaded
    if _prefs_loaded:
        return
    _prefs_loaded = True
    try:
        import core.start_manager as sm

        v = sm.get_pref("active_light_theme")
        if v:
            ACTIVE_LIGHT = v
        v = sm.get_pref("active_dark_theme")
        if v:
            ACTIVE_DARK = v
        v = sm.get_pref("appearance_mode")
        if v in ("auto", "light", "dark"):
            APPEARANCE_MODE = v
    except Exception:
        pass


def _load_yaml_theme(path: Path) -> tuple[QPalette, dict[str, str]]:
    """Parse a .yml theme file → (QPalette, QSS_TOKENS).

    Raises ValueError/yaml.YAMLError on parse or schema failure.
    """
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return _build_theme(data)


def _load(variant: str, name: str) -> tuple[QPalette, dict[str, str]]:
    """Load a theme by variant ('light'|'dark') and name.

    Resolution order:
      1. <themes_dir>/<variant>/<name>.yml  — preferred declarative format
      2. gui.themes.<variant>.<name>        — legacy .py module fallback
      3. Hardcoded fallback                 — if file missing, corrupt, or schema mismatch
    """
    # 1. YAML
    yml_path = _THEMES_DIR / variant / f"{name}.yml"
    if yml_path.exists():
        try:
            return _load_yaml_theme(yml_path)
        except Exception as e:
            print(
                f"[themes] Warning: '{yml_path.name}' failed to load ({e}); using built-in fallback.")
            return _fallback(variant)

    # 2. Legacy .py module
    try:
        mod = importlib.import_module(f"{_PKG}.{variant}.{name}")
        return mod.palette, mod.QSS_TOKENS
    except Exception:
        pass

    # 3. Hardcoded fallback — YAML missing and no .py module found
    print(
        f"[themes] Warning: theme '{variant}/{name}' not found; using built-in fallback.")
    return _fallback(variant)


def get_light_theme() -> tuple[QPalette, dict[str, str]]:
    """Return (palette, QSS_TOKENS) for the active light theme."""
    global _active_tokens
    _ensure_prefs()
    result = _load("light", ACTIVE_LIGHT)
    _active_tokens = result[1]
    return result


def get_dark_theme() -> tuple[QPalette, dict[str, str]]:
    """Return (palette, QSS_TOKENS) for the active dark theme."""
    global _active_tokens
    _ensure_prefs()
    result = _load("dark", ACTIVE_DARK)
    _active_tokens = result[1]
    return result


def set_active_theme(variant: str, name: str) -> None:
    """Set the active theme for 'light' or 'dark' and persist to user prefs."""
    global ACTIVE_LIGHT, ACTIVE_DARK
    if variant == "light":
        ACTIVE_LIGHT = name
    else:
        ACTIVE_DARK = name
    try:
        import core.start_manager as sm

        sm.set_pref(f"active_{variant}_theme", name)
    except Exception:
        pass


def set_appearance_mode(mode: str) -> None:
    """Set appearance mode: 'auto' | 'light' | 'dark'. Persists to user prefs."""
    global APPEARANCE_MODE
    if mode not in ("auto", "light", "dark"):
        return
    APPEARANCE_MODE = mode
    try:
        import core.start_manager as sm

        sm.set_pref("appearance_mode", mode)
    except Exception:
        pass


def resolve_is_dark(os_is_dark: bool) -> bool:
    """Return True if dark theme should be used, respecting APPEARANCE_MODE."""
    _ensure_prefs()
    if APPEARANCE_MODE == "dark":
        return True
    if APPEARANCE_MODE == "light":
        return False
    return os_is_dark  # "auto"


def track_mode(is_dark: bool) -> None:
    """Record the last-resolved is_dark state. Called by main._apply_theme()
    so reapply() always has a reliable baseline instead of guessing from palette."""
    global _current_is_dark
    _current_is_dark = is_dark


def _detect_os_dark(app=None) -> bool:
    """Read the current OS dark/light state directly — never uses cached values.

    Resolution order:
      1. QApplication.styleHints().colorScheme()  — Qt 6.5+, most reliable
      2. Windows registry AppsUseLightTheme       — fallback on Windows
      3. False (assume light)                     — safe default
    """
    # 1. Qt colorScheme (reliable on Qt 6.5+; often Unknown on Windows/Fusion)
    if app is not None:
        try:
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                print(f"[themes] _detect_os_dark → Dark (Qt.ColorScheme.Dark)")
                return True
            if scheme == Qt.ColorScheme.Light:
                print(f"[themes] _detect_os_dark → Light (Qt.ColorScheme.Light)")
                return False
            print(
                f"[themes] _detect_os_dark: Qt.ColorScheme returned Unknown ({scheme}), trying registry …")
        except AttributeError:
            print(
                "[themes] _detect_os_dark: Qt.ColorScheme not available, trying registry …")

    # 2. Windows registry
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        result = (val == 0)
        print(
            f"[themes] _detect_os_dark → {'Dark' if result else 'Light'} (registry AppsUseLightTheme={val})")
        return result
    except Exception as e:
        print(
            f"[themes] _detect_os_dark: registry read failed ({e}), defaulting to Light")

    return False


def reapply(app=None) -> None:
    """Re-apply the current active themes to the running QApplication."""
    from PySide6.QtWidgets import QApplication

    if app is None:
        app = QApplication.instance()
    if app is None:
        return

    # For "auto" mode always re-read the live OS state — _current_is_dark is
    # stale when the user switches FROM an explicit mode (dark/light) back to auto.
    if APPEARANCE_MODE == "auto":
        os_is_dark = _detect_os_dark(app)
    else:
        os_is_dark = _current_is_dark

    is_dark = resolve_is_dark(os_is_dark)
    print(
        f"[themes] reapply: APPEARANCE_MODE={APPEARANCE_MODE!r}, os_is_dark={os_is_dark}, resolved is_dark={is_dark}")
    track_mode(is_dark)
    palette, tokens = get_dark_theme() if is_dark else get_light_theme()

    app.setPalette(palette)

    if os.path.exists(_QSS_PATH):
        try:
            with open(_QSS_PATH, encoding="utf-8") as f:
                qss = f.read()
            for token, value in tokens.items():
                qss = qss.replace(token, value)
            # Clear first — forces Qt to fully re-evaluate all style rules
            # on every existing widget, including window backgrounds.
            app.setStyleSheet("")
            app.setStyleSheet(qss)
        except Exception:
            pass

    # Force every top-level window (and its children) to repaint immediately.
    # Without this, palette(window) backgrounds stay stale until the next
    # resize/focus event.
    for w in app.topLevelWidgets():
        w.style().unpolish(w)
        w.style().polish(w)
        w.update()


def list_themes(variant: str) -> list[str]:
    """Return names of all available themes for 'light' or 'dark'.
    Discovers both .yml files and legacy .py modules in the variant folder."""
    pkg_dir = _THEMES_DIR / variant

    yml_names = {p.stem for p in pkg_dir.glob("*.yml")}
    py_names = {
        name for _, name, is_pkg in pkgutil.iter_modules([str(pkg_dir)]) if not is_pkg
    }
    return sorted(yml_names | py_names)


def get_theme_name(variant: str, module_name: str) -> str:
    """Return the human-readable name for a theme."""
    yml_path = _THEMES_DIR / variant / f"{module_name}.yml"
    if yml_path.exists():
        try:
            with open(yml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                return data.get("name", module_name)
        except Exception:
            pass

    # Legacy .py fallback
    try:
        mod = importlib.import_module(f"{_PKG}.{variant}.{module_name}")
        return getattr(mod, "NAME", module_name)
    except Exception:
        pass

    return module_name
