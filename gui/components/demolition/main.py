from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox
from gui.components.base_widget import ScrollableForm


class Demolition(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="demolition_data")

        self.demolition_cost    = self.field("demolition_cost",    QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.demolition_year    = self.field("demolition_year",    QSpinBox(),       min_val=1, max_val=200, suffix=" yr")
        self.waste_volume       = self.field("waste_volume",       QDoubleSpinBox(), min_val=0, max_val=1e6, suffix="m³", decimals=2)
        self.disposal_cost      = self.field("disposal_cost",      QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.demolition_method  = self.field("demolition_method",  QComboBox(),      items=["Conventional", "Implosion", "Deconstruction"])
        self.landfill_distance  = self.field("landfill_distance",  QDoubleSpinBox(), min_val=0, max_val=500, suffix="km", decimals=1)

        self.form.addRow("Demolition Cost:",           self.demolition_cost)
        self.form.addRow("Demolition Year:",           self.demolition_year)
        self.form.addRow("Waste Volume:",              self.waste_volume)
        self.form.addRow("Disposal Cost:",             self.disposal_cost)
        self.form.addRow("Demolition Method:",         self.demolition_method)
        self.form.addRow("Landfill Distance:",         self.landfill_distance)