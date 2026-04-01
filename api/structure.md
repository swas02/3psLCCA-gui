# Project.structure (Construction Work Data)

Manages the physical components and materials of the bridge. Data is organized into four main categories: **Foundation**, **Sub Structure**, **Super Structure**, and **Miscellaneous**.

## Structure Hierarchy

- **Category**: High-level grouping (e.g., `foundation`).
- **Component**: User-defined sections within a category (e.g., "Excavation", "Piles").
- **Material**: Individual line items with quantities and rates.

---

## API Namespaces

Access each category via its dedicated namespace:
- `project.structure.foundation`
- `project.structure.sub_structure`
- `project.structure.super_structure`
- `project.structure.misc`

### Common Methods (per Category)

#### `read() -> dict`
Returns all components and materials within the category, organized by component name.

#### `add_component(name: str)`
Creates a new empty component section (e.g., "Well Foundation").

#### `add_material(component: str, name: str, quantity: float, rate: float, unit: str = "", **kwargs)`
Adds a material line item to a specific component.
- **`kwargs`**:
    - **Analysis Flags**: `carbon_emission_enabled=True`, `recyclability_enabled=True`.
    - **Carbon Details**: `emission_factor: float` (kgCO2e per unit), `emission_unit: str`, `conversion_factor: float`.
    - **Recycling Details**: `recyclability_pct: float` (0-100), `scrap_rate: float` (cost per unit).

#### `update_material(component: str, index: int, **fields)`
Updates specific fields of a material. This includes quantity, rate, or any carbon/recycling parameters listed above.

---

## Analysis & Integration

While the structure API manages the raw data, the Carbon and Recycling analyses are derived from these inputs.

### Per-Material Carbon Parameters
- **`emission_factor`**: The amount of CO2e emitted per unit of material.
- **`conversion_factor`**: Multiplier to align the material's structural unit (e.g., `cum`) with its emission unit (e.g., `ton`).
- **`carbon_emission_enabled`**: Toggle to include/exclude this specific material from the total carbon footprint.

### Per-Material Recycling Parameters
- **`recyclability_pct`**: Percentage of the material expected to be recovered after demolition.
- **`scrap_rate`**: The resale or recovery value per unit of recovered material.
- **`recyclability_enabled`**: Toggle to include/exclude this specific material from the total recovery value.

#### `remove_material(component: str, index: int)`
Moves a material to the Trash.

---

## Global Operations

### `Project.structure.import_excel(path: str)`
Parses and imports structural data from an Excel file. Validates the schema before applying changes.

### `Project.structure.trash`
- **`list() -> list[dict]`**: Returns all items currently in the Trash across all categories.
- **`restore(item_id: str)`**: Restores a trashed item to its original location.
- **`clear()`**: Permanently deletes all items in the Trash.

---

## Usage Example

```python
project = cli.open("proj_fb956a4c")

# Add a new material with Carbon and Recycling parameters
project.structure.foundation.add_material(
    component="Pile Cap",
    name="M35 Concrete",
    quantity=450.0,
    unit="cum",
    rate=8500.0,
    # Carbon Parameters
    emission_factor=120.5,       # 120.5 kgCO2e per ton
    emission_unit_den="ton",
    conversion_factor=2.4,        # 2.4 ton per cum
    carbon_emission_include=True,
    # Recycling Parameters
    recyclability_pct=85.0,      # 85% recovered
    scrap_rate=1500.0,             # 1500 per unit recovered
    recyclibilty_include = True
)

# Bulk import from Excel
project.structure.import_excel("data/mthl_quantities.xlsx")

project.save()
```
