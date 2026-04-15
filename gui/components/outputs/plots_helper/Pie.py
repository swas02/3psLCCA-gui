"""
gui/components/outputs/plots_helper/Pie.py

Interactive nested pie chart - LCC cost distribution by stage (inner ring)
and pillar (outer ring). Refined centered dashboard card with capped 
chart sizing and responsive layout.
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
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QCheckBox,
    QLabel,
    QSizePolicy,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QFrame,
    QScrollArea,
)

from gui.theme import (
    FONT_FAMILY,
    FS_XS, FS_SM, FS_BASE, FS_LG, FS_XL, FS_MD,
    SP1, SP2, SP3, SP4, SP5, SP6, RADIUS_LG, RADIUS_XL
)
from gui.themes import get_token
from ..helper_functions.lifecycle_summary import compute_all_summaries

# Register Ubuntu fonts
_UBUNTU_FONT_DIR = os.path.join("gui", "assets", "themes", "Ubuntu_font")
for _ttf in ["Ubuntu-Light.ttf", "Ubuntu-Regular.ttf", "Ubuntu-Medium.ttf", "Ubuntu-Bold.ttf"]:
    _path = os.path.join(_UBUNTU_FONT_DIR, _ttf)
    if os.path.exists(_path): _fm.fontManager.addfont(_path)

matplotlib.rcParams["font.family"] = FONT_FAMILY

# -----------------------------------------------------------------------------
# COLORS & CONSTANTS
# -----------------------------------------------------------------------------

COLORS = {
    "stages": {
        "Initial":        "#CCCCCC",  
        "Use":            "#00C49A",  
        "End-of-Life":    "#EA9E9E",  
    },
    "pillars": {
        "Economic":      "#9e9eff",   
        "Environmental": "#8ad400",   
        "Social":        "#ff5a2a",   
    }
}

WEDGE_PROPS = {"width": 0.3, "edgecolor": "none", "linewidth": 0}

# -----------------------------------------------------------------------------
# WHEEL FORWARDER
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# DATA EXTRACTION
# -----------------------------------------------------------------------------

def _M(x): return float(x) / 1_000_000

def _build_new_pie_data(results: dict) -> list:
    summary = compute_all_summaries(results)
    pw = summary.get("pillar_wise", {})
    mapping = [("initial", "Initial"), ("use_reconstruction", "Use"), ("end_of_life", "End-of-Life")]
    data = []
    for key, label in mapping:
        p_data = pw.get(key, {})
        if not p_data or sum(p_data.values()) <= 0: continue
        data.append({
            "stage": label,
            "pillars": [
                ("Economic", _M(p_data.get("eco", 0)), COLORS["pillars"]["Economic"]),
                ("Environmental", _M(p_data.get("env", 0)), COLORS["pillars"]["Environmental"]),
                ("Social", _M(p_data.get("social", 0)), COLORS["pillars"]["Social"])
            ]
        })
    return data

# -----------------------------------------------------------------------------
# PLOTTER
# -----------------------------------------------------------------------------

class SustainabilityCircularPlotter:
    def __init__(self, data: list, currency: str = "INR"):
        self.data = data
        self.currency = currency
        self.mode = "Value"
        
        self.fig = plt.figure(figsize=(6, 6)) # Natural square aspect
        self.fig.patch.set_alpha(0.0) 
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("none") 
        self.fig.subplots_adjust(left=0.02, right=0.98, bottom=0.15, top=0.98)
        
        self._prepare_data()
        self.fig.canvas.mpl_connect("motion_notify_event", self._hover)

    def _prepare_data(self):
        self.total_value = sum(sum(p[1] for p in e["pillars"]) for e in self.data)
        self.inner_vals, self.inner_colors, self.inner_labels = [], [], []
        self.outer_vals, self.outer_colors, self.outer_labels = [], [], []
        for entry in self.data:
            stage_total = sum(p[1] for p in entry["pillars"])
            self.inner_vals.append(stage_total)
            self.inner_labels.append(entry["stage"])
            self.inner_colors.append(COLORS["stages"].get(entry["stage"], "#DDDDDD"))
            for name, val, color in entry["pillars"]:
                self.outer_vals.append(val)
                self.outer_labels.append(f"{entry['stage']} - {name}")
                self.outer_colors.append(color)

    def _format_val(self, val: float) -> str:
        if self.mode == "Percentage":
            total = self.total_value if self.total_value > 0 else 1.0
            return f"{(val / total * 100):.1f}%"
        return f"{val:,.2f} M {self.currency}"

    def _hover(self, event):
        if event.inaxes != self.ax or not hasattr(self, 'annot'): return
        found = False
        all_wedges = list(self.outer_wedges) + list(self.inner_wedges)
        all_labels = self.outer_labels + [f"Stage: {l}" for l in self.inner_labels]
        all_vals = self.outer_vals + self.inner_vals
        for i, wedge in enumerate(all_wedges):
            if wedge.contains(event)[0]:
                self.annot.set_text(f"{all_labels[i]}\n{self._format_val(all_vals[i])}")
                self.annot.xy = (event.xdata, event.ydata)
                self.annot.set_visible(True)
                found = True
                break
        if not found: self.annot.set_visible(False)
        self.fig.canvas.draw_idle()

    def set_mode(self, is_percentage: bool):
        self.mode = "Percentage" if is_percentage else "Value"
        self.center_text.set_text(f"TOTAL NPV\n{self._format_val(self.total_value)}")
        self.fig.canvas.draw_idle()

    def setup_plot(self):
        text_color = get_token("text")
        sep_color = get_token("surface_mid")
        self.ax.set(aspect="equal")
        self.inner_wedges, _ = self.ax.pie(self.inner_vals, radius=0.8, colors=self.inner_colors, wedgeprops=WEDGE_PROPS)
        self.outer_wedges, _ = self.ax.pie(self.outer_vals, radius=1.1, colors=self.outer_colors, wedgeprops=WEDGE_PROPS)
        
        if self.total_value > 0:
            angles = np.cumsum(self.inner_vals) / self.total_value * 2 * np.pi
            for angle in angles:
                x, y = [0.5 * np.cos(angle), 1.1 * np.cos(angle)], [0.5 * np.sin(angle), 1.1 * np.sin(angle)]
                self.ax.plot(x, y, color=sep_color, lw=1.5, alpha=0.5)

        self.center_text = self.ax.text(0, 0, f"TOTAL NPV\n{self._format_val(self.total_value)}", ha='center', va='center', fontsize=9, fontweight='bold', color=text_color)
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points", 
                                      bbox=dict(boxstyle="round,pad=0.5", fc=get_token("base"), ec=get_token("surface_mid"), alpha=0.9), 
                                      zorder=10, fontweight='bold', color=text_color)
        self.annot.set_visible(False)

        legend_els = [Patch(facecolor=COLORS["stages"].get(l, "#AAA"), label=l) for l in self.inner_labels]
        legend_els += [Patch(facecolor=c, label=l) for l, c in COLORS["pillars"].items()]
        self.ax.legend(handles=legend_els, loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=False, fontsize=8, labelcolor=text_color)

        self.ax.axis("off")
        return self.fig

# -----------------------------------------------------------------------------
# WIDGET
# -----------------------------------------------------------------------------

class LCCPieWidget(QWidget):
    def __init__(self, results: dict, currency: str = "INR", parent=None):
        super().__init__(parent)
        self._results = results
        self._currency = currency
        self._setup_ui()

    def _setup_ui(self):
        self._main_v = QVBoxLayout(self)
        self._main_v.setContentsMargins(0, SP4, 0, SP4)
        
        self.card = QFrame()
        self.card.setStyleSheet(f"QFrame {{ background-color: transparent; border: 1.5px solid {get_token('surface_mid')}; border-radius: {RADIUS_XL}px; }}")
        self.card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.card.setMaximumWidth(1050)
        
        self._card_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.card)
        self._card_layout.setContentsMargins(SP6, SP6, SP6, SP6)
        self._card_layout.setSpacing(SP6)

        # --- Left Panel ---
        self._left_panel = QWidget()
        self._left_panel.setStyleSheet("background: transparent; border: none;")
        self._left_v = QVBoxLayout(self._left_panel)
        self._left_v.setContentsMargins(0, 0, 0, 0)
        self._left_v.setSpacing(SP4)
        self._left_v.setAlignment(Qt.AlignCenter)

        title = QLabel("Sustainability Matrix")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: {FS_XL}pt; font-weight: bold; color: {get_token('text')}; border: none; background: transparent;")
        self._left_v.addWidget(title)

        desc = QLabel("Visualizing the triple-bottom-line convergence. Mapping lifecycle impact across project stages and sustainability pillars.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f"font-size: {FS_BASE}pt; color: {get_token('text_secondary')}; line-height: 1.5; border: none; background: transparent;")
        self._left_v.addWidget(desc)

        summary = compute_all_summaries(self._results)
        pt = summary.get("pillar_totals", {})
        total = sum(pt.values())
        if total > 0:
            r_eco, r_env, r_soc = pt.get("eco", 0)/total*100, pt.get("env", 0)/total*100, pt.get("social", 0)/total*100
            ratio_vals = f"<b>{r_eco:.1f}</b> : <b>{r_env:.1f}</b> : <b>{r_soc:.1f}</b>"
        else: ratio_vals = "0.0 : 0.0 : 0.0"

        self._ratio_box = QFrame()
        self._ratio_box.setStyleSheet(f"background: transparent; border: 1px solid {get_token('surface_mid')}; border-radius: {RADIUS_LG}px;")
        rb_v = QVBoxLayout(self._ratio_box)
        rb_v.setContentsMargins(SP4, SP4, SP4, SP4)
        rb_v.setAlignment(Qt.AlignCenter)
        rb_label = QLabel("ECONOMIC : ENVIRONMENTAL : SOCIAL")
        rb_label.setAlignment(Qt.AlignCenter)
        rb_label.setStyleSheet(f"font-size: {FS_SM}pt; font-weight: bold; color: {get_token('text_disabled')}; letter-spacing: 1.2px; border: none; background: transparent;")
        rb_v.addWidget(rb_label)
        rb_val = QLabel(ratio_vals)
        rb_val.setAlignment(Qt.AlignCenter)
        rb_val.setStyleSheet(f"font-size: {FS_LG}pt; color: {get_token('text')}; margin-top: 8px; font-family: 'Consolas', 'Courier New', monospace; border: none; background: transparent;")
        rb_v.addWidget(rb_val)
        self._left_v.addWidget(self._ratio_box)

        self._mode_cb = QCheckBox("Show Percentage Mode")
        self._mode_cb.setStyleSheet(f"font-size: {FS_BASE}pt; color: {get_token('text_secondary')}; background: transparent; border: none;")
        self._left_v.addWidget(self._mode_cb, 0, Qt.AlignCenter)
        
        self._card_layout.addWidget(self._left_panel, 1)

        # --- Right Panel (Capped Chart) ---
        data = _build_new_pie_data(self._results)
        if not data:
            self._chart_widget = QLabel("Insufficient data for analysis.")
            self._chart_widget.setAlignment(Qt.AlignCenter)
        else:
            plotter = SustainabilityCircularPlotter(data, currency=self._currency)
            fig = plotter.setup_plot()
            self.plotter = plotter
            self._chart_canvas = FigureCanvasQTAgg(fig)
            self._chart_canvas.setStyleSheet("background: transparent; border: none;")
            
            # THE CAP: Limit growth on huge screens
            self._chart_container = QWidget()
            self._chart_container.setStyleSheet("background: transparent; border: none;")
            cc_lay = QVBoxLayout(self._chart_container)
            cc_lay.setContentsMargins(0, 0, 0, 0)
            cc_lay.addWidget(self._chart_canvas, 0, Qt.AlignCenter)
            
            self._chart_canvas.setFixedSize(550, 550) # Strict cap for consistency
            self._chart_widget = self._chart_container
            
            # Connect Checkbox
            self._mode_cb.toggled.connect(self.plotter.set_mode)
            
            # Fix scroll
            self._scroller = WheelForwarder(self)
            self._chart_canvas.installEventFilter(self._scroller)

        self._card_layout.addWidget(self._chart_widget, 2)

        self._main_v.addStretch(1)
        self._main_v.addWidget(self.card, 0, Qt.AlignCenter)
        self._main_v.addStretch(1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = event.size().width()
        is_narrow = width < 850
        
        if is_narrow:
            self._card_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self._left_panel.setMinimumWidth(0)
            self._left_panel.setMaximumWidth(width - 100)
            if hasattr(self, "_chart_canvas"):
                # On narrow screens, allow it to be a bit smaller if needed
                chart_w = min(550, width - 120)
                self._chart_canvas.setFixedSize(chart_w, chart_w)
        else:
            self._card_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self._left_panel.setMinimumWidth(320)
            self._left_panel.setMaximumWidth(320)
            if hasattr(self, "_chart_canvas"):
                self._chart_canvas.setFixedSize(550, 550)

    def minimumSizeHint(self):
        return QSize(250, 600)
