from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox
from gui.components.base_widget import ScrollableForm


class SuperStruct(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="structure_superstructure")

        self.bridge_type      = self.field("bridge_type",      QComboBox(),      items=["Simply Supported", "Continuous", "Cantilever", "Arch", "Cable-stayed", "Suspension"])
        self.span_length      = self.field("span_length",      QDoubleSpinBox(), min_val=0, max_val=2000, suffix="m",  decimals=2)
        self.num_spans        = self.field("num_spans",        QSpinBox(),       min_val=1, max_val=100)
        self.deck_width       = self.field("deck_width",       QDoubleSpinBox(), min_val=0, max_val=100,  suffix="m",  decimals=2)
        self.deck_thickness   = self.field("deck_thickness",   QDoubleSpinBox(), min_val=0, max_val=5,    suffix="m",  decimals=3)
        self.concrete_grade   = self.field("concrete_grade",   QComboBox(),      items=["M25", "M30", "M35", "M40", "M45", "M50"])
        self.steel_grade      = self.field("steel_grade",      QComboBox(),      items=["Fe415", "Fe500", "Fe550"])
        self.concrete_volume  = self.field("concrete_volume",  QDoubleSpinBox(), min_val=0, max_val=1e5,  suffix="m³", decimals=2)
        self.steel_weight     = self.field("steel_weight",     QDoubleSpinBox(), min_val=0, max_val=1e6,  suffix="t",  decimals=2)
        self.unit_cost        = self.field("unit_cost",        QDoubleSpinBox(), min_val=0, max_val=1e9,  decimals=2)

        self.form.addRow("Bridge Type:",       self.bridge_type)
        self.form.addRow("Span Length:",       self.span_length)
        self.form.addRow("Number of Spans:",   self.num_spans)
        self.form.addRow("Deck Width:",        self.deck_width)
        self.form.addRow("Deck Thickness:",    self.deck_thickness)
        self.form.addRow("Concrete Grade:",    self.concrete_grade)
        self.form.addRow("Steel Grade:",       self.steel_grade)
        self.form.addRow("Concrete Volume:",   self.concrete_volume)
        self.form.addRow("Steel Weight:",      self.steel_weight)
        self.form.addRow("Unit Cost:",         self.unit_cost)