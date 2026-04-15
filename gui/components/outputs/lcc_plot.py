"""
gui/components/outputs/lcc_plot.py

Creates an interactive matplotlib chart from LCC analysis results.
Use LCCChartWidget(results) to get a QWidget ready to embed in Qt.
"""

from gui.themes import get_token, theme_manager
from gui.theme import (
    FONT_FAMILY,
    FS_XS, FS_SM, FS_BASE, FS_MD, FS_LG, FS_XL,
    FW_NORMAL, FW_MEDIUM, FW_SEMIBOLD, FW_BOLD,
)
from .plots_helper.Pie import COLORS
from .helper_functions.lcc_colors import COLORS as LCC_PALETTE
from .lcc_data import (
    M, sci_label, _get,
    build_chart_data,
    STAGE_DEFS, stage_totals,
    BREAKDOWN_STAGES,
    CATEGORY_COLORS,
)
from .plots_helper.bar_chart import create_bar_chart

import matplotlib
matplotlib.use("QtAgg")

from PySide6.QtCore import QEvent, QObject, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QFontMetrics
from PySide6.QtWidgets import (
    QApplication, QHeaderView, QLabel, QScrollArea, QFrame,
    QSizePolicy, QStyledItemDelegate, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QToolTip,
)

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
except ImportError:
    from matplotlib.backends.backend_qt import FigureCanvasQTAgg, NavigationToolbar2QT



class LCCDetailsTable(QWidget):
    """Stage × category summary of LCC costs."""

    def __init__(self, results: dict, currency: str = "INR", parent=None):
        super().__init__(parent)
        self._build(results, currency)

    def _build(self, results: dict, currency: str = "INR"):
        # Compute per-stage totals
        stage_rows = []
        for stage_label, result_key, cat_keys in STAGE_DEFS:
            totals = stage_totals(results, result_key, cat_keys)
            if not totals:
                continue  # stage not applicable
            eco  = totals.get("Economic",      0.0)
            env  = totals.get("Environmental", 0.0)
            soc  = totals.get("Social",        0.0)
            # change - store result_key for stage color lookup per row
            stage_rows.append((stage_label, result_key, eco, env, soc, eco + env + soc))

        n_rows = len(stage_rows) + 1  # +1 grand total

        table = QTableWidget(n_rows, 5, self)
        table.setHorizontalHeaderLabels([
            "Stage", f"Economic\n(M {currency})", f"Environmental\n(M {currency})",
            f"Social\n(M {currency})", f"Stage Total\n(M {currency})",
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for col in range(1, 5):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        # table.setAlternatingRowColors(True)
        table.setAlternatingRowColors(False)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # change - map result_key → stage name for color lookups
        _result_key_to_stage = {
            "initial_stage":  "Initial",
            "use_stage":      "Use",
            "reconstruction": "Reconstruction",
            "end_of_life":    "End-of-Life",
        }

        # change - custom header paints section colors directly, bypassing unreliable QSS nth-child
        _header_colors = [
            COLORS["summary_neutral"]["stage_col"],    # col 0: Stage
            COLORS["pillars"]["Economic"],             # col 1: Economic
            COLORS["pillars"]["Environmental"],        # col 2: Environmental
            COLORS["pillars"]["Social"],               # col 3: Social
            COLORS["summary_neutral"]["total_col"],    # col 4: Stage Total
        ]

        class _ColoredHeader(QHeaderView):
            """Paints each header section with its designated pillar/neutral color."""
            def __init__(self, orientation, parent=None):
                super().__init__(orientation, parent)
                self.setSectionsClickable(False)

            def paintSection(self, painter, rect, logical_index):
                painter.save()
                # Fill with designated color
                if logical_index < len(_header_colors):
                    painter.fillRect(rect, QColor(_header_colors[logical_index]))
                else:
                    painter.fillRect(rect, self.palette().button().color())
                # Draw border
                painter.setPen(QColor(get_token("surface_mid")))
                painter.drawRect(rect.adjusted(0, 0, -1, -1))
        # Draw text bold
                bold_font = QFont(FONT_FAMILY, FS_SM, FW_BOLD)
                painter.setFont(bold_font)
                # Use dark text for colored headers as backgrounds are light
                painter.setPen(QColor("#000000"))
                painter.drawText(rect.adjusted(4, 0, -4, 0),
                                 Qt.AlignCenter | Qt.TextWordWrap,
                                 self.model().headerData(logical_index, Qt.Horizontal) or "")
                painter.restore()

        colored_header = _ColoredHeader(Qt.Horizontal, table)
        table.setHorizontalHeader(colored_header)
        table.setFont(QFont(FONT_FAMILY, FS_BASE))
        # Re-apply labels and resize modes after replacing header
        table.setHorizontalHeaderLabels([
            "Stage", f"Economic\n(M {currency})", f"Environmental\n(M {currency})",
            f"Social\n(M {currency})", f"Stage Total\n(M {currency})",
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for col in range(1, 5):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

        table.setStyleSheet(f"QTableWidget {{ gridline-color: {get_token('surface_mid')}; font-family: {FONT_FAMILY}; font-size: {FS_BASE}px; }}")

        bold = QFont(FONT_FAMILY, FS_BASE, FW_BOLD)

        from PySide6.QtGui import QBrush

        # change - _item sets BackgroundRole as QBrush so _ColorDelegate paints correctly
        def _item(text, align=Qt.AlignLeft | Qt.AlignVCenter, font=None,
                  green=False, bg: QColor = None):
            it = QTableWidgetItem(text)
            it.setTextAlignment(align)
            if font:
                it.setFont(font)
            if bg:
                it.setData(Qt.BackgroundRole, QBrush(bg))
                it.setData(Qt.ForegroundRole, QBrush(QColor(get_token("text"))))
            if green:
                it.setData(Qt.ForegroundRole, QBrush(QColor(get_token("success"))))
            it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            return it

        def _val(v, bold_font=None, bg: QColor = None):
            text = f"{v:.4f}"
            return _item(text, Qt.AlignRight | Qt.AlignVCenter, bold_font,
                         green=(v < 0), bg=bg)

        grand_eco = grand_env = grand_soc = grand_total = 0.0

        for row_idx, (label, result_key, eco, env, soc, total) in enumerate(stage_rows):
            grand_eco   += eco
            grand_env   += env
            grand_soc   += soc
            grand_total += total

            # change - col 0 gets stage strip color, cols 1-4 get base background
            stage_name  = _result_key_to_stage.get(result_key, "")
            strip_color = QColor(COLORS["stages"].get(stage_name, "#DDDDDD"))
            base_color  = QColor(get_token("base"))

            # col 0: stage strip color (same as LCC Breakdown left sidebar)
            table.setItem(row_idx, 0, _item(label, font=bold, bg=strip_color))
            # cols 1-4: base data cells - color identity lives in the headers
            table.setItem(row_idx, 1, _val(eco,   bold_font=bold, bg=base_color))
            table.setItem(row_idx, 2, _val(env,   bold_font=bold, bg=base_color))
            table.setItem(row_idx, 3, _val(soc,   bold_font=bold, bg=base_color))
            table.setItem(row_idx, 4, _val(total, bold_font=bold, bg=base_color))

        # change - Grand Total: col 0 silver-grey, cols 1-4 base
        tr = len(stage_rows)
        grand_stage_bg = QColor(COLORS["summary_neutral"]["stage_col"])
        base_color     = QColor(get_token("base"))

        table.setItem(tr, 0, _item("Grand Total", font=bold, bg=grand_stage_bg))
        for col, val in enumerate([grand_eco, grand_env, grand_soc], start=1):
            table.setItem(tr, col, _val(val, bold_font=bold, bg=base_color))
        table.setItem(tr, 4, _val(grand_total, bold_font=bold, bg=base_color))

        # change - _ColorDelegate on all 5 cols to bypass dark-theme QSS
        for col in range(5):
            table.setItemDelegateForColumn(col, _ColorDelegate(table))

        # change - fix row height to 32px for compact summary table
        for row in range(n_rows):
            table.setRowHeight(row, 32)
        table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        lbl = QLabel("<b>LCC Summary</b>")
        lbl.setFont(QFont(FONT_FAMILY, FS_MD, FW_BOLD))
        lbl.setContentsMargins(0, 12, 0, 4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(lbl)
        layout.addWidget(table)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


# ---------------------------------------------------------------------------
# Detailed breakdown table
# ---------------------------------------------------------------------------

class _VerticalTextDelegate(QStyledItemDelegate):
    """Renders cell text rotated 90° counter-clockwise for the stage column."""

    def paint(self, painter, option, index):
        painter.save()
        bg = index.data(Qt.BackgroundRole)
        if bg:
            c = bg.color() if hasattr(bg, "color") else QColor(bg)
            painter.fillRect(option.rect, c)

        painter.translate(
            option.rect.x() + option.rect.width() / 2,
            option.rect.y() + option.rect.height() / 2,
        )
        painter.rotate(-90)

        text_rect = QRect(
            -option.rect.height() // 2,
            -option.rect.width() // 2,
            option.rect.height(),
            option.rect.width(),
        )
        text = (index.data(Qt.DisplayRole) or "").replace("\n", " ")
        font = index.data(Qt.FontRole)
        if font:
            painter.setFont(font)
        fg = index.data(Qt.ForegroundRole)
        painter.setPen(fg.color() if fg and hasattr(fg, "color") else option.palette.text().color())
        painter.drawText(text_rect, Qt.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(64, 80)



class _ColorDelegate(QStyledItemDelegate):
    """Paints cell background from BackgroundRole brush, ignoring QSS overrides.
    This is the only reliable way to force per-item colors in a dark-themed Qt app."""

    def paint(self, painter, option, index):
        painter.save()
        # Fill background from the item's BackgroundRole brush
        bg = index.data(Qt.BackgroundRole)
        if bg:
            color = bg.color() if hasattr(bg, 'color') else QColor(bg)
            painter.fillRect(option.rect, color)
        else:
            painter.fillRect(option.rect, option.palette.base())

        # Draw text with ForegroundRole color
        fg = index.data(Qt.ForegroundRole)
        text_color = fg.color() if fg and hasattr(fg, 'color') else QColor(get_token("text"))
        painter.setPen(text_color)

        text = index.data(Qt.DisplayRole) or ""
        align = index.data(Qt.TextAlignmentRole)
        if align is None:
            align = Qt.AlignLeft | Qt.AlignVCenter

        padding = 6
        text_rect = option.rect.adjusted(padding, 0, -padding, 0)
        painter.drawText(text_rect, int(align), text)
        painter.restore()

    def sizeHint(self, option, index):
        base = super().sizeHint(option, index)
        return base


class LCCBreakdownTable(QWidget):
    """Detailed row-by-row LCC cost breakdown — pure QPainter widget.

    Columns: Stage (fixed) | Cost Item (draggable) | Relative Cost (draggable) | Value (draggable)

    Column dividers can be dragged to resize. Hover over Cost Item or Value cells
    shows the full text as a tooltip. Long labels wrap within their cell.
    """

    _STAGE_W   = 64    # fixed — stage column never resizes
    _PAD_X     = 6
    _LEGEND_H  = 28    # height reserved for legend at top
    _PAD_TOP   = 32    # legend (28) + 4px gap before header
    _MIN_ROW_H = 32
    _DRAG_HIT  = 5     # px tolerance for divider hit-test

    # column ratio/width defaults
    _DEF_ITEM_RATIO = 0.45   # Cost Item share of (W - stage - val)
    _DEF_BAR_RATIO  = 0.35   # Relative Cost share of (W - stage - val)
    # remaining goes to Value; _val_w is derived, not stored separately

    # Colors from lcc_colors.py (single source of truth for this widget)
    _PILLAR_COLORS = {
        "economic":      LCC_PALETTE["eco_color"],
        "environmental": LCC_PALETTE["env_color"],
        "social":        LCC_PALETTE["soc_color"],
    }
    _STAGE_COLORS = {
        "initial_stage":   LCC_PALETTE["init_color"],
        "use_stage":       LCC_PALETTE["use_color"],
        "end_of_life":     LCC_PALETTE["end_color"],
        "reconstruction":  LCC_PALETTE.get("recon_color", "#B0BEC5"),
    }

    def __init__(self, results: dict, currency: str = "INR",
                 stage_labels: dict | None = None,
                 row_labels: dict | None = None,
                 parent=None):
        super().__init__(parent)
        self._currency = currency
        self._stage_labels = stage_labels or {}  # result_key → custom stage name
        self._row_labels   = row_labels   or {}  # cost key   → custom row label
        self._rows = []          # list of (pillar, label, value)
        self._stage_blocks = []  # list of [label, color_hex, start, end, sy, sh]
        self._row_layouts = []   # list of (y, h) per row
        self._total_content_h = 0
        self._max_val = 1.0

        # Column layout state — ratios of the flexible zone (W - _STAGE_W)
        self._item_ratio = self._DEF_ITEM_RATIO   # Cost Item / flex_w
        self._bar_ratio  = self._DEF_BAR_RATIO    # Relative Cost / flex_w
        # Value column gets the rest: flex_w * (1 - item - bar)

        # Drag state
        self._drag_col = None   # "bar" | "val" | None
        self._drag_start_x = 0
        self._drag_start_item = 0.0
        self._drag_start_bar  = 0.0

        self._build(results)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        theme_manager().theme_changed.connect(self.update)

    # ── data ──────────────────────────────────────────────────────────────────

    def _build(self, results: dict):
        row_idx = 0
        _pillar_order = {"economic": 0, "environmental": 1, "social": 2}
        _use_block_idx = None  # index in _stage_blocks for use_stage

        for stage_def in BREAKDOWN_STAGES:
            result_key = stage_def["result_key"]
            stage_data = results.get(result_key, {})

            if stage_def.get("optional") and not isinstance(stage_data.get("economic"), dict):
                continue

            stage_rows = [
                (cat, self._row_labels.get(key, label),
                 float(stage_data.get(cat, {}).get(key, 0.0)))
                for cat, key, label in stage_def["rows"]
                if stage_data.get(cat, {}).get(key) is not None
            ]
            if not stage_rows:
                continue
            if stage_def.get("optional") and all(v == 0.0 for _, _, v in stage_rows):
                continue

            stage_rows.sort(key=lambda r: _pillar_order.get(r[0], 9))
            stage_color = self._STAGE_COLORS.get(result_key, stage_def["stage_color"])

            if result_key == "reconstruction":
                # Fold into use_stage block as a sub-section
                use_color = self._STAGE_COLORS.get("use_stage", stage_color)
                self._rows.append(("_subheader", "Reconstruction", 0.0, use_color))
                row_idx += 1
                for cat, label, value in stage_rows:
                    self._rows.append((cat, label, value, use_color))
                    row_idx += 1
                if _use_block_idx is not None:
                    self._stage_blocks[_use_block_idx][3] = row_idx - 1
            else:
                start = row_idx
                for cat, label, value in stage_rows:
                    self._rows.append((cat, label, value, stage_color))
                    row_idx += 1
                block_idx = len(self._stage_blocks)
                self._stage_blocks.append([
                    self._stage_labels.get(result_key,
                                           stage_def["label"].replace("\n", " ")),
                    stage_color,
                    start,
                    row_idx - 1,
                    0, 0,  # sy, sh — filled by _calculate_layout
                ])
                if result_key == "use_stage":
                    _use_block_idx = block_idx

        if self._rows:
            self._max_val = max(
                abs(r[2]) for r in self._rows if r[0] != "_subheader"
            ) or 1.0

    # ── layout ────────────────────────────────────────────────────────────────

    def _col_x(self, W: int) -> tuple[int, int, int]:
        """Return (x_bar, x_val, val_w) for the current column state."""
        flex_w = W - self._STAGE_W
        x_bar = self._STAGE_W + int(flex_w * self._item_ratio)
        x_val = x_bar + int(flex_w * self._bar_ratio)
        # clamp so val column is never off-screen
        x_val = min(x_val, W - 60)
        return x_bar, x_val, W - x_val

    def _calculate_layout(self):
        W = self.width()
        if W <= 0:
            return

        x_bar, x_val, _ = self._col_x(W)
        item_w = x_bar - self._STAGE_W - self._PAD_X * 2
        item_w = max(item_w, 1)

        fm = QFontMetrics(QFont(FONT_FAMILY, FS_BASE, FW_NORMAL))
        curr_y = self._PAD_TOP + self._MIN_ROW_H  # header height
        self._row_layouts = []

        for cat, label, *_ in self._rows:
            if cat == "_subheader":
                h = 22
            else:
                text_rect = fm.boundingRect(0, 0, item_w, 2000,
                                            Qt.TextWordWrap | Qt.AlignLeft, label)
                h = max(self._MIN_ROW_H, text_rect.height() + 10)
            self._row_layouts.append((curr_y, h))
            curr_y += h

        self._total_content_h = curr_y + 8
        self.setFixedHeight(self._total_content_h)

        for block in self._stage_blocks:
            s, e = block[2], block[3]
            sy = self._row_layouts[s][0]
            ey = self._row_layouts[e][0] + self._row_layouts[e][1]
            block[4] = sy
            block[5] = ey - sy

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._calculate_layout()

    # ── tooltip ───────────────────────────────────────────────────────────────

    def event(self, event: QEvent):
        if event.type() == QEvent.ToolTip:
            W = self.width()
            x_bar, x_val, val_w = self._col_x(W)
            pos = event.pos()

            for idx, (y, h) in enumerate(self._row_layouts):
                if not (y <= pos.y() < y + h):
                    continue
                cat, label, value, _stage_color = self._rows[idx]
                if cat == "_subheader":
                    continue

                # Cost Item column → show full label
                if self._STAGE_W <= pos.x() < x_bar:
                    fm = QFontMetrics(QFont(FONT_FAMILY, FS_BASE, FW_NORMAL))
                    item_w = x_bar - self._STAGE_W - self._PAD_X * 2
                    elided = fm.elidedText(label, Qt.ElideRight, item_w)
                    # Only show tooltip when text is actually clipped
                    tip = label if elided != label or "\n" in label else ""
                    if tip:
                        QToolTip.showText(event.globalPos(), tip, self)
                        return True

                # Relative Cost bar column → show value
                if x_bar <= pos.x() < x_val:
                    QToolTip.showText(
                        event.globalPos(),
                        f"{value:,.2f} {self._currency}",
                        self,
                    )
                    return True

                # Value column → show formatted value with full precision
                if x_val <= pos.x() < W:
                    QToolTip.showText(
                        event.globalPos(),
                        f"{value:,.4f} {self._currency}",
                        self,
                    )
                    return True

            QToolTip.hideText()
        return super().event(event)

    # ── column drag resize ────────────────────────────────────────────────────

    def _divider_at(self, x: int) -> str | None:
        """Return which divider 'bar' or 'val' is within _DRAG_HIT of x."""
        W = self.width()
        x_bar, x_val, _ = self._col_x(W)
        if abs(x - x_bar) <= self._DRAG_HIT:
            return "bar"
        if abs(x - x_val) <= self._DRAG_HIT:
            return "val"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            div = self._divider_at(event.pos().x())
            if div:
                self._drag_col = div
                self._drag_start_x = event.pos().x()
                self._drag_start_item = self._item_ratio
                self._drag_start_bar  = self._bar_ratio
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        W = self.width()
        flex_w = W - self._STAGE_W

        if self._drag_col and flex_w > 0:
            dx = event.pos().x() - self._drag_start_x

            if self._drag_col == "bar":
                # Moving x_bar: adjusts item_ratio, bar_ratio compensates
                new_item = self._drag_start_item + dx / flex_w
                new_item = max(0.15, min(new_item, 1.0 - self._bar_ratio - 0.10))
                delta = new_item - self._item_ratio
                self._item_ratio = new_item
                self._bar_ratio = max(0.10, self._bar_ratio - delta)

            elif self._drag_col == "val":
                # Moving x_val: adjusts bar_ratio, val column compensates
                new_bar = self._drag_start_bar + dx / flex_w
                total_fixed = self._item_ratio
                new_bar = max(0.10, min(new_bar, 1.0 - total_fixed - 0.10))
                self._bar_ratio = new_bar

            self._calculate_layout()
            self.update()
            event.accept()
            return

        # Cursor hint
        div = self._divider_at(event.pos().x())
        if div:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.unsetCursor()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_col:
            self._drag_col = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ── paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        if not self._row_layouts:
            self._calculate_layout()

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        color_text      = QColor(get_token("text"))
        color_header_bg = QColor(get_token("surface_mid"))
        color_grid      = QColor(get_token("surface_mid"))
        color_success   = QColor(get_token("success"))

        pillar_colors = {k: QColor(v) for k, v in self._PILLAR_COLORS.items()}

        W = self.width()
        x_bar, x_val, val_w = self._col_x(W)
        item_w = x_bar - self._STAGE_W
        _bar_pad  = 3
        bar_w_max = x_val - x_bar - _bar_pad * 2

        # ── legend (top) ──────────────────────────────────────────────────────
        legend_y = (self._LEGEND_H - 16) // 2   # vertically center in legend band
        lx = self._STAGE_W + self._PAD_X
        p.setFont(QFont(FONT_FAMILY, FS_BASE, FW_NORMAL))
        for pillar, color in pillar_colors.items():
            p.fillRect(lx, legend_y, 16, 16, QColor(color))
            p.setPen(color_text)
            p.drawText(lx + 20, legend_y - 1, 120, 18,
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       pillar.capitalize())
            lx += 130

        # ── header ────────────────────────────────────────────────────────────
        hdr_y = self._PAD_TOP
        p.fillRect(0, hdr_y, W, self._MIN_ROW_H, color_header_bg)
        p.setFont(QFont(FONT_FAMILY, FS_BASE, FW_SEMIBOLD))
        p.setPen(color_text)
        p.drawText(QRect(0, hdr_y, self._STAGE_W, self._MIN_ROW_H),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, "Stage")
        p.drawText(QRect(self._STAGE_W + self._PAD_X, hdr_y,
                         item_w - self._PAD_X * 2, self._MIN_ROW_H),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "Cost Item")
        p.drawText(QRect(x_bar + self._PAD_X, hdr_y,
                         x_val - x_bar - self._PAD_X * 2, self._MIN_ROW_H),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, "Relative Cost")
        p.drawText(QRect(x_val + self._PAD_X, hdr_y,
                         val_w - self._PAD_X, self._MIN_ROW_H),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   f"Value ({self._currency})")

        # ── data rows ─────────────────────────────────────────────────────────
        row_font = QFont(FONT_FAMILY, FS_BASE, FW_NORMAL)

        for idx, (cat, label, value, stage_color_hex) in enumerate(self._rows):
            ry, rh = self._row_layouts[idx]

            # ── sub-header (Reconstruction label band) ────────────────────────
            if cat == "_subheader":
                sc = QColor(stage_color_hex)
                band = QColor(
                    min(255, sc.red()   * 40 // 100 + 153),
                    min(255, sc.green() * 40 // 100 + 153),
                    min(255, sc.blue()  * 40 // 100 + 153),
                )
                p.fillRect(self._STAGE_W, ry, W - self._STAGE_W, rh, band)
                p.setFont(QFont(FONT_FAMILY, FS_BASE, FW_SEMIBOLD))
                p.setPen(QColor("#1a1a1a"))
                p.drawText(
                    QRect(self._STAGE_W + self._PAD_X, ry,
                          W - self._STAGE_W - self._PAD_X * 2, rh),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    label,
                )
                continue

            pillar_color = pillar_colors.get(cat, QColor("#888888"))

            # Cost Item + Relative Cost — same light shade across both columns
            tint = QColor(
                min(255, pillar_color.red()   * 25 // 100 + 191),
                min(255, pillar_color.green() * 25 // 100 + 191),
                min(255, pillar_color.blue()  * 25 // 100 + 191),
            )
            p.fillRect(self._STAGE_W, ry, x_val - self._STAGE_W, rh, tint)

            # Cost Item label (word-wrap) — dark text, bg is always light
            p.setFont(row_font)
            p.setPen(QColor("#1a1a1a"))
            p.drawText(
                QRect(self._STAGE_W + self._PAD_X, ry,
                      item_w - self._PAD_X * 2, rh),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextWordWrap,
                label,
            )
            p.setPen(color_text)

            # Relative Cost bar — same color as Cost Item column bg (full opacity)
            filled = int((abs(value) / self._max_val) * bar_w_max)
            if value != 0:
                filled = max(filled, 1)
            bar_color = QColor(pillar_color)
            bar_h = rh - _bar_pad * 2
            p.fillRect(x_bar + _bar_pad, ry + _bar_pad,
                       filled, bar_h, bar_color)

            # Value — same tint background, semibold dark text
            p.fillRect(x_val, ry, val_w, rh, tint)
            p.setFont(QFont(FONT_FAMILY, FS_BASE, FW_SEMIBOLD))
            p.setPen(color_success if value < 0 else QColor("#1a1a1a"))
            p.drawText(
                QRect(x_val + self._PAD_X, ry, val_w - self._PAD_X * 2, rh),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{value:,.2f}",
            )
            p.setFont(row_font)

        # ── stage blocks ──────────────────────────────────────────────────────
        p.setFont(QFont(FONT_FAMILY, FS_MD, FW_NORMAL))
        for stage_label, stage_color_hex, _, _, sy, sh in self._stage_blocks:
            sc = QColor(stage_color_hex)
            stage_tint = QColor(
                min(255, sc.red()   * 25 // 100 + 191),
                min(255, sc.green() * 25 // 100 + 191),
                min(255, sc.blue()  * 25 // 100 + 191),
            )
            p.fillRect(0, sy, self._STAGE_W, sh, stage_tint)
            p.save()
            p.translate(self._STAGE_W / 2, sy + sh / 2)
            p.rotate(-90)
            p.setPen(QColor("#1a1a1a"))
            p.drawText(QRect(-sh // 2, -self._STAGE_W // 2, sh, self._STAGE_W),
                       Qt.AlignmentFlag.AlignCenter, stage_label)
            p.restore()

        # ── grid lines ────────────────────────────────────────────────────────
        total_h = self._total_content_h - 8
        grid_col = QColor(color_grid)
        grid_col.setAlpha(120)
        p.setPen(QPen(grid_col, 1))
        for x in (self._STAGE_W, x_bar, x_val):
            p.drawLine(x, self._PAD_TOP, x, total_h)
        grid_row = QColor(color_grid)
        grid_row.setAlpha(60)
        p.setPen(QPen(grid_row, 1))
        for _, (ry, rh) in enumerate(self._row_layouts):
            p.drawLine(self._STAGE_W, ry + rh, W, ry + rh)

        # ── strong stage dividers ─────────────────────────────────────────────
        stage_border = QColor(get_token("text_secondary"))
        stage_border.setAlpha(180)
        p.setPen(QPen(stage_border, 2))
        for _, _, _, _, sy, sh in self._stage_blocks:
            bottom_y = sy + sh
            p.drawLine(0, bottom_y, W, bottom_y)

        # ── divider drag handles (visible hint in header) ─────────────────────
        handle_color = QColor(get_token("text_secondary"))
        handle_color.setAlpha(100)
        p.setPen(QPen(handle_color, 2))
        for x in (x_bar, x_val):
            p.drawLine(x, hdr_y + 6, x, hdr_y + self._MIN_ROW_H - 6)

        # ── outer border ──────────────────────────────────────────────────────
        border_color = QColor(get_token("surface_mid"))
        border_color.setAlpha(200)
        p.setPen(QPen(border_color, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(0, self._PAD_TOP, W - 1, total_h - self._PAD_TOP)

        p.end()

    @classmethod
    def in_scroll(cls, results: dict, currency: str = "INR",
                  stage_labels: dict | None = None,
                  row_labels: dict | None = None,
                  parent=None) -> QScrollArea:
        chart = cls(results, currency, stage_labels=stage_labels, row_labels=row_labels)
        scroll = QScrollArea(parent)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(chart)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Don't let the inner scroll area force the outer page wider
        scroll.setMinimumWidth(0)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return scroll


# ---------------------------------------------------------------------------
# Public widget
# ---------------------------------------------------------------------------

class _ScrollForwarder(QObject):
    """Forward wheel events from the canvas to the nearest parent QScrollArea."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            parent = obj.parent()
            while parent is not None:
                if isinstance(parent, QScrollArea):
                    QApplication.sendEvent(parent.verticalScrollBar(), event)
                    return True
                parent = parent.parent()
        return False


class LCCChartWidget(QWidget):
    """
    Interactive LCC bar chart widget.
    Includes a navigation toolbar (zoom / pan / save) and hover tooltips.
    """

    def __init__(self, results: dict, currency: str = "INR", parent=None):
        super().__init__(parent)
        self._currency = currency

        # Use theme colors for the graph
        text_color = get_token("text")
        bg_color   = get_token("window")

        self._values, self._labels, stage_info = build_chart_data(results)
        fig, self._bars = create_bar_chart(
            self._values, self._labels, stage_info, text_color, bg_color, currency=currency
        )

        self._canvas = FigureCanvasQTAgg(fig)
        self._canvas.setMinimumHeight(480)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._scroll_forwarder = _ScrollForwarder(self)
        self._canvas.installEventFilter(self._scroll_forwarder)
        toolbar = NavigationToolbar2QT(self._canvas, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(toolbar)
        layout.addWidget(self._canvas)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # ── Hover annotation ──────────────────────────────────────────────
        ax = fig.axes[0]
        self._annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(14, 14),
            textcoords="offset points",
            bbox=dict(
                boxstyle="round,pad=0.5",
                fc=bg_color,
                ec="#aaaaaa",
                alpha=0.95,
                linewidth=1,
            ),
            fontsize=FS_SM,
            fontfamily=FONT_FAMILY,
            color=text_color,
            zorder=10,
        )
        self._annot.set_visible(False)

        self._canvas.mpl_connect("motion_notify_event", self._on_hover)
        self._canvas.mpl_connect("axes_leave_event",    self._on_leave)

    def sizeHint(self):
        # toolbar ≈ 36px + canvas minimum 480px
        return QSize(super().sizeHint().width(), 520)

    # ── Hover handlers ────────────────────────────────────────────────────

    def _on_hover(self, event):
        if event.inaxes is None:
            self._set_annot_visible(False)
            return

        for bar, label, val in zip(self._bars, self._labels, self._values):
            if bar.contains(event)[0]:
                x = bar.get_x() + bar.get_width() / 2
                self._annot.xy = (x, val)
                inr = val * 1_000_000
                sign = "−" if val < 0 else ""
                self._annot.set_text(
                    f"{label}\n"
                    f"{self._currency} {sign}{abs(inr):,.0f}\n"
                    f"({sign}{abs(val):.4f} M {self._currency})"
                )
                self._set_annot_visible(True)
                return

        self._set_annot_visible(False)

    def _on_leave(self, event):
        self._set_annot_visible(False)

    def _set_annot_visible(self, visible: bool):
        if self._annot.get_visible() != visible:
            self._annot.set_visible(visible)
            self._canvas.draw_idle()


# Keep backward-compatible alias for any existing call sites
def create_lcc_figure(results: dict):
    palette = QApplication.instance().palette()
    text_color = palette.windowText().color().name()
    bg_color   = palette.window().color().name()
    values, labels, stage_info = build_chart_data(results)
    fig, _ = create_bar_chart(values, labels, stage_info, text_color, bg_color)
    return fig
