
# ─────────────────────────────────────────────────────────────────────────────
# Section key constants
# ─────────────────────────────────────────────────────────────────────────────

KEY_SHOW_BRIDGE_DESC        = "show_bridge_desc"
KEY_SHOW_FINANCIAL          = "show_financial"
KEY_SHOW_CONSTRUCTION       = "show_construction"
KEY_SHOW_LCC_ASSUMPTIONS    = "show_lcc_assumptions"
KEY_SHOW_USE_STAGE          = "show_use_stage"
KEY_SHOW_AVG_TRAFFIC        = "show_avg_traffic"
KEY_SHOW_ROAD_TRAFFIC       = "show_road_traffic"
KEY_SHOW_PEAK_HOUR          = "show_peak_hour"
KEY_SHOW_HUMAN_INJURY       = "show_human_injury"
KEY_SHOW_VEHICLE_DAMAGE     = "show_vehicle_damage"
KEY_SHOW_TYRE_COST          = "show_tyre_cost"
KEY_SHOW_FUEL_OIL           = "show_fuel_oil"
KEY_SHOW_NEW_VEHICLE        = "show_new_vehicle"
KEY_SHOW_SOCIAL_CARBON      = "show_social_carbon"
KEY_SHOW_MATERIAL_EMISSION  = "show_material_emission"
KEY_SHOW_USE_EMISSION       = "show_use_emission"
KEY_SHOW_VEHICLE_EMISSION   = "show_vehicle_emission"
KEY_SHOW_ONSITE_EMISSION    = "show_onsite_emission"

KEY_FRAMEWORK_FIGURE        = "framework_figure"
KEY_BRIDGE_DESC             = "bridge_desc"
KEY_FINANCIAL               = "financial"
KEY_CONSTRUCTION            = "construction"
KEY_LCC_ASSUMPTIONS         = "lcc_assumptions"
KEY_USE_STAGE               = "use_stage"
KEY_AVG_TRAFFIC             = "avg_traffic"
KEY_ROAD_TRAFFIC            = "road_traffic"
KEY_PEAK_HOUR               = "peak_hour"
KEY_HUMAN_INJURY            = "human_injury"
KEY_VEHICLE_DAMAGE          = "vehicle_damage"
KEY_TYRE_COST               = "tyre_cost"
KEY_FUEL_OIL                = "fuel_oil"
KEY_NEW_VEHICLE             = "new_vehicle"
KEY_SOCIAL_CARBON           = "social_carbon"
KEY_MATERIAL_EMISSION       = "material_emission"
KEY_USE_EMISSION            = "use_emission"
KEY_VEHICLE_EMISSION        = "vehicle_emission"
KEY_ONSITE_EMISSION         = "onsite_emission"

# Results keys
KEY_LCC_COMPONENTS          = "lcc_components"
KEY_STAGE_COSTS             = "stage_costs"
KEY_PILLAR_COSTS            = "pillar_costs"
KEY_ECONOMIC_COSTS          = "economic_costs"
KEY_SOCIAL_COSTS            = "social_costs"
KEY_RUC_CONSTRUCTION        = "ruc_construction"
KEY_ENVIRONMENTAL_COSTS     = "environmental_costs"

# Section 3 result keys
KEY_LCC_TABLE1              = "lcc_table1"
KEY_ENVIRONMENTAL_COSTS_37  = "environmental_costs_37"

# New keys added for transport emission table
KEY_SHOW_TRANSPORT_EMISSION = "show_transport_emission"
KEY_TRANSPORT_EMISSION      = "transport_emission"

# Top-level section toggle keys
KEY_SHOW_TITLE_PAGE         = "show_title_page"
KEY_SHOW_INTRODUCTION       = "show_introduction"
KEY_SHOW_LCCA_RESULTS       = "show_lcca_results"

# Chart plot keys (filenames injected at report-generation time)
KEY_PLOT_PILLAR_DONUT          = "plot_pillar_donut"
KEY_PLOT_SUSTAINABILITY_MATRIX = "plot_sustainability_matrix"
KEY_PLOT_STAGE_BARS            = "plot_stage_bars"
KEY_PLOT_PILLAR_BARS           = "plot_pillar_bars"

# ─────────────────────────────────────────────────────────────────────────────
# Report structure- single source of truth for UI tree and generation
# ─────────────────────────────────────────────────────────────────────────────

SECTION_MAP = {
    "Title page": [],
    "Input data": [
        "Bridge geometry and description",
        "User note",
        "Construction data",
        "Traffic data",
        "Environmental input data",
    ],
    "LCCA results": [],
}

SUBSECTION_TABLE_MAP = {
    "Bridge geometry and description": [
        ("Table 2-1: Bridge description", KEY_SHOW_BRIDGE_DESC),
    ],
    "User note": [
        ("Table 2-2: Financial Data", KEY_SHOW_FINANCIAL),
    ],
    "Construction data": [
        ("Table 2-3: Construction materials", KEY_SHOW_CONSTRUCTION),
        ("Table 2-4: LCC assumptions", KEY_SHOW_LCC_ASSUMPTIONS),
        ("Table 2-5: Use stage details", KEY_SHOW_USE_STAGE),
    ],
    "Traffic data": [
        ("Table 2-6: Average daily traffic", KEY_SHOW_AVG_TRAFFIC),
        ("Table 2-7: Road and traffic data", KEY_SHOW_ROAD_TRAFFIC),
        ("Table 2-8: Peak hour distribution", KEY_SHOW_PEAK_HOUR),
        ("Table 2-9: Human injury cost", KEY_SHOW_HUMAN_INJURY),
        ("Table 2-10: Vehicle damage cost", KEY_SHOW_VEHICLE_DAMAGE),
        ("Table 2-11: Tyre cost data", KEY_SHOW_TYRE_COST),
        ("Table 2-12: Fuel, oil and grease", KEY_SHOW_FUEL_OIL),
        ("Table 2-13: Cost of new vehicle", KEY_SHOW_NEW_VEHICLE),
    ],
    "Environmental input data": [
        ("Table 2-14: Social cost of carbon", KEY_SHOW_SOCIAL_CARBON),
        ("Table 2-15: Material emission factors", KEY_SHOW_MATERIAL_EMISSION),
        ("Table 2-16: Use stage emissions", KEY_SHOW_USE_EMISSION),
        ("Table 2-17: Vehicle emission factors", KEY_SHOW_VEHICLE_EMISSION),
        ("Table 2-18: On-site emissions", KEY_SHOW_ONSITE_EMISSION),
        ("Table 2-19: Transport emissions", KEY_SHOW_TRANSPORT_EMISSION),
    ],
}
