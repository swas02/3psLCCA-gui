"""
gui/components/outputs/plots_helper/AggregateChart.py

Stacked bar chart showing aggregated LCC impacts across project stages and 
sustainability pillars. Polished dashboard component with 100% width and 
centered explanation including lifecycle stage ratios and Indian formatting.
"""

import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, FancyBboxPatch
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
    FS_SM, FS_BASE, FS_LG, FS_XL, FS_MD, FS_XS, FS_DISP,
    SP1, SP2, SP3, SP4, SP5, SP6, RADIUS_LG, RADIUS_XL
)
from gui.themes import get_token
from gui.components.utils.display_format import fmt_currency
from ..helper_functions.lifecycle_summary import compute_all_summaries
from ..helper_functions.lcc_colors import COLORS as LCC_COLORS

# Register Ubuntu fonts
_UBUNTU_FONT_DIR = os.path.join("gui", "assets", "themes", "Ubuntu_font")
for _ttf in ["Ubuntu-Light.ttf", "Ubuntu-Regular.ttf", "Ubuntu-Medium.ttf", "Ubuntu-Bold.ttf"]:
    _path = os.path.join(_UBUNTU_FONT_DIR, _ttf)
    if os.path.exists(_path): _fm.fontManager.addfont(_path)

matplotlib.rcParams["font.family"] = FONT_FAMILY

# -----------------------------------------------------------------------------
# COLORS
# -----------------------------------------------------------------------------

COLORS = {
    "pillars": {
        "Economic":      LCC_COLORS["eco_color"],   
        "Environmental": LCC_COLORS["env_color"],   
        "Social":        LCC_COLORS["soc_color"],   
    }
}

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

def _build_aggregate_data(results: dict) -> list:
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
                ("Economic", _M(p_data.get("eco", 0))),
                ("Environmental", _M(p_data.get("env", 0))),
                ("Social", _M(p_data.get("social", 0)))
            ]
        })
    return data

# -----------------------------------------------------------------------------
# PLOTTER
# -----------------------------------------------------------------------------

class SustainabilityBarPlotter:
    def __init__(self, data: list, currency: str = "INR"):
        self.data = data
        self.currency = currency
        self.stages = [d["stage"] for d in data]
        self.categories = ["Economic", "Environmental", "Social"]
        self.values = {cat: [next((p[1] for p in d["pillars"] if p[0] == cat), 0) for d in data] for cat in self.categories}
        
        self.fig = plt.figure(figsize=(9, 6))
        self.fig.patch.set_alpha(0.0) 
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("none") 
        self.fig.subplots_adjust(left=0.1, right=0.75, bottom=0.15, top=0.9)
        self.fig.canvas.mpl_connect("motion_notify_event", self._hover)

    def _apply_rounded_corners(self, container, radius=0.05):
        for patch in container:
            bb = patch.get_bbox()
            if bb.height <= 0: continue
            rounded_patch = FancyBboxPatch((bb.xmin, bb.ymin), bb.width, bb.height, boxstyle=f"round,pad=0,rounding_size={radius}", ec="none", lw=0, fc=patch.get_facecolor(), mutation_scale=1, zorder=patch.get_zorder())
            patch.set_visible(False)
            self.ax.add_patch(rounded_patch)

    def _hover(self, event):
        if event.inaxes != self.ax or not hasattr(self, 'annot'): return
        found = False
        for patch in self.ax.patches:
            if isinstance(patch, FancyBboxPatch) and patch.contains(event)[0]:
                for cat in self.categories:
                    if np.allclose(patch.get_facecolor()[:3], matplotlib.colors.to_rgb(COLORS["pillars"][cat])):
                        x_pos = patch.get_x() + patch.get_width()/2
                        stage_idx = int(round(x_pos))
                        if 0 <= stage_idx < len(self.stages):
                            val = self.values[cat][stage_idx]
                            # Use Indian format for tooltips
                            self.annot.set_text(f"{self.stages[stage_idx]}\n{cat}: {fmt_currency(val, self.currency, decimals=2)} Million")
                            self.annot.xy = (event.xdata, event.ydata)
                            self.annot.set_visible(True)
                            found = True
                            break
                if found: break
        if not found: self.annot.set_visible(False)
        self.fig.canvas.draw_idle()

    def setup_plot(self):
        text_color, grid_color = get_token("text"), get_token("surface_mid")
        x, bottom = np.arange(len(self.stages)), np.zeros(len(self.stages))
        for cat in self.categories:
            container = self.ax.bar(x, self.values[cat], bottom=bottom, label=cat, color=COLORS["pillars"][cat], edgecolor='none', width=0.5)
            self._apply_rounded_corners(container)
            bottom += self.values[cat]

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(self.stages, fontweight='bold', color=text_color, fontsize=9)
        self.ax.set_ylabel(f"Total Cost (Million {self.currency})", fontweight='bold', color=text_color, fontsize=9)
        self.ax.tick_params(axis='both', colors=text_color, labelsize=8)
        self.ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=grid_color)
        self.ax.set_axisbelow(True)
        for s in self.ax.spines.values(): s.set_visible(False)

        self.annot = self.ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", fc=get_token("base"), ec=get_token("surface_mid"), alpha=0.9), zorder=10, fontweight='bold', color=text_color, fontsize=8)
        self.annot.set_visible(False)

        legend_els = [Patch(facecolor=COLORS["pillars"][cat], label=cat) for cat in self.categories]
        leg = self.ax.legend(handles=legend_els, title="Sustainability Pillars", loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=8, title_fontsize=9, labelcolor=text_color)
        plt.setp(leg.get_title(), color=text_color)
        return self.fig

# -----------------------------------------------------------------------------
# WIDGET
# -----------------------------------------------------------------------------

class AggregateChartWidget(QWidget):
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
        
        self._card_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.card)
        self._card_layout.setContentsMargins(SP6, SP6, SP6, SP6)
        self._card_layout.setSpacing(SP6)

        # --- Text Panel ---
        self._text_panel = QWidget()
        self._text_panel.setStyleSheet("background: transparent; border: none;")
        self._text_v = QVBoxLayout(self._text_panel)
        self._text_v.setContentsMargins(0, 0, 0, 0)
        self._text_v.setSpacing(SP4)
        self._text_v.setAlignment(Qt.AlignCenter)

        title_box = QHBoxLayout()
        accent = QFrame()
        accent.setFixedWidth(4)
        accent.setFixedHeight(24)
        accent.setStyleSheet(f"background: {get_token('info')}; border-radius: 2px;")
        title_box.addWidget(accent)
        
        title = QLabel("Lifecycle Aggregation")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: {FS_DISP}pt; font-weight: bold; color: {get_token('text')}; border: none; background: transparent; letter-spacing: 0.5px;")
        title_box.addWidget(title)
        title_box.addStretch()
        self._text_v.addLayout(title_box)

        desc = QLabel("Comparative analysis of cumulative project impacts across all design phases. This stacked visualization highlights the proportional distribution of direct capital investments versus long-term externalized liabilities, enabling data-driven optimization of material selection and maintenance scheduling.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f"font-size: {FS_MD}pt; color: {get_token('text_secondary')}; line-height: 1.5; border: none; background: transparent;")
        self._text_v.addWidget(desc)

        # Ratios: Stage Balance
        summary = compute_all_summaries(self._results)
        st = summary.get("stagewise", {})
        total_s = sum(st.values())
        if total_s > 0:
            r_ini, r_use, r_end = st.get("initial", 0)/total_s*100, st.get("use_reconstruction", 0)/total_s*100, st.get("end_of_life", 0)/total_s*100
            stage_ratio = f"<b>{r_ini:.1f}</b> : <b>{r_use:.1f}</b> : <b>{r_end:.1f}</b>"
        else: stage_ratio = "0.0 : 0.0 : 0.0"

        ratio_box = QFrame()
        ratio_box.setStyleSheet(f"background: transparent; border: 1px solid {get_token('surface_mid')}; border-radius: {RADIUS_LG}px;")
        rb_v = QVBoxLayout(ratio_box)
        rb_v.setContentsMargins(SP4, SP4, SP4, SP4)
        rb_v.setAlignment(Qt.AlignCenter)
        
        rb_label = QLabel("INITIAL : USE : END-OF-LIFE")
        rb_label.setAlignment(Qt.AlignCenter)
        rb_label.setStyleSheet(f"font-size: {FS_XS}pt; font-weight: bold; color: {get_token('text_disabled')}; letter-spacing: 1.2px; border: none; background: transparent;")
        rb_v.addWidget(rb_label)
        
        rb_val = QLabel(stage_ratio)
        rb_val.setAlignment(Qt.AlignCenter)
        rb_val.setStyleSheet(f"font-size: {FS_LG}pt; color: {get_token('text')}; margin-top: 8px; font-family: 'Consolas', monospace; border: none; background: transparent;")
        rb_v.addWidget(rb_val)
        
        self._text_v.addWidget(ratio_box)

        self._card_layout.addWidget(self._text_panel, 1)

        # --- Chart Panel ---
        data = _build_aggregate_data(self._results)
        if not data:
            self._chart_widget = QLabel("Insufficient data.")
            self._chart_widget.setAlignment(Qt.AlignCenter)
        else:
            plotter = SustainabilityBarPlotter(data, currency=self._currency)
            fig = plotter.setup_plot()
            self.plotter = plotter
            self._chart_canvas = FigureCanvasQTAgg(fig)
            self._chart_canvas.setStyleSheet("background: transparent; border: none;")
            self._chart_canvas.setMinimumSize(450, 350)
            
            self._chart_container = QWidget()
            cc_lay = QVBoxLayout(self._chart_container)
            cc_lay.setContentsMargins(0, 0, 0, 0)
            cc_lay.addWidget(self._chart_canvas, 0, Qt.AlignCenter)
            self._chart_widget = self._chart_container
            
            self._scroller = WheelForwarder(self)
            self._chart_canvas.installEventFilter(self._scroller)

        self._card_layout.addWidget(self._chart_widget, 2)
        # Horizontal mode: Move chart back to left (index 0)
        self._card_layout.insertWidget(0, self._chart_widget)

        self._main_v.addWidget(self.card)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = event.size().width()
        is_narrow = width < 880
        
        if is_narrow:
            self._card_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self._card_layout.insertWidget(0, self._text_panel)
            self._text_panel.setMaximumWidth(width - 100)
        else:
            self._card_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self._card_layout.insertWidget(0, self._chart_widget)
            self._text_panel.setFixedWidth(350)

    def minimumSizeHint(self):
        return QSize(250, 600)
