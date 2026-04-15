# lifecycle_summary.py

sample_input = {
    "initial_stage": {
        "economic": {
            "initial_construction_cost": 13510517.107590165,
            "time_cost_of_loan": 226864.09976495153,
        },
        "environmental": {
            "initial_material_carbon_emission_cost": 362252.33909257106,
            "initial_vehicular_emission_cost": 7687.78,
        },
        "social": {"initial_road_user_cost": 133646.6},
    },
    "use_stage": {
        "economic": {
            "routine_inspection_costs": 691806.0284941545,
            "periodic_maintenance": 769450.9703114751,
            "major_inspection_costs": 641209.1419262293,
            "major_repair_cost": 557984.3565434739,
            "replacement_costs_for_bearing_and_expansion_joint": 1391899.311934074,
        },
        "environmental": {
            "periodic_carbon_costs": 18911.74561466677,
            "major_repair_material_carbon_emission_costs": 822.8561882487752,
            "major_repair_vehicular_emission_costs": 1831.76,
            "vehicular_emission_costs_for_replacement_of_bearing_and_expansion_joint": 115.02,
        },
        "social": {
            "major_repair_road_user_costs": 31843.87,
            "road_user_costs_for_replacement_of_bearing_and_expansion_joint": 1999.56,
        },
    },
    "reconstruction": {
        "economic": {
            "total_demolition_and_disposal_costs": 447198.11626123457,
            "cost_of_reconstruction_after_demolition": 4471981.162612345,
            "total_scrap_value": 0.0,
            "time_cost_of_loan": 75092.01702219897,
        },
        "environmental": {
            "carbon_costs_demolition_and_disposal": 11990.552423964102,
            "carbon_cost_of_reconstruction_after_demolition": 119905.52423964103,
            "demolition_vehicular_emission_cost": 489.36,
            "reconstruction_vehicular_emission_cost": 2544.66,
        },
        "social": {"ruc_demolition": 8507.12, "ruc_reconstruction": 44237.03},
    },
    "end_of_life": {
        "economic": {
            "total_demolition_and_disposal_costs": 312092.94518533285,
            "total_scrap_value": 0.0,
        },
        "environmental": {
            "carbon_costs_demolition_and_disposal": 8368.029033038392,
            "demolition_vehicular_emission_cost": 341.51,
        },
        "social": {"ruc_demolition": 5936.99},
    },
    "warnings": [],
    "notes": [],
}


def _sum_dict(d):
    """Sum all numeric values in a dict. Returns 0 if input is not a dict.

    Used to collapse a pillar's line-item costs (e.g. all economic line items)
    into a single total for that pillar within a stage.
    """
    return sum(d.values()) if isinstance(d, dict) else 0


def _stage_totals(stage_data):
    """Given one stage's data dict, return its three pillar sub-totals.

    Expects stage_data to contain any of the keys:
        "economic", "environmental", "social"
    Each key maps to a flat dict of {cost_label: value}.

    Returns:
        {"eco": float, "env": float, "social": float}
    """
    return {
        "eco": _sum_dict(stage_data.get("economic", {})),
        "env": _sum_dict(stage_data.get("environmental", {})),
        "social": _sum_dict(stage_data.get("social", {})),
    }


def compute_all_summaries(data):
    """Compute four summary views from a full LCCA result dict.

    The input `data` is expected to contain stage keys:
        "initial_stage", "use_stage", "reconstruction", "end_of_life"
    plus optional non-stage keys ("warnings", "notes") which are ignored.

    NOTE: "use_stage" and "reconstruction" are merged into a single
    "use_reconstruction" group in all outputs, matching the reporting format.

    Returns a dict with four keys:

    1) "stagewise"  — total LCCA cost per reporting stage (eco + env + social)
            {
                "initial":          float,   # initial_stage total
                "use_reconstruction": float, # use_stage + reconstruction total
                "end_of_life":      float,   # end_of_life total
            }

    2) "pillar_wise" — per-stage breakdown by pillar
            {
                "initial":            {"eco": float, "env": float, "social": float},
                "use_reconstruction": {"eco": float, "env": float, "social": float},
                "end_of_life":        {"eco": float, "env": float, "social": float},
            }

    3) "pillar_totals" — lifetime total for each pillar across ALL stages
            {"eco": float, "env": float, "social": float}

    4) "environmental_split" — env costs only, by reporting stage
            {
                "initial":            float,
                "use_reconstruction": float,
                "end_of_life":        float,
            }
    """

    # ---- Step 1: Compute per-stage pillar totals ----
    stages = {}
    for k, v in data.items():
        if isinstance(v, dict):
            stages[k] = _stage_totals(v)

    # helper: sum all three pillars for a single raw stage key
    def total_of(stage):
        s = stages.get(stage, {})
        return s.get("eco", 0) + s.get("env", 0) + s.get("social", 0)

    # ---- 1) Stagewise (correct & explicit) ----
    stagewise = {
        "initial": total_of("initial_stage"),
        "use_reconstruction": total_of("use_stage") + total_of("reconstruction"),
        "end_of_life": total_of("end_of_life"),
    }

    # ---- 2) Pillar-wise ----
    pillar_wise = {
        "initial": stages.get("initial_stage", {"eco": 0, "env": 0, "social": 0}),
        "use_reconstruction": {
            "eco": stages.get("use_stage", {}).get("eco", 0)
            + stages.get("reconstruction", {}).get("eco", 0),
            "env": stages.get("use_stage", {}).get("env", 0)
            + stages.get("reconstruction", {}).get("env", 0),
            "social": stages.get("use_stage", {}).get("social", 0)
            + stages.get("reconstruction", {}).get("social", 0),
        },
        "end_of_life": stages.get("end_of_life", {"eco": 0, "env": 0, "social": 0}),
    }

    # ---- 3) Pillar totals ----
    pillar_totals = {"eco": 0, "env": 0, "social": 0}
    for s in stages.values():
        for k in pillar_totals:
            pillar_totals[k] += s.get(k, 0)

    # ---- 4) Environmental split ----
    env_split = {
        "initial": stages.get("initial_stage", {}).get("env", 0),
        "use_reconstruction": (
            stages.get("use_stage", {}).get("env", 0)
            + stages.get("reconstruction", {}).get("env", 0)
        ),
        "end_of_life": stages.get("end_of_life", {}).get("env", 0),
    }

    return {
        "stagewise": stagewise,
        "pillar_wise": pillar_wise,
        "pillar_totals": pillar_totals,
        "environmental_split": env_split,
    }



print(compute_all_summaries(sample_input))