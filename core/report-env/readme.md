# Report Environment — Osdag LaTeX

This directory provides the python execution context for **Osdag's LaTeX environment**. It allows Osdag to compile `.tex` reports and generate PDFs via a standalone TeX toolchain instead of relying on external system-wide installations like MiKTeX or TeX Live.

## Installation

The actual TeX binaries (~1.3 GB) are **not tracked in git**. By default, users get the pre-built LaTeX package via Conda:

```bash
conda install osdag::osdag_latex_env
```

This installs the TeX binary assets into the Conda environment (under `sys.prefix/share/osdag_latex_env` or `sys.prefix/Library/share/osdag_latex_env`). 

### For Core Developers

If you are developing or testing without the Conda package, you can populate the assets locally from the root submodule directory. Run this from the repo root:

```bash
# Auto-detect your platform (copies only the relevant assets):
python core/report-env/setup_assets.py

# Or copy all platforms:
python core/report-env/setup_assets.py --platform all
```

*Note: The script copies assets from `osdag-latex-env/assets/` into `core/report-env/assets/`. The local `assets/` directory is `.gitignore`d.*

## Using the API

The `OsdagLatexEnv` Python wrapper bridges your Python code and the binaries:

```python
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
report_env_dir = project_root / "core" / "report-env"
sys.path.insert(0, str(report_env_dir))

from osdag_latex_env import OsdagLatexEnv

env = OsdagLatexEnv()

# Check if the environment is properly installed and available
if env.available:
    # Compile a .tex file to PDF
    pdf_path = env.compile_tex("path/to/report.tex")
    print(f"PDF generated: {pdf_path}")
else:
    print("LaTeX environment not found. (Use `conda install osdag::osdag_latex_env`)")
```

### Manual Execution

```python
env = OsdagLatexEnv()
env.configure_environment()   # Sets PATH, TEXMFHOME, TEXINPUTS, etc.

# Now use env.pdflatex directly via subprocess
import subprocess
subprocess.run([str(env.pdflatex), "-interaction=nonstopmode", "report.tex"])
```

## How It Works (Asset Discovery Strategy)

The `OsdagLatexEnv` class discovers the LaTeX toolchain dynamically with the following priority tier:

1. **Repo-local** — `core/report-env/assets/<platform>/` (mostly used by devs who run `setup_assets.py`)
2. **Conda prefix** — `<sys.prefix>/[Library/]share/osdag_latex_env/` (the standard method for production users)
3. **System PATH** — Fallback to any pre-existing distribution using `shutil.which("pdflatex")`

## Directory Structure

```
core/report-env/
├── osdag_latex_env/          # Python API wrapper (this repo)
│   ├── __init__.py
│   ├── __config__.py         
│   └── latex_env.py          # Discovers assets, exposes 'compile_tex()'
├── setup_assets.py           # Developer convenience script
├── .gitignore                # Explicitly ignores local assets/
└── readme.md                 # This file
```

*(You will see the original `osdag-latex-env/` external repository mounted at the repo's root via git submodule).*
