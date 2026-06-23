# SPDX-FileCopyrightText: 2026 Frank Winter <https://www.frankwinter.com/>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of Low Poly Colorizer (LPC). <https://github.com/wasdcat/low-poly-colorizer>
# A WASDCAT Games project. <https://www.wasdcat.com/>

"""Generic, engine-agnostic template export.

A target is a folder of `.tpl` files (see registry.py). Export renders every
`.tpl` in the chosen set into the chosen output directory: `{{key}}`
placeholders are substituted from the scene's material parameters
(`build_context`), the `.tpl` marker is dropped from the written filename, and
literal braces in the body are left intact (so shader code survives).

Alongside the rendered templates, `write_textures` writes the palette + the
preset LUT as PNGs -- binary data the `.tpl` text-substitution mechanism
can't carry, so it's a separate step in `LPC_OT_export.execute`, not another
template.

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
from .. import constants
from ..model import palette as model_palette
from ..model import presets as model_presets
from ..picker import interface as picker_interface
from ..ui import preview_material

# Filenames the palette + preset LUT textures are written under in the export
# folder -- referenced literally by the .tres templates (ExtResource paths
# are fixed text, not engine-agnostic, so the names live here rather than in
# the templates themselves).
PALETTE_IMAGE_FILENAME = "lpc_palette.png"
PRESET_LUT_IMAGE_FILENAME = "lpc_preset_lut.png"

# Base name the .tres templates suffix into their own resource_name
# ("{{name}}_multicolor" / "{{name}}_singlecolor") -- deliberately NOT
# `preview_material.MATERIAL_NAME` (the Blender datablock, itself suffixed
# "_multicolor" since Blender's preview only ever renders that variant): this
# base feeds BOTH exported resources, so it must stay variant-neutral.
EXPORT_MATERIAL_NAME = constants.PREFIX + "material"


def _fmt(value):
    return repr(round(float(value), 6))


def _preset_legend(scene):
    """A `lpc_preset_position` value <-> preset name comment block -- list
    position is a plain int with no name attached once it's on a mesh, so
    this is the one place a human (hand-setting the singlecolor variant's
    instance uniforms in Godot) can look up which number means what.
    Re-exporting after any preset add/delete/rename regenerates it; it goes
    stale otherwise, hence the "at the time of the last export" caveat in the
    template using it."""
    presets = list(scene.lpc_presets)
    if not presets:
        return "//   (no presets)"
    return "\n".join(f"//   {i} = {p.name}" for i, p in enumerate(presets))


def build_context(scene):
    """The substitution values available to every template -- engine-agnostic
    material parameters from the scene. Unknown placeholders in a template are
    left untouched, unused keys here are simply ignored."""
    g = scene.lpc_globals
    cols, rows = model_palette.cell_count(picker_interface.params_from_scene(scene))
    preset_count = max(len(scene.lpc_presets), 1)
    return {
        "name": EXPORT_MATERIAL_NAME,
        "emission_factor": _fmt(g.emission_factor),
        "clearcoat_roughness": _fmt(g.clearcoat_roughness),
        "preset_count": str(preset_count),
        # *_max are the highest VALID index (count - 1) -- only useful as
        # `hint_range` upper bounds on the singlecolor shader's instance
        # uniforms (lpc_preset_position, lpc_palette_cell_x/y), clamping
        # hand-typed Inspector values to what the exported LUT/palette
        # textures actually contain. Godot's hint_range only accepts
        # int/float uniforms, not vectors -- hence cell_x/y as two
        # separate placeholders rather than one vec2.
        "preset_count_max": str(preset_count - 1),
        "palette_cols": str(cols),
        "palette_rows": str(rows),
        "palette_cols_max": str(cols - 1),
        "palette_rows_max": str(rows - 1),
        "palette_image_filename": PALETTE_IMAGE_FILENAME,
        "preset_lut_image_filename": PRESET_LUT_IMAGE_FILENAME,
        "preset_legend": _preset_legend(scene),
    }


def export_fingerprint(scene):
    """Deterministic snapshot of every value that ends up in the exported
    files -- `build_context` (covers preset names/count, globals, palette
    grid size) plus the preset LUT pixels (covers preset VALUES, which
    `build_context` only counts) plus the palette params (a stand-in for
    the palette pixels themselves -- `model_palette.build_pixels` is a pure
    function of them, so they carry the same information without hashing
    the whole pixel array)."""
    lut = tuple(round(v, 6) for v in model_presets.build_preset_lut_pixels(scene))
    palette_params = tuple(sorted(picker_interface.params_from_scene(scene).items()))
    return repr((build_context(scene), lut, palette_params))


def is_export_dirty(scene):
    """True if `scene`'s current export-relevant state no longer matches
    `scene.lpc_export_fingerprint` (set at the last successful export) --
    the Export button's red highlight. Computed live on every panel
    redraw, never toggled, so undo/redo/manual reverts are reflected
    automatically. Stored as a real Scene property (not plain Python
    state) so it persists across saves -- safe to do only because
    `LPC_OT_export` is itself undo-registered (see its bl_options), which
    gives the property write its own undo-snapshot boundary; without that,
    a later undo could jump past the export to a stale pre-export snapshot
    even though e.g. a preset's roughness on that same snapshot correctly
    reverts (the property and the data it describes would desync)."""
    try:
        return export_fingerprint(scene) != scene.lpc_export_fingerprint
    except AttributeError:
        return False  # lpc_* properties unexpectedly missing -- fail safe, not loud


def _mark_exported(scene):
    scene.lpc_export_fingerprint = export_fingerprint(scene)


def write_textures(scene, out_dir):
    """Write the palette + preset LUT images as PNGs into `out_dir`, via
    Blender's own `Image.save()` -- guarantees the exported pixels are
    byte-identical to whatever the Blender preview just sampled (no separate
    encoder to risk a rounding/gamma divergence). Returns the list of written
    filenames."""
    written = []
    for image, filename in (
        (preview_material.ensure_palette_image(scene), PALETTE_IMAGE_FILENAME),
        (preview_material.ensure_preset_lut_image(scene), PRESET_LUT_IMAGE_FILENAME),
    ):
        path = os.path.join(out_dir, filename)
        image.filepath_raw = path
        image.file_format = "PNG"
        image.save()
        written.append(filename)
    return written


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
    """Export the selected template set into a chosen folder: the shader(s), material(s), and the palette + preset LUT textures. Pick the target in the dropdown; the per-face references (palette cell + preset index) travel in the lpc UV maps, so import the .blend separately"""

    bl_idname = "lpc.export"
    bl_label = "Export"
    # UNDO (not just REGISTER): writes scene.lpc_export_fingerprint
    # (is_export_dirty), which needs its own undo-snapshot boundary so a
    # later undo can't jump past it to a stale pre-export value -- see
    # is_export_dirty's docstring.
    bl_options = {"REGISTER", "UNDO"}

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
            written += write_textures(scene, out_dir)
        except (OSError, ValueError) as exc:
            self.report({"ERROR"}, f"Export failed: {exc}")
            return {"CANCELLED"}
        _mark_exported(scene)

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

