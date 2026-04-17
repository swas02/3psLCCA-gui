
from pylatex import Section, Subsection, Subsubsection, NoEscape
from pylatex.utils import escape_latex
from ..constants import (
    KEY_LCC_TABLE1,
    KEY_STAGE_COSTS,
    KEY_PILLAR_COSTS,
    KEY_ECONOMIC_COSTS,
    KEY_SOCIAL_COSTS,
    KEY_RUC_CONSTRUCTION,
    KEY_ENVIRONMENTAL_COSTS_37,
    KEY_PLOT_PILLAR_DONUT,
    KEY_PLOT_SUSTAINABILITY_MATRIX,
    KEY_PLOT_STAGE_BARS,
    KEY_PLOT_PILLAR_BARS,
)

def add_lcca_results(doc, config, data):
    """Section 3: LCCA Results - Tables 3-1 through 3-7."""
    doc.append(NoEscape(r"\newpage"))
    with doc.create(Section("LCCA results")):
        doc.append(
            "This chapter presents software-generated numerical results "
            "in tabular and graphical formats."
        )

        # ── 3.1 Life cycle cost results ──────────────────────────────────
        with doc.create(Subsection("Life cycle cost results")):
            doc.append(NoEscape(
                r"The total life cycle cost of the bridge is "
                r"\underline{\hspace{4cm}}. "
                r"The contribution of different life cycle cost components "
                r"is provided in the \textit{Table 3-1} below."
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{8\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Contribution of different "
                r"life cycle cost components}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            
            lcc = data.get(KEY_LCC_TABLE1, {})
            # 8-col: 1.6 : 4.5 : 2.3 : 1.0 : 1.2 : 1.2 : 1.1 : 1.1  (total 14.0)
            col_spec = (
                r"|>{\raggedright\arraybackslash}p{\colw{0.114}}"
                r"|>{\raggedright\arraybackslash}p{\colw{0.321}}"
                r"|>{\raggedright\arraybackslash}p{\colw{0.164}}"
                r"|>{\raggedright\arraybackslash}p{\colw{0.071}}"
                r"|>{\raggedright\arraybackslash}p{\colw{0.086}}"
                r"|>{\raggedright\arraybackslash}p{\colw{0.086}}"
                r"|>{\raggedright\arraybackslash}p{\colw{0.079}}"
                r"|>{\raggedright\arraybackslash}p{\colw{0.079}}|"
            )
            header_row = (
                r" & \textbf{Costs} & \textbf{Cost in Present time}"
                r" & \textbf{in cr} & \textbf{in lakhs} & \textbf{in Millions}"
                r" & \textbf{\% of initial cost} & \textbf{\% LCC} \\"
            )
    
            rows_tex = ""
            for stage_label, stage_rows in lcc.items():
                first = True
                row_count = len(stage_rows)
                cost_items = list(stage_rows.items())

                for idx, (cost_label, vals) in enumerate(cost_items):
                    if first:
                        stage_cell = (
r"\multirow{" + str(row_count) + r"}{*}"
r"{\parbox[t]{1.5cm}{\raggedright\footnotesize\textbf{\hspace{0pt}" + escape_latex(stage_label) + r"}}}"
)
                        first = False
                    else:
                        stage_cell = ""

                    cells = [stage_cell, r"\textbf{" + escape_latex(cost_label) + r"}"]
                    cells += [escape_latex(str(v)) for v in vals]
                    rows_tex += " & ".join(cells) + r" \\" + "\n"

                    if idx < row_count - 1:
                        rows_tex += r"\cline{2-8}" + "\n"
                    else:
                        rows_tex += r"\hline" + "\n"

            longtable_tex = (
                r"{\footnotesize" + "\n"
                + r"\begin{longtable}{" + col_spec + r"}" + "\n"
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

        # ── 3.2 Stage-wise distribution ──────────────────────────────────
        with doc.create(Subsection("Stage-wise distribution of life cycle costs")):
            doc.add_kv_table(
                "Life cycle stage wise costs",
                data.get(KEY_STAGE_COSTS, {}),
            )

        # ── 3.3 Pillar-wise distribution ─────────────────────────────────
        with doc.create(Subsection("Pillar-wise distribution of life cycle costs")):
            doc.add_kv_table(
                "Sustainability pillar wise cost",
                data.get(KEY_PILLAR_COSTS, {}),
            )

            # ── 3.3.1 Economic costs ──────────────────────────────────────
            with doc.create(Subsubsection("Economic costs")):
                doc.append(
                    "Different components of economic pillar of sustainability"
                )
                doc.add_kv_table(
                    "Economic cost results across different stages",
                    data.get(KEY_ECONOMIC_COSTS, {}),
                    key_frac=0.62,
                )

            # ── 3.3.2 Social costs ────────────────────────────────────────
            with doc.create(Subsubsection("Social costs")):
                doc.append(
                    "Road user cost during different life cycle stages"
                )
                doc.add_kv_table(
                    "Social cost across different stages",
                    data.get(KEY_SOCIAL_COSTS, {}),
                    key_frac=0.62,
                )
                doc.add_kv_table(
                    "Road user costs during construction",
                    data.get(KEY_RUC_CONSTRUCTION, {}),
                )

            # ── 3.3.3 Environmental costs ─────────────────────────────────
            with doc.create(Subsubsection("Environmental costs")):
                doc.append(
                    "Environmental cost contribution across the bridge life cycle."
                )
                doc.add_kv_table(
                    "Environmental costs across different stages",
                    data.get(KEY_ENVIRONMENTAL_COSTS_37, {}),
                    key_frac=0.69,
                )

        # ── 3.4 Charts ────────────────────────────────────────────────────────
        _charts = [
            (KEY_PLOT_PILLAR_DONUT,
             "Pillar distribution- Economic : Environmental : Social"),
            (KEY_PLOT_SUSTAINABILITY_MATRIX,
             "Sustainability Matrix- stage and pillar decomposition"),
            (KEY_PLOT_STAGE_BARS,
             "Lifecycle disaggregation- stage-wise cost bars"),
            (KEY_PLOT_PILLAR_BARS,
             "Lifecycle disaggregation- pillar-wise stacked bars"),
        ]
        _available = [(k, cap) for k, cap in _charts if data.get(k)]
        if _available:
            with doc.create(Subsection("Life cycle cost distribution- charts")):
                doc.append(
                    "The following charts visualise the distribution of life cycle "
                    "costs across stages and sustainability pillars."
                )
                for key, caption in _available:
                    fname = data[key].replace("\\", "/")
                    doc.append(NoEscape(r"\vspace{8pt}"))
                    doc.append(NoEscape(
                        r"\begin{figure}[H]"
                        r"\centering"
                        r"\includegraphics[width=0.88\textwidth]{" + fname + r"}"
                        r"\captionof{figure}{" + escape_latex(caption) + r"}"
                        r"\end{figure}"
                    ))
