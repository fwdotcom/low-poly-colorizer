# SPDX-License-Identifier: GPL-3.0-or-later

"""Generic, engine-agnostic template export.

A target is a folder of `.tpl` files (see registry.py). Export renders every
`.tpl` in the chosen set into the chosen output directory: `{{key}}`
placeholders are substituted from the scene's material parameters
(`build_context`), the `.tpl` marker is dropped from the written filename, and
literal braces in the body are left intact (so shader code survives).

Nothing here is Godot-specific -- the only thing that knows about a particular
engine is its template folder + its registry entry. The render context is the
engine-agnostic material state; a template uses whatever subset it needs and
cross-file references (e.g. a material pointing at its shader file) are written
literally in the template, since each set's output filenames are fixed.
"""

import os
import re

import bpy

from . import registry
from ..ui import preview_material


def _fmt(value):
    return repr(round(float(value), 6))


def build_context(scene):
    """The substitution values available to every template -- engine-agnostic
    material parameters from the scene. Unknown placeholders in a template are
    left untouched, unused keys here are simply ignored."""
    g = scene.lpc_globals
    return {
        "name": preview_material.MATERIAL_NAME,
        "emission_factor": _fmt(g.emission_factor),
        "clearcoat_roughness": _fmt(g.clearcoat_roughness),
    }


def _render(text, mapping):
    return re.sub(
        r"\{\{(\w+)\}\}",
        lambda m: mapping.get(m.group(1), m.group(0)),
        text,
    )


def _strip_tpl(name):
    return name[:-4] if name.endswith(".tpl") else name


def render_set(set_id, out_dir, context):
    """Render every `.tpl` in the set's folder into `out_dir`. Returns the list
    of written filenames. Raises ValueError for an unknown set, OSError on IO."""
    tdir = registry.template_dir(set_id)
    if tdir is None or not os.path.isdir(tdir):
        raise ValueError(f"unknown export template set: {set_id!r}")
    written = []
    for entry in sorted(os.listdir(tdir)):
        if not entry.endswith(".tpl"):
            continue
        with open(os.path.join(tdir, entry), "r", encoding="utf-8") as f:
            text = f.read()
        out_name = _strip_tpl(entry)
        with open(os.path.join(out_dir, out_name), "w", encoding="utf-8") as f:
            f.write(_render(text, context))
        written.append(out_name)
    return written


def _uv_problem_count(scene):
    """Painted meshes whose param UVs are missing or out of the leading UV
    order -- a UV-transport target would mis-import them (see Fix UV Maps)."""
    seen = set()
    count = 0
    for obj in scene.objects:
        if obj.type == "MESH" and obj.data not in seen:
            seen.add(obj.data)
            if preview_material.mesh_needs_uv_fix(obj.data):
                count += 1
    return count


# EnumProperty items must outlive the registration call (Blender keeps no copy
# of the strings), so hold them at module level.
EXPORT_TARGET_ITEMS = registry.enum_items()


class LPC_OT_export(bpy.types.Operator):
    """Export the selected template set into a chosen folder. Pick the target in the dropdown; the per-face look travels in the mesh data (vertex colour + the lpc UV maps), so import the .blend separately"""

    bl_idname = "lpc.export"
    bl_label = "Export"
    bl_options = {"REGISTER"}

    # Directory picker (every output filename is fixed by the templates).
    directory: bpy.props.StringProperty(subtype="DIR_PATH")
    filter_folder: bpy.props.BoolProperty(default=True, options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        scene = context.scene
        set_id = scene.lpc_export_target
        entry = registry.get(set_id)
        if entry is None:
            self.report({"ERROR"}, "No export target selected")
            return {"CANCELLED"}
        out_dir = self.directory
        if not out_dir or not os.path.isdir(out_dir):
            self.report({"ERROR"}, "Choose an existing output folder")
            return {"CANCELLED"}

        try:
            written = render_set(set_id, out_dir, build_context(scene))
        except (OSError, ValueError) as exc:
            self.report({"ERROR"}, f"Export failed: {exc}")
            return {"CANCELLED"}

        label = entry["label"]
        broken = _uv_problem_count(scene)
        if broken:
            self.report(
                {"WARNING"},
                f"Exported {label} ({len(written)} file(s)), but {broken} "
                f"mesh(es) have the lpc UV maps missing or out of order -- run "
                f"'Fix UV Maps' in Object Mode so the params import correctly",
            )
        else:
            self.report(
                {"INFO"}, f"Exported {label} ({len(written)} file(s))"
            )
        return {"FINISHED"}
