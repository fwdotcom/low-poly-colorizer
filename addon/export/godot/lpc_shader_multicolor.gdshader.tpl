shader_type spatial;
// SPDX-License-Identifier: MIT

// Low Poly Colorizer -- the per-face/multicolor shared shader (Godot 4).
//
// Godot imports the .blend geometry directly (Blender's own glTF export
// under the hood). All painted faces share ONE material, so they import as
// ONE surface; set its Material Override to lpc_material_multicolor.tres.
//
// Per-face data carried through stock glTF:
//   * UV  (TEXCOORD_0, from lpc_uv0) = the picked palette cell, normalized
//   * UV2 (TEXCOORD_1, from lpc_uv1) = (preset list position, unused)
// All corners of a face share one value, so each channel reads flat per face.
//
// IMPORTANT: lpc_uv0 / lpc_uv1 must be the first two UV maps on the mesh so
// they import as UV / UV2 (use "Fix UV Maps" in the add-on if they aren't).
//
// For meshes that did NOT come from this add-on (no per-face data at all),
// use lpc_shader_singlecolor.gdshader / lpc_material_singlecolor.tres instead.

#include "lpc_shader_common.gdshaderinc"

uniform float emission_factor : hint_range(0.0, 16.0) = 1.0;
uniform float clearcoat_roughness_value : hint_range(0.0, 1.0) = 0.0;

void fragment() {
    vec3 albedo = lpc_sample_palette(UV);
    vec4 preset = lpc_sample_preset(UV2.x);
    ALBEDO = albedo;
    ROUGHNESS = preset.x;
    METALLIC = preset.y;
    CLEARCOAT = preset.z;
    EMISSION = albedo * preset.w * emission_factor;
    CLEARCOAT_ROUGHNESS = clearcoat_roughness_value;
}
