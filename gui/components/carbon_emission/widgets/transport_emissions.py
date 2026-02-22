from PySide6.QtWidgets import QDoubleSpinBox
from gui.components.base_widget import ScrollableForm


class TransportEmissions(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="carbon_transport")

        self.material_mass   = self.field("material_mass",   QDoubleSpinBox(), min_val=0, max_val=1e6,  suffix="t",          decimals=2)
        self.transport_dist  = self.field("transport_dist",  QDoubleSpinBox(), min_val=0, max_val=5000, suffix="km",         decimals=1)
        self.emission_factor = self.field("emission_factor", QDoubleSpinBox(), min_val=0, max_val=1,    suffix="tCO2/t.km",  decimals=6, default=0.000062)
        self.num_trips       = self.field("num_trips",       QDoubleSpinBox(), min_val=0, max_val=1e5,  decimals=0)

        self.form.addRow("Total Material Mass:",   self.material_mass)
        self.form.addRow("Transport Distance:",    self.transport_dist)
        self.form.addRow("Emission Factor:",       self.emission_factor)
        self.form.addRow("Number of Trips:",       self.num_trips)