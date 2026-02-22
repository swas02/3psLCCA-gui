from PySide6.QtWidgets import QLineEdit, QComboBox, QDoubleSpinBox
from PySide6.QtCore import Signal
from gui.components.base_widget import BaseDataWidget


class GeneralInfo(BaseDataWidget):
    """
    General Information panel — manages the 'general_info' data chunk.

    Fixes:
        - Resolved NameError by using self.form (inherited from BaseDataWidget).
        - Fixed Layout Conflict by not calling QFormLayout(self) twice.
        - Simplified field registration using the base class pattern.
    """

    created = Signal()  # Kept for compatibility with ProjectWindow state management

    def __init__(self, controller=None):
        # BaseDataWidget.__init__ sets up self.form and connects project_loaded signals
        super().__init__(controller=controller, chunk_name="general_info")

        # Use the already initialized self.form from BaseDataWidget
        # This prevents the "Attempting to add QLayout which already has a layout" warning
        layout = self.form

        # Field registration — BaseDataWidget handles signal connections + data extraction
        # Note: If your BaseDataWidget uses 'register_field', keep it.
        # If it uses 'field', change the method name below.
        self.project_name = self.register_field("project_name", QLineEdit())
        self.project_code = self.register_field("project_code", QLineEdit())
        self.client_name = self.register_field("client", QLineEdit())
        self.location = self.register_field("location", QLineEdit())

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

        # Add rows to the form
        layout.addRow("Project Name:", self.project_name)
        layout.addRow("Project Code:", self.project_code)
        layout.addRow("Client:", self.client_name)
        layout.addRow("Location:", self.location)
        layout.addRow("Currency:", self.currency)
        layout.addRow("Discount Rate:", self.discount_rate)
        layout.addRow("Analysis Period:", self.analysis_period)

    def _on_field_changed(self):
        """
        Emit the created signal in addition to the base autosave behaviour,
        so ProjectWindow can update its title/state when this chunk changes.
        """
        super()._on_field_changed()
        self.created.emit()
