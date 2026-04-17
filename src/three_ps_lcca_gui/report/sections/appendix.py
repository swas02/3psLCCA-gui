
from pylatex import NoEscape
from .appendix_A_content import APPENDIX_A_LATEX
from .appendix_B_content import APPENDIX_B_LATEX

def add_full_appendix(doc):
    """
    Add the massive Summary and Appendix sections from hardcoded LaTeX.
    """
    doc.append(NoEscape(APPENDIX_A_LATEX))
    doc.append(NoEscape(APPENDIX_B_LATEX))
