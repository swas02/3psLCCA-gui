"""
gui/components/outputs/plots_helper/Pie.py

Two-tab pie widget:
  Tab 0 – Simple pillar donut  (Eco / Env / Social, lifetime totals)
  Tab 1 – Nested stage+pillar donut (existing Sustainability Matrix)
"""

import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib import font_manager as _fm

matplotlib.use("QtAgg")

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
except ImportError:
    from matplotlib.backends.backend_qt import FigureCanvasQTAgg

from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QCheckBox,
    QLabel,
    QSizePolicy,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFrame,
    QScrollArea,
)

from three_ps_lcca_gui.gui.theme import (
    FONT_FAMILY,
    FS_XS, FS_SM, FS_BASE, FS_LG, FS_SUBHEAD, FS_XL, FS_MD,
    FW_NORMAL, FW_BOLD,
    SP1, SP2, SP3, SP4, SP5, SP6, RADIUS_LG, RADIUS_XL,
)
from three_ps_lcca_gui.gui.themes import get_token
from three_ps_lcca_gui.gui.styles import font as _f
from three_ps_lcca_gui.gui.components.utils.display_format import fmt_currency
from ..helper_functions.lifecycle_summary import compute_all_summaries
from ..helper_functions.ratio_helper import format_ratio_string
from ..helper_functions.lcc_colors import COLORS as LCC_COLORS
from .AggregateChart import StageBarPlotter, _build_pillar_total_data

# ── Register Ubuntu fonts ────────────────────────────────────────────────────
_UBUNTU_FONT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "themes", "Ubuntu_font")
)
for _ttf in ["Ubuntu-Light.ttf", "Ubuntu-Regular.ttf", "Ubuntu-Medium.ttf", "Ubuntu-Bold.ttf"]:
    _path = os.path.join(_UBUNTU_FONT_DIR, _ttf)
    if os.path.exists(_path):
        _fm.fontManager.addfont(_path)

matplotlib.rcParams["font.family"] = FONT_FAMILY

# ─────────────────────────────────────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    "stages": {
        "Initial":     "#CCCCCC",
        "Use":         "#00C49A",
        "End-of-Life": "#EA9E9E",
    },
    "pillars": {
        "Economic":      "#9e9eff",
        "Environmental": "#8ad400",
        "Social":        "#ff5a2a",
    },
}

# Original wedge widths preserved
_WEDGE      = {"width": 0.30, "edgecolor": "none", "linewidth": 0}
_WEDGE_SIMP = {"width": 0.42, "edgecolor": "none", "linewidth": 0}

_TAB_META = [
    {
        "title": "Pillar Distribution",
        "desc": "Lifetime cost breakdown across the three sustainability pillars- Economic, Environmental, and Social- aggregated over all lifecycle stages.",
    },
    {
        "title": "Sustainability Matrix",
        "desc": "The ring maps cumulative cost per lifecycle stage, while the outer ring provides a disaggregated view of each stage across the Economic, Environmental, and Social pillars.",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# WHEEL FORWARDER
# ─────────────────────────────────────────────────────────────────────────────

class WheelForwarder(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            parent = obj.parent()
            while parent is not None:
                if isinstance(parent, QScrollArea):
                    QApplication.sendEvent(parent.verticalScrollBar(), event)
                    return True
                parent = parent.parent()
        return False

# ─────────────────────────────────────────────────────────────────────────────
# DATA & CHART HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _M(x): return float(x) / 1_000_000

def _pillar_totals_ok(results: dict) -> bool:
    pt = compute_all_summaries(results).get("pillar_totals", {})
    return all(v >= 0 for v in pt.values())

def _nested_data_ok(results: dict) -> bool:
    pw = compute_all_summaries(results).get("pillar_wise", {})
    return all(v >= 0 for stage in pw.values() for v in stage.values())

def _build_pillar_data(results: dict):
    pt = compute_all_summaries(results).get("pillar_totals", {})
    rows = [
        ("Economic",      pt.get("eco",    0), COLORS["pillars"]["Economic"]),
        ("Environmental", pt.get("env",    0), COLORS["pillars"]["Environmental"]),
        ("Social",        pt.get("social", 0), COLORS["pillars"]["Social"]),
    ]
    return [(l, _M(v), c) for l, v, c in rows if v > 0]

def _build_nested_pie_data(results: dict) -> list:
    pw = compute_all_summaries(results).get("pillar_wise", {})
    mapping = [("initial", "Initial"), ("use_reconstruction", "Use"), ("end_of_life", "End-of-Life")]
    data = []
    for key, label in mapping:
        p = pw.get(key, {})
        if not p or sum(p.values()) <= 0: continue
        data.append({
            "stage": label,
            "pillars": [
                ("Economic",      _M(p.get("eco",    0)), COLORS["pillars"]["Economic"]),
                ("Environmental", _M(p.get("env",    0)), COLORS["pillars"]["Environmental"]),
                ("Social",        _M(p.get("social", 0)), COLORS["pillars"]["Social"]),
            ],
        })
    return data
def _add_smart_labels(ax, wedges, labels, text_color, line_color, threshold=None, leader_radius=1.3):
    """
    Forces all labels completely OUTSIDE the pie chart using leader lines.
    Lines are pinned slightly inside the slice and forced to render with no shrink padding.
    """
    for i, p in enumerate(wedges):
        slice_width = p.theta2 - p.theta1
        if slice_width <= 0.1: continue

        angle = (p.theta2 + p.theta1) / 2.0
        theta_rad = np.deg2rad(angle)
        x = np.cos(theta_rad)
        y = np.sin(theta_rad)
        label_text = labels[i]

        # Start the line slightly inside the pie slice (95% of radius) so it clearly connects
        x_edge, y_edge = x * (p.r * 0.95), y * (p.r * 0.95)
        x_text, y_text = x * leader_radius, y * leader_radius
        ha = "left" if x >= 0 else "right"
        
        ax.annotate(
            label_text, 
            xy=(x_edge, y_edge), 
            xytext=(x_text, y_text),
            ha=ha, va="center", color=text_color, fontsize=8, fontweight="bold",
            # We use text_color for the line to guarantee it shows up, and remove shrink padding
            arrowprops=dict(arrowstyle="-", color=text_color, lw=1.0, alpha=0.6, shrinkA=0, shrinkB=0),
            zorder=10, annotation_clip=False
        )

# ─────────────────────────────────────────────────────────────────────────────
# CHART 0 – Simple pillar donut
# ─────────────────────────────────────────────────────────────────────────────

class SimplePillarPlotter:
    def __init__(self, results: dict, currency: str = "INR"):
        items = _build_pillar_data(results)
        self.labels, self.values, self.colors = [i[0] for i in items], [i[1] for i in items], [i[2] for i in items]
        self.total, self.currency, self.mode = sum(self.values), currency, "Value"
        
        # Original layout size
        self.fig = plt.figure(figsize=(7, 6))
        self.fig.patch.set_alpha(0.0)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("none")
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.15, top=0.95)

    def _fmt(self, val: float) -> str:
        if self.mode == "Percentage": return f"{val / (self.total or 1) * 100:.1f}%"
        return f"{fmt_currency(val, self.currency, decimals=2)} M {self.currency}"

    def set_mode(self, is_percentage: bool):
        self.mode = "Percentage" if is_percentage else "Value"
        self.ax.clear()
        self.setup_plot()
        self.fig.canvas.draw_idle()

    def setup_plot(self):
        tc, lc = get_token("text"), get_token("surface_mid")
        self.ax.set(aspect="equal")
        if not self.values:
            self.ax.text(0, 0, "No Data", ha="center", va="center", color=tc)
            self.ax.axis("off")
            return self.fig

        # Original radius restored
        self.wedges, _ = self.ax.pie(self.values, radius=1.05, colors=self.colors, wedgeprops=_WEDGE_SIMP)
        
        display_labels = [f"{l}\n{self._fmt(v)}" for l, v in zip(self.labels, self.values)]
        _add_smart_labels(self.ax, self.wedges, display_labels, tc, lc, threshold=15.0, leader_radius=1.25)

        self.ax.text(0, 0, f"TOTAL\n{self._fmt(self.total)}", ha="center", va="center", fontsize=10, fontweight="bold", color=tc)
        
        # Original Legend
        legend_els = [Patch(facecolor=c, label=l) for l, c in zip(self.labels, self.colors)]
        self.ax.legend(handles=legend_els, loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=False, fontsize=8, labelcolor=tc)
        
        self.ax.axis("off")
        # Restored original bounds to keep size exactly as it was
        self.ax.set_xlim(-1.6, 1.6)
        self.ax.set_ylim(-1.6, 1.6)
        return self.fig

# ─────────────────────────────────────────────────────────────────────────────
# CHART 1 – Nested stage+pillar donut
# ─────────────────────────────────────────────────────────────────────────────

class SustainabilityCircularPlotter:
    def __init__(self, data: list, currency: str = "INR"):
        self.data, self.currency, self.mode = data, currency, "Value"
        
        # Original layout size
        self.fig = plt.figure(figsize=(7, 6))
        self.fig.patch.set_alpha(0.0)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("none")
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.15, top=0.95)
        self._prepare_data()

    def _prepare_data(self):
        self.total_value = sum(sum(p[1] for p in e["pillars"]) for e in self.data)
        self.inner_vals, self.inner_colors, self.inner_labels = [], [], []
        self.outer_vals, self.outer_colors, self.outer_labels = [], [], []
        for entry in self.data:
            self.inner_vals.append(sum(p[1] for p in entry["pillars"]))
            self.inner_labels.append(entry["stage"])
            self.inner_colors.append(COLORS["stages"].get(entry["stage"], "#DDDDDD"))
            for name, val, color in entry["pillars"]:
                self.outer_vals.append(val); self.outer_labels.append(f"{entry['stage']} - {name}"); self.outer_colors.append(color)

    def _fmt(self, val: float) -> str:
        if self.mode == "Percentage": return f"{val / (self.total_value or 1) * 100:.1f}%"
        return f"{fmt_currency(val, self.currency, decimals=2)} M {self.currency}"

    def set_mode(self, is_percentage: bool):
        self.mode = "Percentage" if is_percentage else "Value"
        self.ax.clear()
        self.setup_plot()
        self.fig.canvas.draw_idle()

    def setup_plot(self):
        tc, sep = get_token("text"), get_token("surface_mid")
        self.ax.set(aspect="equal")
        
        # Original radii restored
        self.inner_wedges, _ = self.ax.pie(self.inner_vals, radius=0.8, colors=self.inner_colors, wedgeprops=_WEDGE)
        self.outer_wedges, _ = self.ax.pie(self.outer_vals, radius=1.1, colors=self.outer_colors, wedgeprops=_WEDGE)
        
        inner_disp = [f"{l}\n{self._fmt(v)}" for l, v in zip(self.inner_labels, self.inner_vals)]
        outer_disp = [f"{l.split(' - ')[1]}\n{self._fmt(v)}" for l, v in zip(self.outer_labels, self.outer_vals)]
        
        _add_smart_labels(self.ax, self.inner_wedges, inner_disp, tc, sep, threshold=20.0, leader_radius=1.45)
        _add_smart_labels(self.ax, self.outer_wedges, outer_disp, tc, sep, threshold=15.0, leader_radius=1.20)

        # Original connecting lines restored
        if self.total_value > 0:
            angles = np.cumsum(self.inner_vals) / self.total_value * 2 * np.pi
            for angle in angles:
                x = [0.5 * np.cos(angle), 1.1 * np.cos(angle)]
                y = [0.5 * np.sin(angle), 1.1 * np.sin(angle)]
                self.ax.plot(x, y, color=sep, lw=1.5, alpha=0.5)

        self.ax.text(0, 0, f"TOTAL\n{self._fmt(self.total_value)}", ha="center", va="center", fontsize=10, fontweight="bold", color=tc)
        
        # Original Legend
        legend_els = [Patch(facecolor=COLORS["stages"].get(l, "#AAA"), label=l) for l in self.inner_labels]
        legend_els += [Patch(facecolor=c, label=l) for l, c in COLORS["pillars"].items()]
        self.ax.legend(handles=legend_els, loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=False, fontsize=8, labelcolor=tc)
        
        self.ax.axis("off")
        # Restored original bounds
        self.ax.set_xlim(-1.6, 1.6)
        self.ax.set_ylim(-1.6, 1.6)
        return self.fig

# ─────────────────────────────────────────────────────────────────────────────
# WIDGET
# ─────────────────────────────────────────────────────────────────────────────

class LCCPieWidget(QWidget):
    def __init__(self, results: dict, currency: str = "INR", parent=None):
        super().__init__(parent)
        self._results, self._currency = results, currency
        self._setup_ui()

    def _setup_ui(self):
        self._main_v = QVBoxLayout(self)
        self._main_v.setContentsMargins(0, SP4, 0, SP4)

        self.card = QFrame()
        self.card.setObjectName("pieCard")
        self.card.setStyleSheet(f"#pieCard {{ background: transparent; border: 1.5px solid {get_token('surface_mid')}; border-radius: {RADIUS_XL}px; }}")
        self.card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        card_v = QVBoxLayout(self.card)
        card_v.setContentsMargins(SP6, SP5, SP6, SP6)
        card_v.setSpacing(SP4)

        content_row = QWidget()
        content_row.setStyleSheet("background: transparent; border: none;")
        self._content_h = QHBoxLayout(content_row)
        self._content_h.setContentsMargins(0, 0, 0, 0)
        self._content_h.setSpacing(SP6)

        self._left_panel = QWidget()
        self._left_panel.setStyleSheet("background: transparent; border: none;")
        left_v = QVBoxLayout(self._left_panel)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(SP4)
        left_v.setAlignment(Qt.AlignCenter)

        title_lbl = QLabel(_TAB_META[1]["title"])
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)
        title_lbl.setFont(_f(FS_SUBHEAD, FW_BOLD))
        title_lbl.setStyleSheet(f"color: {get_token('text')}; border: none; letter-spacing: 0.5px;")
        left_v.addWidget(title_lbl)

        desc_lbl = QLabel(_TAB_META[1]["desc"])
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setFont(_f(FS_BASE))
        desc_lbl.setStyleSheet(f"color: {get_token('text_secondary')}; border: none;")
        left_v.addWidget(desc_lbl)

        summary = compute_all_summaries(self._results)
        pt = summary.get("pillar_totals", {})

        c_eco, c_env, c_soc = get_token("eco"), get_token("env"), get_token("soc")
        _pillar_ok, _nested_ok = _pillar_totals_ok(self._results), _nested_data_ok(self._results)

        ratio = format_ratio_string([pt.get("eco", 0), pt.get("env", 0), pt.get("social", 0)], [c_eco, c_env, c_soc], get_token("text"), get_token("text_secondary"))

        ratio_box = QFrame()
        ratio_box.setStyleSheet(f"background: transparent; border: 1px solid {get_token('surface_mid')}; border-radius: {RADIUS_LG}px;")
        ratio_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        rb_v = QVBoxLayout(ratio_box)
        rb_v.setContentsMargins(SP4, SP4, SP4, SP4)
        rb_v.setSpacing(SP2)

        rb_label = QLabel(f"<span style='color:{c_eco}'>ECONOMIC</span> <span style='color:{get_token('text')}'>:</span> <span style='color:{c_env}'>ENVIRONMENTAL</span> <span style='color:{get_token('text')}'>:</span> <span style='color:{c_soc}'>SOCIAL</span>")
        rb_label.setAlignment(Qt.AlignCenter)
        rb_label.setWordWrap(True)
        rb_label.setTextFormat(Qt.RichText)
        rb_label.setFont(_f(FS_SM, FW_BOLD))
        rb_label.setStyleSheet(f"color: {get_token('text')}; letter-spacing: 1.2px; border: none;")
        rb_v.addWidget(rb_label)

        rb_val = QLabel(ratio)
        rb_val.setAlignment(Qt.AlignCenter)
        rb_val.setWordWrap(True)
        rb_val.setTextFormat(Qt.RichText)
        rb_val.setFont(QFont("Consolas", FS_LG))
        rb_val.setStyleSheet(f"color: {get_token('text')}; border: none;")
        rb_v.addWidget(rb_val)

        rb_note = QLabel("(expressed as ratio)")
        rb_note.setAlignment(Qt.AlignCenter)
        rb_note.setFont(_f(FS_XS, FW_NORMAL, italic=True))
        rb_note.setStyleSheet(f"color: {get_token('text')}; border: none;")
        rb_v.addWidget(rb_note)
        left_v.addWidget(ratio_box)

        self._mode_cb = QCheckBox("Show Percentage Mode")
        self._mode_cb.setFont(_f(FS_BASE))
        self._mode_cb.setStyleSheet(f"color: {get_token('text_secondary')}; background: transparent; border: none;")
        self._mode_cb.setVisible(_pillar_ok)
        left_v.addWidget(self._mode_cb, 0, Qt.AlignCenter)

        self._stage_cb = QCheckBox("See stage wise")
        self._stage_cb.setFont(_f(FS_BASE))
        self._stage_cb.setStyleSheet(f"color: {get_token('text_secondary')}; background: transparent; border: none;")
        self._stage_cb.setVisible(_pillar_ok)
        self._stage_cb.setEnabled(_nested_ok)
        left_v.addWidget(self._stage_cb, 0, Qt.AlignCenter)

        if _pillar_ok and not _nested_ok:
            _stage_note = QLabel("* Stage breakdown unavailable- negative values in stage data.")
            _stage_note.setAlignment(Qt.AlignCenter)
            _stage_note.setWordWrap(True)
            _stage_note.setFont(_f(FS_XS, FW_NORMAL, italic=True))
            _stage_note.setStyleSheet(f"color: {get_token('text_secondary')}; border: none; background: transparent;")
            left_v.addWidget(_stage_note)

        self._content_h.addWidget(self._left_panel, 1)
        self._plotters = []

        if not _pillar_ok:
            pillar_bar_data = _build_pillar_total_data(self._results)
            if pillar_bar_data:
                p_bar = StageBarPlotter(pillar_bar_data, currency=self._currency)
                c_bar = FigureCanvasQTAgg(p_bar.setup_plot())
                c_bar.setMinimumHeight(400); c_bar.setMaximumHeight(500)
                c_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                c_bar.setStyleSheet("background: transparent; border: none;")
                c_bar.installEventFilter(WheelForwarder(self))
                self._content_h.addWidget(c_bar, 2)
            else:
                _no_data = QLabel("No data available.")
                _no_data.setAlignment(Qt.AlignCenter)
                self._content_h.addWidget(_no_data, 2)
        else:
            self._chart_stack = QStackedWidget()
            self._chart_stack.setMaximumHeight(500)
            self._chart_stack.setStyleSheet("background: transparent; border: none;")
            scroller = WheelForwarder(self)

            p0 = SimplePillarPlotter(self._results, currency=self._currency)
            c0 = FigureCanvasQTAgg(p0.setup_plot())
            c0.setMinimumHeight(400); c0.setMaximumHeight(500)
            c0.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            c0.setStyleSheet("background: transparent; border: none;")
            c0.installEventFilter(scroller)
            self._chart_stack.addWidget(c0)
            self._plotters.append(p0)

            if _nested_ok:
                data1 = _build_nested_pie_data(self._results)
                if data1:
                    p1 = SustainabilityCircularPlotter(data1, currency=self._currency)
                    c1 = FigureCanvasQTAgg(p1.setup_plot())
                    c1.setMinimumHeight(400); c1.setMaximumHeight(500)
                    c1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                    c1.setStyleSheet("background: transparent; border: none;")
                    c1.installEventFilter(scroller)
                    self._chart_stack.addWidget(c1)
                    self._plotters.append(p1)

            self._mode_cb.toggled.connect(self._on_mode_change)
            self._stage_cb.toggled.connect(lambda c: self._chart_stack.setCurrentIndex(1 if c else 0))
            self._content_h.addWidget(self._chart_stack, 2)

        card_v.addWidget(content_row)

        if not _pillar_ok:
            _note = QLabel("* Negative cost values detected- pie chart unavailable, showing bar chart instead.")
            _note.setAlignment(Qt.AlignCenter)
            _note.setWordWrap(True)
            _note.setFont(_f(FS_XS, FW_NORMAL, italic=True))
            _note.setStyleSheet(f"color: {get_token('text_secondary')}; border: none; background: transparent;")
            card_v.addWidget(_note)

        self._main_v.addWidget(self.card)

    def _on_mode_change(self, is_percentage: bool):
        for p in self._plotters:
            if p is not None:
                p.set_mode(is_percentage)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.size().width() < 850:
            self._content_h.setDirection(QBoxLayout.Direction.TopToBottom)
            self._left_panel.setMinimumWidth(0)
            self._left_panel.setMaximumWidth(16777215)
        else:
            self._content_h.setDirection(QBoxLayout.Direction.LeftToRight)
            self._left_panel.setFixedWidth(350)

    def minimumSizeHint(self):
        return QSize(0, 400)