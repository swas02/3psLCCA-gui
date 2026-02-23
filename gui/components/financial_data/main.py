from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
    QToolButton,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from gui.components.base_widget import BaseDataWidget


BASE_DOCS_URL = "https://yourdocs.com/financial/"

# (key, title, explanation, unit, is_integer, is_required, doc_slug)
FINANCIAL_FIELDS = [
    (
        "discount_rate",
        "Discount Rate",
        "The rate used to convert future cash flows into present value. "
        "It reflects the time value of money and investment risk.",
        "(%)",
        False,
        True,
        "discount-rate",
    ),
    (
        "inflation_rate",
        "Inflation Rate",
        "Expected annual increase in general price levels over time.",
        "(%)",
        False,
        True,
        "inflation-rate",
    ),
    (
        "interest_rate",
        "Interest Rate",
        "The borrowing or lending rate applied to capital financing.",
        "(%)",
        False,
        True,
        "interest-rate",
    ),
    (
        "investment_ratio",
        "Investment Ratio",
        "Proportion of total cost financed through investment (0–1). "
        "Example: 0.5 means 50%.",
        "",
        False,
        True,
        "investment-ratio",
    ),
    (
        "design_life",
        "Design Life",
        "Expected operational lifetime of the system in years.",
        "(years)",
        True,
        True,
        "design-life",
    ),
    (
        "duration_of_construction",
        "Duration of Construction",
        "Time required to complete construction before operation begins.",
        "(years)",
        False,
        False,
        "duration-of-construction",
    ),
    (
        "analysis_period",
        "Analysis Period",
        "Total time horizon used for financial evaluation.",
        "(years)",
        True,
        True,
        "analysis-period",
    ),
]


class FinancialData(BaseDataWidget):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="financial_data")

        self.required_keys = []

        for (
            key,
            title,
            explanation,
            unit,
            is_integer,
            is_required,
            doc_slug,
        ) in FINANCIAL_FIELDS:

            section = QWidget()
            layout = QVBoxLayout(section)
            layout.setContentsMargins(0, 10, 0, 10)
            layout.setSpacing(4)

            # --- Title ---
            title_label = QLabel(f"{title} *" if is_required else title)
            title_label.setStyleSheet("font-weight: 600;")
            layout.addWidget(title_label)

            # --- Explanation with small inline "i" ---
            doc_url = f"{BASE_DOCS_URL}{doc_slug}"

            explanation_html = (
                explanation + f' <a href="{doc_url}" '
                'style="text-decoration:none;'
                'font-weight:600;"> ⓘ</a>'
            )

            explanation_label = QLabel(explanation_html)
            explanation_label.setWordWrap(True)
            explanation_label.setTextFormat(Qt.RichText)
            explanation_label.setOpenExternalLinks(True)

            layout.addWidget(explanation_label)

            # --- Input ---
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

            widget.setMinimumHeight(30)

            setattr(self, key, self.field(key, widget))

            if is_required:
                self.required_keys.append(key)

            widget.valueChanged.connect(lambda _, w=widget: w.setStyleSheet(""))

            layout.addWidget(widget)
            self.form.addRow(section)

        # --- Load Suggested Button ---
        self.btn_load_suggested = QPushButton("Load Suggested Values")
        self.btn_load_suggested.setMinimumHeight(35)
        self.btn_load_suggested.clicked.connect(self.load_suggested_values)
        self.form.addRow(self.btn_load_suggested)

    def load_suggested_values(self):
        defaults = {
            "discount_rate": 6.70,
            "inflation_rate": 5.15,
            "interest_rate": 7.75,
            "investment_ratio": 0.5000,
            "design_life": 50,
            "duration_of_construction": 0,
            "analysis_period": 50,
        }

        for key, val in defaults.items():
            widget = getattr(self, key, None)
            if widget:
                widget.setValue(val)
                widget.setStyleSheet("")

        self._on_field_changed()

        if self.controller and self.controller.engine:
            self.controller.engine._log("Financial: Suggested values applied.")

    def validate(self):
        errors = []

        for key in self.required_keys:
            widget = getattr(self, key, None)
            if widget and widget.value() <= 0:
                label = next(f[1] for f in FINANCIAL_FIELDS if f[0] == key)
                errors.append(label)
                widget.setStyleSheet("border: 1px solid red;")

        if errors:
            msg = f"Missing required financial data: {', '.join(errors)}"
            if self.controller and self.controller.engine:
                self.controller.engine._log(msg)
            return False, errors

        return True, []
