# Project.traffic (Traffic & Road Data)

Manages traffic volume and road parameters. The API distinguishes between **India-specific** detailed modeling and **Global** (simplified) modeling.

## `Project.traffic.india` (India Mode)

Contains detailed modeling tools compliant with Indian IRC standards.

### `road` (Road Parameters)
- **`read()`** / **`write(alternate_lane_config, width, capacity, roughness, rise, fall, reroute_km, travel_time_min)`**

### `safety` (Safety & Risk)
- **`read()`** / **`write(crash_rate, work_zone_multiplier, severity_minor, severity_major, severity_fatal)`**

### `flow` (Traffic Flow & Peak Hours)
- **`read()`** / **`write(num_peak_hours, distribution, force_free_flow_off_peak)`**

### `vehicles` (Vehicle Traffic Data)
- **`read() -> dict`**: Returns `vpd` and `acc_percent` per vehicle type.
- **`write(data: dict)`**: e.g. `{"small_cars": {"vpd": 5000, "acc_percent": 30.0}}`.

### `wpi` (Wholesale Price Index)

Manages cost adjustment factors by selecting standard profiles or creating custom ones specifically for this project.

#### Discovery
- **`read() -> dict`**: Returns the currently active profile (ID, name, year) and the full matrix of adjustment ratios.
- **`list_available() -> list[dict]`**: Lists all profiles available for this project:
    - **Defaults**: Built-in IRC/DB profiles (e.g., `wpi_2019`, `wpi_2023`).
    - **Custom**: Profiles created and stored within this project.

#### Selection & Management
- **`select(profile_id: str)`**: Switches the project to use the specified WPI profile.
- **`create_custom(name, year, data, remark="") -> str`**: Creates a new custom profile local to this project and returns its unique ID.
- **`update_custom(profile_id, data)`**: Updates the adjustment ratios for an existing custom profile in this project.
- **`delete_custom(profile_id)`**: Removes a custom profile from the project.

## `Project.traffic.global` (Global Mode)

A simplified model for projects where detailed Indian traffic data is unavailable.

- **`read() -> dict`**: Returns `road_user_cost_per_day`.
- **`write(road_user_cost_per_day: float)`**: Sets the daily road user cost directly.
