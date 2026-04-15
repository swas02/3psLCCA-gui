import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any
from matplotlib.patches import Patch, FancyBboxPatch

# -----------------------------------------------------------------------------
# GLOBAL CONSISTENCY STANDARDS
# -----------------------------------------------------------------------------

STAGE_COLORS = {"Initial": "#CCCCCC", "Use": "#00C49A", "End-of-Life": "#EA9E9E"}
PILLAR_COLORS = {"Economic": "#9e9eff", "Environmental": "#8ad400", "Social": "#ff5a2a"}

TITLE_STYLE = {"fontsize": 16, "fontweight": "bold", "color": "#2c3e50", "pad": 40}
ANNOT_STYLE = dict(boxstyle="round,pad=0.5", fc="w", ec="#cccccc", alpha=0.95)

# -----------------------------------------------------------------------------
# BAR PLOTTER
# -----------------------------------------------------------------------------

class SustainabilityBarPlotter:
    def __init__(self, data: List[Dict[str, Any]], title: str = "Sustainability Analysis"):
        self.data = data
        self.plot_title = title
        self.stages = [d["stage"] for d in data]
        self.categories = list(PILLAR_COLORS.keys())
        
        self.fig, self.ax = plt.subplots(figsize=(12, 8.5))
        plt.subplots_adjust(left=0.1, right=0.75, bottom=0.15, top=0.85)
        
        self.values = {cat: [next((p[1] for p in d["pillars"] if p[0] == cat), 0) for d in data] for cat in self.categories}
        self.fig.canvas.mpl_connect("motion_notify_event", self._hover)

    def _apply_rounded_corners(self, container, radius=0.05):
        for patch in container:
            bb = patch.get_bbox()
            if bb.height <= 0: continue
            rounded_patch = FancyBboxPatch((bb.xmin, bb.ymin), bb.width, bb.height, boxstyle=f"round,pad=0,rounding_size={radius}",
                                         ec="none", lw=0, fc=patch.get_facecolor(), mutation_scale=1, zorder=patch.get_zorder())
            patch.set_visible(False)
            self.ax.add_patch(rounded_patch)

    def _hover(self, event):
        if event.inaxes != self.ax or not hasattr(self, 'annot'): return
        found = False
        for container in self.ax.containers:
            for i, patch in enumerate(container):
                if patch.contains(event)[0]:
                    cat = container.get_label()
                    self.annot.set_text(f"{self.stages[i]}\n{cat}: {self.values[cat][i]:,.2f}")
                    self.annot.xy = (event.xdata, event.ydata)
                    self.annot.set_visible(True)
                    found = True
                    break
            if found: break
        if not found and self.annot.get_visible(): self.annot.set_visible(False)
        self.fig.canvas.draw_idle()

    def plot(self):
        x, bottom = np.arange(len(self.stages)), np.zeros(len(self.stages))
        for cat in self.categories:
            container = self.ax.bar(x, self.values[cat], bottom=bottom, label=cat, color=PILLAR_COLORS[cat], edgecolor='none', width=0.5)
            self._apply_rounded_corners(container)
            bottom += self.values[cat]

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(self.stages, fontweight='bold')
        self.ax.set_ylabel("Sustainability Impact Value", fontweight='bold')
        self.ax.yaxis.grid(True, linestyle='--', alpha=0.4)
        self.ax.set_axisbelow(True)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

        self.annot = self.ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points", bbox=ANNOT_STYLE, fontweight='bold', zorder=10)
        self.annot.set_visible(False)

        legend_els = [Patch(facecolor=PILLAR_COLORS[cat], label=cat) for cat in self.categories]
        self.ax.legend(handles=legend_els, title="Sustainability Pillars", loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True, borderpad=1)

        self.ax.set_title(self.plot_title, **TITLE_STYLE)
        plt.show()

if __name__ == "__main__":
    data = [
        {"stage": "Initial", "pillars": [("Economic", 13737381.21, "#9e9eff"), ("Environmental", 369940.12, "#8ad400"), ("Social", 20574204.61, "#ff5a2a")]},
        {"stage": "Use", "pillars": [("Economic", 9046621.11, "#9e9eff"), ("Environmental", 156611.48, "#8ad400"), ("Social", 13329710.65, "#ff5a2a")]},
        {"stage": "End-of-Life", "pillars": [("Economic", 312092.95, "#9e9eff"), ("Environmental", 8709.54, "#8ad400"), ("Social", 913969.47, "#ff5a2a")]}
    ]
    SustainabilityBarPlotter(data, title="Sustainability Life-Cycle Stacked Bar Chart").plot()
