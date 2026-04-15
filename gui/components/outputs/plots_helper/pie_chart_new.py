import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any
from matplotlib.patches import Patch
from matplotlib.widgets import Button

# -----------------------------------------------------------------------------
# GLOBAL CONSISTENCY STANDARDS
# -----------------------------------------------------------------------------

STAGE_COLORS = {"Initial": "#CCCCCC", "Use": "#00C49A", "End-of-Life": "#EA9E9E"}
PILLAR_COLORS = {"Economic": "#9e9eff", "Environmental": "#8ad400", "Social": "#ff5a2a"}

TITLE_STYLE = {"fontsize": 16, "fontweight": "bold", "color": "#2c3e50", "pad": 40}
ANNOT_STYLE = dict(boxstyle="round,pad=0.5", fc="w", ec="#cccccc", alpha=0.95)
WEDGE_PROPS = {"width": 0.3, "edgecolor": "white", "linewidth": 1.2}

# -----------------------------------------------------------------------------
# CIRCULAR PLOTTER
# -----------------------------------------------------------------------------

class SustainabilityCircularPlotter:
    def __init__(self, data: List[Dict[str, Any]], title: str = "Sustainability Analysis"):
        self.data = data
        self.plot_title = title
        self.mode = "Value"
        
        self.fig, self.ax = plt.subplots(figsize=(12, 8.5))
        plt.subplots_adjust(left=0.1, right=0.75, bottom=0.15, top=0.85)
        
        self._prepare_data()
        self.fig.canvas.mpl_connect("motion_notify_event", self._hover)

    def _prepare_data(self):
        self.total_value = 0
        self.inner_vals, self.inner_labels, self.inner_colors = [], [], []
        self.outer_vals, self.outer_labels, self.outer_colors = [], [], []
        for entry in self.data:
            stage_total = sum(p[1] for p in entry["pillars"])
            self.inner_vals.append(stage_total)
            self.inner_labels.append(entry["stage"])
            self.inner_colors.append(STAGE_COLORS.get(entry["stage"], "#DDDDDD"))
            self.total_value += stage_total
            for name, val, color in entry["pillars"]:
                self.outer_vals.append(val)
                self.outer_labels.append(f"{entry['stage']} - {name}")
                self.outer_colors.append(color)

    def _format_val(self, val: float) -> str:
        if self.mode == "Percentage":
            return f"{(val / self.total_value * 100):.1f}%"
        return f"{val:,.2f}"

    def _hover(self, event):
        if event.inaxes != self.ax or not hasattr(self, 'annot'): return
        found = False
        all_wedges = self.outer_wedges + self.inner_wedges
        all_labels = self.outer_labels + [f"Stage: {l}" for l in self.inner_labels]
        all_vals = self.outer_vals + self.inner_vals
        for i, wedge in enumerate(all_wedges):
            if wedge.contains(event)[0]:
                self.annot.set_text(f"{all_labels[i]}\n{self._format_val(all_vals[i])}")
                self.annot.xy = (event.xdata, event.ydata)
                self.annot.set_visible(True)
                found = True
                break
        if not found and self.annot.get_visible(): self.annot.set_visible(False)
        self.fig.canvas.draw_idle()

    def _set_mode(self, new_mode: str):
        self.mode = new_mode
        self.center_text.set_text(f"TOTAL\n{self._format_val(self.total_value)}")
        self.btn_val.color = PILLAR_COLORS["Economic"] if self.mode == "Value" else "#f0f0f0"
        self.btn_pct.color = PILLAR_COLORS["Economic"] if self.mode == "Percentage" else "#f0f0f0"
        self.fig.canvas.draw_idle()

    def plot(self):
        self.ax.set(aspect="equal")
        self.inner_wedges, _ = self.ax.pie(self.inner_vals, radius=0.8, colors=self.inner_colors, wedgeprops=WEDGE_PROPS)
        self.outer_wedges, _ = self.ax.pie(self.outer_vals, radius=1.1, colors=self.outer_colors, wedgeprops=WEDGE_PROPS)
        
        # Radial separators
        angles = np.cumsum(self.inner_vals) / self.total_value * 2 * np.pi
        for angle in angles:
            x, y = [0.5 * np.cos(angle), 1.1 * np.cos(angle)], [0.5 * np.sin(angle), 1.1 * np.sin(angle)]
            self.ax.plot(x, y, color="white", lw=2)

        self.center_text = self.ax.text(0, 0, "", ha='center', va='center', fontsize=12, fontweight='bold', color="#333333")
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points", bbox=ANNOT_STYLE, zorder=10, fontweight='bold')
        self.annot.set_visible(False)

        # Legend
        legend_els = [Patch(facecolor=c, label=l) for l, c in {**STAGE_COLORS, **PILLAR_COLORS}.items()]
        self.ax.legend(handles=legend_els, title="Legend", loc="center left", bbox_to_anchor=(1.2, 0.5), frameon=True, borderpad=1)

        # UI Toggle Buttons
        ax_v, ax_p = plt.axes([0.1, 0.05, 0.14, 0.04]), plt.axes([0.26, 0.05, 0.14, 0.04])
        self.btn_val, self.btn_pct = Button(ax_v, 'Absolute Value'), Button(ax_p, 'Percentage Mode')
        self.btn_val.on_clicked(lambda _: self._set_mode("Value"))
        self.btn_pct.on_clicked(lambda _: self._set_mode("Percentage"))
        self._set_mode("Value")

        self.ax.set_title(self.plot_title, **TITLE_STYLE)
        plt.show()

if __name__ == "__main__":
    data = [
        {"stage": "Initial", "pillars": [("Economic", 13737381.21, "#9e9eff"), ("Environmental", 369940.12, "#8ad400"), ("Social", 20574204.61, "#ff5a2a")]},
        {"stage": "Use", "pillars": [("Economic", 9046621.11, "#9e9eff"), ("Environmental", 156611.48, "#8ad400"), ("Social", 13329710.65, "#ff5a2a")]},
        {"stage": "End-of-Life", "pillars": [("Economic", 312092.95, "#9e9eff"), ("Environmental", 8709.54, "#8ad400"), ("Social", 913969.47, "#ff5a2a")]}
    ]
    SustainabilityCircularPlotter(data, title="Sustainability Life-Cycle Circular Plot").plot()
