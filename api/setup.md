# Setup & Initialization

This guide explains how to install and start using the 3psLCCA Python API.

## 1. Requirements

- **Python**: 3.9 or higher.
- **Dependencies**: `PySide6` (for GUI interaction), `pandas`, `openpyxl` (for Excel processing).
- **Environment**: The API must have read/write access to the `user_projects` directory.

## 2. Installation

Currently, the API is provided as a local package within the 3psLCCA repository.

```bash
# Navigate to the project root
cd osbridgelcca_new

# Install in editable mode
pip install -e .
```

## 3. Initializing the CLI

The entry point for all operations is the `3psLCCA_cli` module.

```python
import 3psLCCA_cli as cli

# 1. List all available projects to find an ID
projects = cli.list_projects()
for p in projects:
    print(f"ID: {p['id']} | Name: {p['name']}")

# 2. Open a specific project
project = cli.open("proj_fb956a4c")

# 3. Perform operations...
print(project.bridge.specs.read())

# 4. Save and release the lock
project.save()
project.close()
```

## 4. Troubleshooting

### Project Lock Error
If a project is already open in the 3psLCCA GUI, the CLI will raise a `RuntimeError` on `open()`. You must either:
1. Close the GUI window.
2. Use `cli.gui.refresh()` to interact with the project while the GUI is open (Read-only recommended for CLI while GUI is active).

### Missing Modules
Ensure all requirements in `requirements.txt` are installed in your Python environment.
