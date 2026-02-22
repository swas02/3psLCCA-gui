import os
from PySide6.QtWidgets import QApplication, QMessageBox
from gui.project_controller import controller
from gui.project_window import ProjectWindow


class ProjectManager:
    def __init__(self):
        self.windows = []

    def broadcast_refresh(self):
        for win in self.windows:
            win.home_widget.refresh_project_list()

    def get_available_window(self):
        for win in self.windows:
            if win.controller.engine is None:
                return win
        return None

    def open_project(self, project_id=None, is_new=False, target=None):
        # If already open in a window, just focus it
        if project_id:
            for win in self.windows:
                if win.project_id == project_id:
                    win.show_project_view()
                    win.show()
                    win.activateWindow()
                    return

        if target is None:
            target = self.get_available_window()
        if target is None or (target.controller.engine and (is_new or project_id)):
            target = self.create_window()

        if is_new:
            new_id = f"proj_{os.urandom(4).hex()}"
            success = controller.init_project(new_id, is_new=True)
        elif project_id:
            success = controller.init_project(project_id, is_new=False)
        else:
            target.show_home()
            target.show()
            return

        if success:
            target.project_id = controller.active_project_id
            target.show_project_view()
        else:
            QMessageBox.warning(None, "Error", "Could not open project engine.")
            target.show_home()

        target.show()
        target.activateWindow()

    def create_window(self):
        win = ProjectWindow(self)
        self.windows.append(win)
        return win

    def remove_window(self, win):
        if win in self.windows:
            self.windows.remove(win)
        if not self.windows:
            QApplication.quit()