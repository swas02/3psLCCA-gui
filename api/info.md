# Project.info (General Information)

Manages high-level project metadata, evaluating agency details, and global settings.

## `Project.info.general` (Project Identity)

- **`read() -> dict`**: Returns current identity fields.
- **`write(name=None, code=None, description=None, remarks=None)`**: Updates identity fields.

## `Project.info.agency` (Evaluating Agency)

- **`read() -> dict`**: Returns agency details.
- **`write(name=None, contact=None, address=None, country=None, email=None, phone=None, logo_path=None)`**: Updates agency fields. `logo_path` is a local image path.

## `Project.info.settings` (Global Project Settings)

- **`read() -> dict`**: Returns global project settings.
- **`write(material_database=None)`**: Sets the active Material/SOR database.
- **Note**: Core settings like `country`, `currency`, and `unit_system` are immutable after creation.
