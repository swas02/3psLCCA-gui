import json
from typing import Any, Dict

from .utils import _fmt, _fmt_unit, _currency, _pct
from .constants import (
    KEY_SHOW_BRIDGE_DESC,
    KEY_SHOW_FINANCIAL,
    KEY_SHOW_CONSTRUCTION,
    KEY_SHOW_LCC_ASSUMPTIONS,
    KEY_SHOW_USE_STAGE,
    KEY_SHOW_AVG_TRAFFIC,
    KEY_SHOW_ROAD_TRAFFIC,
    KEY_SHOW_PEAK_HOUR,
    KEY_SHOW_HUMAN_INJURY,
    KEY_SHOW_VEHICLE_DAMAGE,
    KEY_SHOW_TYRE_COST,
    KEY_SHOW_FUEL_OIL,
    KEY_SHOW_NEW_VEHICLE,
    KEY_SHOW_SOCIAL_CARBON,
    KEY_SHOW_MATERIAL_EMISSION,
    KEY_SHOW_USE_EMISSION,
    KEY_SHOW_VEHICLE_EMISSION,
    KEY_SHOW_ONSITE_EMISSION,
    KEY_FRAMEWORK_FIGURE,
    KEY_BRIDGE_DESC,
    KEY_FINANCIAL,
    KEY_CONSTRUCTION,
    KEY_LCC_ASSUMPTIONS,
    KEY_USE_STAGE,
    KEY_AVG_TRAFFIC,
    KEY_ROAD_TRAFFIC,
    KEY_PEAK_HOUR,
    KEY_HUMAN_INJURY,
    KEY_VEHICLE_DAMAGE,
    KEY_TYRE_COST,
    KEY_FUEL_OIL,
    KEY_NEW_VEHICLE,
    KEY_SOCIAL_CARBON,
    KEY_MATERIAL_EMISSION,
    KEY_USE_EMISSION,
    KEY_VEHICLE_EMISSION,
    KEY_ONSITE_EMISSION,
    KEY_LCC_COMPONENTS,
    KEY_STAGE_COSTS,
    KEY_PILLAR_COSTS,
    KEY_ECONOMIC_COSTS,
    KEY_SOCIAL_COSTS,
    KEY_RUC_CONSTRUCTION,
    KEY_ENVIRONMENTAL_COSTS,
    KEY_LCC_TABLE1,
    KEY_ENVIRONMENTAL_COSTS_37,
    KEY_SHOW_TRANSPORT_EMISSION,
    KEY_TRANSPORT_EMISSION,
    KEY_SHOW_TITLE_PAGE,
)




class LCCATemplate:
    """Structures export dict data for the report."""

    def __init__(self, data: Dict):
        self.raw      = data
        self.inputs   = data.get("inputs", {})
        self.computed = data.get("computed", {})
        self.results  = data.get("results", {})
        self.currency = self.inputs.get("general_info", {}).get("project_currency", "INR")

    def get_config(self) -> Dict[str, bool]:
        """Return a dict of display flags - all True by default."""
        return {
            KEY_SHOW_TITLE_PAGE:        True,
            KEY_SHOW_BRIDGE_DESC:       True,
            KEY_SHOW_FINANCIAL:         True,
            KEY_SHOW_CONSTRUCTION:      True,
            KEY_SHOW_LCC_ASSUMPTIONS:   True,
            KEY_SHOW_USE_STAGE:         True,
            KEY_SHOW_AVG_TRAFFIC:       True,
            KEY_SHOW_ROAD_TRAFFIC:      True,
            KEY_SHOW_PEAK_HOUR:         True,
            KEY_SHOW_HUMAN_INJURY:      True,
            KEY_SHOW_VEHICLE_DAMAGE:    True,
            KEY_SHOW_TYRE_COST:         True,
            KEY_SHOW_FUEL_OIL:          True,
            KEY_SHOW_NEW_VEHICLE:       True,
            KEY_SHOW_SOCIAL_CARBON:     True,
            KEY_SHOW_MATERIAL_EMISSION: True,
            KEY_SHOW_USE_EMISSION:      True,
            KEY_SHOW_VEHICLE_EMISSION:  True,
            KEY_SHOW_ONSITE_EMISSION:   True,
            KEY_SHOW_TRANSPORT_EMISSION: True,
        }

    def get_report_data(self) -> Dict[str, Any]:
        """Return the complete flat data dict used by lcca_generate.py."""
        gi = self.inputs.get("general_info", {})
        return {
            KEY_FRAMEWORK_FIGURE:   r"resource/image.jpeg",
            KEY_BRIDGE_DESC:        self._bridge_description(),
            KEY_FINANCIAL:          self._financial_data(),
            KEY_CONSTRUCTION:       self._construction_materials(),
            KEY_LCC_ASSUMPTIONS:    self._lcc_assumptions(),
            KEY_USE_STAGE:          self._use_stage_details(),
            KEY_AVG_TRAFFIC:        self._avg_daily_traffic(),
            KEY_ROAD_TRAFFIC:       self._road_traffic_data(),
            KEY_PEAK_HOUR:          self._peak_hour_distribution(),
            KEY_HUMAN_INJURY:       self._human_injury_cost(),
            KEY_VEHICLE_DAMAGE:     self._vehicle_damage_cost(),
            KEY_TYRE_COST:          self._tyre_cost_data(),
            KEY_FUEL_OIL:           self._fuel_oil_grease(),
            KEY_NEW_VEHICLE:        self._new_vehicle_cost(),
            KEY_SOCIAL_CARBON:      self._social_cost_carbon(),
            KEY_MATERIAL_EMISSION:  self._material_emission_factors(),
            KEY_USE_EMISSION:       self._use_stage_emission_assumptions(),
            KEY_VEHICLE_EMISSION:   self._vehicle_emission_factors(),
            KEY_ONSITE_EMISSION:    self._onsite_emissions(),
            KEY_TRANSPORT_EMISSION: self._transport_emissions(),
            # Results sections
            KEY_LCC_COMPONENTS:     self._lcc_components(),
            KEY_STAGE_COSTS:        self._stage_costs(),
            KEY_PILLAR_COSTS:       self._pillar_costs(),
            KEY_ECONOMIC_COSTS:     self._economic_costs(),
            KEY_SOCIAL_COSTS:       self._social_costs(),
            KEY_RUC_CONSTRUCTION:   self._ruc_construction(),
            KEY_ENVIRONMENTAL_COSTS:self._environmental_costs(),
            # Section 3 specific
            KEY_LCC_TABLE1:             self._lcc_table1(),
            KEY_ENVIRONMENTAL_COSTS_37: self._environmental_costs_37(),
            # Meta
            "currency":             self.currency,
            "exported_at":          self.raw.get("exported_at", ""),
            # Title page fields
            "project_name":         gi.get("project_name", ""),
            "project_code":         gi.get("project_code", ""),
            "project_description":  gi.get("project_description", ""),
            "remarks":              gi.get("remarks", ""),
            "agency_name":          gi.get("agency_name", ""),
            "contact_person":       gi.get("contact_person", ""),
            "agency_address":       gi.get("agency_address", ""),
            "agency_email":         gi.get("agency_email", ""),
            "agency_phone":         gi.get("agency_phone", ""),
            "agency_logo_b64":      gi.get("agency_logo", ""),
            "reviewer_name":        gi.get("reviewer_name", ""),
            "reviewer_organization": gi.get("reviewer_organization", ""),
            "reviewer_address":     gi.get("reviewer_address", ""),
            "reviewer_email":       gi.get("reviewer_email", ""),
            "reviewer_phone":       gi.get("reviewer_phone", ""),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Section 2.1: Bridge Description
    # FIX: Added new rows from updated template:
    #   - Direction of traffic (One way/Two way)
    #   - No of days in a month traffic on road is affected
    #   - Analysis period (years)
    # FIX: All zero values now show as "0" instead of blank
    # ─────────────────────────────────────────────────────────────────────────
    def _bridge_description(self) -> Dict[str, str]:
        bd  = self.inputs.get("bridge_data", {})
        dur_months = bd.get("duration_construction_months", 0)
        dur_years  = round(dur_months / 12, 2) if dur_months else 0

        def _v(val):
            if val is None:
                return ""
            if val == "":
                return ""
            if isinstance(val, float) and val == int(val):
                return str(int(val))
            return str(val)

        # Analysis period = design life (same field used in LCCA)
        design_life = bd.get("design_life", 0)

        return {
            "Name of bridge":
                _v(bd.get("bridge_name")),
            "Name of user/agency":
                _v(bd.get("user_agency")),
            "Location of bridge (Country)":
                _v(bd.get("project_country")),
            "Location of bridge (State)":
                _v(bd.get("location_address")),
            "Type of bridge":
                _v(bd.get("bridge_type")),
            "Span (m)":
                _v(bd.get("span")),
            "No. of lanes":
                _v(bd.get("num_lanes")),
            "Direction of traffic (One way/Two way)":
                _v(bd.get("vehicle_path_direction")),
            "Footpath (Yes/No)":
                _v(bd.get("footpath")),
            "Wind Speed (m/sec)":
                _v(bd.get("wind_speed")),
            "Carriageway width (m)":
                _v(bd.get("carriageway_width")),
            "Year of construction/Present year for life cycle cost assessment":
                _v(bd.get("year_of_construction")),
            "Duration of construction (months)":
                _v(bd.get("duration_construction_months")),
            "No. of working days in a month":
                _v(bd.get("working_days_per_month")),
            "No of days in a month traffic on road is affected":
                _v(bd.get("days_per_month")),
            "Design life (years)":
                _v(design_life),
            "Analysis period (years)":
                _v(design_life),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Section 2.2: Financial Data
    # FIX: 0 values now display as "0" not blank
    # ─────────────────────────────────────────────────────────────────────────
    def _financial_data(self) -> Dict[str, str]:
        fd = self.inputs.get("financial_data", {})
        def _fv(val):
            if val is None:
                return ""
            return str(val)
        return {
            "Discount rate":    _fv(fd.get("discount_rate")),
            "Inflation rate":   _fv(fd.get("inflation_rate")),
            "Interest rate":    _fv(fd.get("interest_rate")),
            "Investment ratio": _fv(fd.get("investment_ratio")),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Section 2.3: Construction materials
    # FIX: 0 quantities/rates show as "0" not blank
    # ─────────────────────────────────────────────────────────────────────────
    def _construction_materials(self) -> Dict[str, list]:
        cwd = self.inputs.get("construction_work_data", {})
        result = {}

        for cat_name, cat_data in cwd.items():
            if cat_name == "grand_total":
                continue
            components = cat_data.get("components", {})
            cat_rows = {}

            for comp_name, comp_data in components.items():
                items = comp_data.get("items", [])
                if not items:
                    continue

                rows = []
                for item in items:
                    vals          = item.get("values", {})
                    meta          = item.get("meta", {})
                    mat           = vals.get("material_name", "").strip() or comp_name
                    qty           = vals.get("quantity", 0)
                    unit          = vals.get("unit", "")
                    rate          = vals.get("rate", 0)
                    rate_source   = vals.get("rate_source", "").strip()
                    meta_source   = meta.get("source", "")
                    source_db_key = meta.get("source_db_key", "").strip()

                    db_modified = (meta_source == "db_modified")

                    if meta_source in ("db", "db_modified"):
                        source_display = source_db_key
                    else:
                        # manual or anything else - no db key, show blank
                        source_display = ""

                    rows.append([
                        mat,
                        _fmt(qty),
                        _fmt_unit(unit),
                        _fmt(rate),
                        source_display,
                        db_modified,   # True => light green background on source cell
                    ])

                if rows:
                    cat_rows[comp_name] = rows

            if cat_rows:
                result[cat_name] = cat_rows

        if not result:
            result[""] = {"": [["", "", "", "", "", False]]}

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Section 2.3 continued: LCC Assumptions
    # FIX: 0% shows as "0%" not blank
    # ─────────────────────────────────────────────────────────────────────────
    def _lcc_assumptions(self) -> Dict[str, list]:
        md  = self.inputs.get("maintenance_data", {})
        dem = self.inputs.get("demolition_data", {})
        return {
            "Routine inspection cost":     [_pct(md.get("routine_inspection_cost")),     "Initial construction cost"],
            "Major inspection cost":       [_pct(md.get("major_inspection_cost")),        "Initial construction cost"],
            "Replacement cost":            [_pct(md.get("bearing_exp_joint_cost")),       "Initial superstructure cost"],
            "Demolition and disposal cost":[_pct(dem.get("demolition_cost_pct")),         "Initial construction cost"],
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Section 2.3 continued: Use Stage Details
    # FIX: 0 values show as "0" not blank
    # ─────────────────────────────────────────────────────────────────────────
    def _use_stage_details(self) -> Dict[str, str]:
        md  = self.inputs.get("maintenance_data", {})
        dem = self.inputs.get("demolition_data", {})

        def _iv(val):
            if val is None:
                return ""
            if isinstance(val, float) and val == int(val):
                return str(int(val))
            return str(val)

        return {
            "Duration of routine inspections (days)":                       "",
            "Interval for routine inspection (years)":                      _iv(md.get("routine_inspection_freq")),
            "Duration of periodic maintenance (days)":                      "",
            "Interval for periodic maintenance (years)":                    _iv(md.get("periodic_maintenance_freq")),
            "Duration of major inspection (days)":                          "",
            "Interval for major inspection (years)":                        _iv(md.get("major_inspection_freq")),
            "Duration of replacement of bearing and expansion joint (days)":"",
            "Interval for replacement of bearing and expansion joint (years)":
                _iv(md.get("bearing_exp_joint_freq")),
            "Duration of repairs and rehabilitation (days)":                "",
            "Interval for repairs and rehabilitation (years)":              _iv(md.get("major_repair_freq")),
            "Duration of major repairs (days)":                             _iv(md.get("major_repair_duration")),
            "Interval for major repairs (years)":                           _iv(md.get("major_repair_freq")),
            "Duration of demolition and disposal (years)":                  _iv(dem.get("demolition_duration")),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Section 2.4: Traffic Data
    # ─────────────────────────────────────────────────────────────────────────
    def _avg_daily_traffic(self) -> Dict[str, str]:
        trd = self.inputs.get("traffic_and_road_data", {})
        vd  = trd.get("vehicle_data", {})
        label_map = {
            "small_cars":   "Small car",
            "big_cars":     "Big car",
            "two_wheelers": "Two-wheeler",
            "o_buses":      "Ordinary bus",
            "d_buses":      "Deluxe bus",
            "lcv":          "LCV - Light Commercial Vehicles",
            "hcv":          "HCV - Two/Three Axle Heavy Commercial Vehicles",
            "mcv":          "MCV - Multi Axle Vehicles",
        }
        result = {}
        for key, label in label_map.items():
            vpd = vd.get(key, {}).get("vehicles_per_day", 0)
            # FIX: 0 shows as "0" not blank
            result[label] = str(int(vpd)) if vpd is not None else ""
        return result

    def _road_traffic_data(self) -> Dict[str, str]:
        trd = self.inputs.get("traffic_and_road_data", {})
        def _rv(val):
            if val is None:
                return ""
            return str(val)
        return {
            "Average Daily Traffic (ADT)":
                "",
            "Average speed":
                "",
            "Additional travel time":
                _rv(trd.get("additional_travel_time_min")),
            "Additional distance travelled, Average detour, Detour/affected distance":
                _rv(trd.get("additional_reroute_distance_km")),
            "Terrain":
                "",
            "Alternate route's roadway classification":
                _rv(trd.get("alternate_road_carriageway")),
            "One way or Two way":
                _rv(trd.get("vehicle_path_direction",
                    self.inputs.get("bridge_data", {}).get("vehicle_path_direction"))),
            "Road capacity":
                _rv(trd.get("hourly_capacity")),
            "Roughness, RG":
                _rv(trd.get("road_roughness_mm_per_km")),
            "Rise/Fall, RF":
                _rv(trd.get("road_rise_m_per_km")),
            "Rise, RS":
                "",
            "Fall, FL":
                "",
            "Crash rate":
                _rv(trd.get("crash_rate_accidents_per_million_km")),
            "Work zone accident multiplier":
                _rv(trd.get("work_zone_multiplier")),
            "No of peak hours":
                _rv(trd.get("num_peak_hours")),
        }

    def _peak_hour_distribution(self) -> Dict[str, str]:
        """Table 2-11: Peak hour distribution."""
        trd  = self.inputs.get("traffic_and_road_data", {})
        dist = trd.get("peak_hour_distribution", {}) or {}
        result = {}
        for key, val in dist.items():
            label = key.replace("_", " ").title()
            result[label] = _fmt(val) if val is not None else ""
        if not result:
            result[""] = ""
        return result

    def _human_injury_cost(self) -> Dict[str, str]:
        trd  = self.inputs.get("traffic_and_road_data", {})
        return {
            "Fatal":        _fmt(trd.get("severity_fatal")),
            "Major injury": _fmt(trd.get("severity_major")),
            "Minor injury": _fmt(trd.get("severity_minor")),
        }

    def _vehicle_damage_cost(self) -> Dict[str, str]:
        trd  = self.inputs.get("traffic_and_road_data", {})
        vd   = trd.get("vehicle_data", {})
        label_map = {
            "small_cars":   "Small car",
            "big_cars":     "Big car",
            "two_wheelers": "Two-wheeler",
            "o_buses":      "Ordinary bus",
            "d_buses":      "Deluxe bus",
            "lcv":          "LCV",
            "hcv":          "HCV",
            "mcv":          "MCV",
        }
        result = {}
        for key, label in label_map.items():
            acc_pct = vd.get(key, {}).get("accident_percentage", 0)
            result[label] = _fmt(acc_pct)
        return result

    def _tyre_cost_data(self) -> Dict[str, list]:
        trd  = self.inputs.get("traffic_and_road_data", {})
        wpi  = trd.get("wpi", {}).get("data_snapshot", {})
        tyre = wpi.get("selected", {}).get("vehicle_cost", {}).get("tyre_cost", {})
        wheels = {
            "small_cars": 4, "big_cars": 4, "two_wheelers": 2,
            "o_buses": 6, "d_buses": 6, "lcv": 6, "hcv": 10, "mcv": 18,
        }
        label_map = {
            "small_cars": "Small car", "big_cars": "Big car",
            "two_wheelers": "Two-wheeler", "o_buses": "Ordinary bus",
            "d_buses": "Deluxe bus", "lcv": "LCV", "hcv": "HCV", "mcv": "MCV",
        }
        result = {}
        for key, label in label_map.items():
            cost = tyre.get(key, 0)
            result[label] = [str(wheels[key]), _fmt(cost), "1.0"]
        return result

    def _fuel_oil_grease(self) -> Dict[str, str]:
        trd  = self.inputs.get("traffic_and_road_data", {})
        wpi  = trd.get("wpi", {}).get("data_snapshot", {})
        fuel = wpi.get("selected", {}).get("fuel_cost", {})
        return {
            "Cost of engine oil (Rs/liter) (2019)":  _fmt(fuel.get("engine_oil", 0)),
            "WPI for engine oil":                    "1.0",
            "Petrol price (Rs/liter)":               _fmt(fuel.get("petrol", 0)),
            "Diesel price (Rs/liter)":               _fmt(fuel.get("diesel", 0)),
            "Cost of other oil (Rs/liter) (2019)":   _fmt(fuel.get("other_oil", 0)),
            "WPI ratio for other oil":               "1.0",
            "Cost of grease (Rs/kg)":                _fmt(fuel.get("grease", 0)),
            "WPI ratio for grease":                  "1.0",
        }

    def _new_vehicle_cost(self) -> Dict[str, list]:
        label_map = {
            "small_cars": "Small car", "big_cars": "Big car",
            "two_wheelers": "Two-wheeler", "o_buses": "Ordinary bus",
            "d_buses": "Deluxe bus", "lcv": "LCV", "hcv": "HCV", "mcv": "MCV",
        }
        result = {}
        for key, label in label_map.items():
            result[label] = ["", ""]
        return result

    def _social_cost_carbon(self) -> Dict[str, str]:
        ced  = self.inputs.get("carbon_emission_data", {})
        scd  = ced.get("social_cost_data", {})
        res  = scd.get("result", {})
        cost = res.get("cost_of_carbon_local", 0)
        scc_val = _fmt(cost, 4) if cost is not None else "0"
        return {
            "Social Cost of Carbon (SCC) \u20b9/kgCO\u2082e": scc_val,
        }

    def _material_emission_factors(self) -> Dict[str, list]:
        """
        Returns {material: [category, quantity, unit, conversion_factor, emission_factor, ef_unit]}
        to match the 7-column template table:
        Category | Material | Quantity | Unit | Conversion factor | Emission factor | Emission factor unit
        """
        ced   = self.inputs.get("carbon_emission_data", {})
        items = ced.get("material_emissions_data", {}).get("included_items", [])

        result: Dict[str, list] = {}
        seen_mats = set()

        for item in items:
            mat = item.get("material", "").strip()
            if not mat:
                continue
            if mat in seen_mats:
                continue
            seen_mats.add(mat)

            category = item.get("category", "").strip()
            qty      = item.get("quantity", 0)
            mat_unit = item.get("unit", "")
            cf       = item.get("conversion_factor", 1)
            ef       = item.get("carbon_emission", 0)
            ef_unit  = item.get("carbon_unit", "")

            result[mat] = [
                category if category else "",
                _fmt(qty),
                _fmt_unit(mat_unit) if mat_unit else "",
                str(cf) if cf is not None else "1",
                _fmt(ef, 4) if ef is not None else "0",
                _fmt_unit(ef_unit) if ef_unit else "",
            ]

        if not result:
            result[""] = ["", "", "", "", "", ""]

        return result

    def _use_stage_emission_assumptions(self) -> Dict[str, str]:
        md  = self.inputs.get("maintenance_data", {})
        dem = self.inputs.get("demolition_data", {})
        return {
            "Periodic maintenance carbon emission":
                _pct(md.get("periodic_maintenance_carbon_cost")),
            "Major repair related carbon emission":
                _pct(md.get("major_repair_carbon_cost")),
            "Demolition and disposal related carbon emissions":
                _pct(dem.get("demolition_carbon_cost_pct")),
        }

    def _vehicle_emission_factors(self) -> Dict[str, str]:
        trd = self.inputs.get("traffic_and_road_data", {})
        emf = trd.get("diversion_emissions", {}).get("emission_factors", {})

        label_map = {
            "small_cars": "Small car",
            "big_cars": "Big car",
            "two_wheelers": "Two-wheeler",
            "o_buses": "Ordinary bus",
            "d_buses": "Deluxe bus",
            "lcv": "LCV - Light Commercial Vehicles",
            "hcv": "HCV - Two/Three Axle Heavy Commercial Vehicles",
            "mcv": "MCV - Multi Axle Vehicles",
        }

        result = {}
        for key, label in label_map.items():
            val = emf.get(key, 0)
            result[label] = _fmt(val)
        return result

    def _onsite_emissions(self) -> Dict[str, list]:
        """Returns {equipment_name: [source, rate, hrs, days, ef]}"""
        ced     = self.inputs.get("carbon_emission_data", {})
        mach    = ced.get("machinery_emissions_data", {})
        rows    = mach.get("detailed", {}).get("rows", [])
        result  = {}
        for row in rows:
            name = row.get("name", "")
            hrs  = row.get("hrs", 0)
            days = row.get("days", 0)
            rate = row.get("rate", 0)
            ef   = row.get("ef", 0)
            src  = row.get("source", "")
            result[name] = [
                src,
                _fmt(rate),
                _fmt(hrs),
                str(days),
                _fmt(ef, 3),
            ]
        return result

    def _transport_emissions(self) -> Dict[str, list]:
        """
        Table 2-17: Data for emissions related to transportation of material.
        Returns {material: [vehicle_name, GVW, cargo_cap, distance, source, destination, ef]}
        """
        ced   = self.inputs.get("carbon_emission_data", {})
        trans = ced.get("transport_emissions_data", {})
        rows  = trans.get("rows", []) if isinstance(trans, dict) else []
        result = {}
        for row in rows:
            mat  = row.get("material", "")
            veh  = row.get("vehicle_name", "")
            gvw  = row.get("gvw", 0)
            cap  = row.get("cargo_capacity", 0)
            dist = row.get("distance", 0)
            src  = row.get("source", "")
            dst  = row.get("destination", "")
            ef   = row.get("emission_factor", 0)
            result[mat] = [veh, _fmt(gvw), _fmt(cap), _fmt(dist), src, dst, _fmt(ef, 4)]
        if not result:
            result[""] = ["", "", "", "", "", "", ""]
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Results section extractors
    # FIX: All 0 values display as "INR 0.00" not blank
    # ─────────────────────────────────────────────────────────────────────────

    def _lcc_table1(self) -> dict:
        init  = self.results.get("initial_stage", {})
        use   = self.results.get("use_stage", {})
        recon = self.results.get("reconstruction", {})
        eol   = self.results.get("end_of_life", {})
        ic    = self.computed.get("initial_construction_cost", 0) or 1

        def _total_lcc():
            total = 0.0
            for stage in [init, use, eol]:
                for pillar in stage.values():
                    if isinstance(pillar, dict):
                        for v in pillar.values():
                            try: total += float(v)
                            except: pass
            return total or 1

        lcc_total = _total_lcc()

        def _row(cost):
            try: cost = float(cost)
            except: cost = 0.0
            cr     = cost / 1e7
            lakhs  = cost / 1e5
            mil    = cost / 1e6
            pct_ic = cost / ic * 100
            pct_lcc= cost / lcc_total * 100
            cur = self.currency
            return [
                f"{cur} {cost:,.2f}",
                f"{cur} {cr:.2f}",
                f"{cur} {lakhs:.2f}",
                f"{cur} {mil:.2f}",
                f"{pct_ic:.2f}",
                f"{pct_lcc:.2f}",
            ]

        eco  = init.get("economic", {})
        env  = init.get("environmental", {})
        soc  = init.get("social", {})
        ueco = use.get("economic", {})
        uenv = use.get("environmental", {})
        usoc = use.get("social", {})
        eeco = eol.get("economic", {})
        eenv = eol.get("environmental", {})
        esoc = eol.get("social", {})

        recon_note = recon.get("Note", "")
        recon_na   = "not applicable" in recon_note.lower()
        reco       = recon.get("economic", {})
        renv       = recon.get("environmental", {})
        rsoc       = recon.get("social", {})

        def _rv(d, key): return 0.0 if recon_na else float(d.get(key, 0) or 0)

        return {
            "Initial Stage Costs": {
                "Initial construction costs":
                    _row(eco.get("initial_construction_cost", 0)),
                "Initial carbon emissions (material)":
                    _row(env.get("initial_material_carbon_emission_cost", 0)),
                "Initial carbon emissions (on-site)":
                    _row(env.get("initial_vehicular_emission_cost", 0)),
                "Time costs":
                    _row(eco.get("time_cost_of_loan", 0)),
                "Road user costs during initial construction":
                    _row(soc.get("initial_road_user_cost", 0)),
                "Carbon emissions due to rerouting during initial construction (vehicles)":
                    _row(0),
            },
            "Use Stage Costs": {
                "Routine inspection costs":
                    _row(ueco.get("routine_inspection_costs", 0)),
                "Periodic maintenance costs":
                    _row(ueco.get("periodic_maintenance", 0)),
                "Periodic maintenance carbon emissions (material)":
                    _row(uenv.get("periodic_carbon_costs", 0)),
                "Major inspection costs":
                    _row(ueco.get("major_inspection_costs", 0)),
                "Major repair costs":
                    _row(ueco.get("major_repair_cost", 0)),
                "Major repair related carbon emissions (materials)":
                    _row(uenv.get("major_repair_material_carbon_emission_costs", 0)),
                "Road user costs during major repairs":
                    _row(usoc.get("major_repair_road_user_costs", 0)),
                "Carbon emissions due to rerouting during major repairs (vehicles)":
                    _row(uenv.get("major_repair_vehicular_emission_costs", 0)),
                "Replacement cost of bearing and expansion joint":
                    _row(ueco.get("replacement_costs_for_bearing_and_expansion_joint", 0)),
                "Road user costs during replacement":
                    _row(usoc.get("road_user_costs_for_replacement_of_bearing_and_expansion_joint", 0)),
                "Carbon emissions due to rerouting during replacement (vehicles)":
                    _row(uenv.get("vehicular_emission_costs_for_replacement_of_bearing_and_expansion_joint", 0)),
            },
            "Reconstruction": {
                "Demolition and disposal costs of existing bridge":
                    _row(_rv(reco, "demolition_cost")),
                "Demolition and disposal related carbon emissions (materials) of existing bridge":
                    _row(_rv(renv, "demolition_carbon_cost")),
                "Road user costs during demolition and disposal of existing bridge":
                    _row(_rv(rsoc, "ruc_demolition")),
                "Carbon emissions due to rerouting during demolition and disposal (vehicles) of existing bridge":
                    _row(0),
                "Recycling Costs for reconstruction":
                    _row(0),
                "Reconstruction costs":
                    _row(_rv(reco, "reconstruction_cost")),
                "Reconstruction carbon emissions (materials)":
                    _row(_rv(renv, "reconstruction_carbon_cost")),
                "Reconstruction time costs":
                    _row(_rv(reco, "time_cost_reconstruction")),
                "Road user costs during reconstruction":
                    _row(_rv(rsoc, "ruc_reconstruction")),
                "Carbon emissions due to rerouting during reconstruction (vehicles)":
                    _row(0),
            },
            "End-of-life Stage Costs": {
                "Demolition and disposal costs":
                    _row(eeco.get("total_demolition_and_disposal_costs", 0)),
                "Demolition and disposal related carbon emissions (materials)":
                    _row(eenv.get("carbon_costs_demolition_and_disposal", 0)),
                "Road user costs during demolition and disposal":
                    _row(esoc.get("ruc_demolition", 0)),
                "Carbon emissions due to rerouting during demolition and disposal (vehicles)":
                    _row(eenv.get("demolition_vehicular_emission_cost", 0)),
                "Recycling costs":
                    _row(-(eeco.get("total_scrap_value", 0) or 0)),
            },
        }

    def _lcc_components(self) -> Dict[str, list]:
        init  = self.results.get("initial_stage", {})
        use   = self.results.get("use_stage", {})
        eol   = self.results.get("end_of_life", {})
        ic    = self.computed.get("initial_construction_cost", 0)

        def row(cost):
            if cost is None: cost = 0
            try: cost = float(cost)
            except: cost = 0
            cr      = cost / 1e7
            lakh    = cost / 1e5
            mil     = cost / 1e6
            pct_ic  = (cost / ic * 100) if ic else 0
            return [
                _currency(cost, self.currency),
                _fmt(cr, 4),
                _fmt(lakh, 2),
                _fmt(mil, 4),
                _fmt(pct_ic, 2),
            ]

        eco  = init.get("economic", {})
        env  = init.get("environmental", {})
        soc  = init.get("social", {})
        ueco = use.get("economic", {})
        uenv = use.get("environmental", {})
        usoc = use.get("social", {})
        eeco = eol.get("economic", {})
        eenv = eol.get("environmental", {})
        esoc = eol.get("social", {})

        entries = {}
        entries["Initial construction costs"]                          = row(eco.get("initial_construction_cost"))
        entries["Initial carbon emissions (material)"]                 = row(env.get("initial_material_carbon_emission_cost"))
        entries["Initial carbon emissions (on-site)"]                  = row(env.get("initial_vehicular_emission_cost"))
        entries["Time costs"]                                          = row(eco.get("time_cost_of_loan"))
        entries["Road user costs during initial construction"]         = row(soc.get("initial_road_user_cost"))
        entries["Routine inspection costs"]                            = row(ueco.get("routine_inspection_costs"))
        entries["Periodic maintenance costs"]                          = row(ueco.get("periodic_maintenance"))
        entries["Periodic maintenance carbon emissions (material)"]    = row(uenv.get("periodic_carbon_costs"))
        entries["Major inspection costs"]                              = row(ueco.get("major_inspection_costs"))
        entries["Major repair costs"]                                  = row(ueco.get("major_repair_cost"))
        entries["Major repair-related carbon emissions (materials)"]   = row(uenv.get("major_repair_material_carbon_emission_costs"))
        entries["Road user costs during major repairs"]                = row(usoc.get("major_repair_road_user_costs"))
        entries["Replacement cost of bearings & expansion joint"]      = row(ueco.get("replacement_costs_for_bearing_and_expansion_joint"))
        entries["Road user costs during replacement"]                  = row(usoc.get("road_user_costs_for_replacement_of_bearing_and_expansion_joint"))
        entries["Demolition and disposal costs"]                       = row(eeco.get("total_demolition_and_disposal_costs"))
        entries["Demolition and disposal carbon emissions (materials)"]= row(eenv.get("carbon_costs_demolition_and_disposal"))
        entries["Road user costs during demolition and disposal"]      = row(esoc.get("ruc_demolition"))
        entries["Recycling costs"]                                     = row(-abs(eeco.get("total_scrap_value", 0)))
        return entries

    def _stage_costs(self) -> Dict[str, str]:
        init = self.results.get("initial_stage", {})
        use  = self.results.get("use_stage", {})
        eol  = self.results.get("end_of_life", {})

        def _sum_dict(d: dict) -> float:
            total = 0.0
            for sub in d.values():
                if isinstance(sub, dict):
                    for v in sub.values():
                        try: total += float(v)
                        except: pass
                else:
                    try: total += float(sub)
                    except: pass
            return total

        init_total = _sum_dict(init)
        use_total  = _sum_dict(use)
        eol_total  = _sum_dict(eol)

        return {
            "Initial stage cost":  _currency(init_total, self.currency),
            "Use stage cost":      _currency(use_total,  self.currency),
            "End of life cost":    _currency(eol_total,  self.currency),
        }

    def _pillar_costs(self) -> Dict[str, str]:
        """Compute pillar costs from results."""
        init = self.results.get("initial_stage", {})
        use  = self.results.get("use_stage", {})
        eol  = self.results.get("end_of_life", {})
        recon = self.results.get("reconstruction", {})

        def _sum_pillar(pillar_key):
            total = 0.0
            for stage in [init, use, eol, recon]:
                d = stage.get(pillar_key, {})
                for v in d.values():
                    try: total += float(v)
                    except: pass
            return total

        return {
            "Economic cost":      _currency(_sum_pillar("economic"),     self.currency),
            "Social cost":        _currency(_sum_pillar("social"),       self.currency),
            "Environmental cost": _currency(_sum_pillar("environmental"), self.currency),
        }

    def _economic_costs(self) -> Dict[str, str]:
        init = self.results.get("initial_stage", {}).get("economic", {})
        use  = self.results.get("use_stage", {}).get("economic", {})
        eol  = self.results.get("end_of_life", {}).get("economic", {})
        rec  = self.results.get("reconstruction", {}).get("economic", {})
        return {
            "Initial construction cost":
                _currency(init.get("initial_construction_cost"), self.currency),
            "Time cost":
                _currency(init.get("time_cost_of_loan"), self.currency),
            "Periodic maintenance cost":
                _currency(use.get("periodic_maintenance"), self.currency),
            "Routine inspection cost":
                _currency(use.get("routine_inspection_costs"), self.currency),
            "Major inspection cost":
                _currency(use.get("major_inspection_costs"), self.currency),
            "Major repair cost":
                _currency(use.get("major_repair_cost"), self.currency),
            "Replacement cost of bearing and expansion joint":
                _currency(use.get("replacement_costs_for_bearing_and_expansion_joint"), self.currency),
            "Demolition and disposal cost for reconstruction":
                _currency(rec.get("demolition_cost"), self.currency),
            "Reconstruction cost":
                _currency(rec.get("reconstruction_cost"), self.currency),
            "Time cost for reconstruction":
                _currency(rec.get("time_cost"), self.currency),
            "Demolition and disposal cost":
                _currency(eol.get("total_demolition_and_disposal_costs"), self.currency),
            "Recycling cost":
                _currency(-abs(eol.get("total_scrap_value", 0)), self.currency),
        }

    def _social_costs(self) -> Dict[str, str]:
        init = self.results.get("initial_stage", {}).get("social", {})
        use  = self.results.get("use_stage", {}).get("social", {})
        eol  = self.results.get("end_of_life", {}).get("social", {})
        rec  = self.results.get("reconstruction", {}).get("social", {})
        return {
            "Road user cost during construction":
                _currency(init.get("initial_road_user_cost"), self.currency),
            "Road user cost during major repairs":
                _currency(use.get("major_repair_road_user_costs"), self.currency),
            "Road user costs during replacement of bearings and expansion joint":
                _currency(use.get("road_user_costs_for_replacement_of_bearing_and_expansion_joint"), self.currency),
            "Road user cost during demolition for reconstruction":
                _currency(rec.get("ruc_demolition"), self.currency),
            "Road user cost during reconstruction":
                _currency(rec.get("ruc_reconstruction"), self.currency),
            "Road user costs during demolition":
                _currency(eol.get("ruc_demolition"), self.currency),
        }

    def _ruc_construction(self) -> Dict[str, str]:
        ruc = self.computed.get("daily_road_user_cost_with_vehicular_emissions", {})
        voc = ruc.get("vehicle_operation_cost", {}).get("total", {}).get("IT", 0)
        vot = ruc.get("value_of_time", {}).get("total_Cost", 0)
        acc = ruc.get("accident_cost", {}).get("total_accident_cost_INR_per_day", 0)
        return {
            "Vehicle Operating Cost":  _currency(voc, self.currency),
            "Value of Time Cost":      _currency(vot, self.currency),
            "Accident Cost":           _currency(acc, self.currency),
        }

    def _environmental_costs_37(self) -> Dict[str, str]:
        init  = self.results.get("initial_stage", {}).get("environmental", {})
        use   = self.results.get("use_stage", {}).get("environmental", {})
        recon = self.results.get("reconstruction", {})
        eol   = self.results.get("end_of_life", {}).get("environmental", {})
        recon_na = "not applicable" in recon.get("Note", "").lower()

        def _rv(key):
            if recon_na: return _currency(0, self.currency)
            d = recon.get("environmental", {})
            return _currency(d.get(key, 0), self.currency)

        return {
            "Carbon emission cost from construction material":
                _currency(init.get("initial_material_carbon_emission_cost"), self.currency),
            "Carbon emission cost due to on-site activities":
                _currency(init.get("initial_vehicular_emission_cost"), self.currency),
            "Carbon emission cost due to rerouting":
                _currency(init.get("initial_vehicular_emission_cost"), self.currency),
            "Carbon emission cost due to periodic maintenance":
                _currency(use.get("periodic_carbon_costs"), self.currency),
            "Carbon emission cost due to major repairs":
                _currency(use.get("major_repair_material_carbon_emission_costs"), self.currency),
            "Carbon emission cost due rerouting of vehicles during major repairs":
                _currency(use.get("major_repair_vehicular_emission_costs"), self.currency),
            "Carbon emissions cost due to replacement of bearings and expansion joint":
                _currency(use.get("vehicular_emission_costs_for_replacement_of_bearing_and_expansion_joint"), self.currency),
            "Carbon emission cost due rerouting of vehicles during replacement of bearing and expansion joint":
                _currency(use.get("vehicular_emission_costs_for_replacement_of_bearing_and_expansion_joint"), self.currency),
            "Carbon emission cost due to demolition and disposal for reconstruction":
                _rv("demolition_carbon_cost"),
            "Carbon emission cost due rerouting of vehicles during demolition for reconstruction":
                _rv("demolition_vehicular_emission_cost"),
            "Carbon emission cost due to reconstruction":
                _rv("reconstruction_carbon_cost"),
            "Carbon emission cost due rerouting of vehicles during reconstruction":
                _rv("reconstruction_vehicular_emission_cost"),
            "Carbon emission cost due to demolition and disposal":
                _currency(eol.get("carbon_costs_demolition_and_disposal"), self.currency),
            "Carbon emission cost due rerouting of vehicles during demolition":
                _currency(eol.get("demolition_vehicular_emission_cost"), self.currency),
        }

    def _environmental_costs(self) -> Dict[str, str]:
        return self._environmental_costs_37()


# ─────────────────────────────────────────────────────────────────────────────
# CLI convenience
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, pprint
    parser = argparse.ArgumentParser(description="Preview extracted LCCA template data")
    parser.add_argument("json", help="Path to .3psLCCA JSON file")
    args = parser.parse_args()

    with open(args.json, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    tmpl = LCCATemplate(raw)
    data = tmpl.get_report_data()
    pprint.pprint(data, width=120)
