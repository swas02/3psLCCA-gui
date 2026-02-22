from PySide6.QtWidgets import QLineEdit, QDoubleSpinBox
from gui.components.base_widget import BaseDataWidget

class BridgeData(BaseDataWidget):
    """
    Bridge Data panel — manages the 'bridge_data' chunk.
    """
    def __init__(self, controller=None):
        # BaseDataWidget handles self.form and data-loading signals
        super().__init__(controller=controller, chunk_name="bridge_data")

        # 1. Use 'self.field' to match the BaseDataWidget's auto-loading logic.
        # This ensures data is actually pulled from the engine.
        self.bridge_name = self.field("bridge_name", QLineEdit())
        self.bridge_id   = self.field("bridge_id",   QLineEdit())
        
        self.bridge_length = self.field("bridge_length", QDoubleSpinBox())
        self.bridge_length.setRange(0, 10000)
        self.bridge_length.setSuffix(" m")

        self.bridge_width = self.field("bridge_width", QDoubleSpinBox())
        self.bridge_width.setRange(0, 1000)
        self.bridge_width.setSuffix(" m")

        # 2. Add to self.form (inherited) to avoid the QLayout warning.
        self.form.addRow("Bridge Name:",   self.bridge_name)
        self.form.addRow("Bridge ID:",     self.bridge_id)
        self.form.addRow("Total Length:",  self.bridge_length)
        self.form.addRow("Total Width:",   self.bridge_width)