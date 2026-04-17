
import os
from pylatex import Section, Figure, NoEscape
from ..constants import KEY_FRAMEWORK_FIGURE

def add_introduction(doc, config, data):
    """
    Add Section 1: Introduction to LCCA with framework figure.
    """
    with doc.create(Section("Introduction to LCCA")):
        doc.append(
            NoEscape(
                r"The life cycle cost is calculated using the 3PS-LCC approach, "
                r"as illustrated in the figure below. Additional details about each "
                r"component of this framework can be found at the following link. "
                r"The components of the life-cycle cost analysis (LCCA) are also shown "
                r"in the figure below. The assumptions adopted in the life-cycle cost "
                r"calculations under this framework are listed in Appendix~A."
            )
        )

        # Figure 1-1
        fig_path = data.get(KEY_FRAMEWORK_FIGURE, "").replace("\\", "/")
        if os.path.exists(fig_path):
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Figure(position="H")) as fig:
                fig.add_image(fig_path, width=NoEscape(r"\textwidth"))
                fig.add_caption("3PS Life Cycle cost assessment")
