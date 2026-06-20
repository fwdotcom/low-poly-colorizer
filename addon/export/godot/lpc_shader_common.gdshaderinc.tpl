// SPDX-License-Identifier: MIT

// Low Poly Colorizer -- shared palette + preset lookup (Godot 4).
//
// #include'd by both shader variants (lpc_shader_multicolor / lpc_shader_singlecolor)
// so the actual sampling math lives in exactly one place; the two variants
// differ only in WHERE the palette cell / preset index come from (per-face
// vertex UVs vs. per-instance uniforms).
//
// Both textures hold RAW data (Blender authors them "Non-Color" -- the same
// linear values its vertex colors always used, deliberately not sRGB-gamma-
// encoded). No `:source_color` hint on the samplers below -- if colors ever
// look washed out or too dark compared to the Blender preview, check the
// imported texture's color-space/sRGB import setting first.
//
// `textureLod(..., 0.0)` forces mip level 0 explicitly -- belt-and-suspenders
// on top of `filter_nearest` so a palette cell never blends with its
// neighbor even if the texture import ever ends up with mipmaps generated.

uniform sampler2D lpc_palette_tex : filter_nearest, repeat_disable;
uniform sampler2D lpc_preset_lut_tex : filter_nearest, repeat_disable;
const int LPC_PRESET_COUNT = {{preset_count}};
// (cols, rows) of the palette grid -- only the singlecolor variant needs
// this (to turn a hand-set cell into a UV), but it lives here alongside
// LPC_PRESET_COUNT so every project-wide export constant is in one place.
const vec2 LPC_PALETTE_SIZE = vec2({{palette_cols}}.0, {{palette_rows}}.0);

// `uv` is already a normalized, texel-center 0..1 coordinate -- no division
// needed here. The multicolor variant gets it straight from a UV map
// (baked in by model/faces.encode_palette_uv at paint time); the
// singlecolor variant computes it from a hand-set cell + LPC_PALETTE_SIZE.
vec3 lpc_sample_palette(vec2 uv) {
    return textureLod(lpc_palette_tex, uv, 0.0).rgb;
}

// `position` is the preset's list index as a raw float (0..LPC_PRESET_COUNT-1),
// NOT pre-normalized -- the texel-center conversion happens here, since the
// raw integer-ish value has no Blender-side equivalent normalization step.
// Returns (roughness, metallic, clearcoat, emission).
vec4 lpc_sample_preset(float position) {
    float u = (position + 0.5) / float(LPC_PRESET_COUNT);
    return textureLod(lpc_preset_lut_tex, vec2(u, 0.5), 0.0);
}
