"""
gui/components/utils/doc_handler/__init__.py

Opens an offline Markdown doc page in a singleton in-app QDialog.

Usage:
    from ..utils.doc_handler import open_doc

    open_doc(["financial", "discount-rate"])   # opens docs/financial/discount-rate.md
    open_doc(["carbon", "social-cost", "scc-methodology"])
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QTextBrowser, QVBoxLayout


DOCS_DIR = Path(__file__).parent / "docs"

_dialog: QDialog | None = None


def open_doc(slug_parts: list[str], parent: QWidget | None = None) -> None:
    """
    Render ``docs/<slug_parts...>.md`` in a singleton in-app doc viewer.

    Parameters
    ----------
    slug_parts : list[str]
        Path segments, e.g. ``["financial", "discount-rate"]``.
        Empty list is a no-op.
    parent : QWidget, optional
        Parent widget for the dialog. If provided and is a QDialog,
        the viewer will automatically close when the parent finishes.
    """
    if not slug_parts:
        return

    # Auto-cleanup: if parent is a QDialog, wire it to close the viewer on finish
    if parent:
        window = parent.window()
        if isinstance(window, QDialog) and not hasattr(window, "_doc_wired"):
            window.finished.connect(close_doc)
            setattr(window, "_doc_wired", True)

    md_path = DOCS_DIR.joinpath(*slug_parts).with_suffix(".md")
    if not md_path.exists():
        fallback = DOCS_DIR / "404.md"
        if not fallback.exists():
            return
        md_path = fallback

    _show(md_path.read_text(encoding="utf-8"), md_path.stem, parent=parent)


def close_doc() -> None:
    """Close the singleton doc viewer if it is open."""
    global _dialog
    if _dialog is not None:
        _dialog.close()


def _show(content: str, stem: str, parent: QWidget | None = None) -> None:
    global _dialog

    if QApplication.instance() is None:
        return

    if _dialog is None:
        _dialog = QDialog(parent)
        _dialog.setWindowFlags(
            Qt.Window |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        _dialog.resize(700, 540)
        _dialog.setAttribute(Qt.WA_DeleteOnClose, False)

        layout = QVBoxLayout(_dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        browser = QTextBrowser()
        browser.setObjectName("_doc_browser")
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet("border: none;")
        layout.addWidget(browser)
    elif parent is not None:
        _dialog.setParent(parent)
        _dialog.setWindowFlags(
            Qt.Window |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

    browser: QTextBrowser = _dialog.findChild(QTextBrowser, "_doc_browser")
    browser.setMarkdown(content)

    _dialog.setWindowTitle(stem.replace("-", " ").title())
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
