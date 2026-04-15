"""
gui/components/outputs/outputs_page.py
"""

import json
import logging
import traceback

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QObject, QThread, QTimer, Signal, QSize

from gui.themes import get_token, theme_manager
from gui.styles import (
    font as _f,
    btn_primary,
    btn_outline,
    btn_ghost,
)
from gui.theme import (
    SP1, SP2, SP3, SP4, SP5, SP6,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
    FS_XS, FS_SM, FS_BASE, FS_MD, FS_LG, FS_XL, 
    FS_DISP, FS_DISP_LG, FS_DISP_XL,
    FW_NORMAL, FW_MEDIUM, FW_SEMIBOLD, FW_BOLD,
    BTN_MD, BTN_SM, FONT_FAMILY
)
from gui.components.base_widget import ScrollableForm
from gui.components.utils.form_builder.form_definitions import (
    FieldDef,
    ValidationStatus,
)
from gui.components.utils.form_builder.form_builder import build_form
from gui.components.utils.validation_helpers import (
    clear_field_styles,
    freeze_form,
    validate_form,
)
from three_ps_lcca_core.core.main import run_full_lcc_analysis

from gui.components.utils.display_format import fmt_currency
from .lcc_plot import LCCBreakdownTable, LCCDetailsTable
from .plots_helper.Pie import LCCPieWidget
from .plots_helper.AggregateChart import AggregateChartWidget
from .helper_functions.lifecycle_summary import compute_all_summaries
from .data_preparer import DataPreparer
from .report_section_dialog import ReportSectionDialog



CHUNK = "outputs_data"
CHUNK_AP = "analysis_period"

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
        default=0,
    ),
]

OUTPUTS_WARN_RULES = {
    "analysis_period": (
        None,
        500,
        None,
        "Analysis period exceeds 500 years - please verify",
    ),
}
_log = logging.getLogger(__name__)


def _make_issue_card(page_name: str, issues: list, icon: str, navigate_cb) -> QGroupBox:
    """Standalone card widget for a single page's validation errors or warnings."""
    card = QGroupBox()
    card.setStyleSheet(
        f"QGroupBox {{ border: 1px solid {get_token('surface_mid')}; "
        f"border-radius: {RADIUS_MD}px; padding: {SP3}px; }}"
    )
    layout = QVBoxLayout(card)
    layout.setSpacing(SP2)

    h_row = QWidget()
    h_lay = QHBoxLayout(h_row)
    h_lay.setContentsMargins(0, 0, 0, 0)

    name_lbl = QLabel(page_name.upper())
    name_lbl.setFont(_f(FS_SM, FW_BOLD))
    name_lbl.setStyleSheet(f"color: {get_token('text_disabled')}; letter-spacing: 1px;")
    h_lay.addWidget(name_lbl, 0, Qt.AlignVCenter)
    h_lay.addStretch()

    go_btn = QPushButton("Fix Issues →")
    go_btn.setFixedHeight(26)
    go_btn.setFont(_f(FS_SM, FW_SEMIBOLD))
    go_btn.setStyleSheet(btn_ghost())
    go_btn.setCursor(Qt.PointingHandCursor)
    go_btn.clicked.connect(lambda checked=False, p=page_name: navigate_cb(p))
    h_lay.addWidget(go_btn, 0, Qt.AlignVCenter)

    layout.addWidget(h_row)

    for issue in issues:
        msg = issue if isinstance(issue, str) else issue.get("msg", str(issue))
        
        issue_row = QHBoxLayout()
        issue_row.setSpacing(SP2)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(_f(FS_MD))
        issue_row.addWidget(icon_lbl, 0, Qt.AlignTop)

        txt_lbl = QLabel(msg)
        txt_lbl.setFont(_f(FS_BASE))
        txt_lbl.setStyleSheet(f"color: {get_token('text')};")
        txt_lbl.setWordWrap(True)
        issue_row.addWidget(txt_lbl, 1)

        layout.addLayout(issue_row)

    return card



class _LCCAWorker(QObject):
    # Carries (results, all_data, lcc_breakdown)
    finished = Signal(object, object, object)
    errored = Signal(object, str)

    def __init__(self, all_data: dict, analysis_period_years: int):
        super().__init__()
        self._all_data = all_data
        self._analysis_period_years = analysis_period_years

    def run(self):
        try:
            all_data = self._all_data
            is_global, data_object = DataPreparer.prepare_data_object(all_data, self._analysis_period_years)
            wpi_metadata = None
            if not is_global:
                wpi_metadata = DataPreparer.prepare_wpi_object(all_data)
            lcc_breakdown = DataPreparer.prepare_life_cycle_construction_cost(all_data)
            results = run_full_lcc_analysis(data_object, lcc_breakdown, wpi=wpi_metadata, debug=True)
            self.finished.emit(results, all_data, lcc_breakdown)
        except Exception as exc:
            self.errored.emit(exc, traceback.format_exc())


class LCCSummaryCards(QWidget):
    def __init__(self, results: dict, currency: str = "INR", parent=None):
        super().__init__(parent)
        self._results = results
        self._currency = currency
        self._cards = []
        self._setup_ui()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def _setup_ui(self):
        self._grid_layout = QGridLayout(self)
        self._grid_layout.setContentsMargins(0, SP2, 0, SP4)
        self._grid_layout.setSpacing(SP4)

        summary = compute_all_summaries(self._results)
        stagewise = summary.get('stagewise', {})
        total_lcca = sum(stagewise.values())
        initial = stagewise.get('initial', 0)
        future = stagewise.get('use_reconstruction', 0) + stagewise.get('end_of_life', 0)

        cards_data = [
            ("Total LCCA (NPV)", total_lcca, get_token("primary"), "Cumulative cost across all life stages"),
            ("Initial Investment", initial, get_token("success"), "Capital expenditure for construction"),
            ("Future Liabilities", future, get_token("warning"), "Maintenance, repairs & end-of-life")
        ]

        for title, val, color, sub in cards_data:
            self._cards.append(self._create_card(title, val, color, sub))

        self._rearrange_layout(self.width())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rearrange_layout(event.size().width())

    def _rearrange_layout(self, width):
        is_narrow = width < 750
        for i in reversed(range(self._grid_layout.count())): self._grid_layout.takeAt(i)
        if is_narrow:
            for i, card in enumerate(self._cards): self._grid_layout.addWidget(card, i, 0)
        else:
            for i, card in enumerate(self._cards): self._grid_layout.addWidget(card, 0, i)

    def _create_card(self, title, value, color_hex, subtitle):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: transparent; border: 1.5px solid {get_token('surface_mid')}; border-radius: {RADIUS_XL}px; }}")
        v = QVBoxLayout(card); v.setContentsMargins(SP5, SP5, SP5, SP5); v.setSpacing(0)
        
        l1 = QLabel(title.upper()); l1.setWordWrap(True)
        l1.setStyleSheet(f"color: {get_token('text')}; font-family: {FONT_FAMILY}; font-size: {FS_MD}pt; font-weight: {FW_BOLD}; letter-spacing: 1.5px; border: none;")
        v.addWidget(l1); v.addSpacing(SP2)

        r = QWidget(); r.setStyleSheet("background: transparent; border: none;")
        rl = QHBoxLayout(r); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(SP1)
        
        curr = QLabel(self._currency)
        curr.setStyleSheet(f"color: {get_token('text_secondary')}; font-family: {FONT_FAMILY}; font-size: {FS_LG}pt; font-weight: {FW_BOLD}; margin-bottom: {SP2}px;")
        rl.addWidget(curr, 0, Qt.AlignBottom)
        
        val_str = fmt_currency(value, self._currency, decimals=0)
        val = QLabel(val_str); val.setWordWrap(True)
        val.setStyleSheet(f"color: {color_hex}; font-family: {FONT_FAMILY}; font-size: {FS_DISP_LG}pt; font-weight: {FW_BOLD};")
        rl.addWidget(val, 1, Qt.AlignBottom)
        v.addWidget(r); v.addSpacing(SP3)

        l2 = QLabel(subtitle); l2.setWordWrap(True)
        l2.setStyleSheet(f"color: {get_token('text_secondary')}; font-family: {FONT_FAMILY}; font-size: {FS_BASE}pt; font-weight: {FW_NORMAL}; border: none;")
        v.addWidget(l2)
        return card


class OutputsPage(ScrollableForm):
    navigate_requested = Signal(str)
    calculation_completed = Signal()
    validate_requested = Signal()

    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name=CHUNK)
        self._pages = {}
        self._has_results = False
        self._calc_thread = None
        self._calc_worker = None
        self._timeout_timer = None
        self._elapsed_timer = None
        self._elapsed_secs = 0
        self._currency = "INR"
        self._current_status = "idle"
        self._status_args: dict = {}
        self._build_ui()
        theme_manager().theme_changed.connect(self._refresh_styles)

    def _build_ui(self):
        f = self.form
        self._header = QLabel("Outputs")
        self._header.setFont(_f(FS_DISP, FW_BOLD))
        self._header.setStyleSheet(f"color: {get_token('primary')}; margin-bottom: {SP2}px;")
        f.addRow(self._header)

        self.required_keys = build_form(self, OUTPUTS_FIELDS, None)
        self._ap_label = f.labelForField(self.analysis_period)

        self._btn_row = QWidget()
        btn_layout = QHBoxLayout(self._btn_row); btn_layout.setContentsMargins(0, SP2, 0, SP4)
        self.btn_calculate = QPushButton("Validate  ▶")
        self.btn_calculate.setFixedHeight(BTN_MD); self.btn_calculate.setFixedWidth(180)
        self.btn_calculate.setFont(_f(FS_BASE, FW_MEDIUM)); self.btn_calculate.setStyleSheet(btn_primary())
        self.btn_calculate.clicked.connect(self.validate_requested.emit)
        btn_layout.addWidget(self.btn_calculate); btn_layout.addStretch()
        f.addRow(self._btn_row)

        self._status_widget = QWidget()
        self._status_layout = QVBoxLayout(self._status_widget)
        self._status_layout.setContentsMargins(0, 0, 0, 0); self._status_layout.setSpacing(SP4)
        f.addRow(self._status_widget)
        self._show_idle()

    def _refresh_styles(self):
        self._header.setStyleSheet(f"color: {get_token('primary')}; margin-bottom: {SP2}px;")
        self.btn_calculate.setStyleSheet(btn_primary())
        s = self._current_status
        if s == "idle": self._show_idle()
        elif s == "issues": self.show_results(self._status_args["errors"], self._status_args["warnings"])
        elif s == "success": self.show_success()
        elif s == "calc_error": self._show_calculation_error(self._status_args["error"], self._status_args.get("tb", ""))
        elif s == "calc_success" and hasattr(self, "_last_results"): self._show_calculation_success(self._last_results)

    def _clear_status(self):
        while self._status_layout.count():
            item = self._status_layout.takeAt(0)
            if item.widget(): item.widget().hide(); item.widget().setParent(None)

    def _set_inputs_visible(self, visible: bool):
        f = self.form
        for row in range(1, f.rowCount() - 1):
            for role in [QFormLayout.FieldRole, QFormLayout.SpanningRole, QFormLayout.LabelRole]:
                item = f.itemAt(row, role)
                if item and item.widget(): item.widget().setVisible(visible)

    def _show_idle(self):
        self._current_status = "idle"; self._clear_status(); self._set_inputs_visible(True)
        note = QLabel("Press Validate to check all pages for consistency before calculation.")
        note.setFont(_f(FS_BASE)); note.setStyleSheet(f"color: {get_token('text_secondary')}; font-style: italic;")
        self._status_layout.addWidget(note)

    CALC_TIMEOUT_MS = 30_000

    def _show_calculating(self):
        self._current_status = "calculating"; self._clear_status(); self.btn_calculate.setEnabled(False)
        c = QWidget(); v = QVBoxLayout(c); v.setContentsMargins(SP4, SP4, SP4, SP4); v.setSpacing(SP2)
        h_row = QWidget(); h = QHBoxLayout(h_row); h.setContentsMargins(0, 0, 0, 0)
        s_lbl = QLabel("⏳  Performing Analysis…"); s_lbl.setFont(_f(FS_MD, FW_MEDIUM)); h.addWidget(s_lbl); h.addStretch()
        self._elapsed_label = QLabel("0s / 30s"); self._elapsed_label.setFont(_f(FS_SM)); h.addWidget(self._elapsed_label); v.addWidget(h_row)
        bar = QProgressBar(); bar.setRange(0, 0); bar.setTextVisible(False); bar.setFixedHeight(8); v.addWidget(bar)
        self._countdown_bar = QProgressBar(); self._countdown_bar.setRange(0, 30); self._countdown_bar.setValue(30); self._countdown_bar.setTextVisible(False); self._countdown_bar.setFixedHeight(4); v.addWidget(self._countdown_bar)
        self._status_layout.addWidget(c)
        self._elapsed_secs = 0; self._elapsed_timer = QTimer(self); self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._tick_elapsed); self._elapsed_timer.start()
        self._timeout_timer = QTimer(self); self._timeout_timer.setSingleShot(True); self._timeout_timer.setInterval(30000)
        self._timeout_timer.timeout.connect(self._on_calc_timeout); self._timeout_timer.start()

    def _tick_elapsed(self):
        self._elapsed_secs += 1
        if hasattr(self, "_elapsed_label"): self._elapsed_label.setText(f"{self._elapsed_secs}s / 30s")
        if hasattr(self, "_countdown_bar"): self._countdown_bar.setValue(max(0, 30 - self._elapsed_secs))

    def _stop_timers(self):
        if self._timeout_timer: self._timeout_timer.stop(); self._timeout_timer.deleteLater(); self._timeout_timer = None
        if self._elapsed_timer: self._elapsed_timer.stop(); self._elapsed_timer.deleteLater(); self._elapsed_timer = None

    def _on_calc_timeout(self):
        self._stop_timers()
        if self._calc_thread and self._calc_thread.isRunning(): self._calc_thread.terminate()
        self.btn_calculate.setEnabled(True)
        self._show_calculation_error(TimeoutError("Analysis timed out."), "")

    def show_results(self, all_errors: dict, all_warnings: dict):
        self._current_status = "issues"; self._status_args = {"errors": all_errors, "warnings": all_warnings}; self._clear_status(); self._set_inputs_visible(True)
        if all_errors:
            banner = QGroupBox(); banner.setStyleSheet(f"QGroupBox {{ background: transparent; border: 1px solid {get_token('danger')}; border-radius: {RADIUS_MD}px; padding: {SP3}px; }}")
            v = QVBoxLayout(banner); t = QLabel("🛑  Calculation Blocked"); t.setFont(_f(FS_MD, FW_BOLD)); t.setStyleSheet(f"color: {get_token('danger')};"); v.addWidget(t); self._status_layout.addWidget(banner)
            for page, issues in all_errors.items(): self._status_layout.addWidget(_make_issue_card(page, issues, "❌", self.navigate_requested.emit))
        if all_warnings:
            banner = QGroupBox(); banner.setStyleSheet(f"QGroupBox {{ background: transparent; border: 1px solid {get_token('warning')}; border-radius: {RADIUS_MD}px; padding: {SP3}px; }}")
            v = QVBoxLayout(banner); t = QLabel("⚠️  Warnings"); t.setFont(_f(FS_MD, FW_BOLD)); t.setStyleSheet(f"color: {get_token('warning')};"); v.addWidget(t); self._status_layout.addWidget(banner)
            for page, issues in all_warnings.items(): self._status_layout.addWidget(_make_issue_card(page, issues, "🟡", self.navigate_requested.emit))
        if not all_errors:
            run_btn = QPushButton("Proceed with Calculation ▶"); run_btn.setFixedHeight(BTN_MD); run_btn.setStyleSheet(btn_primary()); run_btn.clicked.connect(self._on_proceed); self._status_layout.addWidget(run_btn)
        self._status_layout.addStretch()

    def show_success(self):
        self._current_status = "success"; self._clear_status(); self._set_inputs_visible(True)
        banner = QGroupBox(); banner.setStyleSheet(f"QGroupBox {{ background: transparent; border: 1px solid {get_token('success')}; border-radius: {RADIUS_MD}px; padding: {SP3}px; }}")
        v = QVBoxLayout(banner); t = QLabel("✅  All checks passed"); t.setFont(_f(FS_MD, FW_BOLD)); t.setStyleSheet(f"color: {get_token('success')};"); v.addWidget(t); self._status_layout.addWidget(banner); self._status_layout.addStretch()

    def register_pages(self, widget_map: dict):
        self._pages = {n: p for n, p in widget_map.items() if n != "Outputs" and hasattr(p, "validate")}

    def run_validation(self):
        all_errors = {}; all_warnings = {}; ap = self.analysis_period.value()
        if ap <= 0:
            self.analysis_period.setStyleSheet(f"border: 1.5px solid {get_token('danger')};")
            all_errors["Analysis Period"] = ["Required field must be greater than zero."]
        else: self.analysis_period.setStyleSheet("")
        for name, page in self._pages.items():
            res = page.validate()
            if isinstance(res, dict):
                if res.get("errors"): all_errors[name] = res["errors"]
                if res.get("warnings"): all_warnings[name] = res["warnings"]
            else:
                status, issues = res
                if status == ValidationStatus.ERROR: all_errors[name] = issues
                elif status == ValidationStatus.WARNING: all_warnings[name] = issues
        if all_errors or all_warnings: self.show_results(all_errors, all_warnings)
        else: self.show_success(); self.run_calculation()

    def run_calculation(self):
        all_data = {}
        for name, page in self._pages.items():
            if hasattr(page, "get_data"):
                res = page.get_data(); all_data[res["chunk"]] = res["data"]
        self._currency = all_data.get('general_info', {}).get('project_currency', "INR")
        self._show_calculating(); self._calc_thread = QThread(self)
        self._calc_worker = _LCCAWorker(all_data, int(self.analysis_period.value()))
        self._calc_worker.moveToThread(self._calc_thread); self._calc_thread.started.connect(self._calc_worker.run)
        self._calc_worker.finished.connect(self._on_calc_finished); self._calc_worker.errored.connect(self._on_calc_errored)
        self._calc_worker.finished.connect(self._calc_thread.quit); self._calc_worker.errored.connect(self._calc_thread.quit)
        self._calc_thread.finished.connect(self._calc_thread.deleteLater); QTimer.singleShot(0, self._calc_thread.start)

    def _on_calc_finished(self, results, all_data, lcc_breakdown):
        self._stop_timers(); self._last_all_data, self._last_lcc_breakdown = all_data, lcc_breakdown
        self._show_calculation_success(results)

    def _on_calc_errored(self, exc, tb): self._stop_timers(); self._show_calculation_error(exc, tb)

    def _show_calculation_error(self, error: Exception, tb: str = ""):
        self._current_status = "calc_error"; self._status_args = {"error": error, "tb": tb}; self.btn_calculate.setEnabled(True); self._set_inputs_visible(True); self._clear_status()
        banner = QGroupBox(); banner.setStyleSheet(f"QGroupBox {{ border: 1px solid {get_token('danger')}; border-radius: {RADIUS_MD}px; padding: {SP4}px; }}")
        v = QVBoxLayout(banner); t = QLabel(f"🛑  Analysis Failed: {type(error).__name__}"); t.setFont(_f(FS_LG, FW_BOLD)); t.setStyleSheet(f"color: {get_token('danger')};"); v.addWidget(t)
        m = QLabel(str(error).splitlines()[0] if str(error) else "Unknown error"); m.setFont(_f(FS_BASE)); m.setWordWrap(True); v.addWidget(m); self._status_layout.addWidget(banner); self._status_layout.addStretch()

    def _show_calculation_success(self, results):
        self._current_status = "calc_success"; self.btn_calculate.setEnabled(True); self._set_inputs_visible(False); self._last_results = results; self._clear_status()
        banner = QGroupBox(); banner.setStyleSheet(f"QGroupBox {{ background: transparent; border: 1px solid {get_token('success')}; border-radius: {RADIUS_MD}px; padding: {SP3}px; }}")
        v = QVBoxLayout(banner); t = QLabel("✅  Analysis completed successfully."); t.setFont(_f(FS_MD, FW_BOLD)); t.setStyleSheet(f"color: {get_token('success')};"); v.addWidget(t)
        btns = QHBoxLayout(); pdf_btn = QPushButton("📄  Generate PDF Report"); pdf_btn.setFixedHeight(34); pdf_btn.setFont(_f(FS_SM, FW_MEDIUM)); pdf_btn.setStyleSheet(btn_primary()); pdf_btn.clicked.connect(self._generate_pdf_report); btns.addWidget(pdf_btn); v.addLayout(btns); self._status_layout.addWidget(banner)

        self._pending_results = results
        def _add_hr():
            line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFixedHeight(1); line.setStyleSheet(f"background-color: {get_token('surface_mid')}; margin-top: {SP4}px; margin-bottom: {SP2}px; border: none;")
            return line
        def _add_text(text, is_sub=False):
            lbl = QLabel(text); lbl.setWordWrap(True)
            if is_sub: lbl.setFont(_f(FS_MD)); lbl.setStyleSheet(f"color: {get_token('text_secondary')}; margin-bottom: {SP4}px; line-height: 1.5;")
            else: lbl.setFont(_f(FS_DISP, FW_BOLD)); lbl.setStyleSheet(f"color: {get_token('text')}; margin-top: {SP5}px; margin-bottom: {SP2}px; letter-spacing: 0.5px;")
            return lbl

        self._result_build_steps = [
            lambda r: LCCSummaryCards(r, currency=self._currency),
            lambda r: LCCPieWidget(r, currency=self._currency),
            lambda r: AggregateChartWidget(r, currency=self._currency),
            lambda r: _add_hr(),
            lambda r: _add_text("Comprehensive Lifecycle Cost Breakdown"),
            lambda r: _add_text("This breakdown isolates every individual cost component spanning the entire lifecycle of the infrastructure. By converting future liabilities into Net Present Value (NPV), it normalizes the temporal value of money, empowering engineers and stakeholders to accurately identify high-impact cost drivers. Use this granular visibility to pinpoint targeted design optimizations that yield the most substantial long-term economic and environmental savings.", True),
            lambda r: LCCBreakdownTable(r, currency=self._currency),
            lambda r: _add_hr(),
            lambda r: _add_text("Executive Sustainability Summary"),
            lambda r: _add_text("This table consolidates the granular breakdown into the three foundational pillars of sustainability: Economic (direct capital and maintenance outlays), Environmental (monetized carbon footprints), and Social (impacts on public mobility and safety). This 'triple-bottom-line' synthesis transcends traditional financial accounting, providing a holistic metric of the project's true cost to society over its entire design life, critical for justifying sustainable investments.", True),
            lambda r: LCCDetailsTable(r, currency=self._currency),
        ]
        QTimer.singleShot(0, self._build_next_result_widget)

    def _build_next_result_widget(self):
        if not self._result_build_steps: return
        factory = self._result_build_steps.pop(0)
        try:
            widget = factory(self._pending_results)
            if widget:
                # Insert with No Alignment (fills 100% width)
                self._status_layout.insertWidget(self._status_layout.count() - 1, widget)
        except Exception as e:
            err = QLabel(f"Chart error: {e}"); err.setStyleSheet("color: gray; font-style: italic;"); self._status_layout.insertWidget(self._status_layout.count() - 1, err)
        QTimer.singleShot(0, self._build_next_result_widget)

    def reset_for_edit(self): self._has_results = False; self._show_idle(); self._save_state("idle", {})
    def freeze(self, frozen: bool): self.btn_calculate.setEnabled(not frozen); freeze_form(OUTPUTS_FIELDS, self, frozen)
    def clear_validation(self): clear_field_styles(OUTPUTS_FIELDS, self)
    def validate(self): return validate_form(OUTPUTS_FIELDS, self, warn_rules=OUTPUTS_WARN_RULES)
    def _on_field_changed(self):
        if not self._loading:
            self.data_changed.emit()
            if self.controller: self.controller.save_chunk_data(CHUNK_AP, self.get_data_dict())
    def refresh_from_engine(self):
        if self.controller and self.controller.engine and self.controller.engine.is_active():
            data = self.controller.get_chunk(CHUNK_AP) or {}
            if data and data != self._loaded_data: self._loaded_data = data; self.load_data_dict(data)
    def _build_export_dict(self) -> dict: return DataPreparer.build_export_dict(getattr(self, "_last_all_data", {}), getattr(self, "_last_lcc_breakdown", {}), getattr(self, "_last_results", {}))
    def _generate_pdf_report(self): dlg = ReportSectionDialog(export_dict=self._build_export_dict(), parent=self); dlg.exec()
    def _on_proceed(self): self.run_calculation()
    def _save_state(self, status: str, data: dict):
        if self.controller and self.controller.engine: self.controller.engine.stage_update(chunk_name=self.chunk_name, data={"status": status, "data": data})
    def on_refresh(self):
        if self.controller and self.controller.engine:
            self.refresh_from_engine()
            state = self.controller.engine.fetch_chunk(CHUNK) or {}
            s = state.get("status", "idle"); d = state.get("data", {})
            if s == "issues": self.show_results(d.get("errors", {}), d.get("warnings", {}))
            elif s == "success": self.show_success()
            else: self._show_idle()
