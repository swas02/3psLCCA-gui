
from typing import Any
from pathlib import Path
import importlib.util

_root = Path(__file__).resolve().parent.parent.parent  # → src/
_pkg  = _root / "three_ps_lcca_gui"

LOGO_3PS_PATH = str(_pkg / "gui" / "assets" / "logo" / "logo-3psLCCA-light.png")

definitions_path = _pkg / "gui" / "components" / "utils" / "definitions.py"

if definitions_path.exists():
    spec = importlib.util.spec_from_file_location("definitions", str(definitions_path))
    definitions = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(definitions)
    UNIT_DISPLAY = definitions.UNIT_DISPLAY
else:
    UNIT_DISPLAY = {}

def _fmt(value: Any, decimals: int = 2) -> str:
    """
    Return a nicely formatted string.
    0 / 0.0 shows as '0', None/missing shows as blank.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        if value == 0.0:
            return "0"
        return f"{value:,.{decimals}f}"
    if isinstance(value, int):
        return str(value)
    return str(value)


def _fmt_unit(unit: str) -> str:
    """Return the display symbol for a unit code, e.g. m3 → m³."""
    return UNIT_DISPLAY.get(unit, unit)


def _currency(value: Any, currency: str = "INR") -> str:
    """
    Format as currency string.
    0 shows as 'INR 0.00', None/missing shows as blank.
    """
    if value is None:
        return ""
    try:
        f = float(value)
        return f"{currency} {f:,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _pct(value: Any) -> str:
    """Format a percentage value; show 0 as '0%', None as blank."""
    if value is None:
        return ""
    try:
        f = float(value)
        return f"{f}%"
    except (TypeError, ValueError):
        return str(value)
