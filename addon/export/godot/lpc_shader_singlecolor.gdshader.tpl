shader_type spatial;
// SPDX-License-Identifier: MIT

// Low Poly Colorizer -- the singlecolor (instance-uniform-driven) shared
// shader (Godot 4).
//
// For meshes that did NOT come from this add-on (no per-face lpc data at
// all, e.g. a purchased asset or a procedurally generated mesh) -- gives the
// WHOLE mesh ONE palette cell + ONE preset, set per MeshInstance3D as
// instance-uniform overrides in the Godot inspector (no separate
// ShaderMaterial resource needed per object; many instances can share this
// one material and still each look different).
//
// For meshes painted in the add-on, use lpc_shader_multicolor.gdshader /
// lpc_material_multicolor.tres instead (per-face data via vertex UVs).

#include "lpc_shader_common.gdshaderinc"

uniform float emission_factor : hint_range(0.0, 16.0) = 1.0;
uniform float clearcoat_roughness_value : hint_range(0.0, 1.0) = 0.0;
uniform vec2 lpc_palette_size = vec2({{palette_cols}}.0, {{palette_rows}}.0);

// Raw cell coordinates (e.g. (3.0, 5.0)), not a pre-normalized UV -- friendlier
// to type by hand in the inspector than a 0..1 value.
instance uniform vec2 lpc_palette_cell = vec2(0.0, 0.0);

// lpc_preset_position legend (list order at the time of the last export --
// re-export after adding/renaming/deleting a preset to refresh this):
{{preset_legend}}
instance uniform float lpc_preset_position = 0.0;
// -1.0 = use the preset's own emission value; any other value overrides it.
instance uniform float lpc_emission_override = -1.0;

void fragment() {
    vec2 uv = (lpc_palette_cell + 0.5) / lpc_palette_size;
    vec3 albedo = lpc_sample_palette(uv);
    vec4 preset = lpc_sample_preset(lpc_preset_position);
    float emission_value = lpc_emission_override < 0.0 ? preset.w : lpc_emission_override;
    ALBEDO = albedo;
    ROUGHNESS = preset.x;
    METALLIC = preset.y;
    CLEARCOAT = preset.z;
    EMISSION = albedo * emission_value * emission_factor;
    CLEARCOAT_ROUGHNESS = clearcoat_roughness_value;
}
