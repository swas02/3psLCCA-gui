from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox
from gui.components.base_widget import ScrollableForm


class TrafficEmissions(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="carbon_traffic")

        self.diverted_vehicles = self.field("diverted_vehicles", QSpinBox(),       min_val=0, max_val=1_000_000)
        self.detour_length     = self.field("detour_length",     QDoubleSpinBox(), min_val=0, max_val=500,  suffix="km",      decimals=2)
        self.car_ef            = self.field("car_ef",            QDoubleSpinBox(), min_val=0, max_val=1,    suffix="tCO₂/km", decimals=6, default=0.000192)
        self.truck_ef          = self.field("truck_ef",          QDoubleSpinBox(), min_val=0, max_val=1,    suffix="tCO₂/km", decimals=6, default=0.000900)
        self.truck_percent     = self.field("truck_percent",     QDoubleSpinBox(), min_val=0, max_val=100,  suffix="%",       decimals=1)
        self.work_zone_days    = self.field("work_zone_days",    QSpinBox(),       min_val=0, max_val=3650)

        self.form.addRow("Diverted Vehicles/day:",  self.diverted_vehicles)
        self.form.addRow("Detour Length:",          self.detour_length)
        self.form.addRow("Car Emission Factor:",    self.car_ef)
        self.form.addRow("Truck Emission Factor:",  self.truck_ef)
        self.form.addRow("Truck Percentage:",       self.truck_percent)
        self.form.addRow("Work Zone Duration:",     self.work_zone_days)