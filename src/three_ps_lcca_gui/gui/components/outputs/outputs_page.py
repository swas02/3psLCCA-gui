"""
gui/components/outputs/outputs_page.py
"""

import logging
import traceback

from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QObject, QSize, QThread, QTimer, Signal

from three_ps_lcca_gui.gui.themes import get_token, theme_manager
from three_ps_lcca_gui.gui.styles import font as _f, btn_primary, btn_ghost
from three_ps_lcca_gui.gui.theme import (
    SP1,
    SP2,
    SP3,
    SP4,
    SP5,
    SP6,
    RADIUS_LG,
    FS_XS,
    FS_SM,
    FS_BASE,
    FS_MD,
    FS_LG,
    FS_SUBHEAD,
    FS_XL,
    FS_DISP,
    FW_NORMAL,
    FW_MEDIUM,
    FW_SEMIBOLD,
    FW_BOLD,
    BTN_MD,
    BTN_LG,
    FONT_FAMILY,
)
from three_ps_lcca_gui.gui.components.base_widget import ScrollableForm
from three_ps_lcca_gui.gui.components.utils.form_builder.form_definitions import (
    FieldDef,
    ValidationStatus,
)
from three_ps_lcca_gui.gui.components.utils.form_builder.form_builder import build_form
from three_ps_lcca_gui.gui.components.utils.validation_helpers import (
    clear_field_styles,
    freeze_form,
    validate_form,
)
from three_ps_lcca_core.core.main import run_full_lcc_analysis

from three_ps_lcca_gui.gui.components.utils.display_format import fmt_currency
from .lcc_plot import LCCBreakdownTable, LCCDetailsTable
from .plots_helper.Pie import LCCPieWidget
from .plots_helper.AggregateChart import AggregateChartWidget
from .helper_functions.lifecycle_summary import compute_all_summaries
from .data_preparer import DataPreparer
from .report_section_dialog import ReportSectionDialog


CHUNK = "outputs_data"
CHUNK_AP = "analysis_period"
CHUNK_COMPARISON = "comparison_cache"

OUTPUTS_FIELDS = [
    FieldDef(
        "analysis_period",
        "Analysis Period",
        "Total time horizon used for life cycle cost evaluation.",
        "int",
        options=(0, 999),
        required=True,
        unit="(years)",
        doc_slug="analysis-period",
        default=50,
    ),
]

OUTPUTS_WARN_RULES = {
    "analysis_period": (
        None,
        500,
        None,
        "Analysis period exceeds 500 years- please verify.",
    ),
}

_log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(
        f"background-color: {get_token('surface_pressed')}; "
        f"margin-top: {SP5}px; margin-bottom: {SP5}px; border: none;"
    )
    return line


def _section_heading(title: str) -> QLabel:
    lbl = QLabel(title)
    lbl.setWordWrap(True)
    lbl.setContentsMargins(0, SP6, 0, SP1)
    lbl.setFont(_f(FS_SUBHEAD, FW_BOLD))
    lbl.setStyleSheet(f"color: {get_token('text')};")
    return lbl


def _section_description(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setFont(_f(FS_MD))
    lbl.setStyleSheet(
        f"color: {get_token('text_secondary')}; margin-bottom: {SP4}px;"
    )
    return lbl


def _make_issue_card(page_name: str, issues: list, severity: str, navigate_cb) -> QFrame:
    """severity: 'error' or 'warning'"""
    border_color = get_token("danger" if severity == "error" else "warning")

    card = QFrame()
    card.setObjectName("issueCard")
    card.setStyleSheet(
        f"#issueCard {{"
        f"  border: 1px solid {get_token('surface_mid')};"
        f"  border-left: 4px solid {border_color};"
        f"  border-radius: {RADIUS_LG}px;"
        f"  background-color: {get_token('surface')};"
        f"}}"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(SP3, SP3, SP3, SP3)
    layout.setSpacing(SP3)

    # header row
    h_row = QWidget()
    h_row.setStyleSheet("background: transparent;")
    h_lay = QHBoxLayout(h_row)
    h_lay.setContentsMargins(0, 0, 0, 0)

    name_lbl = QLabel(page_name.upper())
    name_lbl.setFont(_f(FS_SM, FW_MEDIUM))
    name_lbl.setStyleSheet(
        f"color: {get_token('text_secondary')}; letter-spacing: 1px; background: transparent;"
    )
    h_lay.addWidget(name_lbl, 0, Qt.AlignVCenter)
    h_lay.addStretch()

    go_btn = QPushButton("Fix Issues →" if severity == "error" else "Fix Warnings →")
    go_btn.setFixedHeight(BTN_MD)
    go_btn.setFont(_f(FS_SM, FW_SEMIBOLD))
    go_btn.setStyleSheet(btn_primary() if severity == "error" else btn_ghost())
    go_btn.setCursor(Qt.PointingHandCursor)
    go_btn.clicked.connect(lambda checked=False, p=page_name: navigate_cb(p))
    h_lay.addWidget(go_btn, 0, Qt.AlignVCenter)

    layout.addWidget(h_row)

    # issue rows
    for issue in issues:
        msg = issue if isinstance(issue, str) else issue.get("msg", str(issue))

        row = QHBoxLayout()
        row.setSpacing(SP1)

        dot_wrapper = QWidget()
        dot_wrapper.setFixedWidth(10)
        dot_wrapper.setStyleSheet("background: transparent;")
        dw_v = QVBoxLayout(dot_wrapper)
        dw_v.setContentsMargins(0, 0, 0, 0)
        dw_v.setSpacing(0)
        dw_v.addSpacing(6)
        dot = QFrame()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(
            f"background-color: {border_color}; border-radius: 3px;"
        )
        dw_v.addWidget(dot)
        dw_v.addStretch()
        row.addWidget(dot_wrapper)

        txt_lbl = QLabel(msg)
        txt_lbl.setFont(_f(FS_BASE))
        txt_lbl.setStyleSheet(f"color: {get_token('text')}; background: transparent;")
        txt_lbl.setWordWrap(True)
        row.addWidget(txt_lbl, 1)

        layout.addLayout(row)

    return card


# ──────────────────────────────────────────────────────────────
# Background worker
# ──────────────────────────────────────────────────────────────


class _LCCAWorker(QObject):
    """Runs the full LCC analysis on a background thread."""

    finished = Signal(object, object, object)
    errored = Signal(object, str)

    def __init__(self, all_data: dict, analysis_period_years: int):
        super().__init__()
        self._all_data = all_data
        self._analysis_period_years = analysis_period_years
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            all_data = self._all_data
            if self._cancel:
                return
            is_global, data_object = DataPreparer.prepare_data_object(
                all_data, self._analysis_period_years
            )
            if self._cancel:
                return
            wpi_metadata = None
            if not is_global:
                wpi_metadata = DataPreparer.prepare_wpi_object(all_data)
            if self._cancel:
                return
            lcc_breakdown = DataPreparer.prepare_life_cycle_construction_cost(all_data)
            if self._cancel:
                return
            results = run_full_lcc_analysis(
                data_object, lcc_breakdown, wpi=wpi_metadata, debug=True
            )
            self.finished.emit(results, all_data, lcc_breakdown)
        except Exception as exc:
            self.errored.emit(exc, traceback.format_exc())


# ──────────────────────────────────────────────────────────────
# Summary cards
# ──────────────────────────────────────────────────────────────


class LCCSummaryCards(QWidget):
    """Three top-line KPI cards: Total LCCA, Initial Investment, Future Liabilities."""

    def __init__(self, results: dict, currency: str, parent=None):
        super().__init__(parent)
        self._results = results
        self._currency = currency
        self._cards = []
        self._last_cols = None
        self._setup_ui()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def _setup_ui(self):
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, SP3, 0, SP5)
        self._grid.setSpacing(SP5)

        summary = compute_all_summaries(self._results)
        stagewise = summary.get("stagewise", {})

        total_lcca = sum(stagewise.values())
        initial = stagewise.get("initial", 0)
        future = stagewise.get("use_reconstruction", 0) + stagewise.get("end_of_life", 0)

        cards_data = [
            (
                "Total Life-Cycle Cost (NPV)",
                total_lcca,
                get_token("primary"),
                "Comprehensive total of all life-cycle expenditures discounted to the assessment year.",
            ),
            (
                "Initial Cost",
                initial,
                get_token("success"),
                "Cumulative total of construction, economic, social, and environmental costs incurred during the initial phase.",
            ),
            (
                "Future Cost",
                future,
                get_token("warning"),
                "Cumulative cost expected for maintenance, repairs, replacement and demolition.",
            ),
        ]

        for title, val, color, subtitle in cards_data:
            self._cards.append(self._create_card(title, val, color, subtitle))

        self._rearrange(self.width())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rearrange(event.size().width())

    def _rearrange(self, width: int):
        new_cols = width >= 750
        if self._last_cols == new_cols:
            return
        self._last_cols = new_cols
        for i in reversed(range(self._grid.count())):
            self._grid.takeAt(i)
        if not new_cols:
            for i, card in enumerate(self._cards):
                self._grid.addWidget(card, i, 0)
        else:
            for i, card in enumerate(self._cards):
                self._grid.addWidget(card, 0, i)

    def _create_card(self, title: str, value: float, color_hex: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setObjectName("kpiCard")
        card.setStyleSheet(
            f"#kpiCard {{"
            f"  background-color: {get_token('surface')};"
            f"  border: 1px solid {get_token('surface_mid')};"
            f"  border-radius: {RADIUS_LG}px;"
            f"}}"
        )

        v = QVBoxLayout(card)
        v.setContentsMargins(SP5, SP4, SP5, SP4)
        v.setSpacing(0)

        title_lbl = QLabel(title.upper())
        title_lbl.setWordWrap(False)
        title_lbl.setFont(_f(FS_SM, FW_MEDIUM))
        title_lbl.setStyleSheet(
            f"color: {get_token('text_secondary')}; letter-spacing: 1px; border: none;"
        )
        v.addWidget(title_lbl)
        v.addSpacing(SP3)

        val_str = fmt_currency(value, self._currency, decimals=0)
        val_lbl = QLabel(val_str)
        val_lbl.setWordWrap(False)
        val_lbl.setFont(_f(FS_DISP, FW_BOLD))
        val_lbl.setStyleSheet(f"color: {color_hex}; border: none;")
        v.addWidget(val_lbl)

        curr_lbl = QLabel(self._currency)
        curr_lbl.setFont(_f(FS_XS, FW_NORMAL))
        curr_lbl.setStyleSheet(
            f"color: {get_token('text_disabled')}; border: none; letter-spacing: 0.5px;"
        )
        v.addWidget(curr_lbl)
        v.addSpacing(SP3)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setWordWrap(True)
        sub_lbl.setFont(_f(FS_MD, FW_NORMAL))
        sub_lbl.setStyleSheet(f"color: {get_token('text_secondary')}; border: none;")
        v.addWidget(sub_lbl)

        card.setMinimumHeight(140)
        return card


# ──────────────────────────────────────────────────────────────
# Report intro
# ──────────────────────────────────────────────────────────────


class LCCIntroWidget(QWidget):
    """One-paragraph context block shown at the top of every results report."""

    def __init__(self, results: dict, analysis_period: int, currency: str, parent=None):
        super().__init__(parent)
        self._build(results, analysis_period, currency)

    def _build(self, results: dict, analysis_period: int, currency: str):
        stages_present = []
        if results.get("initial_stage"):
            stages_present.append("Initial Construction")
        if results.get("use_stage"):
            stages_present.append("Use & Maintenance")
        if results.get("reconstruction"):
            stages_present.append("Reconstruction")
        if results.get("end_of_life"):
            stages_present.append("End-of-Life")
        stage_str = " → ".join(stages_present)

        ap_str = f"{analysis_period}-year" if analysis_period else "full"
        body = (
            f"This report presents a <b>{ap_str}</b> life-cycle cost analysis "
            f"in <b>{currency}</b>, covering: {stage_str}."
        )

        frame = QFrame(self)
        frame.setObjectName("introFrame")
        frame.setStyleSheet(
            f"#introFrame {{"
            f"  background-color: {get_token('surface')};"
            f"  border-left: 3px solid {get_token('primary')};"
            f"  border-top: 1px solid {get_token('surface_mid')};"
            f"  border-right: 1px solid {get_token('surface_mid')};"
            f"  border-bottom: 1px solid {get_token('surface_mid')};"
            f"  border-radius: {RADIUS_LG}px;"
            f"}}"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(SP5, SP4, SP5, SP4)
        fl.setSpacing(SP2)

        title = QLabel("About This Report")
        title.setFont(_f(FS_LG, FW_BOLD))
        title.setStyleSheet(f"color: {get_token('text')}; border: none;")
        fl.addWidget(title)

        lbl = QLabel(body)
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.RichText)
        lbl.setFont(_f(FS_BASE))
        lbl.setStyleSheet(f"color: {get_token('text_secondary')}; border: none;")
        fl.addWidget(lbl)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)


# ──────────────────────────────────────────────────────────────
# Key findings / smart insights
# ──────────────────────────────────────────────────────────────


class LCCInsightsWidget(QWidget):
    """Auto-generated key findings computed directly from LCCA results."""

    _TOKEN_COLORS = {
        "primary": "primary",
        "warning": "warning",
        "danger": "danger",
        "success": "success",
        "text": "text_secondary",
    }

    def __init__(self, results: dict, currency: str, parent=None):
        super().__init__(parent)
        self._currency = currency
        self._build(results)

    def _build(self, results: dict):
        findings = self._compute(results)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        card = QFrame()
        card.setObjectName("insightsCard")
        card.setStyleSheet(
            f"#insightsCard {{"
            f"  background-color: {get_token('surface')};"
            f"  border: 1px solid {get_token('surface_mid')};"
            f"  border-radius: {RADIUS_LG}px;"
            f"}}"
        )
        card_v = QVBoxLayout(card)
        card_v.setContentsMargins(SP4, SP3, SP4, SP3)
        card_v.setSpacing(0)

        for i, (icon, color_token, html) in enumerate(findings):
            bullet_color = get_token(self._TOKEN_COLORS.get(color_token, "text_secondary"))

            if i > 0:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setFixedHeight(1)
                sep.setStyleSheet(
                    f"background-color: {get_token('surface_mid')}; border: none;"
                )
                card_v.addWidget(sep)

            row_frame = QFrame()
            row_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
            row_h = QHBoxLayout(row_frame)
            row_h.setContentsMargins(0, SP3, 0, SP3)
            row_h.setSpacing(SP3)

            dot_wrapper = QWidget()
            dot_wrapper.setFixedWidth(10)
            dot_wrapper.setStyleSheet("background: transparent;")
            dw_v = QVBoxLayout(dot_wrapper)
            dw_v.setContentsMargins(0, 0, 0, 0)
            dw_v.setSpacing(0)
            dw_v.addSpacing(5)
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(
                f"background-color: {bullet_color}; border-radius: 4px; border: none;"
            )
            dw_v.addWidget(dot)
            dw_v.addStretch()
            row_h.addWidget(dot_wrapper)

            lbl = QLabel(html)
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.RichText)
            lbl.setFont(_f(FS_BASE))
            lbl.setStyleSheet(f"color: {get_token('text')}; background: transparent;")
            row_h.addWidget(lbl, 1)

            card_v.addWidget(row_frame)

        outer.addWidget(card)

    def _compute(self, r: dict) -> list:
        """Return list of (icon, color_token, html_text) tuples."""
        c = self._currency
        findings = []

        def _get(stage, pillar, key, default=0.0):
            return r.get(stage, {}).get(pillar, {}).get(key, default)

        def _stage_total(stage):
            return sum(
                sum(v.values()) if isinstance(v, dict) else 0
                for v in r.get(stage, {}).values()
                if isinstance(v, dict)
            )

        def _pillar_total(stage, pillar):
            return sum(r.get(stage, {}).get(pillar, {}).values())

        all_stages = ["initial_stage", "use_stage", "reconstruction", "end_of_life"]
        stage_totals_raw = {s: _stage_total(s) for s in all_stages}
        grand = sum(stage_totals_raw.values()) or 1.0

        eco_total = sum(_pillar_total(s, "economic") for s in all_stages)
        env_total = sum(_pillar_total(s, "environmental") for s in all_stages)
        soc_total = sum(_pillar_total(s, "social") for s in all_stages)

        stage_labels = {
            "initial_stage": "Initial Construction",
            "use_stage": "Use & Maintenance",
            "reconstruction": "Reconstruction",
            "end_of_life": "End-of-Life",
        }
        dominant = max(stage_totals_raw, key=stage_totals_raw.get)
        dom_pct = stage_totals_raw[dominant] / grand * 100
        dom_val = fmt_currency(stage_totals_raw[dominant], c, decimals=0)
        findings.append((
            "●", "primary",
            f"<b>{stage_labels[dominant]}</b> is the largest cost stage at "
            f"<b>{dom_pct:.0f}%</b> of total lifecycle cost ({c} {dom_val}).",
        ))

        soc_pct = soc_total / grand * 100
        eco_pct = eco_total / grand * 100
        findings.append((
            "●", "warning",
            f"Road users carry <b>{soc_pct:.0f}%</b> of the total life cycle cost through traffic delays "
            f"and detours. This 'Social Cost' is often hidden from traditional budgets, which "
            f"primarily focus on the owner's direct spending (currently <b>{eco_pct:.0f}%</b>).",
        ))

        construction = _get("initial_stage", "economic", "initial_construction_cost")
        ruc_init = _get("initial_stage", "social", "initial_road_user_cost")
        if construction > 0 and ruc_init > 0:
            ratio = ruc_init / construction
            findings.append((
                "●", "danger",
                f"Building this bridge costs road users <b>{c} {fmt_currency(ruc_init, c, decimals=0)}</b> "
                f"in delays—that is <b>{ratio:.1f}× the construction contract value</b> "
                f"({c} {fmt_currency(construction, c, decimals=0)}). Faster construction directly reduces this social burden.",
            ))

        bej = _get("use_stage", "economic", "replacement_costs_for_bearing_and_expansion_joint")
        use_eco = _pillar_total("use_stage", "economic") or 1.0
        if bej > 0:
            bej_pct = bej / use_eco * 100
            findings.append((
                "●", "text",
                f"Bearing & expansion joint replacements account for <b>{bej_pct:.0f}%</b> of all "
                f"maintenance expenditure ({c} {fmt_currency(bej, c, decimals=0)}). "
                f"This is the single largest recurring maintenance cost item.",
            ))

        recon_soc = _pillar_total("reconstruction", "social")
        eol_soc = _pillar_total("end_of_life", "social")
        if recon_soc > 0 and eol_soc > 0:
            rd_ratio = recon_soc / eol_soc
            findings.append((
                "●", "warning",
                f"Mid-life reconstruction disrupts road users <b>{rd_ratio:.1f}× more</b> than "
                f"final end-of-life demolition ({c} {fmt_currency(recon_soc, c, decimals=0)} vs "
                f"{c} {fmt_currency(eol_soc, c, decimals=0)}). Minimising reconstruction frequency "
                f"has an outsized social benefit.",
            ))

        env_pct = env_total / grand * 100
        mat_c = _get("initial_stage", "environmental", "initial_material_carbon_emission_cost")
        veh_c = _get("initial_stage", "environmental", "initial_vehicular_emission_cost")
        carbon_note = ""
        if mat_c > 0 and veh_c > 0:
            mc_ratio = mat_c / veh_c
            carbon_note = (
                f" The environmental impact of construction materials is "
                f"<b>{mc_ratio:.0f}× higher</b> than the impact of vehicle detours during construction."
            )
        findings.append((
            "●", "success",
            f"Environmental (carbon) costs represent <b>{env_pct:.1f}%</b> of the total project "
            f"impact. While smaller than economic costs, they represent the project's direct "
            f"contribution to climate change.{carbon_note}",
        ))

        scrap_recon = _get("reconstruction", "economic", "total_scrap_value")
        scrap_eol = _get("end_of_life", "economic", "total_scrap_value")
        if scrap_recon == 0 and scrap_eol == 0:
            findings.append((
                "●", "text",
                "No residual or scrap value is recovered at reconstruction or end-of-life. "
                "Designing for material recovery (steel, aggregate) could offset demolition costs.",
            ))

        loan_init = _get("initial_stage", "economic", "time_cost_of_loan")
        if loan_init > 0 and construction > 0:
            loan_pct = loan_init / construction * 100
            findings.append((
                "●", "text",
                f"Financing cost over the loan period is <b>{loan_pct:.1f}%</b> of construction value "
                f"({c} {fmt_currency(loan_init, c, decimals=0)})- a relatively small component of total cost.",
            ))

        return findings


# ──────────────────────────────────────────────────────────────
# Main outputs page
# ──────────────────────────────────────────────────────────────


class OutputsPage(ScrollableForm):
    navigate_requested = Signal(str)
    calculation_completed = Signal()
    validate_requested = Signal()
    compare_requested = Signal(str)

    CALC_TIMEOUT_MS = 30_000

    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name=CHUNK)
        self._pages = {}
        self._has_results = False
        self._calc_thread = None
        self._calc_worker = None
        self._timeout_timer = None
        self._elapsed_timer = None
        self._elapsed_secs = 0
        self._currency = ""
        self._current_status = "idle"
        self._status_args: dict = {}
        self._build_ui()
        theme_manager().theme_changed.connect(self._refresh_styles)

    # ── Layout construction ───────────────────────────────────

    def _build_ui(self):
        f = self.form

        self._header = QLabel("Outputs")
        self._header.setFont(_f(FS_DISP, FW_BOLD))
        self._header.setStyleSheet(
            f"color: {get_token('text')}; margin-bottom: {SP2}px;"
        )
        f.addRow(self._header)

        self.required_keys = build_form(self, OUTPUTS_FIELDS, None)
        self._ap_label = f.labelForField(self.analysis_period)

        self._btn_row = QWidget()
        btn_layout = QHBoxLayout(self._btn_row)
        btn_layout.setContentsMargins(0, SP3, 0, SP5)

        self.btn_calculate = QPushButton("Validate inputs")
        self.btn_calculate.setFixedHeight(BTN_LG)
        self.btn_calculate.setFixedWidth(180)
        self.btn_calculate.setFont(_f(FS_MD, FW_MEDIUM))
        self.btn_calculate.setStyleSheet(btn_primary())
        self.btn_calculate.clicked.connect(self.validate_requested.emit)
        btn_layout.addWidget(self.btn_calculate)
        btn_layout.addStretch()
        f.addRow(self._btn_row)

        self._status_widget = QWidget()
        self._status_layout = QVBoxLayout(self._status_widget)
        self._status_layout.setContentsMargins(0, 0, 0, 0)
        self._status_layout.setSpacing(SP4)
        f.addRow(self._status_widget)

        self._show_idle()

    # ── Theme refresh ─────────────────────────────────────────

    def _refresh_styles(self):
        self._header.setFont(_f(FS_DISP, FW_BOLD))
        self._header.setStyleSheet(
            f"color: {get_token('text')}; margin-bottom: {SP2}px;"
        )
        self.btn_calculate.setStyleSheet(btn_primary())
        s = self._current_status
        if s == "idle":
            self._show_idle()
        elif s == "issues":
            self.show_results(
                self._status_args["errors"], self._status_args["warnings"]
            )
        elif s == "success":
            self.show_success()
        elif s == "calc_error":
            self._show_calculation_error(
                self._status_args["error"], self._status_args.get("tb", "")
            )
        elif s == "calc_success" and hasattr(self, "_last_results"):
            self._show_calculation_success(self._last_results)

    # ── Status area helpers ───────────────────────────────────

    def _clear_status(self):
        while self._status_layout.count():
            item = self._status_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _set_inputs_visible(self, visible: bool):
        f = self.form
        for row in range(1, f.rowCount() - 1):
            for role in (
                QFormLayout.FieldRole,
                QFormLayout.SpanningRole,
                QFormLayout.LabelRole,
            ):
                item = f.itemAt(row, role)
                if item and item.widget():
                    item.widget().setVisible(visible)

    def _inline_banner(self, text: str, token: str) -> QWidget:
        """Status banner with a coloured left strip."""
        outer = QWidget()
        h = QHBoxLayout(outer)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        strip = QFrame()
        strip.setFixedWidth(3)
        strip.setStyleSheet(f"background-color: {get_token(token)}; border-radius: 2px;")
        h.addWidget(strip)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: transparent; border: none; }")
        v = QVBoxLayout(inner)
        v.setContentsMargins(SP3, SP2, SP3, SP2)
        lbl = QLabel(text)
        lbl.setFont(_f(FS_BASE, FW_MEDIUM))
        lbl.setStyleSheet(f"color: {get_token(token)}; background: transparent;")
        v.addWidget(lbl)
        h.addWidget(inner, 1)

        return outer

    # ── State: idle ───────────────────────────────────────────

    def _show_idle(self):
        self._current_status = "idle"
        self._clear_status()
        self._set_inputs_visible(True)

        card = QFrame()
        card.setObjectName("idleCard")
        card.setStyleSheet(
            f"#idleCard {{"
            f"  background-color: {get_token('surface')};"
            f"  border-left: 3px solid {get_token('primary')};"
            f"  border-top: 1px solid {get_token('surface_mid')};"
            f"  border-right: 1px solid {get_token('surface_mid')};"
            f"  border-bottom: 1px solid {get_token('surface_mid')};"
            f"  border-radius: {RADIUS_LG}px;"
            f"}}"
        )
        card_v = QVBoxLayout(card)
        card_v.setContentsMargins(SP4, SP3, SP4, SP3)

        hint = QLabel(
            "Set the analysis period above, then press Validate to check all "
            "input pages before running the life-cycle cost calculation."
        )
        hint.setFont(_f(FS_BASE))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {get_token('text_secondary')}; background: transparent;")
        card_v.addWidget(hint)

        self._status_layout.addWidget(card)

    # ── State: calculating ────────────────────────────────────

    def _show_calculating(self):
        self._current_status = "calculating"
        self._clear_status()
        self.btn_calculate.setEnabled(False)

        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(SP4, SP4, SP4, SP4)
        v.setSpacing(SP3)

        h_row = QWidget()
        h = QHBoxLayout(h_row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(SP2)

        status_lbl = QLabel("Running life-cycle cost analysis…")
        status_lbl.setFont(_f(FS_MD, FW_MEDIUM))
        h.addWidget(status_lbl)
        h.addStretch()

        self._elapsed_label = QLabel("0 s")
        self._elapsed_label.setFont(_f(FS_SM))
        self._elapsed_label.setStyleSheet(
            f"color: {get_token('text_secondary')}; background: transparent;"
        )
        h.addWidget(self._elapsed_label)
        v.addWidget(h_row)

        activity_bar = QProgressBar()
        activity_bar.setRange(0, 0)
        activity_bar.setTextVisible(False)
        activity_bar.setFixedHeight(6)
        v.addWidget(activity_bar)

        self._status_layout.addWidget(container)

        self._elapsed_secs = 0
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)
        self._elapsed_timer.start()

        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.setInterval(self.CALC_TIMEOUT_MS)
        self._timeout_timer.timeout.connect(self._on_calc_timeout)
        self._timeout_timer.start()

    def _tick_elapsed(self):
        self._elapsed_secs += 1
        if hasattr(self, "_elapsed_label"):
            self._elapsed_label.setText(f"{self._elapsed_secs} s")

    def _stop_timers(self):
        if self._timeout_timer:
            self._timeout_timer.stop()
            self._timeout_timer.deleteLater()
            self._timeout_timer = None
        if self._elapsed_timer:
            self._elapsed_timer.stop()
            self._elapsed_timer.deleteLater()
            self._elapsed_timer = None

    def _on_calc_timeout(self):
        self._stop_timers()
        if self._calc_worker:
            self._calc_worker.cancel()
        self.btn_calculate.setEnabled(True)
        self._show_calculation_error(
            TimeoutError("Analysis timed out after 30 seconds."), ""
        )

    # ── State: validation issues ──────────────────────────────

    def show_results(self, all_errors: dict, all_warnings: dict):
        self._current_status = "issues"
        self._status_args = {"errors": all_errors, "warnings": all_warnings}
        self._clear_status()
        self._set_inputs_visible(True)
        self._save_state("issues", {"errors": all_errors, "warnings": all_warnings})

        if all_errors:
            self._status_layout.addWidget(
                self._inline_banner("Calculation blocked — fix the errors below", "danger")
            )
            for page, issues in all_errors.items():
                self._status_layout.addWidget(
                    _make_issue_card(page, issues, "error", self.navigate_requested.emit)
                )

        if all_warnings:
            self._status_layout.addWidget(
                self._inline_banner("Warnings — review before proceeding", "warning")
            )
            for page, issues in all_warnings.items():
                self._status_layout.addWidget(
                    _make_issue_card(page, issues, "warning", self.navigate_requested.emit)
                )

        if not all_errors:
            run_btn = QPushButton("Proceed with Calculation")
            run_btn.setFixedHeight(BTN_LG)
            run_btn.setStyleSheet(btn_primary())
            run_btn.clicked.connect(self._on_proceed)
            self._status_layout.addWidget(run_btn)

        self._status_layout.addStretch()

    # ── State: validation passed ──────────────────────────────

    def show_success(self):
        self._current_status = "success"
        self._clear_status()
        self._set_inputs_visible(True)
        self._save_state("success", {})
        self._status_layout.addWidget(
            self._inline_banner(
                "All checks passed — calculation will start automatically", "success"
            )
        )
        self._status_layout.addStretch()

    # ── State: calculation error ──────────────────────────────

    def _show_calculation_error(self, error: Exception, tb: str = ""):
        self._current_status = "calc_error"
        self._status_args = {"error": error, "tb": tb}
        self._save_state("calc_error", {"error": str(error)})
        self.btn_calculate.setEnabled(True)
        self._set_inputs_visible(True)
        self._clear_status()

        card = QFrame()
        card.setObjectName("calcErrorCard")
        card.setStyleSheet(
            f"#calcErrorCard {{"
            f"  background-color: {get_token('surface')};"
            f"  border: 1px solid {get_token('surface_mid')};"
            f"  border-left: 4px solid {get_token('danger')};"
            f"  border-radius: {RADIUS_LG}px;"
            f"}}"
        )
        v = QVBoxLayout(card)
        v.setContentsMargins(SP4, SP4, SP4, SP4)
        v.setSpacing(SP2)

        title_lbl = QLabel(f"Analysis Failed: {type(error).__name__}")
        title_lbl.setFont(_f(FS_MD, FW_SEMIBOLD))
        title_lbl.setStyleSheet(
            f"color: {get_token('danger')}; background: transparent;"
        )
        v.addWidget(title_lbl)

        msg = str(error).splitlines()[0] if str(error) else "An unknown error occurred."
        msg_lbl = QLabel(msg)
        msg_lbl.setFont(_f(FS_BASE))
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(
            f"color: {get_token('text_secondary')}; background: transparent;"
        )
        v.addWidget(msg_lbl)

        retry_btn = QPushButton("Retry")
        retry_btn.setFixedHeight(BTN_MD)
        retry_btn.setFont(_f(FS_BASE, FW_MEDIUM))
        retry_btn.setStyleSheet(btn_primary())
        retry_btn.clicked.connect(self.validate_requested.emit)
        v.addWidget(retry_btn, 0, Qt.AlignLeft)

        self._status_layout.addWidget(card)
        self._status_layout.addStretch()

    # ── State: calculation success ────────────────────────────

    def _show_calculation_success(self, results):
        self._current_status = "calc_success"
        self.btn_calculate.setEnabled(True)
        self._set_inputs_visible(False)
        self._last_results = results
        self._clear_status()

        # Toolbar for results (PDF + Comparison)
        toolbar_row = QWidget()
        tl_h = QHBoxLayout(toolbar_row)
        tl_h.setContentsMargins(0, 0, 0, SP3)
        tl_h.setSpacing(SP3)

        pdf_btn = QPushButton("Generate PDF Report")
        pdf_btn.setFixedHeight(BTN_MD)
        pdf_btn.setFont(_f(FS_BASE, FW_MEDIUM))
        pdf_btn.setStyleSheet(btn_primary())
        pdf_btn.clicked.connect(self._generate_pdf_report)
        tl_h.addWidget(pdf_btn)

        comp_btn = QPushButton("Add to Comparison ↗")
        comp_btn.setFixedHeight(BTN_MD)
        comp_btn.setFont(_f(FS_BASE, FW_MEDIUM))
        comp_btn.setStyleSheet(btn_ghost())
        comp_btn.setToolTip("Close project and add to the comparison workspace")
        comp_btn.clicked.connect(self._on_compare_clicked)
        tl_h.addWidget(comp_btn)

        tl_h.addStretch()
        self._status_layout.addWidget(toolbar_row)

        sections = [
            lambda r: _section_heading("At a Glance"),
            lambda r: LCCSummaryCards(r, currency=self._currency),
            lambda r: _divider(),
            lambda r: _section_heading("Life cycle cost distribution"),
            lambda r: _section_description(
                "These charts illustrate the distribution of project costs. The Sustainability Matrix disaggregates costs across the Economic, Environmental, and Social Pillars. The aggregation chart compares the relative weight of three lifecycle phases: Initial Construction, the combined Use/Maintenance/Reconstruction stage, and the final End-of-Life phase."
            ),
            lambda r: LCCPieWidget(r, currency=self._currency),
            lambda r: AggregateChartWidget(r, currency=self._currency),
            lambda r: _divider(),
            lambda r: _section_heading("Consolidated stage summary"),
            lambda r: _section_description(
                "A consolidated presentation of costs across the three pillars (economic, social, and environmental) for each lifecycle stage. This table facilitates the identification of phases that bear the most substantial burden."
            ),
            lambda r: LCCDetailsTable(r, currency=self._currency),
            lambda r: _divider(),
            lambda r: _section_heading("Itemized detail"),
            lambda r: _section_description(
                "An itemised schedule of each individual cost component. All values are discounted to the year of assessment, thus representing the present sum of money required to meet future expenditures."
            ),
            lambda r: LCCBreakdownTable(r, currency=self._currency),
        ]
        QTimer.singleShot(0, lambda: self._build_result_widgets(results, sections))

    def _build_result_widgets(self, results, sections):
        insert_pos = 1  # pdf_row is at 0; insert result sections after it
        for factory in sections:
            try:
                widget = factory(results)
                if widget:
                    self._status_layout.insertWidget(insert_pos, widget)
                    insert_pos += 1
            except Exception as e:
                err = QLabel(f"Render error: {e}")
                err.setFont(_f(FS_BASE, italic=True))
                err.setStyleSheet(f"color: {get_token('text_secondary')};")
                self._status_layout.insertWidget(insert_pos, err)
                insert_pos += 1

        scroll = self.layout.itemAt(0).widget()
        if scroll and hasattr(scroll, "verticalScrollBar"):
            scroll.verticalScrollBar().setValue(0)

    # ── Page wiring ───────────────────────────────────────────

    def register_pages(self, widget_map: dict):
        self._pages = {
            n: p
            for n, p in widget_map.items()
            if n != "Outputs" and hasattr(p, "validate")
        }

    # ── Validation & calculation ──────────────────────────────

    def run_validation(self):
        all_errors = {}
        all_warnings = {}
        ap = self.analysis_period.value()

        if ap <= 0:
            self.analysis_period.setStyleSheet(
                f"border: 1.5px solid {get_token('danger')};"
            )
            all_errors["Analysis Period"] = [
                "Required field must be greater than zero."
            ]
        else:
            self.analysis_period.setStyleSheet("")

        for name, page in self._pages.items():
            res = page.validate()
            if isinstance(res, dict):
                if res.get("errors"):
                    all_errors[name] = res["errors"]
                if res.get("warnings"):
                    all_warnings[name] = res["warnings"]
            else:
                status, issues = res
                if status == ValidationStatus.ERROR:
                    all_errors[name] = issues
                elif status == ValidationStatus.WARNING:
                    all_warnings[name] = issues

        if all_errors or all_warnings:
            self.show_results(all_errors, all_warnings)
        else:
            self.show_success()
            self.run_calculation()

    def run_calculation(self, save_cache: bool = True):
        self._save_cache_on_finish = save_cache
        all_data = {}
        for name, page in self._pages.items():
            if hasattr(page, "get_data"):
                res = page.get_data()
                all_data[res["chunk"]] = res["data"]

        self._currency = all_data.get("general_info", {}).get("project_currency")
        self._show_calculating()

        self._calc_thread = QThread(self)
        self._calc_worker = _LCCAWorker(all_data, int(self.analysis_period.value()))
        self._calc_worker.moveToThread(self._calc_thread)

        self._calc_thread.started.connect(self._calc_worker.run)
        self._calc_worker.finished.connect(self._on_calc_finished)
        self._calc_worker.errored.connect(self._on_calc_errored)
        self._calc_worker.finished.connect(self._calc_thread.quit)
        self._calc_worker.errored.connect(self._calc_thread.quit)
        self._calc_thread.finished.connect(self._calc_thread.deleteLater)

        QTimer.singleShot(0, self._calc_thread.start)

    def _on_calc_finished(self, results, all_data, lcc_breakdown):
        self._stop_timers()
        self._has_results = True
        self._last_all_data = all_data
        self._last_lcc_breakdown = lcc_breakdown
        
        if getattr(self, "_save_cache_on_finish", True):
            self._write_comparison_cache(results, all_data, lcc_breakdown)
            
        self._show_calculation_success(results)
        self.calculation_completed.emit()

    def _on_calc_errored(self, exc, tb):
        self._stop_timers()
        self._show_calculation_error(exc, tb)

    # ── Toolbar / public API ──────────────────────────────────

    def reset_for_edit(self):
        self._has_results = False
        self._show_idle()
        self._save_state("idle", {})
        self._destroy_comparison_cache()

    def freeze(self, frozen: bool):
        self.btn_calculate.setEnabled(not frozen)
        freeze_form(OUTPUTS_FIELDS, self, frozen)

    def clear_validation(self):
        clear_field_styles(OUTPUTS_FIELDS, self)

    def validate(self):
        return validate_form(OUTPUTS_FIELDS, self, warn_rules=OUTPUTS_WARN_RULES)

    def _on_field_changed(self):
        if not self._loading:
            self.data_changed.emit()
            if self.controller:
                self.controller.save_chunk_data(CHUNK_AP, self.get_data_dict())

    def refresh_from_engine(self):
        if (
            self.controller
            and self.controller.engine
            and self.controller.engine.is_active()
        ):
            data = self.controller.get_chunk(CHUNK_AP) or {}
            if data and data != self._loaded_data:
                self._loaded_data = data
                self.load_data_dict(data)

    def _build_export_dict(self) -> dict:
        d = DataPreparer.build_export_dict(
            getattr(self, "_last_all_data", {}),
            getattr(self, "_last_lcc_breakdown", {}),
            getattr(self, "_last_results", {}),
        )
        if self.controller:
            d["project_name"] = (
                self.controller.active_display_name or self.controller.active_project_id
            )
        return d

    def _generate_pdf_report(self):
        dlg = ReportSectionDialog(export_dict=self._build_export_dict(), parent=self)
        dlg.exec()

    def _on_proceed(self):
        self.run_calculation()

    def _on_compare_clicked(self):
        if self.controller and self.controller.active_project_id:
            self.compare_requested.emit(self.controller.active_project_id)

    def _write_comparison_cache(self, results: dict, all_data: dict, lcc_breakdown: dict):
        if self.controller:
            self.controller.save_chunk_data(CHUNK_COMPARISON, {
                "is_valid": True,
                "analysis_period": int(self.analysis_period.value()),
                "currency": self._currency,
                "all_data": all_data,
                "lcc_breakdown": lcc_breakdown,
                "results": results,
            })
            if self.controller.engine:
                self.controller.engine.force_sync()
                self.controller.engine.write_user_meta("fit_for_comparison", True)

    def _destroy_comparison_cache(self):
        if self.controller and self.controller.engine:
            self.controller.engine.delete_chunk(CHUNK_COMPARISON)
            self.controller.engine.write_user_meta("fit_for_comparison", False)

    def _save_state(self, status: str, data: dict):
        if self.controller and self.controller.engine:
            self.controller.engine.stage_update(
                chunk_name=self.chunk_name, data={"status": status, "data": data}
            )

    def on_refresh(self):
        if self.controller and self.controller.engine:
            self.refresh_from_engine()
            state = self.controller.engine.fetch_chunk(CHUNK) or {}
            s = state.get("status", "idle")
            d = state.get("data", {})
            if s == "issues":
                self.show_results(d.get("errors", {}), d.get("warnings", {}))
            elif s == "success":
                self.show_success()
            else:
                self._show_idle()
