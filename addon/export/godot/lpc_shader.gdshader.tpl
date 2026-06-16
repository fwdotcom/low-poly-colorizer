shader_type spatial;
// SPDX-License-Identifier: MIT

// Low Poly Colorizer -- the single shared material shader (Godot 4).
//
// Godot imports the .blend geometry directly (Blender's own glTF export under
// the hood). All painted faces share ONE material, so they import as ONE
// surface; set its Material Override to lpc_material.tres.
//
// Per-face data carried through stock glTF:
//   * COLOR_0 (vertex colour, from lpc_color) -> ALBEDO and the emission tint
//   * UV  (TEXCOORD_0, from lpc_uv0) = (roughness, metallic)
//   * UV2 (TEXCOORD_1, from lpc_uv1) = (clearcoat, raw emission)
// All corners of a face share one value, so each channel reads flat per face.
//
// The two project-wide globals are uniforms, set in lpc_material.tres.
//
// IMPORTANT: lpc_uv0 / lpc_uv1 must be the first two UV maps on the mesh so
// they import as UV / UV2. If your mesh also has a texturing UV map, reorder
// so the lpc maps come first. If Godot rejects CLEARCOAT / CLEARCOAT_ROUGHNESS,
// check the spatial-shader built-in names for your version.

uniform float emission_factor = 1.0;
uniform float clearcoat_roughness_value : hint_range(0.0, 1.0) = 0.0;

void fragment() {
    ALBEDO = COLOR.rgb;
    ROUGHNESS = UV.x;
    METALLIC = UV.y;
    CLEARCOAT = UV2.x;
    EMISSION = COLOR.rgb * UV2.y * emission_factor;
    CLEARCOAT_ROUGHNESS = clearcoat_roughness_value;
}
