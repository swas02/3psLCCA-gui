import os
import base64
import tempfile
from pylatex import NoEscape
from pylatex.utils import escape_latex
from ..utils import LOGO_3PS_PATH  # now should point to PNG


def _decode_agency_logo(b64: str) -> str:
    """Decode base64 agency logo to a temp image file. Returns path or ''."""
    if not b64:
        return ""
    try:
        data = base64.b64decode(b64)

        # detect PNG vs JPG
        ext = ".png" if data.startswith(b"\x89PNG") else ".jpg"

        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        tmp.write(data)
        tmp.close()
        return tmp.name
    except Exception:
        return ""


def _esc(value: str) -> str:
    return escape_latex(str(value)) if value else ""


def add_title_page(doc, config, data):
    project_name   = _esc(data.get("project_name", ""))
    project_code   = _esc(data.get("project_code", ""))
    project_desc   = _esc(data.get("project_description", ""))
    agency_name    = _esc(data.get("agency_name", ""))
    contact_person = _esc(data.get("contact_person", ""))
    agency_addr    = _esc(data.get("agency_address", ""))
    agency_email   = _esc(data.get("agency_email", ""))
    agency_phone   = _esc(data.get("agency_phone", ""))
    reviewer_name  = _esc(data.get("reviewer_name", ""))
    reviewer_org   = _esc(data.get("reviewer_organization", ""))
    reviewer_addr  = _esc(data.get("reviewer_address", ""))
    reviewer_email = _esc(data.get("reviewer_email", ""))
    reviewer_phone = _esc(data.get("reviewer_phone", ""))

    # ✅ Use PNG directly (no conversion)
    app_logo_path = (LOGO_3PS_PATH or "").replace("\\", "/")
    agency_logo_path = _decode_agency_logo(
        data.get("agency_logo_b64", "")
    ).replace("\\", "/")

    app_logo_tex = (
        r"\includegraphics[height=1.6cm]{" + app_logo_path + r"}"
        if app_logo_path and os.path.exists(app_logo_path)
        else r"\textbf{3psLCCA}"
    )

    agency_logo_tex = (
        r"\includegraphics[height=2cm,keepaspectratio]{" + agency_logo_path + r"}"
        if agency_logo_path and os.path.exists(agency_logo_path)
        else r"\small Agency Logo"
    )

    doc.append(NoEscape(r"""
\begin{titlepage}
\vspace*{-\topskip}
% ── TOP BAND ────────────────────────────────────────────────────────────────
\begin{tikzpicture}[remember picture,overlay]
  \fill[blue!10]
    (current page.north west)
    rectangle ([yshift=-2cm]current page.north east);
\end{tikzpicture}

\vspace{0.6cm}

% ── LOGOS ───────────────────────────────────────────────────────────────────
\noindent
\begin{minipage}[c]{0.5\textwidth}
  \begin{minipage}[c][2.5cm][c]{4cm}
    \centering
""" + agency_logo_tex + r"""
  \end{minipage}
\end{minipage}%
\begin{minipage}[c]{0.5\textwidth}
  \raggedleft
""" + app_logo_tex + r"""
\end{minipage}

\vspace{0.6cm}
\noindent\rule{\textwidth}{0.5pt}
\vspace{1.2cm}

% ── TITLE ───────────────────────────────────────────────────────────────────
\centering
{\Large\bfseries Bridge Life Cycle Cost Analysis Report}

\vspace{1cm}

{\large\itshape Prepared using 3psLCCA}\\[0.2cm]
{\small \href{https://osdag.iitb.ac.in/3pslcca}{osdag.iitb.ac.in/3pslcca}}

\vspace{1.6cm}

% ── PROJECT INFO BOX ────────────────────────────────────────────────────────
\noindent
\begin{tikzpicture}
\node[draw=gray!40, fill=gray!5, rounded corners, inner sep=12pt,
      text width=\dimexpr\textwidth-2\pgflinewidth\relax] {%
  \textbf{\large Project Information}

  \vspace{3mm}

  \renewcommand{\arraystretch}{1.4}
  \begin{tabular}{p{5cm} p{9.5cm}}
""" + rf"""    \textbf{{Project Name:}}        & {project_name} \\
    \textbf{{Project Code:}}        & {project_code} \\
    \textbf{{Project Description:}} & {project_desc} \\""" + r"""
  \end{tabular}
};
\end{tikzpicture}

\vfill

% ── EVALUATED BY / REVIEWED BY ──────────────────────────────────────────────
\noindent
\begin{minipage}[t]{0.48\textwidth}
  \textbf{\large Evaluated By}

  \vspace{0.3cm}

  \renewcommand{\arraystretch}{1.3}
  \begin{tabular}{p{2.7cm} p{5.5cm}}
""" + rf"""    \textbf{{Name:}}         & {contact_person} \\
    \textbf{{Organization:}} & {agency_name} \\
    \textbf{{Address:}}      & {agency_addr} \\
    \textbf{{Email:}}        & {agency_email} \\
    \textbf{{Phone:}}        & {agency_phone} \\""" + r"""
  \end{tabular}

  \vspace{1.5cm}
  {\centering\rule{0.7\textwidth}{0.4pt}\\[-0.1cm]\small Signature\par}
\end{minipage}%
\hfill
\begin{minipage}[t]{0.48\textwidth}
  \textbf{\large Reviewed By}

  \vspace{0.3cm}

  \renewcommand{\arraystretch}{1.3}
  \begin{tabular}{p{3cm} p{5.5cm}}
""" + rf"""    \textbf{{Name:}}         & {reviewer_name} \\
    \textbf{{Organization:}} & {reviewer_org} \\
    \textbf{{Address:}}      & {reviewer_addr} \\
    \textbf{{Email:}}        & {reviewer_email} \\
    \textbf{{Phone:}}        & {reviewer_phone} \\""" + r"""
  \end{tabular}

  \vspace{1.5cm}
  {\centering\rule{0.7\textwidth}{0.4pt}\\[-0.1cm]\small Signature\par}
\end{minipage}

\vspace{1.2cm}

% ── FOOTER ──────────────────────────────────────────────────────────────────
{\raggedright\small\textcolor{gray}{%
Generated using 3psLCCA. The software is provided without any warranty,
express or implied.\\
The life cycle cost analysis (LCCA) results depend on user-provided inputs.
The evaluating agency is solely responsible for the accuracy of the input data
and for any use of the results.
}\par}

\end{titlepage}
"""))
