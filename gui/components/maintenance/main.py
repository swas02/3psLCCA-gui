from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox
from gui.components.base_widget import ScrollableForm


class Maintenance(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="maintenance_data")

        self.routine_cost       = self.field("routine_cost",       QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.routine_interval   = self.field("routine_interval",   QSpinBox(),       min_val=1, max_val=50,  suffix=" yr", default=1)
        self.major_cost         = self.field("major_cost",         QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.major_interval     = self.field("major_interval",     QSpinBox(),       min_val=1, max_val=100, suffix=" yr", default=20)
        self.rehab_cost         = self.field("rehab_cost",         QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.rehab_year         = self.field("rehab_year",         QSpinBox(),       min_val=1, max_val=200, suffix=" yr", default=40)
        self.inspection_cost    = self.field("inspection_cost",    QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.inspection_interval= self.field("inspection_interval",QSpinBox(),       min_val=1, max_val=20,  suffix=" yr", default=2)
        self.maintenance_strategy = self.field("maintenance_strategy", QComboBox(), items=["Corrective", "Preventive", "Condition-based"])

        self.form.addRow("Routine Maintenance Cost:",  self.routine_cost)
        self.form.addRow("Routine Interval:",          self.routine_interval)
        self.form.addRow("Major Repair Cost:",         self.major_cost)
        self.form.addRow("Major Repair Interval:",     self.major_interval)
        self.form.addRow("Rehabilitation Cost:",       self.rehab_cost)
        self.form.addRow("Rehabilitation Year:",       self.rehab_year)
        self.form.addRow("Inspection Cost:",           self.inspection_cost)
        self.form.addRow("Inspection Interval:",       self.inspection_interval)
        self.form.addRow("Maintenance Strategy:",      self.maintenance_strategy)
