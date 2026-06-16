# SPDX-License-Identifier: GPL-3.0-or-later

"""Export template-set registry (the export "config").

One entry per export target ("template set"): a human label shown in the
export dropdown mapped to a folder of `.tpl` files under `addon/export/`.
Godot is just one target -- adding another engine is: drop a folder of `.tpl`
templates under `addon/export/<dir>/` and add an entry here. No code change in
the exporter.

The exporter (exporter.py) renders EVERY `.tpl` in the chosen set's folder
into the chosen output directory, substituting the scene's material
parameters (build_context). Each template uses whatever placeholders it needs.
"""

import os

# id          stable key, stored in the scene's lpc_export_target enum
# label       shown in the dropdown
# dir         folder under export/ holding this set's .tpl files
# description tooltip
TEMPLATE_SETS = (
    {
        "id": "godot",
        "label": "Godot Materials",
        "dir": "godot",
        "description": "Godot 4 spatial shader + ShaderMaterial (.tres)",
    },
)

_BASE = os.path.dirname(__file__)


def get(set_id):
    """The set entry for `set_id`, or None."""
    for entry in TEMPLATE_SETS:
        if entry["id"] == set_id:
            return entry
    return None


def template_dir(set_id):
    """Absolute path of the set's template folder, or None for an unknown id."""
    entry = get(set_id)
    return os.path.join(_BASE, entry["dir"]) if entry is not None else None


def enum_items():
    """`(id, label, description)` tuples for an EnumProperty. Kept alive by the
    caller (Blender does not copy enum item strings)."""
    return [
        (e["id"], e["label"], e.get("description", "")) for e in TEMPLATE_SETS
    ]
