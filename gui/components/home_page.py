"""
gui/components/home_page.py

Home screen for the LCCA application.
Extracted from ProjectWindow._setup_home_ui() and upgraded to a
standalone widget with a proper layout — no QSS required.
"""

import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QFrame, QSizePolicy, QMessageBox, QSpacerItem
)
from core.safechunk_engine import SafeChunkEngine


class ProjectListItem(QListWidgetItem):
    """A richer list item that stores project metadata."""
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.setText(project_id)
        self.setSizeHint(QSize(0, 40))


class HomePage(QWidget):
    """
    Self-contained home screen.

    Signals handled via callbacks (to keep it decoupled from the window):
        on_new_project()          — user clicked "New Project"
        on_open_project(pid)      — user wants to open a specific project
        on_return_to_project()    — user clicked "Return to Active Project"
    """

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._active_project_id = None   # set externally when a project is open

        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────────
    # UI CONSTRUCTION
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────────
        header = self._make_header()
        root.addWidget(header)

        # ── Body (centred, max-width card) ────────────────────────────────────
        body_row = QHBoxLayout()
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.addStretch(1)
        body_row.addWidget(self._make_body(), stretch=0)
        body_row.addStretch(1)

        body_wrapper = QWidget()
        body_wrapper.setLayout(body_row)
        body_wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(body_wrapper, stretch=1)

        # ── Footer ────────────────────────────────────────────────────────────
        root.addWidget(self._make_footer())

    def _make_header(self) -> QWidget:
        bar = QFrame()
        bar.setFrameShape(QFrame.StyledPanel)
        bar.setFixedHeight(64)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(28, 0, 28, 0)

        title = QLabel("OS Bridge  LCCA")
        f = QFont()
        f.setPointSize(15)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        layout.addStretch()

        subtitle = QLabel("Life Cycle Cost Analysis")
        sub_f = QFont()
        sub_f.setPointSize(10)
        subtitle.setFont(sub_f)
        subtitle.setEnabled(False)          # renders greyed-out naturally
        layout.addWidget(subtitle)

        return bar

    def _make_body(self) -> QWidget:
        card = QWidget()
        card.setFixedWidth(480)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 40, 0, 40)
        layout.setSpacing(0)

        # ── Section: New project ──────────────────────────────────────────────
        layout.addWidget(self._section_label("Start"))
        layout.addSpacing(8)

        self.btn_new = QPushButton("＋  New Project")
        self.btn_new.setFixedHeight(40)
        self.btn_new.setDefault(True)
        self.btn_new.clicked.connect(
            lambda: self.manager.open_project(is_new=True)
        )
        layout.addWidget(self.btn_new)

        layout.addSpacing(32)
        layout.addWidget(self._divider())
        layout.addSpacing(24)

        # ── Section: Project list ─────────────────────────────────────────────
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self._section_label("Projects"))
        row.addStretch()
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setToolTip("Refresh list")
        refresh_btn.clicked.connect(self.refresh_project_list)
        row.addWidget(refresh_btn)
        layout.addLayout(row)

        layout.addSpacing(8)

        self.project_list = QListWidget()
        self.project_list.setMinimumHeight(200)
        self.project_list.setAlternatingRowColors(True)
        self.project_list.itemDoubleClicked.connect(self._open_selected)
        layout.addWidget(self.project_list)

        layout.addSpacing(10)

        # ── Open / Delete buttons ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_open = QPushButton("Open")
        self.btn_open.setFixedHeight(34)
        self.btn_open.clicked.connect(self._open_selected)
        btn_row.addWidget(self.btn_open)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setFixedHeight(34)
        self.btn_delete.clicked.connect(self._delete_selected)
        btn_row.addWidget(self.btn_delete)

        layout.addLayout(btn_row)

        layout.addSpacing(32)
        layout.addWidget(self._divider())
        layout.addSpacing(24)

        # ── Return to active project (hidden until a project is open) ─────────
        self.btn_return = QPushButton("← Return to Active Project")
        self.btn_return.setFixedHeight(36)
        self.btn_return.hide()
        self.btn_return.clicked.connect(
            lambda: self.manager.open_project(
                project_id=self._active_project_id
            )
        )
        layout.addWidget(self.btn_return)

        return card

    def _make_footer(self) -> QWidget:
        bar = QFrame()
        bar.setFrameShape(QFrame.StyledPanel)
        bar.setFixedHeight(32)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)

        lbl = QLabel("OS Bridge LCCA  •  v1.5.0")
        lbl.setEnabled(False)
        f = QFont()
        f.setPointSize(9)
        lbl.setFont(f)
        layout.addWidget(lbl)
        layout.addStretch()

        return bar

    # ──────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text.upper())
        f = QFont()
        f.setPointSize(8)
        f.setBold(True)
        lbl.setFont(f)
        lbl.setEnabled(False)
        return lbl

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC API  (called by ProjectWindow)
    # ──────────────────────────────────────────────────────────────────────────

    def set_active_project(self, project_id: str | None):
        """Tell the home page whether a project is currently open."""
        self._active_project_id = project_id
        if project_id:
            self.btn_return.show()
            self.btn_return.setText(f"← Return to  {project_id}")
        else:
            self.btn_return.hide()

    def refresh_project_list(self):
        self.project_list.clear()
        projects = sorted(SafeChunkEngine.list_all_projects())
        if not projects:
            placeholder = QListWidgetItem("No projects found.")
            placeholder.setFlags(placeholder.flags() & ~Qt.ItemIsSelectable)
            placeholder.setForeground(QColor("#888888"))
            self.project_list.addItem(placeholder)
        else:
            for pid in projects:
                self.project_list.addItem(ProjectListItem(pid))

    # ──────────────────────────────────────────────────────────────────────────
    # INTERNAL SLOTS
    # ──────────────────────────────────────────────────────────────────────────

    def _selected_pid(self) -> str | None:
        item = self.project_list.currentItem()
        if isinstance(item, ProjectListItem):
            return item.project_id
        return None

    def _open_selected(self):
        pid = self._selected_pid()
        if pid:
            self.manager.open_project(project_id=pid)

    def _delete_selected(self):
        pid = self._selected_pid()
        if not pid:
            QMessageBox.information(self, "Delete", "Select a project first.")
            return

        result = QMessageBox.warning(
            self,
            "Delete Project",
            f"Permanently delete  '{pid}'?\n\nThis cannot be undone.",
            QMessageBox.Ok | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if result == QMessageBox.Ok:
            engine, _ = SafeChunkEngine.open(pid)
            if engine:
                engine.delete_project(confirmed=True)
            self.refresh_project_list()