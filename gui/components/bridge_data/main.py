# gui/components/bridge_data/main.py
from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit
from PySide6.QtCore import Signal

class BridgeData(QWidget):
    created = Signal()

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.chunk_name = "bridge_data"

        layout = QFormLayout(self)
        self.bridge_id = QLineEdit()
        layout.addRow("Bridge ID:", self.bridge_id)

        self.bridge_id.textChanged.connect(self.trigger_autosave)

    def get_data_dict(self):
        return {"bridge_id": self.bridge_id.text()}

    def trigger_autosave(self):
        self.created.emit()
        if self.controller:
            self.controller.save_chunk_data(self.chunk_name, self.get_data_dict())