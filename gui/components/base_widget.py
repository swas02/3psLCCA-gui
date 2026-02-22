"""
gui/components/base_widget.py

Centralized base for all data-entry panels in the LCCA app.
Handles: field registration, autosave, load-from-engine, signal wiring.

Usage in subclasses:
    class MyPanel(ScrollableForm):
        def __init__(self, controller=None):
            super().__init__(controller=controller, chunk_name="my_chunk")

            self.my_line  = self.field("my_key",  QLineEdit(), placeholder="Enter value")
            self.my_spin  = self.field("my_spin", QDoubleSpinBox(), min_val=0, max_val=100, suffix="m")
            self.my_combo = self.field("my_combo", QComboBox(), items=["A", "B", "C"])

            self.form.addRow("My Field:",  self.my_line)
            self.form.addRow("My Spin:",   self.my_spin)
            self.form.addRow("My Combo:",  self.my_combo)

That's it. Save / load / autosave are fully automatic.
"""

from PySide6.QtWidgets import (
    QWidget, QLineEdit, QComboBox, QDoubleSpinBox,
    QSpinBox, QCheckBox, QTextEdit, QFormLayout,
    QScrollArea, QVBoxLayout
)
from PySide6.QtCore import Signal, Qt


class BaseDataWidget(QWidget):
    """
    Base class for all data-entry widgets.

    Subclasses only need to:
      1. Call super().__init__(controller=..., chunk_name="...")
      2. Use self.field(key, widget, **options) to create + register each input
      3. Build their layout normally

    Everything else (autosave, load, signal wiring) is automatic.
    """
    data_changed = Signal()

    def __init__(self, controller=None, chunk_name: str = None):
        super().__init__()
        self.controller = controller
        self.chunk_name = chunk_name
        self._field_map = {}    # key -> widget
        self._loading   = False

        if self.controller and hasattr(self.controller, 'project_loaded'):
            self.controller.project_loaded.connect(self.refresh_from_engine)

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def field(self, key: str, widget: QWidget, *,
              default=None,
              placeholder: str = None,
              suffix: str = None,
              decimals: int = None,
              min_val=None,
              max_val=None,
              items: list = None) -> QWidget:
        """
        Configure, register, and return a field widget in one call.

        Args:
            key:         JSON key this widget maps to in the saved chunk.
            widget:      A QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
                         QCheckBox, or QTextEdit instance.
            default:     Initial value applied to the widget.
            placeholder: Placeholder text  (QLineEdit / QTextEdit).
            suffix:      Unit suffix string (QDoubleSpinBox / QSpinBox).
            decimals:    Decimal places     (QDoubleSpinBox).
            min_val:     Minimum value      (spin boxes).
            max_val:     Maximum value      (spin boxes).
            items:       Strings to populate a QComboBox.

        Returns the configured widget so it can be assigned + laid out inline.
        """
        # Configure
        if placeholder and isinstance(widget, (QLineEdit, QTextEdit)):
            widget.setPlaceholderText(placeholder)

        if suffix and isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            widget.setSuffix(f" {suffix}")

        if decimals is not None and isinstance(widget, QDoubleSpinBox):
            widget.setDecimals(decimals)

        if min_val is not None and isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            widget.setMinimum(min_val)

        if max_val is not None and isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            widget.setMaximum(max_val)

        if items and isinstance(widget, QComboBox):
            widget.addItems(items)

        if default is not None:
            self._apply_value(widget, default)

        # Register
        self._field_map[key] = widget
        self._connect_widget(widget)

        return widget

    def register_field(self, key: str, widget: QWidget) -> QWidget:
        """
        Back-compat alias for field() without options.
        GeneralInfo and BridgeData use this — no changes needed there.
        """
        self._field_map[key] = widget
        self._connect_widget(widget)
        return widget

    def refresh_from_engine(self):
        """Loads stored data from the engine into all registered widgets."""
        if not self.controller or not self.controller.engine:
            return
        if not self.controller.engine.is_active() or not self.chunk_name:
            return
        data = self.controller.engine.fetch_chunk(self.chunk_name)
        if data:
            self.load_data_dict(data)

    def get_data_dict(self) -> dict:
        """Extracts current widget values into a plain dict for saving."""
        data = {}
        for key, widget in self._field_map.items():
            if isinstance(widget, QLineEdit):
                data[key] = widget.text()
            elif isinstance(widget, QTextEdit):
                data[key] = widget.toPlainText()
            elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                data[key] = widget.value()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                data[key] = widget.isChecked()
        return data

    def load_data_dict(self, data: dict):
        """
        Populates widgets from a dict.
        Blocks all change signals during load to prevent feedback-loop autosaves.
        """
        if not data:
            return
        self._loading = True
        try:
            for key, widget in self._field_map.items():
                if key not in data:
                    continue
                widget.blockSignals(True)
                try:
                    self._apply_value(widget, data[key])
                finally:
                    widget.blockSignals(False)
        finally:
            self._loading = False

    # ── INTERNALS ─────────────────────────────────────────────────────────────

    def _connect_widget(self, widget: QWidget):
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(self._on_field_changed)
        elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            widget.valueChanged.connect(self._on_field_changed)
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(self._on_field_changed)
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(self._on_field_changed)
        elif isinstance(widget, QTextEdit):
            widget.textChanged.connect(self._on_field_changed)

    def _on_field_changed(self):
        if self._loading:
            return
        self.data_changed.emit()
        if self.controller and self.chunk_name:
            self.controller.save_chunk_data(self.chunk_name, self.get_data_dict())

    @staticmethod
    def _apply_value(widget: QWidget, val):
        """Write a value to any supported widget type."""
        if isinstance(widget, QLineEdit):
            widget.setText(str(val))
        elif isinstance(widget, QTextEdit):
            widget.setPlainText(str(val))
        elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            widget.setValue(float(val))
        elif isinstance(widget, QComboBox):
            idx = widget.findText(str(val))
            if idx >= 0:
                widget.setCurrentIndex(idx)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(val))


# ── SCROLLABLE FORM ───────────────────────────────────────────────────────────

class ScrollableForm(BaseDataWidget):
    """
    A BaseDataWidget that wraps its content in a QScrollArea and exposes
    a QFormLayout (self.form) for adding labelled rows.

    This is the recommended base class for all flat data-entry panels.
    Tab-based panels (Structure, CarbonEmission) use BaseDataWidget directly
    since they manage their own layout.

    Example:
        class TrafficData(ScrollableForm):
            def __init__(self, controller=None):
                super().__init__(controller=controller, chunk_name="traffic_data")
                self.aadt = self.field("aadt", QSpinBox(), min_val=0, max_val=10_000_000)
                self.form.addRow("AADT:", self.aadt)
    """

    def __init__(self, controller=None, chunk_name: str = None):
        super().__init__(controller=controller, chunk_name=chunk_name)

        # Inner widget holds the form
        self._content = QWidget()
        self.form = QFormLayout(self._content)
        self.form.setContentsMargins(24, 20, 24, 20)
        self.form.setSpacing(12)
        self.form.setLabelAlignment(Qt.AlignRight)

        # Wrap in scroll area
        scroll = QScrollArea()
        scroll.setWidget(self._content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)