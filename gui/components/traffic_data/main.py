from PySide6.QtWidgets import QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit
from gui.components.base_widget import ScrollableForm


class TrafficData(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="traffic_data")

        self.aadt          = self.field("aadt",           QSpinBox(),       min_val=0, max_val=10_000_000, placeholder="Vehicles/day")
        self.truck_percent = self.field("truck_percent",  QDoubleSpinBox(), min_val=0, max_val=100, suffix="%", decimals=1)
        self.growth_rate   = self.field("growth_rate",    QDoubleSpinBox(), min_val=0, max_val=20,  suffix="%", decimals=2)
        self.speed_limit   = self.field("speed_limit",    QDoubleSpinBox(), min_val=0, max_val=200, suffix="km/h", decimals=1)
        self.detour_length = self.field("detour_length",  QDoubleSpinBox(), min_val=0, max_val=500, suffix="km", decimals=2)
        self.detour_type   = self.field("detour_type",    QComboBox(),      items=["None", "Partial", "Full"])
        self.work_zone_duration = self.field("work_zone_duration", QSpinBox(), min_val=0, max_val=3650, suffix=" days")

        self.form.addRow("AADT (vehicles/day):",       self.aadt)
        self.form.addRow("Truck Percentage:",          self.truck_percent)
        self.form.addRow("Annual Growth Rate:",        self.growth_rate)
        self.form.addRow("Speed Limit:",               self.speed_limit)
        self.form.addRow("Detour Length:",             self.detour_length)
        self.form.addRow("Detour Type:",               self.detour_type)
        self.form.addRow("Work Zone Duration:",        self.work_zone_duration)