"""
setup_assets.py — Populate core/report-env/assets/ with the LaTeX toolchain.

This script copies the platform-specific TeX binaries and texmf trees from
the osdag-latex-env/ source directory into core/report-env/assets/ so that
the integrated OsdagLatexEnv module can discover them at runtime.

Usage
─────
    python core/report-env/setup_assets.py [--platform win|linux|mac|all] [--source PATH]

If ``--source`` is omitted it defaults to ``<repo>/osdag-latex-env/assets/``.
If ``--platform`` is omitted it auto-detects the current OS (or use ``all``
to copy every platform).
"""

import argparse
import platform
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_SOURCE = REPO_ROOT / "osdag-latex-env" / "assets"
TARGET_DIR = SCRIPT_DIR / "assets"

PLATFORM_MAP = {
    "windows": "win",
    "linux":   "linux",
    "darwin":  "mac",
}


def current_platform_key() -> str:
    """Return the platform folder name for the current OS."""
    return PLATFORM_MAP.get(platform.system().lower(), "")


def copy_platform(source: Path, platform_key: str) -> None:
    """Copy a single platform's assets into the target directory."""
    src = source / platform_key
    if not src.exists():
        print(f"  [WARN] Source not found, skipping: {src}")
        return

    dst = TARGET_DIR / platform_key
    if dst.exists():
        print(f"  [OK] Already present: {dst}")
        return

    print(f"  [..] Copying {platform_key} assets...")
    print(f"     {src}  →  {dst}")
    shutil.copytree(src, dst)
    print(f"  [OK] Done ({platform_key})")


def check_status() -> None:
    """Print a summary of which platform assets are present."""
    print("\n-- Asset status --------------------------------------")
    for plat_key in ("win", "linux", "mac"):
        d = TARGET_DIR / plat_key
        if d.exists():
            # Quick check for texmf-dist
            texmf = d / "texmf-dist"
            if not texmf.exists():
                # macOS nesting
                texmf = d / "TinyTeX" / "texmf-dist"
            status = "[OK] texmf-dist found" if texmf.exists() else "[WARN] texmf-dist missing"
            print(f"  [{plat_key:>5}]  {status}  — {d}")
        else:
            print(f"  [{plat_key:>5}]  [NO] not present")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set up LaTeX assets for Osdag's self-contained TeX environment.",
    )
    parser.add_argument(
        "--platform",
        choices=["win", "linux", "mac", "all", "auto"],
        default="auto",
        help="Which platform assets to install (default: auto-detect).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Source directory of platform assets (default: {DEFAULT_SOURCE}).",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Only print current asset status, don't copy anything.",
    )
    args = parser.parse_args()

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    if args.status:
        check_status()
        return

    if not args.source.exists():
        print(f"[ERROR] Source asset directory not found: {args.source}")
        print("   Make sure osdag-latex-env/ is present at the repo root,")
        print("   or pass --source /path/to/assets explicitly.")
        sys.exit(1)

    # Determine which platforms to copy
    if args.platform == "all":
        targets = ["win", "linux", "mac"]
    elif args.platform == "auto":
        key = current_platform_key()
        if not key:
            print(f"[ERROR] Unsupported platform: {platform.system()}")
            sys.exit(1)
        targets = [key]
    else:
        targets = [args.platform]

    print(f"Source : {args.source}")
    print(f"Target : {TARGET_DIR}")
    print(f"Platforms: {', '.join(targets)}\n")

    for key in targets:
        copy_platform(args.source, key)

    check_status()
    print("[OK] Setup complete. OsdagLatexEnv can now discover these assets.")


if __name__ == "__main__":
    main()
