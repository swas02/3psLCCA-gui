from PySide6.QtWidgets import QDoubleSpinBox, QComboBox
from gui.components.base_widget import ScrollableForm


class SocialCost(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="carbon_social")

        self.social_cost_carbon = self.field("social_cost_carbon", QDoubleSpinBox(), min_val=0, max_val=1000, suffix="/tCO₂", decimals=2, default=51.0)
        self.currency           = self.field("currency",           QComboBox(),      items=["USD", "EUR", "GBP", "INR"])
        self.total_emissions    = self.field("total_emissions",    QDoubleSpinBox(), min_val=0, max_val=1e6,  suffix="tCO₂",  decimals=2)
        self.discount_rate      = self.field("discount_rate",      QDoubleSpinBox(), min_val=0, max_val=20,   suffix="%",      decimals=2, default=3.5)

        self.form.addRow("Social Cost of Carbon:",  self.social_cost_carbon)
        self.form.addRow("Currency:",               self.currency)
        self.form.addRow("Total Emissions:",        self.total_emissions)
        self.form.addRow("Discount Rate:",          self.discount_rate)