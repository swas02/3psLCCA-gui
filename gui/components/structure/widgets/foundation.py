from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit
from gui.components.base_widget import ScrollableForm


class Foundation(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="structure_foundation")

        self.foundation_type  = self.field("foundation_type",  QComboBox(),      items=["Pile", "Spread Footing", "Well Foundation", "Raft"])
        self.pile_length      = self.field("pile_length",      QDoubleSpinBox(), min_val=0, max_val=200,  suffix="m",  decimals=2)
        self.pile_diameter    = self.field("pile_diameter",    QDoubleSpinBox(), min_val=0, max_val=10,   suffix="m",  decimals=3)
        self.num_piles        = self.field("num_piles",        QSpinBox(),       min_val=0, max_val=1000)
        self.concrete_grade   = self.field("concrete_grade",   QComboBox(),      items=["M20", "M25", "M30", "M35", "M40", "M45", "M50"])
        self.steel_grade      = self.field("steel_grade",      QComboBox(),      items=["Fe415", "Fe500", "Fe550"])
        self.concrete_volume  = self.field("concrete_volume",  QDoubleSpinBox(), min_val=0, max_val=1e5,  suffix="m³", decimals=2)
        self.steel_weight     = self.field("steel_weight",     QDoubleSpinBox(), min_val=0, max_val=1e6,  suffix="t",  decimals=2)
        self.unit_cost        = self.field("unit_cost",        QDoubleSpinBox(), min_val=0, max_val=1e9,  decimals=2)

        self.form.addRow("Foundation Type:",   self.foundation_type)
        self.form.addRow("Pile Length:",       self.pile_length)
        self.form.addRow("Pile Diameter:",     self.pile_diameter)
        self.form.addRow("Number of Piles:",   self.num_piles)
        self.form.addRow("Concrete Grade:",    self.concrete_grade)
        self.form.addRow("Steel Grade:",       self.steel_grade)
        self.form.addRow("Concrete Volume:",   self.concrete_volume)
        self.form.addRow("Steel Weight:",      self.steel_weight)
        self.form.addRow("Unit Cost:",         self.unit_cost)