# 3psLCCA Python API: Overview

The 3psLCCA Python API provides a high-level, project-centric interface for both programmatic interaction (CLI) and graphical user interface control (GUI).

## 1. Top-Level Management (`3psLCCA_cli`)

### `open(project_id: str) -> Project`
Opens an existing project and returns a `Project` instance.

### `create_new(name: str, country: str, unit_system: str = "metric") -> Project`
Creates a new project and returns a `Project` instance.

## 2. The `Project` Object

A `Project` instance represents an active connection to a 3psLCCA project. It provides access to the project's data, divided by functional pages.

### Core Methods
- **`project.save()`**: Flushes all staged updates to disk.
- **`project.close()`**: Gracefully closes the project and releases the file lock.

## 3. GUI Control (`3psLCCA_cli.gui`)

- **`launch(project_id=None)`**: Launches the application.
- **`refresh()`**: Refreshes all open windows.
- **`is_running()`**: Returns `True` if the GUI is active.
- **`exit()`**: Closes the application.

---

## Documentation Index
- [General Information (Project.info)](info.md)
- [Bridge Data (Project.bridge)](bridge.md)
- [Traffic & Road Data (Project.traffic)](traffic.md)
- [Construction Work Data (Project.structure)](structure.md)
- [Financial Data (Project.finance)](finance.md)
- [Carbon Emission Data (Project.emissions)](emissions.md)
- [Maintenance and Repair (Project.maintenance)](maintenance.md)
- [Recycling & Demolition (Project.lifecycle)](lifecycle.md)
