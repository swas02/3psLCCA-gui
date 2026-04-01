# Project.bridge (Bridge Data)

Manages the physical and technical specifications of the bridge.

## `Project.bridge.identity` (Identification)

- **`read() -> dict`**: Returns `name` and `owner`.
- **`write(name=None, owner=None)`**: Updates bridge identification.

## `Project.bridge.location` (Location)

- **`read() -> dict`**: Returns `country`, `from`, `via`, and `to`.
- **`write(from=None, via=None, to=None)`**: Updates location details.
- **Note**: `country` is read-only.

## `Project.bridge.specs` (Technical Specifications)

- **`read() -> dict`**: Returns `type`, `span`, `width`, `lanes`, `direction`, `has_footpath`, and `wind_speed`.
- **`write(type=None, span=None, width=None, lanes=None, direction=None, has_footpath=None, wind_speed=None)`**: Updates structural specs.

## `Project.bridge.lifecycle` (Life Cycle & Schedule)

- **`read() -> dict`**: Returns `design_life`, `construction_year`, `duration_months`, `working_days`, and `affected_days`.
- **`write(design_life=None, year=None, duration=None, working_days=None, affected_days=None)`**: Updates lifecycle and schedule details.
