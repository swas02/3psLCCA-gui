from PySide6.QtWidgets import QDoubleSpinBox, QLineEdit
from gui.components.base_widget import ScrollableForm


class Misc(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="structure_misc")

        self.railing_cost     = self.field("railing_cost",     QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.expansion_joints = self.field("expansion_joints", QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.bearings_cost    = self.field("bearings_cost",    QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.waterproofing    = self.field("waterproofing",    QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.drainage_cost    = self.field("drainage_cost",    QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.lighting_cost    = self.field("lighting_cost",    QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.signage_cost     = self.field("signage_cost",     QDoubleSpinBox(), min_val=0, max_val=1e9, decimals=2)
        self.notes            = self.field("notes",            QLineEdit(),      placeholder="Any additional notes")

        self.form.addRow("Railing Cost:",          self.railing_cost)
        self.form.addRow("Expansion Joints Cost:", self.expansion_joints)
        self.form.addRow("Bearings Cost:",         self.bearings_cost)
        self.form.addRow("Waterproofing Cost:",    self.waterproofing)
        self.form.addRow("Drainage Cost:",         self.drainage_cost)
        self.form.addRow("Lighting Cost:",         self.lighting_cost)
        self.form.addRow("Signage Cost:",          self.signage_cost)
        self.form.addRow("Notes:",                 self.notes)