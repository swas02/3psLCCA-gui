# Unit System - Reference & Refactoring Plan

## Overview

The unit system handles everything related to physical units across the app:
measurement unit selection (material dialog), SOR string normalization (excel importer),
conversion factor suggestion and validation (carbon emission), and display symbols (UI widgets).

It spans two source files (`definitions.py`, `unit_resolver.py`), one implicit data store
(`CustomMaterialDB`), and is consumed by at least 8 other modules.

---

## Source Files

### `gui/components/utils/definitions.py`

The hardcoded data store. Every unit-related constant originates here.

| Export | Type | Description |
|--------|------|-------------|
| `UNIT_TO_SI` | `dict[str, float]` | Maps unit code → SI equivalent (e.g. `"tonne": 1000.0` means 1 tonne = 1000 kg) |
| `UNIT_DIMENSION` | `dict[str, str]` | Maps unit code → dimension name (e.g. `"sqm": "Area"`) |
| `SI_BASE_UNITS` | `dict[str, str]` | Maps dimension → its SI base unit code (e.g. `"Mass": "kg"`) |
| `UNIT_DISPLAY` | `dict[str, str]` | Maps unit code → pretty display symbol (e.g. `"sqm": "m²"`) |
| `UNIT_TO_KG` | `dict[str, float]` | Maps unit code → kg equivalent. Separate from UNIT_TO_SI. Has extra entries (`"bag"`, `"kgs"`, `"gm"`, `"t"`) that UNIT_TO_SI lacks |
| `ConstructionUnits` | class | Groups units by dimension with name + example strings. One method: `get_dropdown_data()` |
| `_CONSTRUCTION_UNITS` | `ConstructionUnits` instance | Singleton used by material_dialog for grouped dropdown |
| `UNIT_DROPDOWN_DATA` | `list[tuple]` | Flat list of `(code, name, example)` from `_CONSTRUCTION_UNITS.get_dropdown_data()` |
| `STRUCTURE_CHUNKS` | `list[tuple]` | Not unit-related. Structure section definitions |
| `DEFAULT_VEHICLES` | `dict` | Not unit-related. Transport emission presets |

---

### `gui/components/utils/unit_resolver.py`

Pure logic module. Imports data from `definitions.py`, adds alias resolution and custom unit support.

#### Internal state

| Name | Type | Description |
|------|------|-------------|
| `_custom_units_cache` | `list[dict]` | In-process cache of user-defined custom units loaded from `CustomMaterialDB` |
| `_UNIT_ALIASES` | `dict[str, str]` | Normalises raw SOR strings to canonical unit codes. Only 11 entries - incomplete |

#### Public functions

| Function | Signature | Returns | Description |
|----------|-----------|---------|-------------|
| `load_custom_units` | `() → None` | - | Reads `CustomMaterialDB.list_custom_units()` into `_custom_units_cache`. Call at startup and after any custom unit add/delete |
| `get_custom_units` | `() → list[dict]` | Current cache | Returns in-process custom unit list without hitting DB |
| `get_known_units` | `() → set[str]` | Set of strings | All recognised unit codes: `UNIT_TO_SI.keys()` ∪ `_UNIT_ALIASES.keys()`. Does NOT include custom units |
| `get_unit_info` | `(code, custom_units=None) → (float\|None, str\|None)` | `(to_si, dimension)` | Main resolution function. Order: canonical registry → custom cache → alias fallback. Returns `(None, None)` if unknown |
| `suggest_cf` | `(mat_code, denom_code, custom_units=None) → float\|None` | CF or None | Suggests conversion factor between two unit codes. Returns `mat_si / denom_si` if same dimension, `None` if different dimensions or unknown |
| `analyze_conversion_sympy` | `(mat_unit, carbon_unit_denom, conv_factor, custom_units=None) → dict` | Analysis dict | Full CF plausibility analysis. Returns `{kg_factor, is_suspicious, comment, debug_dim_match}` |
| `validate_cf_simple` | `(mat_unit, carbon_unit_denom, cf) → dict` | `{sus, suggest}` | Quick plausibility check. Returns `{sus: bool, suggest: str\|None}` |

---

## Who Calls What

### `load_custom_units()`
- `gui/main.py` - called once at app startup
- `gui/components/structure/widgets/material_dialog.py` - called after user saves a new custom unit

### `get_custom_units()`
- `gui/components/structure/widgets/material_dialog.py` - populates "Custom" section in unit dropdown; checks for duplicate symbols on add

### `get_known_units()`
- `gui/components/structure/excel_importer.py` (lines 381, 392) - validates unit strings during SOR Excel import

### `get_unit_info()`
- `gui/components/structure/excel_importer.py` (line 474) - resolves each SOR item's unit string during import
- Called internally by `suggest_cf`, `analyze_conversion_sympy`, `validate_cf_simple`

### `analyze_conversion_sympy()`
- `gui/components/carbon_emission/widgets/material_emissions.py` - checks whether stored conversion factor is plausible when displaying emission data

### `UNIT_TO_SI`
- `gui/components/utils/unit_resolver.py` - core lookup table
- `gui/components/structure/widgets/material_dialog.py` - `_get_unit_info()`, duplicate symbol check

### `UNIT_DIMENSION`
- `gui/components/utils/unit_resolver.py` - dimension comparison
- `gui/components/carbon_emission/widgets/transport_emissions.py` - filters unit dropdown by dimension
- `gui/components/carbon_emission/widgets/transport_dialog.py` - same

### `SI_BASE_UNITS`
- `gui/components/utils/unit_resolver.py` - imported but not directly used in functions (available for callers)

### `UNIT_DISPLAY`
- `gui/components/carbon_emission/widgets/material_emissions.py` - formats unit symbol in emission display
- `gui/components/structure/widgets/base_table.py` - shows unit column symbol in material table
- `gui/components/carbon_emission/widgets/transport_dialog.py` - unit symbol in transport form
- `gui/components/recycling/main.py` - unit symbol in recycling panel

### `_CONSTRUCTION_UNITS` / `UNIT_DROPDOWN_DATA`
- `gui/components/structure/widgets/material_dialog.py` - builds the grouped unit dropdown

---

## Known Problems

### 1. `UNIT_TO_KG` vs `UNIT_TO_SI` - two separate mass dicts

`UNIT_TO_KG` has entries that `UNIT_TO_SI` does not:

| Code | In UNIT_TO_KG | In UNIT_TO_SI |
|------|---------------|---------------|
| `"t"` | 1000.0 | ✗ (only via alias → "tonne") |
| `"bag"` | 50.0 | ✗ |
| `"kgs"` | 1.0 | ✗ |
| `"gm"`, `"gram"` | 0.001 | ✗ |
| `"quintal"` | 100.0 | ✗ (only `"q"`) |
| `"lb"`, `"lbs"`, `"pound"` | 0.453592 | ✗ |

Since `kg` is the SI base for Mass, `UNIT_TO_KG` and `UNIT_TO_SI` (Mass subset) should be the same thing. They are not.

### 2. `"t"` is not a first-class unit

`"t"` (tonne) is the most commonly used mass unit in Indian SORs. It exists in `UNIT_TO_KG`
and in `_UNIT_ALIASES` (`"t" → "tonne"`) but NOT in `UNIT_TO_SI`. So `get_unit_info("t")`
hits the alias fallback and resolves via `"tonne"`. Fragile - and `"t"` appears in `UNIT_DISPLAY`
as a direct key (`"t": "t"`), which means display works but resolution is indirect.

### 3. `_UNIT_ALIASES` is too small - only 11 entries

Current aliases:
```
rmt → rm       lmt → rm       sqmt → sqm     t → tonne
kgs → kg       ton → tonne    metric_ton → tonne
kilogram → kg  meter → m      metre → m
sqft → sqft    sqyd → sqyd    cft → cft
```

Missing common SOR strings: `"Sqm"`, `"Sqm."`, `"SQM"`, `"MT"`, `"M.T."`, `"Nos."`,
`"Nos"`, `"RM"`, `"Cum"`, `"CUM"`, `"Cft"`, `"Pcs"`, `"bag"`, `"Bag"` etc.
When these appear in an imported SOR, `get_unit_info()` returns `(None, None)`.

### 4. Duplicate canonical codes for the same physical unit

| Physical unit | Code 1 | Code 2 | Why both? |
|--------------|--------|--------|-----------|
| Square metre | `m2` | `sqm` | `m2` is ISO notation, `sqm` is SOR convention |
| Cubic metre | `m3` | `cum` | same - ISO vs SOR |
| Metric tonne | `mt` | `tonne` | `mt` is SOR abbreviation |

Both codes exist in `UNIT_TO_SI` and `UNIT_DIMENSION` with identical values. The canonical
one is unclear. The system works but is confusing to extend.

### 5. `ConstructionUnits` class is structural overhead

The class exists only to group units for the dropdown. `get_dropdown_data()` just flattens
the dict into a list. The grouping info (dimension) is already in `UNIT_DIMENSION`. The
name and example strings are not stored anywhere else - they live only inside `ConstructionUnits`.

### 6. `get_known_units()` does not include custom units

`get_known_units()` returns `UNIT_TO_SI.keys() ∪ _UNIT_ALIASES.keys()`. It does not include
custom units from `CustomMaterialDB`. So `excel_importer.py` using this function will
flag a custom unit as "unrecognised" even if it is defined by the user.

---

## Proposed Refactoring

### Goal

Replace scattered hardcoded dicts with a single `units.json` data file.
Keep all public function signatures and export names identical - no other file changes.

### `units.json` structure

```json
{
  "dimensions": {
    "Mass":   { "si": "kg",  "common": "t"   },
    "Length": { "si": "m",   "common": "m"   },
    "Area":   { "si": "sqm", "common": "sqm" },
    "Volume": { "si": "cum", "common": "cum" },
    "Count":  { "si": "nos", "common": "nos" }
  },
  "units": {
    "kg": {
      "dimension": "Mass",
      "to_si":     1.0,
      "display":   "kg",
      "name":      "Kilogram",
      "example":   "Reinforcement steel",
      "aliases":   ["kilogram", "KG", "Kg", "kgs"],
      "systems":   ["metric"],
      "preferred_in": ["global"]
    },
    "t": {
      "dimension": "Mass",
      "to_si":     1000.0,
      "display":   "t",
      "name":      "Metric Tonne",
      "example":   "Bulk steel, structural steel billing",
      "aliases":   ["MT", "M.T.", "tonne", "Tonne", "ton", "metric ton", "metric_ton"],
      "systems":   ["metric"],
      "preferred_in": ["INDIA", "UK", "global"]
    }
  }
}
```

Key fields per unit:
- `dimension` - replaces `UNIT_DIMENSION`
- `to_si` - replaces `UNIT_TO_SI` and `UNIT_TO_KG`
- `display` - replaces `UNIT_DISPLAY`
- `name` + `example` - replaces `ConstructionUnits` name/example strings
- `aliases` - replaces `_UNIT_ALIASES` (flattened at load time)
- `systems` - metric / imperial / traditional (for filtering)
- `preferred_in` - country codes where this unit appears first in dropdowns

### `dimensions` block

- `si` - the SI base unit code for this dimension
- `common` - the practical reference unit for construction (e.g. `t` not `kg` for mass)

### Migration steps

| Step | Change | Risk |
|------|--------|------|
| 1 | Write `units.json` seeded from current data, fix inconsistencies | None - file only |
| 2 | Rewrite `definitions.py` to load from `units.json`, keep same exports | Low - same interface |
| 3 | Flatten aliases from `units.json` in `unit_resolver.py`, remove `_UNIT_ALIASES` hardcode | Low - same interface |
| 4 | Fix `get_known_units()` to include custom units | Additive - no breakage |
| 5 | Build Unit Manager devtool to read/write `units.json` | Additive |
| 6 | Use `preferred_in` in material dialog dropdown ordering | Enhancement |

**No other file in the codebase needs to change at any step.**

---

## Custom Units

Custom units are user-defined units stored in `CustomMaterialDB` (global, not per-project).

Storage: `CustomMaterialDB.save_custom_unit(u)` where `u = {symbol, dimension, to_si}`

Current gap: the material dialog lets users **add** custom units via `+ Add Custom Unit...`
but there is no UI to **view, edit, or delete** existing custom units.

The Unit Manager devtool will fill this gap.

---

## Devtool: Unit Manager

Four tabs:

| Tab | Purpose |
|-----|---------|
| **Dimensions** | View/edit dimensions. Set `si` and `common` unit per dimension |
| **Units** | Full table of all units from `units.json`. Add / edit / delete. Filter by dimension or system |
| **Custom Units** | Same table for `CustomMaterialDB` entries. Add / edit / delete |
| **Tester** | Type any raw string → shows resolved unit, dimension, to_si, display symbol, or "unrecognised" |
