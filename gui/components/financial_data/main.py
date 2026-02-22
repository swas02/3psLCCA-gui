from PySide6.QtWidgets import QDoubleSpinBox, QComboBox, QSpinBox
from gui.components.base_widget import ScrollableForm


class FinancialData(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="financial_data")

        self.initial_cost       = self.field("initial_cost",       QDoubleSpinBox(), min_val=0, max_val=1e9,  suffix="", decimals=2)
        self.discount_rate      = self.field("discount_rate",      QDoubleSpinBox(), min_val=0, max_val=50,   suffix="%", decimals=2, default=3.5)
        self.analysis_period    = self.field("analysis_period",    QSpinBox(),       min_val=1, max_val=200,  suffix=" yr", default=75)
        self.inflation_rate     = self.field("inflation_rate",     QDoubleSpinBox(), min_val=0, max_val=50,   suffix="%", decimals=2)
        self.cost_escalation    = self.field("cost_escalation",    QDoubleSpinBox(), min_val=0, max_val=50,   suffix="%", decimals=2)
        self.residual_value     = self.field("residual_value",     QDoubleSpinBox(), min_val=0, max_val=1e9,  suffix="", decimals=2)
        self.funding_source     = self.field("funding_source",     QComboBox(),      items=["Government", "Private", "PPP", "Other"])

        self.form.addRow("Initial Construction Cost:", self.initial_cost)
        self.form.addRow("Discount Rate:",             self.discount_rate)
        self.form.addRow("Analysis Period:",           self.analysis_period)
        self.form.addRow("Inflation Rate:",            self.inflation_rate)
        self.form.addRow("Cost Escalation Rate:",      self.cost_escalation)
        self.form.addRow("Residual Value:",            self.residual_value)
        self.form.addRow("Funding Source:",            self.funding_source)