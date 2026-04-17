
import os

from .base_report import LCCAReportBase
from .lcca_template import LCCATemplate
from .constants import KEY_SHOW_TITLE_PAGE, KEY_SHOW_INTRODUCTION, KEY_SHOW_LCCA_RESULTS
from .sections.title_page import add_title_page
from .sections.introduction import add_introduction
from .sections.input_data import add_input_data
from .sections.results import add_lcca_results
from .sections.appendix import add_full_appendix
from .plot_exporter import generate_plots

class LCCAReportLatex(LCCAReportBase):

    def save_latex(self, filename="LCCA_Report", output_dir=None):
        if not output_dir:
            output_dir = os.getcwd()
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, filename)
        self.generate_tex(path)
        return path + ".tex"

    def generate_pdf_output(self, filename="LCCA_Report", output_dir=None):
        if not output_dir:
            output_dir = os.getcwd()
        try:
            self.generate_pdf(
                os.path.join(output_dir, filename),
                compiler=self.LATEX_EXEC,
                clean_tex=False,
            )
            return os.path.join(output_dir, f"{filename}.pdf")
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None


def generate_report(output_filename="LCCA_Report", export_dict=None, config_override=None, output_dir=None):
    """Entry point for report generation."""
    if not export_dict:
        raise ValueError("export_dict is required")

    template = LCCATemplate(export_dict)
    config = template.get_config()
    if config_override:
        config.update(config_override)
    data = template.get_report_data()

    # Generate chart PNGs into the same directory as the .tex file so that
    # pdflatex can resolve them by filename alone (no path prefix needed).
    _results  = export_dict.get("results", {})
    _currency = export_dict.get("inputs", {}).get("general_info", {}).get("project_currency", "INR")
    _out_dir  = output_dir or os.getcwd()
    try:
        data.update(generate_plots(_results, _out_dir, _currency))
    except Exception as _e:
        print(f"[lcca_generate] chart generation failed: {_e}")

    doc = LCCAReportLatex()
    if config.get(KEY_SHOW_TITLE_PAGE, True):
        add_title_page(doc, config, data)
    if config.get(KEY_SHOW_INTRODUCTION, False):
        add_introduction(doc, config, data)
    add_input_data(doc, config, data)
    if config.get(KEY_SHOW_LCCA_RESULTS, True):
        add_lcca_results(doc, config, data)
    add_full_appendix(doc)

    doc.save_latex(filename=output_filename, output_dir=output_dir)
    return doc.generate_pdf_output(filename=output_filename, output_dir=output_dir)

