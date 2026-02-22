from PySide6.QtWidgets import QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox
from PySide6.QtCore import Signal
from gui.components.base_widget import BaseDataWidget


class GeneralInfo(BaseDataWidget):
    """
    General Information panel — manages the 'general_info' data chunk.

    Loading fix:
        The old version manually connected sync_completed → refresh_from_engine
        and also called refresh_from_engine() directly in __init__. Both were wrong:
        - The __init__ call always failed because the engine wasn't attached yet.
        - sync_completed fires after every autosave, which would overwrite the UI
          while the user is typing in a different field.

        Now: BaseDataWidget.__init__ connects project_loaded → refresh_from_engine
        automatically for every subclass. No manual wiring needed here.
    """
    created = Signal()  # Kept for compatibility with ProjectWindow state management

    def __init__(self, controller=None):
        # BaseDataWidget.__init__ handles project_loaded connection automatically
        super().__init__(controller=controller, chunk_name="general_info")

        layout = QFormLayout(self)

        # Field registration — BaseDataWidget handles signal connections + data extraction
        self.project_name = self.register_field("project_name", QLineEdit())
        self.project_code = self.register_field("project_code", QLineEdit())
        self.client_name  = self.register_field("client", QLineEdit())
        self.location     = self.register_field("location", QLineEdit())

        self.currency = self.register_field("currency", QComboBox())
        self.currency.addItems(["USD", "EUR", "GBP", "INR", "JPY", "AUD"])

        self.discount_rate = self.register_field("discount_rate", QDoubleSpinBox())
        self.discount_rate.setRange(0, 100)
        self.discount_rate.setSuffix(" %")
        self.discount_rate.setValue(3.5)

        self.analysis_period = self.register_field("analysis_period", QDoubleSpinBox())
        self.analysis_period.setRange(1, 200)
        self.analysis_period.setSuffix(" Years")
        self.analysis_period.setDecimals(0)

        layout.addRow("Project Name:",   self.project_name)
        layout.addRow("Project Code:",   self.project_code)
        layout.addRow("Client:",         self.client_name)
        layout.addRow("Location:",       self.location)
        layout.addRow("Currency:",       self.currency)
        layout.addRow("Discount Rate:",  self.discount_rate)
        layout.addRow("Analysis Period:", self.analysis_period)

    def _on_field_changed(self):
        """
        Emit the created signal in addition to the base autosave behaviour,
        so ProjectWindow can update its title/state when this chunk changes.
        """
        super()._on_field_changed()
        self.created.emit()