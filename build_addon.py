# SPDX-FileCopyrightText: 2026 Frank Winter <https://www.frankwinter.com/>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of Low Poly Colorizer (LPC). <https://github.com/wasdcat/low-poly-colorizer>
# A WASDCAT Games project. <https://www.wasdcat.com/>

"""Builds an installable addon zip into dist/.

Filename: low-poly-colorizer-<version>-<branch>.zip
  <version> from addon/blender_manifest.toml (field "version")
  <branch>  current git branch (HEAD name, special characters replaced with "-")

Usage:
    python build_addon.py
"""

import re
import subprocess
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ADDON_DIR = ROOT / "addon"
DIST_DIR = ROOT / "dist"
MANIFEST_PATH = ADDON_DIR / "blender_manifest.toml"


def read_manifest():
    with MANIFEST_PATH.open("rb") as f:
        return tomllib.load(f)


def read_branch():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            branch = result.stdout.strip()
            return re.sub(r"[^A-Za-z0-9._-]+", "-", branch)
    except Exception:
        pass
    return "main"


def build():
    manifest = read_manifest()
    version = manifest["version"]
    module_name = manifest["id"]
    branch = read_branch()

    DIST_DIR.mkdir(exist_ok=True)
    zip_path = DIST_DIR / f"low-poly-colorizer-{version}-{branch}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ADDON_DIR.rglob("*")):
            if path.is_dir() or "__pycache__" in path.parts:
                continue
            arcname = Path(module_name) / path.relative_to(ADDON_DIR)
            zf.write(path, arcname)

    print(f"written: {zip_path}")
    return zip_path


if __name__ == "__main__":
    build()
