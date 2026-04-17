
from pylatex import Section, Subsection, Tabular, NoEscape
from pylatex.utils import bold, escape_latex
from ..constants import (
    KEY_SHOW_BRIDGE_DESC, KEY_BRIDGE_DESC,
    KEY_SHOW_FINANCIAL, KEY_FINANCIAL,
    KEY_SHOW_CONSTRUCTION, KEY_CONSTRUCTION,
    KEY_SHOW_LCC_ASSUMPTIONS, KEY_LCC_ASSUMPTIONS,
    KEY_SHOW_USE_STAGE, KEY_USE_STAGE,
    KEY_SHOW_AVG_TRAFFIC, KEY_AVG_TRAFFIC,
    KEY_SHOW_ROAD_TRAFFIC, KEY_ROAD_TRAFFIC,
    KEY_SHOW_PEAK_HOUR, KEY_PEAK_HOUR,
    KEY_SHOW_HUMAN_INJURY, KEY_HUMAN_INJURY,
    KEY_SHOW_VEHICLE_DAMAGE, KEY_VEHICLE_DAMAGE,
    KEY_SHOW_SOCIAL_CARBON, KEY_SOCIAL_CARBON,
    KEY_SHOW_MATERIAL_EMISSION, KEY_MATERIAL_EMISSION,
    KEY_SHOW_USE_EMISSION, KEY_USE_EMISSION,
    KEY_SHOW_VEHICLE_EMISSION, KEY_VEHICLE_EMISSION,
    KEY_SHOW_TRANSPORT_EMISSION, KEY_TRANSPORT_EMISSION,
    KEY_SHOW_ONSITE_EMISSION, KEY_ONSITE_EMISSION,
)

# ── Column specs using \colw{fraction} ───────────────────────────────────────
# All fractions within a spec sum to 1.0, so each table fills exactly \linewidth.

# 3-col: LCC assumptions (5.5 : 3.0 : 5.0 → 0.407 : 0.222 : 0.370)
_COL_LCC_ASSUMPTIONS = (
    r"|p{\colw{0.407}}|p{\colw{0.222}}|p{\colw{0.370}}|"
)

# 2-col: avg daily traffic (10 : 4.5 → 0.690 : 0.310)
_COL_AVG_TRAFFIC = r"|p{\colw{0.690}}|p{\colw{0.310}}|"

# 2-col: peak hour / human injury / vehicle damage (7 : 7.5 → 0.483 : 0.517)
_COL_HALF = r"|p{\colw{0.483}}|p{\colw{0.517}}|"

# 2-col: use/vehicle emission (9 : 5 → 0.643 : 0.357)
_COL_USE_EMISSION = r"|p{\colw{0.643}}|p{\colw{0.357}}|"

# 6-col: construction (2.0 : 4.0 : 1.6 : 1.2 : 2.2 : 2.4 → /13.4)
_COL_CONSTRUCTION = (
    r"|>{\raggedright\arraybackslash}p{\colw{0.149}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.299}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.119}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.090}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.164}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.179}}|"
)

# 7-col: material emission (2.2 : 3.2 : 1.3 : 1.0 : 1.8 : 1.8 : 2.0 → /13.3)
_COL_MATERIAL_EMISSION = (
    r"|p{\colw{0.165}}|p{\colw{0.241}}|p{\colw{0.098}}"
    r"|p{\colw{0.075}}|p{\colw{0.135}}|p{\colw{0.135}}|p{\colw{0.150}}|"
)

# 8-col: transport emission (2.0 : 2.0 : 1.3 : 1.5 : 1.5 : 1.5 : 1.5 : 2.1 → /13.4)
_COL_TRANSPORT = (
    r"|p{\colw{0.149}}|p{\colw{0.149}}|p{\colw{0.097}}"
    r"|p{\colw{0.112}}|p{\colw{0.112}}|p{\colw{0.112}}"
    r"|p{\colw{0.112}}|p{\colw{0.157}}|"
)

# 6-col: onsite emission (2.8 : 2.0 : 2.3 : 1.5 : 1.8 : 2.3 → /12.7)
_COL_ONSITE = (
    r"|p{\colw{0.220}}|p{\colw{0.157}}|p{\colw{0.181}}"
    r"|p{\colw{0.118}}|p{\colw{0.142}}|p{\colw{0.181}}|"
)


def add_input_data(doc, config, data):
    """Section 2: Input Data - all tables matching Word doc."""
    doc.append(NoEscape(r"\newpage"))
    with doc.create(Section("Input data")):
        doc.append(
            "This chapter provides general project information, including "
            "bridge configuration, analysis period, financial data and other "
            "inputs required for conducting life cycle cost assessment."
        )

        # ── 2.1 Bridge geometry ──────────────────────────────────────────
        with doc.create(Subsection("Bridge geometry and description")):
            doc.append(
                "Details of bridge type, span length, number of spans, "
                "and functional classification."
            )
            if config.get(KEY_SHOW_BRIDGE_DESC, True):
                doc.add_kv_table(
                    "Bridge description",
                    data.get(KEY_BRIDGE_DESC, {}),
                    key_frac=0.62,
                )

        # ── 2.2 User note ────────────────────────────────────────────────
        with doc.create(Subsection("User note")):
            if config.get(KEY_SHOW_FINANCIAL, True):
                doc.add_kv_table(
                    "Financial Data",
                    data.get(KEY_FINANCIAL, {}),
                )

        # ── 2.3 Construction data ────────────────────────────────────────
        with doc.create(Subsection("Construction data")):
            doc.append("Material quantities and unit rates.")

            if config.get(KEY_SHOW_CONSTRUCTION, True):
                construction = data.get(KEY_CONSTRUCTION, {})
                cat_table_captions = {
                    "Foundation":     "Construction material quantities and rates for foundation",
                    "Sub Structure":  "Construction material quantities and rates for substructure",
                    "Super Structure":"Construction material quantities and rates for superstructure",
                    "Miscellaneous":  "Construction material quantities and rates for miscellaneous activities",
                }
                header_row = (
                    r"\textbf{Category} & \textbf{Material}"
                    r" & \textbf{Rate} & \textbf{Quantity}"
                    r" & \textbf{Unit} & \textbf{Source} \\"
                )

                for cat_name, components in construction.items():
                    caption = cat_table_captions.get(
                        cat_name,
                        f"Construction material quantities and rates for {cat_name.lower()}"
                    )
                    doc.append(NoEscape(r"\vspace{4pt}"))
                    doc.append(NoEscape(r"\needspace{8\baselineskip}"))

                    rows_tex = ""
                    for comp_name, mat_rows in components.items():
                        row_count = len(mat_rows)
                        for idx, row_vals in enumerate(mat_rows):
                            mat         = row_vals[0]
                            qty         = row_vals[1]
                            unit        = row_vals[2]
                            rate        = row_vals[3]
                            source      = row_vals[4]
                            db_modified = row_vals[5] if len(row_vals) > 5 else False

                            if idx == 0:
                                cat_cell = (
                                    r"\multirow{" + str(row_count) + r"}{*}"
                                    r"{\parbox[t]{\colw{0.149}}{\raggedright\footnotesize\textbf{"
                                    + escape_latex(comp_name) + r"}}}"
                                )
                            else:
                                cat_cell = ""

                            source_cell = (
                                r"\cellcolor[HTML]{90EE90}" + escape_latex(source)
                                if db_modified else escape_latex(source)
                            )

                            cells = [
                                cat_cell,
                                escape_latex(mat),
                                escape_latex(str(rate)),
                                escape_latex(str(qty)),
                                escape_latex(unit),
                                source_cell,
                            ]
                            rows_tex += " & ".join(cells) + r" \\" + "\n"

                            if idx < row_count - 1:
                                rows_tex += r"\cline{2-6}" + "\n"
                            else:
                                rows_tex += r"\hline" + "\n"

                    caption_tex = r"\caption{" + escape_latex(caption) + r"}\\" + "\n"
                    longtable_tex = (
                        r"{\footnotesize" + "\n"
                        + r"\begin{longtable}{" + _COL_CONSTRUCTION + r"}" + "\n"
                        + caption_tex
                        + r"\hline" + "\n"
                        + header_row + "\n"
                        + r"\hline" + "\n"
                        + r"\endfirsthead" + "\n"
                        + r"\hline" + "\n"
                        + header_row + "\n"
                        + r"\hline" + "\n"
                        + r"\endhead" + "\n"
                        + r"\endfoot" + "\n"
                        + r"\hline" + "\n"
                        + r"\endlastfoot" + "\n"
                        + rows_tex
                        + r"\end{longtable}" + "\n"
                        + r"}"
                    )
                    doc.append(NoEscape(longtable_tex))
                    doc.append(NoEscape(r"\vspace{4pt}"))

            if config.get(KEY_SHOW_LCC_ASSUMPTIONS, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{8\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Assumptions for different "
                    r"life cycle cost components}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                with doc.create(Tabular(NoEscape(_COL_LCC_ASSUMPTIONS))) as t:
                    t.add_hline()
                    t.add_row(["", bold("Assumed percentage"), ""])
                    t.add_hline()
                    for key, vals in data.get(KEY_LCC_ASSUMPTIONS, {}).items():
                        t.add_row([escape_latex(key),
                                   escape_latex(str(vals[0])),
                                   escape_latex(str(vals[1]))])
                        t.add_hline()
                doc.append(NoEscape(r"\vspace{4pt}"))

            if config.get(KEY_SHOW_USE_STAGE, True):
                doc.add_kv_table(
                    "Details related to duration and interval of use stage activities",
                    data.get(KEY_USE_STAGE, {}),
                    key_frac=0.69,
                )

        # ── 2.4 Traffic data ─────────────────────────────────────────────
        with doc.create(Subsection("Traffic data")):
            doc.append(
                "Average daily traffic by vehicle class, rerouting distance, "
                "construction duration, vehicle operating cost and value of "
                "time parameters."
            )

            if config.get(KEY_SHOW_AVG_TRAFFIC, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{12\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Average Daily Traffic for each vehicle}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                with doc.create(Tabular(NoEscape(_COL_AVG_TRAFFIC))) as t:
                    t.add_hline()
                    t.add_row([bold("Vehicle type"), bold("Vehicles/day")])
                    t.add_hline()
                    for key, val in data.get(KEY_AVG_TRAFFIC, {}).items():
                        t.add_row([escape_latex(key), escape_latex(str(val))])
                        t.add_hline()
                doc.append(NoEscape(r"\vspace{4pt}"))

            if config.get(KEY_SHOW_ROAD_TRAFFIC, True):
                doc.add_kv_table(
                    "Road and traffic related data",
                    data.get(KEY_ROAD_TRAFFIC, {}),
                    key_frac=0.62,
                )

            if config.get(KEY_SHOW_PEAK_HOUR, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{8\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Peak hour distribution}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                with doc.create(Tabular(NoEscape(_COL_HALF))) as t:
                    t.add_hline()
                    t.add_row([bold("Hour Category"), bold("Traffic proportion")])
                    t.add_hline()
                    for key, val in data.get(KEY_PEAK_HOUR, {}).items():
                        t.add_row([escape_latex(key), escape_latex(str(val))])
                        t.add_hline()
                doc.append(NoEscape(r"\vspace{4pt}"))

            if config.get(KEY_SHOW_HUMAN_INJURY, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{8\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Human injury cost data}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                with doc.create(Tabular(NoEscape(_COL_HALF))) as t:
                    t.add_hline()
                    t.add_row([
                        bold("Category of accident"),
                        NoEscape(r"\textbf{Accident distribution (\%)}"),
                    ])
                    t.add_hline()
                    for key, val in data.get(KEY_HUMAN_INJURY, {}).items():
                        t.add_row([escape_latex(key), escape_latex(str(val))])
                        t.add_hline()
                doc.append(NoEscape(r"\vspace{4pt}"))

            if config.get(KEY_SHOW_VEHICLE_DAMAGE, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{12\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Vehicle damage cost data}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                with doc.create(Tabular(NoEscape(_COL_HALF))) as t:
                    t.add_hline()
                    t.add_row([
                        bold("Vehicle type"),
                        NoEscape(r"\textbf{Percentage of accidents for each vehicle type}"),
                    ])
                    t.add_hline()
                    for key, val in data.get(KEY_VEHICLE_DAMAGE, {}).items():
                        t.add_row([escape_latex(key), escape_latex(str(val))])
                        t.add_hline()
                doc.append(NoEscape(r"\vspace{4pt}"))

        # ── 2.5 Environmental input data ─────────────────────────────────
        with doc.create(Subsection("Environmental input data")):
            doc.append(
                "Emission factors for construction and traffic activities "
                "and carbon pricing assumptions."
            )

            if config.get(KEY_SHOW_SOCIAL_CARBON, True):
                doc.add_kv_table(
                    "Social Cost of Carbon",
                    data.get(KEY_SOCIAL_CARBON, {}),
                    key_frac=0.62,
                )

            if config.get(KEY_SHOW_MATERIAL_EMISSION, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{8\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Material related factors for emission}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"{\footnotesize"))
                with doc.create(Tabular(NoEscape(_COL_MATERIAL_EMISSION))) as t:
                    t.add_hline()
                    t.add_row([
                        bold("Category"),
                        bold("Material"),
                        bold("Quantity"),
                        bold("Unit"),
                        bold("Conversion factor"),
                        bold("Emission factor"),
                        NoEscape(r"\textbf{Emission factor unit}"),
                    ])
                    t.add_hline()
                    for mat, vals in data.get(KEY_MATERIAL_EMISSION, {}).items():
                        category = escape_latex(str(vals[0])) if len(vals) > 0 else ""
                        row = [category, escape_latex(mat)] + [escape_latex(str(v)) for v in vals[1:]]
                        t.add_row(row)
                        t.add_hline()
                doc.append(NoEscape(r"}"))
                doc.append(NoEscape(r"\vspace{4pt}"))

            if config.get(KEY_SHOW_USE_EMISSION, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{8\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Assumptions for use stage "
                    r"and end of life emissions}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                with doc.create(Tabular(NoEscape(_COL_USE_EMISSION))) as t:
                    t.add_hline()
                    t.add_row(["", bold("Assumed \\% of initial emission")])
                    t.add_hline()
                    for key, val in data.get(KEY_USE_EMISSION, {}).items():
                        t.add_row([escape_latex(key), escape_latex(str(val))])
                        t.add_hline()
                doc.append(NoEscape(r"\vspace{4pt}"))

            if config.get(KEY_SHOW_VEHICLE_EMISSION, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{12\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Vehicle related emission factors}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                with doc.create(Tabular(NoEscape(_COL_USE_EMISSION))) as t:
                    t.add_hline()
                    t.add_row([bold("Vehicle type"), bold("Emission factor")])
                    t.add_hline()
                    for key, val in data.get(KEY_VEHICLE_EMISSION, {}).items():
                        t.add_row([escape_latex(key), escape_latex(str(val))])
                        t.add_hline()
                doc.append(NoEscape(r"\vspace{4pt}"))

            if config.get(KEY_SHOW_TRANSPORT_EMISSION, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{8\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Data for emissions related to "
                    r"transportation of material}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"{\footnotesize"))
                with doc.create(Tabular(NoEscape(_COL_TRANSPORT))) as t:
                    t.add_hline()
                    t.add_row([
                        bold("Transport Material"),
                        bold("Vehicle name"),
                        NoEscape(r"\textbf{GVW (tonne)}"),
                        NoEscape(r"\textbf{Cargo capacity (tonne)}"),
                        NoEscape(r"\textbf{Distance travelled (km)}"),
                        bold("Source"),
                        bold("Destination"),
                        NoEscape(r"\textbf{Emission Factor (kgCO\textsubscript{2}e/tonne-km)}"),
                    ])
                    t.add_hline()
                    for mat, vals in data.get(KEY_TRANSPORT_EMISSION, {}).items():
                        t.add_row([escape_latex(mat)] +
                                  [escape_latex(str(v)) for v in vals])
                        t.add_hline()
                doc.append(NoEscape(r"}"))
                doc.append(NoEscape(r"\vspace{4pt}"))

            if config.get(KEY_SHOW_ONSITE_EMISSION, True):
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{8\baselineskip}"))
                doc.append(NoEscape(
                    r"\noindent\captionof{table}{Emissions from on-site "
                    r"activities during construction}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"{\footnotesize"))
                with doc.create(Tabular(NoEscape(_COL_ONSITE))) as t:
                    t.add_hline()
                    t.add_row([
                        bold("Construction Equipment"),
                        bold("Energy Source"),
                        NoEscape(r"\textbf{Diesel consumption (l/hour) or Electricity (Kw)}"),
                        NoEscape(r"\textbf{Avg number of hours used per day}"),
                        NoEscape(r"\textbf{Number of days the equipment would be used}"),
                        NoEscape(r"\textbf{Emission factor (kgCO\textsubscript{2}e/unit)}"),
                    ])
                    t.add_hline()
                    for equip, vals in data.get(KEY_ONSITE_EMISSION, {}).items():
                        row_vals = list(vals)[:5]
                        t.add_row([escape_latex(equip)] +
                                  [escape_latex(str(v)) for v in row_vals])
                        t.add_hline()
                doc.append(NoEscape(r"}"))
                doc.append(NoEscape(r"\vspace{4pt}"))
