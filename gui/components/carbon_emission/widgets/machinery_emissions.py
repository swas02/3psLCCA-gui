from PySide6.QtWidgets import QDoubleSpinBox
from gui.components.base_widget import ScrollableForm


class MachineryEmissions(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="carbon_machinery")

        self.fuel_consumption = self.field("fuel_consumption", QDoubleSpinBox(), min_val=0, max_val=1e6, suffix="L",       decimals=2)
        self.fuel_ef          = self.field("fuel_ef",          QDoubleSpinBox(), min_val=0, max_val=5,   suffix="tCO2/kL", decimals=4, default=2.6800)
        self.equipment_hours  = self.field("equipment_hours",  QDoubleSpinBox(), min_val=0, max_val=1e5, suffix="hr",      decimals=1)
        self.idle_factor      = self.field("idle_factor",      QDoubleSpinBox(), min_val=0, max_val=1,   decimals=2,       default=0.15)

        self.form.addRow("Fuel Consumption:",     self.fuel_consumption)
        self.form.addRow("Fuel Emission Factor:", self.fuel_ef)
        self.form.addRow("Equipment Hours:",      self.equipment_hours)
        self.form.addRow("Idle Factor:",          self.idle_factor)