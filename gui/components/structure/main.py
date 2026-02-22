from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from gui.components.structure.widgets.foundation import Foundation
from gui.components.structure.widgets.super_structure import SuperStruct
from gui.components.structure.widgets.substructure import SubStruct
from gui.components.structure.widgets.misc_widget import Misc


class StructureTabView(QWidget):
    def __init__(self, controller=None):
        super().__init__()

        main_layout = QVBoxLayout(self)

        # Top area
        top_area = QWidget()
        top_layout = QHBoxLayout(top_area)
        region_info = QWidget()
        region_info_layout = QVBoxLayout(region_info)
        region_info_layout.addWidget(QLabel("Region Info: India"))
        region_info_layout.addWidget(QLabel("Selected DB: Maharashtra PWD"))
        top_layout.addWidget(region_info)
        top_layout.addStretch()
        top_layout.addWidget(QPushButton("Upload Excel"))
        top_layout.addWidget(QPushButton("Trash"))

        self.tab_view = QTabWidget()
        self.tab_view.addTab(Foundation(controller=controller),  "Foundation")
        self.tab_view.addTab(SuperStruct(controller=controller), "Super-Structure")
        self.tab_view.addTab(SubStruct(controller=controller),   "Substructure")
        self.tab_view.addTab(Misc(controller=controller),        "Miscellaneous")

        main_layout.addWidget(top_area)
        main_layout.addWidget(self.tab_view)

    def select_tab(self, name):
        tabs = ["Foundation", "Super-Structure", "Substructure", "Miscellaneous"]
        if name in tabs:
            self.tab_view.setCurrentIndex(tabs.index(name))