from PySide6.QtWidgets import (QDoubleSpinBox, QSpinBox, QPushButton, 
                             QLabel, QHBoxLayout, QWidget, QToolButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from gui.components.base_widget import BaseDataWidget

# Metadata: (key, label, unit, is_integer, is_required, doc_url)
BASE_DOCS_URL = "https://yourdocs.com/financial/"
FINANCIAL_FIELDS = [
    ("discount_rate", "Discount Rate", "(%)", False, True, f"{BASE_DOCS_URL}discount-rate"),
    ("inflation_rate", "Inflation Rate", "(%)", False, True, f"{BASE_DOCS_URL}inflation-rate"),
    ("interest_rate", "Interest Rate", "(%)", False, True, f"{BASE_DOCS_URL}interest-rate"),
    ("investment_ratio", "Investment Ratio", "", False, True, f"{BASE_DOCS_URL}investment-ratio"),
    ("design_life", "Design Life", "(years)", True, True, f"{BASE_DOCS_URL}design-life"),
    ("duration_of_construction", "Duration of Construction", "(years)", False, False, f"{BASE_DOCS_URL}duration-of-construction"),
    ("analysis_period", "Analysis Period", "(years)", True, True, f"{BASE_DOCS_URL}analysis-period"),
]

class FinancialData(BaseDataWidget):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="financial_data")
        
        self.required_keys = []

        # 1. Build UI Loop
        for key, label_text, unit, is_integer, is_required, doc_url in FINANCIAL_FIELDS:
            # Create the numeric input
            if is_integer:
                widget = QSpinBox()
                widget.setRange(0, 999)
            else:
                widget = QDoubleSpinBox()
                widget.setRange(0.00, 100.00)
                widget.setDecimals(2)
                if key == "investment_ratio":
                    widget.setRange(0.0000, 1.0000)
                    widget.setDecimals(4)

            if unit:
                widget.setSuffix(f" {unit}")

            # Register with BaseDataWidget and track required fields
            setattr(self, key, self.field(key, widget))
            if is_required:
                self.required_keys.append(key)

            # Reset style on change (clears validation error highlight)
            widget.valueChanged.connect(lambda _, w=widget: w.setStyleSheet(""))

            # 2. Help Button (i) and Container
            row_container = QWidget()
            row_layout = QHBoxLayout(row_container)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            help_btn = QToolButton()
            help_btn.setText("ⓘ")
            help_btn.setCursor(Qt.PointingHandCursor)
            help_btn.setToolTip("Click to view documentation")
            help_btn.clicked.connect(lambda checked=False, url=doc_url: QDesktopServices.openUrl(url))

            row_layout.addWidget(widget, 1) # Widget takes available space
            row_layout.addWidget(help_btn)

            # 3. Label Handling
            display_text = f"{label_text} *" if is_required else label_text
            lbl = QLabel(display_text)
            if is_required:
                lbl.setStyleSheet("font-weight: bold;")

            self.form.addRow(lbl, row_container)

        # 4. Load Suggested Values Button
        self.btn_load_suggested = QPushButton("Load Suggested Values")
        self.btn_load_suggested.setMinimumHeight(30)
        self.btn_load_suggested.clicked.connect(self.load_suggested_values)
        self.form.addRow("", self.btn_load_suggested)

    def load_suggested_values(self):
        """Applies hard-coded defaults to the UI."""
        defaults = {
            "discount_rate": 6.70,
            "inflation_rate": 5.15,
            "interest_rate": 7.75,
            "investment_ratio": 0.5000,
            "design_life": 50,
            "duration_of_construction": 0,
            "analysis_period": 50
        }
        for key, val in defaults.items():
            widget = getattr(self, key, None)
            if widget:
                widget.setValue(val)
                widget.setStyleSheet("") # Clear any errors

        self._on_field_changed()
        if self.controller and self.controller.engine:
            self.controller.engine._log("Financial: Suggested values applied.")

    def validate(self):
        """
        Validates that required fields are non-zero.
        Returns (bool, list_of_errors)
        """
        errors = []
        for key in self.required_keys:
            widget = getattr(self, key, None)
            if widget and widget.value() <= 0:
                # Find label for the error message
                label = next(f[1] for f in FINANCIAL_FIELDS if f[0] == key)
                errors.append(label)
                widget.setStyleSheet("background-color: #fff0f0; border: 1px solid red;")
        
        if errors:
            msg = f"Missing required financial data: {', '.join(errors)}"
            if self.controller and self.controller.engine:
                self.controller.engine._log(msg)
            return False, errors
            
        return True, []