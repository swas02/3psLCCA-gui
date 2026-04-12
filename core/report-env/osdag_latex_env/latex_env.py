"""
OsdagLatexEnv — Self-contained LaTeX environment for Osdag.

This module discovers the LaTeX toolchain shipped inside the repository
(under core/report-env/assets/) so that Osdag can compile .tex reports
and generate PDFs **without** requiring an external TeX distribution
(MiKTeX, TinyTeX, TeX Live, etc.) to be installed by the user.

Discovery order
───────────────
1. Repo-local assets  (core/report-env/assets/<platform>/)
2. Conda-prefix path  (sys.prefix based — for conda-packaged builds)
3. System PATH         (fallback — shutil.which)
"""

import os
import shutil
import sys
import platform
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).resolve().parent
_REPORT_ENV_DIR = _THIS_DIR.parent
_ASSETS_DIR = _REPORT_ENV_DIR / "assets"


class OsdagLatexEnv:
    """
    Lightweight interface to the self-contained LaTeX toolchain.

    The class **discovers** (never installs) the LaTeX runtime and exposes:
      • Paths to executables (pdflatex, bibtex, …)
      • A property to check availability
      • The texmf root for environment-variable setup
      • A convenience method to compile a .tex file → .pdf

    Asset discovery priority:
      1. Repo-local  ``core/report-env/assets/<platform>/``
      2. Conda env   ``<sys.prefix>/[Library/]share/osdag_latex_env/``
      3. System PATH  (``shutil.which``)
    """

    def __init__(self) -> None:
        self.__system = platform.system().lower()
        self.__machine = platform.machine().lower()

        self.tex_root: Path | None = self._detect_tex_root()
        self.bin_dir: Path | None = self._detect_bin_dir()
        self.pdflatex: Path | None = self._get_executable("pdflatex")
        self.bibtex: Path | None = self._get_executable("bibtex")
        self.makeindex: Path | None = self._get_executable("makeindex")

        if self.tex_root:
            logger.info("TeX root  : %s", self.tex_root)
        if self.bin_dir:
            logger.info("TeX bindir: %s", self.bin_dir)
        if self.pdflatex:
            logger.info("pdflatex  : %s", self.pdflatex)

    @property
    def available(self) -> bool:
        """Return True if pdflatex is found and can execute ``--version``."""
        if not self.pdflatex:
            return False
        try:
            subprocess.run(
                [str(self.pdflatex), "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return True
        except Exception:
            return False

    @property
    def assets_present(self) -> bool:
        """Return True if the repo-local assets directory has content."""
        platform_dir = self._platform_asset_dir()
        return platform_dir is not None and platform_dir.exists()

    def configure_environment(self) -> None:
        """
        Set environment variables so that pdflatex can locate fonts,
        packages, and configuration from the repo-local texmf tree.

        Call this once before invoking ``compile_tex`` or running
        pdflatex manually.
        """
        if not self.tex_root or not self.bin_dir:
            logger.info("Using system LaTeX from PATH (no bundled TeX root found).")
            return

        texmf_dist = str(self.tex_root / "texmf-dist")

        os.environ["TEXMFHOME"] = texmf_dist
        os.environ["TEXMFVAR"] = str(self.tex_root / "texmf-var")
        os.environ["TEXMFCONFIG"] = str(self.tex_root / "texmf-config")

        # Prepend the binary directory to PATH
        current_path = os.environ.get("PATH", "")
        bin_str = str(self.bin_dir)
        if bin_str not in current_path:
            os.environ["PATH"] = bin_str + os.pathsep + current_path

        sty_base = (self.tex_root / "texmf-dist" / "tex" / "latex").as_posix()
        sep = ";" if self.__system == "windows" else ":"
        pkg_dirs = [f"{sty_base}//"]
        existing = os.environ.get("TEXINPUTS", "")
        os.environ["TEXINPUTS"] = sep.join(pkg_dirs) + sep + existing

        logger.info("LaTeX environment configured.")

    def compile_tex(
        self,
        tex_path: str | Path,
        output_dir: str | Path | None = None,
        *,
        runs: int = 2,
        quiet: bool = True,
    ) -> Path:
        """
        Compile a .tex file to PDF using pdflatex.

        Parameters
        ----------
        tex_path : str | Path
            Path to the .tex source file.
        output_dir : str | Path | None
            Directory for output files. Defaults to the same dir as tex_path.
        runs : int
            Number of pdflatex passes (default=2 for cross-references).
        quiet : bool
            Suppress pdflatex console output.

        Returns
        -------
        Path
            Path to the generated .pdf file.

        Raises
        ------
        FileNotFoundError
            If pdflatex is not available.
        subprocess.CalledProcessError
            If compilation fails.
        """
        if not self.pdflatex:
            raise FileNotFoundError(
                "pdflatex not found. Ensure the LaTeX assets are present in "
                "core/report-env/assets/ or install a TeX distribution."
            )

        self.configure_environment()

        tex_path = Path(tex_path).resolve()
        if output_dir is None:
            output_dir = tex_path.parent
        else:
            output_dir = Path(output_dir).resolve()
            output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.pdflatex),
            "-interaction=nonstopmode",
            f"-output-directory={output_dir}",
        ]
        # Some TeX distributions (including the packaged osdag_latex_env) do not
        # support the -quiet switch on pdflatex.
        if quiet and self.tex_root is None:
            cmd.append("-quiet")
        cmd.append(str(tex_path))

        for i in range(runs):
            logger.info("pdflatex pass %d/%d …", i + 1, runs)
            subprocess.run(cmd, check=True, cwd=str(tex_path.parent))

        pdf_name = tex_path.with_suffix(".pdf").name
        pdf_path = output_dir / pdf_name
        if not pdf_path.exists():
            raise FileNotFoundError(f"Expected PDF not found: {pdf_path}")

        logger.info("PDF generated: %s", pdf_path)
        return pdf_path

    def _platform_asset_dir(self) -> Path | None:
        """Return the expected repo-local asset directory for the current OS."""
        mapping = {
            "windows": "win",
            "linux": "linux",
            "darwin": "mac",
        }
        folder = mapping.get(self.__system)
        if not folder:
            return None
        d = _ASSETS_DIR / folder
        # macOS has an extra TinyTeX subdirectory
        if self.__system == "darwin":
            tt = d / "TinyTeX"
            if tt.exists():
                return tt
        return d if d.exists() else None

    def _detect_tex_root(self) -> Path | None:
        """
        Detect the root directory containing texmf trees.

        Search order:
          1. Repo-local assets/<platform>/
          2. Conda prefix  sys.prefix/[Library/]share/osdag_latex_env/
        """
        # 1. Repo-local
        plat = self._platform_asset_dir()
        if plat and (plat / "texmf-dist").exists():
            return plat

        # 2. Conda prefix
        prefix = Path(sys.prefix)
        if self.__system == "windows":
            conda_dir = prefix / "Library" / "share" / "osdag_latex_env"
        else:
            conda_dir = prefix / "share" / "osdag_latex_env"
        if conda_dir.exists() and (conda_dir / "texmf-dist").exists():
            return conda_dir

        return None

    def _detect_bin_dir(self) -> Path | None:
        """
        Detect the directory containing LaTeX executables.

        Search order:
          1. Repo-local assets/<platform>/bin/<arch>/
          2. Conda prefix
        """
        arch_map = {
            "windows": "x86_64-windows",
            "linux": "x86_64-linux",
            "darwin": "universal-darwin",
        }
        arch = arch_map.get(self.__system)
        if not arch:
            return None

        # 1. Repo-local
        plat = self._platform_asset_dir()
        if plat:
            d = plat / "bin" / arch
            if d.exists():
                return d

        # 2. Conda prefix
        prefix = Path(sys.prefix)
        if self.__system == "windows":
            d = prefix / "Library" / "share" / "osdag_latex_env" / "bin" / arch
        else:
            d = prefix / "share" / "osdag_latex_env" / "bin" / arch
        if d.exists():
            return d

        return None

    def _get_executable(self, name: str) -> Path | None:
        """
        Locate a TeX executable by name.

        Search order:
          1. bin_dir (repo-local or conda)
          2. System PATH
        """
        exe = f"{name}.exe" if self.__system == "windows" else name
        if self.bin_dir:
            p = self.bin_dir / exe
            if p.exists():
                return p
        # Fallback: system PATH
        found = shutil.which(name)
        return Path(found) if found else None
