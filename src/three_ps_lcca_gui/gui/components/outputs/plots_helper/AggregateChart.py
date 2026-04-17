"""
gui/components/outputs/plots_helper/AggregateChart.py

Two-view bar chart widget:
  Default  – Stage-wise bars  (Initial / Use+Rec / End-of-Life, solid colours)
  Checkbox – Pillar-wise bars (stacked Economic / Environmental / Social per stage)
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
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QCheckBox,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFrame,
    QScrollArea,
)

from three_ps_lcca_gui.gui.theme import (
    FONT_FAMILY,
    FS_SM, FS_BASE, FS_LG, FS_SUBHEAD, FS_XL, FS_MD, FS_XS,
    FW_NORMAL, FW_BOLD,
    SP1, SP2, SP3, SP4, SP5, SP6, RADIUS_LG, RADIUS_XL,
)
from three_ps_lcca_gui.gui.themes import get_token
from three_ps_lcca_gui.gui.styles import font as _f
from three_ps_lcca_gui.gui.components.utils.display_format import fmt_currency
from ..helper_functions.lifecycle_summary import compute_all_summaries
from ..helper_functions.ratio_helper import format_ratio_string
from ..helper_functions.lcc_colors import COLORS as LCC_COLORS

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

STAGE_COLORS = {
    "Initial":     "#CCCCCC",
    "Use & Recon": "#00C49A",
    "End-of-Life": "#EA9E9E",
}

PILLAR_COLORS = {
    "Economic":      LCC_COLORS["eco_color"],
    "Environmental": LCC_COLORS["env_color"],
    "Social":        LCC_COLORS["soc_color"],
}

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
# DATA HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _M(x): return float(x) / 1_000_000


def _build_stage_data(results: dict) -> list:
    """[(label, value_M, color), ...] — one entry per stage."""
    st = compute_all_summaries(results).get("stagewise", {})
    mapping = [
        ("initial",            "Initial",     STAGE_COLORS["Initial"]),
        ("use_reconstruction", "Use & Recon", STAGE_COLORS["Use & Recon"]),
        ("end_of_life",        "End-of-Life", STAGE_COLORS["End-of-Life"]),
    ]
    return [(label, _M(st.get(key, 0)), color)
            for key, label, color in mapping if st.get(key, 0) != 0]


def _build_pillar_total_data(results: dict) -> list:
    """[(label, value_M, color), ...] — one bar per pillar total (negatives included)."""
    pt = compute_all_summaries(results).get("pillar_totals", {})
    rows = [
        ("Economic",      pt.get("eco",    0), PILLAR_COLORS["Economic"]),
        ("Environmental", pt.get("env",    0), PILLAR_COLORS["Environmental"]),
        ("Social",        pt.get("social", 0), PILLAR_COLORS["Social"]),
    ]
    return [(l, _M(v), c) for l, v, c in rows if v != 0]


def _build_pillar_data(results: dict) -> list:
    """[{"stage": label, "pillars": [(name, value_M), ...]}, ...] — pillar stacked."""
    pw = compute_all_summaries(results).get("pillar_wise", {})
    mapping = [
        ("initial",            "Initial"),
        ("use_reconstruction", "Use & Recon"),
        ("end_of_life",        "End-of-Life"),
    ]
    data = []
    for key, label in mapping:
        p = pw.get(key, {})
        if not p or all(v == 0 for v in p.values()):
            continue
        data.append({
            "stage": label,
            "pillars": [
                ("Economic",      _M(p.get("eco",    0))),
                ("Environmental", _M(p.get("env",    0))),
                ("Social",        _M(p.get("social", 0))),
            ],
        })
    return data


# ─────────────────────────────────────────────────────────────────────────────
# SHARED HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _rounded_bar(ax, patch, radius=0.05):
    bb = patch.get_bbox()
    if bb.height <= 0:
        return None
    fp = FancyBboxPatch(
        (bb.xmin, bb.ymin), bb.width, bb.height,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        ec="none", lw=0, fc=patch.get_facecolor(),
        mutation_scale=1, zorder=patch.get_zorder(),
    )
    patch.set_visible(False)
    ax.add_patch(fp)
    return fp


# ─────────────────────────────────────────────────────────────────────────────
# CHART 0 – Stage-wise bars  (default)
# ─────────────────────────────────────────────────────────────────────────────

class StageBarPlotter:
    def __init__(self, data: list, currency: str = "INR"):
        # data: [(label, value_M, color), ...]
        self.labels   = [d[0] for d in data]
        self.values   = [d[1] for d in data]
        self.colors   = [d[2] for d in data]
        self.currency = currency

        self.fig = plt.figure(figsize=(9, 6))
        self.fig.patch.set_alpha(0.0)
        self.ax  = self.fig.add_subplot(111)
        self.ax.set_facecolor("none")
        self.fig.subplots_adjust(left=0.1, right=0.75, bottom=0.15, top=0.9)
        self.fig.canvas.mpl_connect("motion_notify_event", self._hover)
        self._fancy: list = []

    def _hover(self, event):
        if event.inaxes != self.ax or not self._fancy:
            return
        found = False
        for i, fp in enumerate(self._fancy):
            if fp is not None and fp.contains(event)[0]:
                val = self.values[i]
                self.annot.set_text(
                    f"{self.labels[i]}\n"
                    f"{fmt_currency(val, self.currency, decimals=2)} Million\n"
                    f"Actual: {self.currency} {fmt_currency(val * 1_000_000, self.currency, decimals=0)}"
                )
                self.annot.xy = (event.xdata, event.ydata)
                self.annot.set_visible(True)
                found = True
                break
        if not found:
            self.annot.set_visible(False)
        self.fig.canvas.draw_idle()

    def setup_plot(self):
        tc = get_token("text")
        gc = get_token("surface_mid")
        x  = np.arange(len(self.labels))

        bars = self.ax.bar(x, self.values, color=self.colors, edgecolor="none", width=0.5)
        self._fancy = [_rounded_bar(self.ax, p) for p in bars.patches]

        max_v = max(self.values) if self.values else 1.0
        min_v = min(self.values) if self.values else 0.0
        pad   = (max_v - min_v) * 0.12 or 1.0
        for i, val in enumerate(self.values):
            if val > 0:
                self.ax.text(
                    i, val + pad * 0.18,
                    f"{fmt_currency(val, self.currency, decimals=2)}",
                    ha="center", va="bottom", fontsize=8, fontweight="bold", color=tc,
                )
            elif val < 0:
                self.ax.text(
                    i, val - pad * 0.18,
                    f"{fmt_currency(val, self.currency, decimals=2)}",
                    ha="center", va="top", fontsize=8, fontweight="bold", color=tc,
                )

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(self.labels, fontweight="bold", color=tc, fontsize=9)
        self.ax.set_ylabel(f"Total Cost (Million {self.currency})", fontweight="bold", color=tc, fontsize=9)
        self.ax.tick_params(axis="both", colors=tc, labelsize=8)
        self.ax.yaxis.grid(True, linestyle="--", alpha=0.3, color=gc)
        self.ax.set_axisbelow(True)
        if self.values:
            self.ax.set_ylim(min(0, min_v) - pad, max(0, max_v) + pad)

        for s in self.ax.spines.values():
            s.set_visible(False)
        for spine in ("left", "bottom"):
            self.ax.spines[spine].set_visible(True)
            self.ax.spines[spine].set_edgecolor(tc)
            self.ax.spines[spine].set_linewidth(0.8)

        self.annot = self.ax.annotate(
            "", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc=get_token("base"),
                      ec=get_token("surface_mid"), alpha=0.9),
            zorder=10, fontweight="bold", color=tc, fontsize=8,
        )
        self.annot.set_visible(False)

        legend_els = [Patch(facecolor=c, label=l) for l, c in zip(self.labels, self.colors)]
        leg = self.ax.legend(
            handles=legend_els, title="Lifecycle Stages",
            loc="center left", bbox_to_anchor=(1.02, 0.5),
            frameon=False, fontsize=8, title_fontsize=9, labelcolor=tc,
        )
        plt.setp(leg.get_title(), color=tc)
        return self.fig


# ─────────────────────────────────────────────────────────────────────────────
# CHART 1 – Pillar-wise stacked bars  (existing)
# ─────────────────────────────────────────────────────────────────────────────

class SustainabilityBarPlotter:
    def __init__(self, data: list, currency: str = "INR"):
        self.data       = data
        self.currency   = currency
        self.stages     = [d["stage"] for d in data]
        self.categories = ["Economic", "Environmental", "Social"]
        self.values     = {
            cat: [next((p[1] for p in d["pillars"] if p[0] == cat), 0) for d in data]
            for cat in self.categories
        }

        self.fig = plt.figure(figsize=(9, 6))
        self.fig.patch.set_alpha(0.0)
        self.ax  = self.fig.add_subplot(111)
        self.ax.set_facecolor("none")
        self.fig.subplots_adjust(left=0.1, right=0.75, bottom=0.15, top=0.9)
        self.fig.canvas.mpl_connect("motion_notify_event", self._hover)

    def _hover(self, event):
        if event.inaxes != self.ax or not hasattr(self, "annot"):
            return
        found = False
        for patch in self.ax.patches:
            if isinstance(patch, FancyBboxPatch) and patch.contains(event)[0]:
                for cat in self.categories:
                    if np.allclose(patch.get_facecolor()[:3],
                                   matplotlib.colors.to_rgb(PILLAR_COLORS[cat])):
                        x_pos     = patch.get_x() + patch.get_width() / 2
                        stage_idx = int(round(x_pos))
                        if 0 <= stage_idx < len(self.stages):
                            val = self.values[cat][stage_idx]
                            self.annot.set_text(
                                f"{self.stages[stage_idx]}\n"
                                f"{cat}: {fmt_currency(val, self.currency, decimals=2)} Million\n"
                                f"Actual: {self.currency} {fmt_currency(val * 1_000_000, self.currency, decimals=0)}"
                            )
                            self.annot.xy = (event.xdata, event.ydata)
                            self.annot.set_visible(True)
                            found = True
                            break
                if found:
                    break
        if not found:
            self.annot.set_visible(False)
        self.fig.canvas.draw_idle()

    def setup_plot(self):
        tc = get_token("text")
        gc = get_token("surface_mid")
        x          = np.arange(len(self.stages))
        pos_bottom = np.zeros(len(self.stages))
        neg_bottom = np.zeros(len(self.stages))

        for cat in self.categories:
            vals     = np.array(self.values[cat])
            pos_vals = np.where(vals > 0, vals, 0.0)
            neg_vals = np.where(vals < 0, vals, 0.0)
            if pos_vals.any():
                container = self.ax.bar(
                    x, pos_vals, bottom=pos_bottom,
                    color=PILLAR_COLORS[cat], edgecolor="none", width=0.5,
                )
                for patch in container:
                    _rounded_bar(self.ax, patch)
                pos_bottom += pos_vals
            if neg_vals.any():
                container = self.ax.bar(
                    x, neg_vals, bottom=neg_bottom,
                    color=PILLAR_COLORS[cat], edgecolor="none", width=0.5,
                )
                for patch in container:
                    _rounded_bar(self.ax, patch)
                neg_bottom += neg_vals

        y_max = max(pos_bottom) if pos_bottom.any() else 0.0
        y_min = min(neg_bottom) if neg_bottom.any() else 0.0
        pad   = (y_max - y_min) * 0.12 or 1.0
        for i in range(len(self.stages)):
            if pos_bottom[i] > 0:
                self.ax.text(
                    i, pos_bottom[i] + pad * 0.18,
                    f"{fmt_currency(pos_bottom[i], self.currency, decimals=2)}",
                    ha="center", va="bottom", fontsize=8, fontweight="bold", color=tc,
                )
            if neg_bottom[i] < 0:
                self.ax.text(
                    i, neg_bottom[i] - pad * 0.18,
                    f"{fmt_currency(neg_bottom[i], self.currency, decimals=2)}",
                    ha="center", va="top", fontsize=8, fontweight="bold", color=tc,
                )

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(self.stages, fontweight="bold", color=tc, fontsize=9)
        self.ax.set_ylabel(f"Total Cost (Million {self.currency})", fontweight="bold", color=tc, fontsize=9)
        self.ax.tick_params(axis="both", colors=tc, labelsize=8)
        self.ax.yaxis.grid(True, linestyle="--", alpha=0.3, color=gc)
        self.ax.set_axisbelow(True)
        self.ax.set_ylim(min(0, y_min) - pad, max(0, y_max) + pad)

        for s in self.ax.spines.values():
            s.set_visible(False)
        for spine in ("left", "bottom"):
            self.ax.spines[spine].set_visible(True)
            self.ax.spines[spine].set_edgecolor(tc)
            self.ax.spines[spine].set_linewidth(0.8)

        self.annot = self.ax.annotate(
            "", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc=get_token("base"),
                      ec=get_token("surface_mid"), alpha=0.9),
            zorder=10, fontweight="bold", color=tc, fontsize=8,
        )
        self.annot.set_visible(False)

        legend_els = [Patch(facecolor=PILLAR_COLORS[cat], label=cat) for cat in self.categories]
        leg = self.ax.legend(
            handles=legend_els, title="Sustainability Pillars",
            loc="center left", bbox_to_anchor=(1.02, 0.5),
            frameon=False, fontsize=8, title_fontsize=9, labelcolor=tc,
        )
        plt.setp(leg.get_title(), color=tc)
        return self.fig


# ─────────────────────────────────────────────────────────────────────────────
# WIDGET
# ─────────────────────────────────────────────────────────────────────────────

class AggregateChartWidget(QWidget):
    def __init__(self, results: dict, currency: str = "INR",
                 default_pillar_view: bool = False,
                 note: str = "",
                 parent=None):
        super().__init__(parent)
        self._results             = results
        self._currency            = currency
        self._default_pillar_view = default_pillar_view
        self._note                = note
        self._setup_ui()

    def _setup_ui(self):
        self._main_v = QVBoxLayout(self)
        self._main_v.setContentsMargins(0, SP4, 0, SP4)

        self.card = QFrame()
        self.card.setObjectName("aggCard")
        self.card.setStyleSheet(
            f"#aggCard {{"
            f"  background-color: transparent;"
            f"  border: 1.5px solid {get_token('surface_mid')};"
            f"  border-radius: {RADIUS_XL}px;"
            f"}}"
        )
        self.card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._card_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.card)
        self._card_layout.setContentsMargins(SP6, SP6, SP6, SP6)
        self._card_layout.setSpacing(SP6)

        # ── Text panel ───────────────────────────────────────────────────────
        self._text_panel = QWidget()
        self._text_panel.setStyleSheet("background: transparent; border: none;")
        text_v = QVBoxLayout(self._text_panel)
        text_v.setContentsMargins(0, 0, 0, 0)
        text_v.setSpacing(SP4)
        text_v.setAlignment(Qt.AlignCenter)

        title = QLabel("Lifecycle Disaggregation")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(_f(FS_SUBHEAD, FW_BOLD))
        title.setStyleSheet(
            f"color: {get_token('text')}; border: none; background: transparent; letter-spacing: 0.5px;"
        )
        text_v.addWidget(title)

        desc = QLabel(
            "Comparative analysis of cumulative project impacts across three core lifecycle "
            "phases: Initial construction, the combined Use/Maintenance/Reconstruction stage, "
            "and final End-of-Life. This visualization highlights the proportional distribution "
            "of direct capital investments versus long-term externalized liabilities."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setFont(_f(FS_BASE))
        desc.setStyleSheet(f"color: {get_token('text_secondary')}; border: none; background: transparent;")
        text_v.addWidget(desc)

        # Ratio box — normalized so smallest = 1
        summary = compute_all_summaries(self._results)
        st      = summary.get("stagewise", {})

        c_init = get_token("init")
        c_use  = get_token("use")
        c_end  = get_token("end")

        v_ini = st.get("initial",            0)
        v_use = st.get("use_reconstruction", 0)
        v_end = st.get("end_of_life",        0)

        stage_ratio = format_ratio_string(
            [v_ini, v_use, v_end],
            [c_init, c_use, c_end],
            get_token("text"),
            get_token("text_secondary")
        )

        ratio_box = QFrame()
        ratio_box.setStyleSheet(
            f"background: transparent;"
            f"border: 1px solid {get_token('surface_mid')};"
            f"border-radius: {RADIUS_LG}px;"
        )
        ratio_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        rb_v = QVBoxLayout(ratio_box)
        rb_v.setContentsMargins(SP4, SP4, SP4, SP4)
        rb_v.setSpacing(SP2)

        rb_label = QLabel(
            f"<span style='color:{c_init}'>INITIAL</span> <span style='color:{get_token('text')}'>:</span> "
            f"<span style='color:{c_use}'>USE</span> <span style='color:{get_token('text')}'>:</span> "
            f"<span style='color:{c_end}'>END-OF-LIFE</span>"
        )
        rb_label.setAlignment(Qt.AlignCenter)
        rb_label.setWordWrap(True)
        rb_label.setTextFormat(Qt.RichText)
        rb_label.setFont(_f(FS_SM, FW_BOLD))
        rb_label.setStyleSheet(
            f"color: {get_token('text')}; letter-spacing: 1.2px; border: none; background: transparent;"
        )
        rb_v.addWidget(rb_label)

        rb_val = QLabel(stage_ratio)
        rb_val.setAlignment(Qt.AlignCenter)
        rb_val.setWordWrap(True)
        rb_val.setTextFormat(Qt.RichText)
        rb_val.setFont(QFont("Consolas", FS_LG))
        rb_val.setStyleSheet(f"color: {get_token('text')}; border: none; background: transparent;")
        rb_v.addWidget(rb_val)

        rb_note = QLabel("(expressed as ratio)")
        rb_note.setAlignment(Qt.AlignCenter)
        rb_note.setFont(_f(FS_XS, FW_NORMAL, italic=True))
        rb_note.setStyleSheet(
            f"color: {get_token('text')}; border: none; background: transparent;"
        )
        rb_v.addWidget(rb_note)

        text_v.addWidget(ratio_box)

        # "Show pillar wise" checkbox
        self._pillar_cb = QCheckBox("Show pillar wise")
        self._pillar_cb.setFont(_f(FS_BASE))
        self._pillar_cb.setStyleSheet(
            f"color: {get_token('text_secondary')}; background: transparent; border: none;"
        )
        text_v.addWidget(self._pillar_cb, 0, Qt.AlignCenter)

        if self._note:
            note_lbl = QLabel(self._note)
            note_lbl.setAlignment(Qt.AlignCenter)
            note_lbl.setWordWrap(True)
            note_lbl.setFont(_f(FS_XS, FW_NORMAL, italic=True))
            note_lbl.setStyleSheet(
                f"color: {get_token('text_secondary')}; border: none; background: transparent;"
            )
            text_v.addWidget(note_lbl)

        self._card_layout.addWidget(self._text_panel, 1)

        # ── Chart stack ──────────────────────────────────────────────────────
        self._chart_stack = QStackedWidget()
        self._chart_stack.setMaximumHeight(420)
        self._chart_stack.setStyleSheet("background: transparent; border: none;")

        scroller = WheelForwarder(self)

        # Chart 0: stage-wise
        stage_data = _build_stage_data(self._results)
        if stage_data:
            p0   = StageBarPlotter(stage_data, currency=self._currency)
            fig0 = p0.setup_plot()
            c0   = FigureCanvasQTAgg(fig0)
            c0.setStyleSheet("background: transparent; border: none;")
            c0.setMinimumHeight(280)
            c0.setMaximumHeight(420)
            c0.installEventFilter(scroller)
            self._chart_stack.addWidget(c0)
        else:
            lbl = QLabel("Insufficient data.")
            lbl.setAlignment(Qt.AlignCenter)
            self._chart_stack.addWidget(lbl)

        # Chart 1: pillar-wise (existing stacked)
        pillar_data = _build_pillar_data(self._results)
        if pillar_data:
            p1   = SustainabilityBarPlotter(pillar_data, currency=self._currency)
            fig1 = p1.setup_plot()
            c1   = FigureCanvasQTAgg(fig1)
            c1.setStyleSheet("background: transparent; border: none;")
            c1.setMinimumHeight(280)
            c1.setMaximumHeight(420)
            c1.installEventFilter(scroller)
            self._chart_stack.addWidget(c1)
        else:
            lbl = QLabel("Insufficient data.")
            lbl.setAlignment(Qt.AlignCenter)
            self._chart_stack.addWidget(lbl)

        self._pillar_cb.toggled.connect(
            lambda checked: self._chart_stack.setCurrentIndex(1 if checked else 0)
        )

        if self._default_pillar_view:
            self._pillar_cb.setChecked(True)

        self._card_layout.addWidget(self._chart_stack, 2)
        # Wide mode: chart on the left
        self._card_layout.insertWidget(0, self._chart_stack)

        self._main_v.addWidget(self.card)

    # ── responsive layout ─────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        is_narrow = event.size().width() < 880
        if is_narrow:
            self._card_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self._card_layout.insertWidget(0, self._text_panel)
            self._text_panel.setMinimumWidth(0)
            self._text_panel.setMaximumWidth(16777215)
        else:
            self._card_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self._card_layout.insertWidget(0, self._chart_stack)
            self._text_panel.setFixedWidth(350)

    def minimumSizeHint(self):
        return QSize(0, 400)
