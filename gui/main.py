import sys
import os
from PySide6.QtWidgets import QApplication
from gui.project_manager import ProjectManager

def main():
    """
    Main entry point for the OS Bridge LCCA application.
    Initializes the QApplication and delegates window management to ProjectManager.
    """
    app = QApplication(sys.argv)
    
    # Optional: Set Application Name for OS-level identification
    app.setApplicationName("OS Bridge LCCA")
    app.setOrganizationName("OSBridge")

    # Optional: Load the QSS theme if available
    qss_path = os.path.join("gui", "assets", "themes", "lightstyle.qss")
    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            print(f"Warning: Could not load stylesheet: {e}")

    # Initialize the Manager
    # The manager handles the lifecycle of one or more ProjectWindows
    manager = ProjectManager()
    
    # open_project() without arguments defaults to showing the Home/Project Selection screen
    manager.open_project()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    # Ensure the script is run from the root directory to maintain correct package imports
    main()