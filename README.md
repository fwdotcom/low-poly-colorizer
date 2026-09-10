# Low Poly Colorizer

![Version](https://img.shields.io/badge/version-0.1.1-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![Blender](https://img.shields.io/badge/Blender-4.2%2B-orange)
![Godot](https://img.shields.io/badge/Godot-4.x-orange)

A high-efficiency Blender extension for painting mesh faces with PBR material properties using an interactive color palette texture – built for clean low-poly asset workflows and 1-click export to game engines like Godot 4.

Originally developed in-house for **WASDCAT Games'** Blender → Godot production pipeline and shared with the community.

---

## Core Concept

- **Single Palette Texture:** All asset colors are mapped to a compact palette texture. Changing palette settings (tint, shade, saturation) dynamically updates all colorized assets across your project.
- **Single Draw-Call Surface:** All colored faces share a single material. Variations in color and PBR properties (roughness, metallic, emission) are stored in two UV channels, eliminating multi-material clutter and draw calls.
- **Instant Live Assignment:** Hover over any palette cell in the GPU overlay or sample existing faces to instantly apply colors and PBR presets in real time.
- **Engine-Ready Pipeline:** 1-click export of optimized meshes and shader templates for Godot 4.x, plus full procedural Geometry Nodes support (`LPC Set Material`).

---

## User Manuals / Benutzerhandbuch

Complete, detailed documentation covering all features, shortcuts, shader integration, and troubleshooting is available as compact 12-page PDFs:

- 🇬🇧 **[English User Manual (PDF)](manual/low_poly_colorizer_en.pdf)** · [Online Markdown](docs/manual/en/)
- 🇩🇪 **[Deutsches Benutzerhandbuch (PDF)](manual/low_poly_colorizer_de.pdf)** · [Online Markdown](docs/manual/de/)

---

## Installation

Requirement: **Blender 4.2 LTS or newer** (Extension system).

### Online (Blender Extensions Platform)
1. Open **Edit ▸ Preferences ▸ Get Extensions**.
2. Search for **Low Poly Colorizer** and click **Install**.

### Manual Installation (ZIP)
1. Download `low_poly_colorizer-0.1.1.zip` from [Releases](../../releases) (or build locally using `python scripts/build_dist.py`).
2. In Blender: **Edit ▸ Preferences ▸ Get Extensions ▸ ▾ (top right menu) ▸ Install from Disk…** and select the ZIP file (or drag & drop the ZIP directly onto the Blender window).
3. In the 3D Viewport, press `N` to open the sidebar and switch to the **LPC** tab.

---

## Development

```bash
# Run tests, compile manuals and build extension package into dist/
python scripts/build_dist.py
```