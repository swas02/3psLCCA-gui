from PySide6.QtWidgets import QDoubleSpinBox, QComboBox
from gui.components.base_widget import ScrollableForm


class Recycling(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="recycling_data")

        self.steel_weight       = self.field("steel_weight",       QDoubleSpinBox(), min_val=0, max_val=1e6, suffix="t",  decimals=2)
        self.steel_recycle_rate = self.field("steel_recycle_rate", QDoubleSpinBox(), min_val=0, max_val=100, suffix="%",  decimals=1, default=90.0)
        self.concrete_weight    = self.field("concrete_weight",    QDoubleSpinBox(), min_val=0, max_val=1e6, suffix="t",  decimals=2)
        self.concrete_recycle_rate = self.field("concrete_recycle_rate", QDoubleSpinBox(), min_val=0, max_val=100, suffix="%", decimals=1, default=70.0)
        self.recycling_revenue  = self.field("recycling_revenue",  QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.recycling_cost     = self.field("recycling_cost",     QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.recycling_method   = self.field("recycling_method",   QComboBox(),      items=["On-site", "Off-site", "Mixed"])

        self.form.addRow("Steel Weight:",              self.steel_weight)
        self.form.addRow("Steel Recycling Rate:",      self.steel_recycle_rate)
        self.form.addRow("Concrete Weight:",           self.concrete_weight)
        self.form.addRow("Concrete Recycling Rate:",   self.concrete_recycle_rate)
        self.form.addRow("Recycling Revenue:",         self.recycling_revenue)
        self.form.addRow("Recycling Cost:",            self.recycling_cost)
        self.form.addRow("Recycling Method:",          self.recycling_method)

