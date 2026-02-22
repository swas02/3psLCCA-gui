from PySide6.QtWidgets import QDoubleSpinBox, QComboBox
from gui.components.base_widget import ScrollableForm


class MaterialEmissions(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="carbon_material")

        self.cement_quantity  = self.field("cement_quantity",  QDoubleSpinBox(), min_val=0, max_val=1e6, suffix="t",      decimals=2)
        self.cement_ef        = self.field("cement_ef",        QDoubleSpinBox(), min_val=0, max_val=2,   suffix="tCO₂/t", decimals=4, default=0.8700)
        self.steel_quantity   = self.field("steel_quantity",   QDoubleSpinBox(), min_val=0, max_val=1e6, suffix="t",      decimals=2)
        self.steel_ef         = self.field("steel_ef",         QDoubleSpinBox(), min_val=0, max_val=5,   suffix="tCO₂/t", decimals=4, default=1.8500)
        self.aggregate_qty    = self.field("aggregate_qty",    QDoubleSpinBox(), min_val=0, max_val=1e6, suffix="t",      decimals=2)
        self.aggregate_ef     = self.field("aggregate_ef",     QDoubleSpinBox(), min_val=0, max_val=1,   suffix="tCO₂/t", decimals=4, default=0.0048)
        self.bitumen_qty      = self.field("bitumen_qty",      QDoubleSpinBox(), min_val=0, max_val=1e6, suffix="t",      decimals=2)
        self.bitumen_ef       = self.field("bitumen_ef",       QDoubleSpinBox(), min_val=0, max_val=5,   suffix="tCO₂/t", decimals=4, default=0.4140)

        self.form.addRow("Cement Quantity:",         self.cement_quantity)
        self.form.addRow("Cement Emission Factor:",  self.cement_ef)
        self.form.addRow("Steel Quantity:",          self.steel_quantity)
        self.form.addRow("Steel Emission Factor:",   self.steel_ef)
        self.form.addRow("Aggregate Quantity:",      self.aggregate_qty)
        self.form.addRow("Aggregate Emission Factor:", self.aggregate_ef)
        self.form.addRow("Bitumen Quantity:",        self.bitumen_qty)
        self.form.addRow("Bitumen Emission Factor:", self.bitumen_ef)