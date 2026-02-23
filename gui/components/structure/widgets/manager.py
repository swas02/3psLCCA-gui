from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QGroupBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QInputDialog,
    QFrame,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
import time
import uuid
import datetime
from .base_table import StructureTableWidget
from PySide6.QtGui import QDoubleValidator


class MaterialDialog(QDialog):
    """
    Universal Popup for adding or editing materials.
    Includes all 12 schema inputs: material_name, quantity, unit, rate,
    rate_source, carbon_emission, carbon_unit, conversion_factor,
    grade, type, scrap_rate, and recyclability_percentage.
    """

    def __init__(self, comp_name, parent=None, data=None):
        super().__init__(parent)
        self.is_edit = data is not None

        # ADD THIS
        if self.is_edit:
            v = data.get("values", {})
            # print(f"[DEBUG] MaterialDialog values: {v}")
        self.setWindowTitle(
            f"Edit Material: {comp_name}"
            if self.is_edit
            else f"Add Material: {comp_name}"
        )
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        self.form = QFormLayout()

        # Extract values if editing, else defaults
        v = data.get("values", {}) if self.is_edit else {}

        # --- Initialize Inputs ---
        self.name_in = QLineEdit(v.get("material_name", ""))
        self.qty_in = QLineEdit(str(v.get("quantity", "0.0")))
        self.unit_in = QLineEdit(v.get("unit", "m3"))
        self.rate_in = QLineEdit(str(v.get("rate", "0.0")))
        self.src_in = QLineEdit(v.get("rate_source", "Standard"))

        self.carbon_em_in = QLineEdit(str(v.get("carbon_emission", "0.0")))
        self.carbon_unit_in = QLineEdit(v.get("carbon_unit", "kgCO2e"))
        self.conv_factor_in = QLineEdit(str(v.get("conversion_factor", "1.0")))

        self.grade_in = QLineEdit(v.get("grade", ""))
        self.type_in = QLineEdit(v.get("type", ""))
        self.scrap_in = QLineEdit(str(v.get("scrap_rate", "0.0")))
        self.recycling_perc_in = QLineEdit(
            str(v.get("recyclability_percentage", "0.0"))
        )

        # --- Validators ---
        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.qty_in.setValidator(validator)
        self.rate_in.setValidator(validator)
        self.carbon_em_in.setValidator(validator)
        self.conv_factor_in.setValidator(validator)
        self.scrap_in.setValidator(validator)
        self.recycling_perc_in.setValidator(validator)


        # --- Add Fields to Form ---
        self.form.addRow("Material Name:", self.name_in)
        self.form.addRow("Quantity:", self.qty_in)
        self.form.addRow("Unit (e.g. m3, kg):", self.unit_in)
        self.form.addRow("Rate (Cost):", self.rate_in)
        self.form.addRow("Rate Source:", self.src_in)

        # Carbon/Sustainability Fields
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.form.addRow(line)
        self.form.addRow(QLabel("<b>Sustainability Data</b>"))

        self.form.addRow("Carbon Emission:", self.carbon_em_in)
        self.form.addRow("Carbon Unit:", self.carbon_unit_in)
        self.form.addRow("Conversion Factor:", self.conv_factor_in)
        self.form.addRow("Scrap Rate (%):", self.scrap_in)
        self.form.addRow("Recyclability (%):", self.recycling_perc_in)

        # Categorization Fields
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        self.form.addRow(line2)
        self.form.addRow("Grade (e.g. M25):", self.grade_in)
        self.form.addRow("Type (e.g. Concrete):", self.type_in)

        layout.addLayout(self.form)

        # Buttons
        btns = QHBoxLayout()
        self.save_btn = QPushButton(
            "Update Changes" if self.is_edit else "Add to Table"
        )
        self.save_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        self.save_btn.clicked.connect(self.validate_and_accept)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

    def validate_and_accept(self):
        """Ensures numeric fields contain valid numbers before closing."""
        try:
            float(self.rate_in.text())
            float(self.qty_in.text())
            float(self.carbon_em_in.text())
            float(self.conv_factor_in.text())
            float(self.scrap_in.text())
            float(self.recycling_perc_in.text() or 0)
            self.accept()
        except ValueError:
            QMessageBox.critical(
                self, "Validation Error", "Please ensure numeric fields are numbers."
            )

    def get_values(self):
        """Returns the dictionary for the add_material function."""
        return {
            "material_name": self.name_in.text(),
            "quantity": float(self.qty_in.text() or 0),
            "unit": self.unit_in.text(),
            "rate": float(self.rate_in.text() or 0),
            "rate_source": self.src_in.text(),
            "carbon_emission": float(self.carbon_em_in.text() or 0),
            "carbon_unit": self.carbon_unit_in.text(),
            "conversion_factor": float(self.conv_factor_in.text() or 1),
            "grade": self.grade_in.text(),
            "type": self.type_in.text(),
            "scrap_rate": float(self.scrap_in.text() or 0),
            "recyclability_percentage": float(self.recycling_perc_in.text() or 0),
            "is_recyclable": float(self.recycling_perc_in.text() or 0) > 0,
        }


class StructureManagerWidget(QWidget):
    def __init__(self, controller, chunk_name, default_components):
        super().__init__()
        self.controller = controller
        self.chunk_name = chunk_name
        self.default_components = default_components
        self.sections = {}
        self.data = {}

        self.main_layout = QVBoxLayout(self)

        # Scroll Area Setup
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; }")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.add_comp_btn = QPushButton("+ Add Component Section")
        self.add_comp_btn.clicked.connect(self.add_new_component)
        btn_layout.addWidget(self.add_comp_btn)
        btn_layout.addStretch()
        self.main_layout.addLayout(btn_layout)

    def on_refresh(self):
        try:
            if not self.controller or not getattr(self.controller, "engine", None):
                return

            data = self.controller.engine.fetch_chunk(self.chunk_name) or {}

            if not data and self.default_components:
                for comp in self.default_components:
                    data[comp] = []
                self.controller.engine.stage_update(
                    chunk_name=self.chunk_name, data=data
                )

            self.data = data
            self.refresh_ui()
        except Exception as e:
            import traceback

            print(f"[ERROR] on_refresh crashed: {e}")
            traceback.print_exc()

    def refresh_ui(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.sections = {}

        for comp_name, items in self.data.items():
            self.create_section(comp_name)
            table = self.sections.get(comp_name)
            if table:
                for original_index, item in enumerate(items):
                    if not item.get("state", {}).get("in_trash", False):
                        table.add_row(item, original_index)

        self.container_layout.addStretch()
        self.container.adjustSize()
        # REMOVE: self.scroll.setWidget(self.container)

    def create_section(self, name):
        group = QGroupBox(name)
        g_layout = QVBoxLayout(group)

        table = StructureTableWidget(self, name)
        self.sections[name] = table

        add_row_btn = QPushButton(f"Add Material to {name}")
        add_row_btn.clicked.connect(lambda checked=False, n=name: self.open_dialog(n))

        g_layout.addWidget(table)
        g_layout.addWidget(add_row_btn)
        self.container_layout.addWidget(group)

    def add_material(self, comp_name, values_dict, is_trash=False):
        """Centralized addition using Values/Meta/State schema."""
        now = datetime.datetime.now().isoformat()
        new_entry = {
            "id": str(uuid.uuid4()),
            "values": values_dict,
            "meta": {
                "created_on": now,
                "modified_on": now,
                "is_user_defined": True,
                "is_from_db": False,
                "source_version": "1.0",
            },
            "state": {
                "in_trash": is_trash,
                "included_in_carbon_emission": True,
                "included_in_recyclability": values_dict.get("is_recyclable", False),
            },
        }

        current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
        if comp_name not in current_data:
            current_data[comp_name] = []

        current_data[comp_name].append(new_entry)
        self.controller.engine.stage_update(
            chunk_name=self.chunk_name, data=current_data
        )
        self.save_current_state()
        self.on_refresh()

    def open_dialog(self, comp_name):
        dialog = MaterialDialog(comp_name, self)
        if dialog.exec():
            self.add_material(comp_name, dialog.get_values())

    def open_edit_dialog(self, comp_name, table_row_index):
        try:
            current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
            items = current_data.get(comp_name, [])

            active_indices = [
                i
                for i, item in enumerate(items)
                if not item.get("state", {}).get("in_trash", False)
            ]

            if table_row_index < len(active_indices):
                original_idx = active_indices[table_row_index]
                item_to_edit = items[original_idx]

                dialog = MaterialDialog(comp_name, self, data=item_to_edit)
                if dialog.exec():
                    item_to_edit["values"] = dialog.get_values()
                    item_to_edit["meta"][
                        "modified_on"
                    ] = datetime.datetime.now().isoformat()

                    self.controller.engine.stage_update(
                        chunk_name=self.chunk_name, data=current_data
                    )
                    self.save_current_state()
                    QTimer.singleShot(0, self.on_refresh)  # <-- deferred, not immediate
        except Exception as e:
            import traceback

            print(f"[ERROR] open_edit_dialog crashed: {e}")
            traceback.print_exc()

    def toggle_trash_status(self, comp_name, data_index, should_trash):
        """Moves item to trash using nested state."""
        data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
        if comp_name in data and len(data[comp_name]) > data_index:
            if "state" not in data[comp_name][data_index]:
                data[comp_name][data_index]["state"] = {}
            data[comp_name][data_index]["state"]["in_trash"] = should_trash

            self.controller.engine.stage_update(chunk_name=self.chunk_name, data=data)
            self.save_current_state()
            self.on_refresh()

            # Refresh Main View for badge/tab updates
            main_view = self.window().findChild(QWidget, "StructureTabView")
            if main_view and hasattr(main_view, "on_refresh"):
                main_view.on_refresh()

    def add_new_component(self):
        name, ok = QInputDialog.getText(self, "New Component", "Enter Component Name:")
        if ok and name.strip():
            clean_name = name.strip()
            self.create_section(clean_name)
            current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
            if clean_name not in current_data:
                current_data[clean_name] = []
                self.controller.engine.stage_update(
                    chunk_name=self.chunk_name, data=current_data
                )
                self.save_current_state()

    def save_current_state(self):
        if self.controller and self.controller.engine:
            eng = self.controller.engine
            eng._last_keystroke_time = time.time()
            eng._has_unsaved_changes = True
            try:
                eng.on_dirty(True)
            except:
                pass
