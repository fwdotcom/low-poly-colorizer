# Low Poly Colorizer – Manual

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![Blender](https://img.shields.io/badge/Blender-4.2%2B-orange)
![Godot](https://img.shields.io/badge/Godot-4.x-orange)

A Blender add-on for painting mesh **faces** with PBR material values
(color, roughness, metallic, emission, clearcoat) through a generated color
palette – with an instant WYSIWYG viewport preview and an export for game
engines (currently Godot).

---

## Contents

1. [Core idea](#1-core-idea)
2. [Installation](#2-installation)
3. [The panel at a glance](#3-the-panel-at-a-glance)
4. [Quick start](#4-quick-start)
5. [The palette & the picker](#5-the-palette--the-picker)
6. [Painting in detail](#6-painting-in-detail)
7. [Managing presets](#7-managing-presets)
8. [Settings dialog](#8-settings-dialog)
9. [Unpainted faces & your own materials](#9-unpainted-faces--your-own-materials)
10. [Export](#10-export)
11. [Godot integration](#11-godot-integration)
12. [Fix UV Maps](#12-fix-uv-maps)
13. [Tips & pitfalls](#13-tips--pitfalls)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Core idea

Instead of building a separate material for every color variant, you paint
**two things per face**:

- **Color (albedo)** – comes from a cell of the generated palette and is
  written onto the face as a **vertex color**. So *one* face can carry any
  color.
- **Material look (preset)** – roughness, metallic, emission and clearcoat,
  bundled under a named **preset**. Many faces (with different colors) can
  share the same preset.

Behind the scenes, all painted faces share **a single material**. The
per-face differences live in the mesh data (vertex color + two UV maps), not
in many materials. That keeps the scene lean and produces **one** surface on
export instead of many.

"Painted" means the face carries a preset. Faces you never painted keep
Blender's plain default look.

---

## 2. Installation

Requirement: **Blender 4.2 or newer** (the add-on is an extension).

1. Build or obtain the add-on as a ZIP
   (`python build_addon.py` writes `dist/low-poly-colorizer-<version>-<branch>.zip`).
2. In Blender: **Edit ▸ Preferences ▸ Add-ons ▸ Install from Disk…** and pick
   the ZIP (or drag & drop the ZIP onto the Blender window).
3. Enable the add-on.
4. In the 3D viewport open the **N-panel** (press `N`) and select the **LPC**
   tab.

A fresh file is automatically populated with a set of default presets so you
can start right away.

---

## 3. The panel at a glance

The whole workflow lives in the N-panel **LPC ▸ LPC Palette**:

```
┌─ LPC Palette ─────────────────────────────┐
│ [Swatch] [X] [Y]              [🎨 Picker]  │  ← current color + cell
│ 3 faces in 1 object selected               │  ← selection hint
│                                            │
│ ┌ Preset list ──────────────┐  [+]         │
│ │ Solid                  0   │  [-]         │  ← presets, refcount on right
│ │ Metallic               12  │  [▾ Menu]    │
│ │ Emission               0   │              │
│ └───────────────────────────┘              │
│                                            │
│ Roughness  ▓▓▓▓▓░░░░                        │  ← active preset's values
│ Metallic   ░░░░░░░░░                        │
│ Emission   ░░░░░░░░░                        │
│ Clearcoat  ░░░░░░░░░                        │
│                                            │
│ [👁 Sample]            [🖌 Assign]          │
│ [Select]              [Deselect]           │  ← Edit Mode only
│                                            │
│ Export   [Godot Materials ▾]      [⤓]      │  ← footer
│ [Settings…]                                │
└────────────────────────────────────────────┘
```

- **Swatch / X / Y / Picker** – the currently selected palette cell. The
  swatch shows its color, `X`/`Y` the column/row (directly editable), and the
  picker button opens the palette as an overlay.
- **Selection hint** – what a brush stroke would hit (number of faces or
  objects). Also warns when no preset is selected.
- **Preset list** – your presets. The number on the right is the **refcount**
  (how many faces use the preset). `+`/`-` add/delete; the `▾` menu holds
  Duplicate, JSON import/export and the default presets.
- **Value sliders** – roughness/metallic/emission/clearcoat of the **active**
  preset. Changes take effect immediately on every face that uses it.
- **Sample / Assign** – tool buttons (see below).
- **Select / Deselect** – only shown in Edit Mode.
- **Footer** – the export selector + button and the Settings dialog.

---

## 4. Quick start

Paint your first faces in under a minute:

1. Select an object (Object Mode) **or** enter Edit Mode and select a few
   faces.
2. Pick a preset in the **preset list** (e.g. "Solid").
3. Click the **🎨 Picker** next to the swatch. The palette appears as an
   overlay in the viewport.
4. **Click a color cell.** The picker closes and the selection is painted
   immediately (color + preset in one step).

That's it. The painted faces show the color with the preset's material look
directly in the viewport.

> **Live assign:** Clicking a cell paints the current selection right away –
> you don't have to press "Assign" separately. You need "Assign" to re-apply
> the same color/preset combination after changing the selection.

---

## 5. The palette & the picker

### The picker (overlay)

Clicking the 🎨 button opens the palette centered in the viewport. Controls:

| Action | Result |
|--------|--------|
| **Left-click a cell** | selects it, paints the selection immediately, closes |
| **Mouse wheel** | zoom (centered on the cursor) |
| **Middle mouse button + drag** | pan |
| **Right-click / Esc / click outside** | cancel (nothing changes) |

The cell under the cursor is outlined in white. The picker overlay shows the
**true** colors (unlike the small swatch in the panel, see
[Troubleshooting](#14-troubleshooting)).

### How the palette is built

The palette is fully computed from parameters (adjustable in the
[Settings dialog](#8-settings-dialog)):

- **Columns** – number of **hue** columns.
- **Add Greyscale Column** – prepends an extra column on the left with a plain
  white-to-black ramp (column `X = 0`). The hue columns then start at `X = 1`.
- **Rows** – number of rows. The **middle** row shows the base tone (full
  saturation/brightness); upward it blends toward white, downward toward
  black.
- **Saturation / Brightness** – saturation/brightness of the middle row.
- **Tint** – how far the top row goes toward white.
- **Shade** – how far the bottom row goes toward black.

The palette itself is not stored in the file; it is recomputed from these
parameters at any time. The **parameters**, however, are stored per scene in
the `.blend`.

---

## 6. Painting in detail

### Object Mode vs. Edit Mode

- **Object Mode:** a brush stroke paints **all** faces of the selected
  objects.
- **Edit Mode:** only the **selected** faces are painted.

### The tools

- **🖌 Assign** – applies the current brush (selected color + active preset)
  to the selection. Disabled when nothing is selected.
- **👁 Sample** *(Edit Mode)* – "eyedroppers" a painted face back into the
  UI: sets the matching preset and the nearest palette cell as the current
  brush. Only works for a selection that uniformly carries *one* color +
  *one* preset.
- **Select / Deselect** *(Edit Mode)* – add/remove all faces that exactly
  match the current brush (same color **and** same preset) to/from the
  selection. Handy for re-coloring specific faces later.

> **The "brush"** is always the pair *(selected color, active preset)*.
> Assign, Sample, Select and Deselect all act on this pair.

---

## 7. Managing presets

A **preset** bundles the four material values under a name.

- **Add** `+` – a new preset with neutral values.
- **Delete** `-` – only possible when **no** face uses the preset
  (refcount 0). While it is in use, the button is locked and the list shows
  the count with a shield icon.
- **Rename** – double-click the name in the list.
- **Change values** – the sliders below the list act on the **active** preset
  and propagate **immediately** to every face using it.

Via the **`▾` menu** next to the list:

- **Duplicate** – copy the active preset.
- **Import / Export** – load/save presets as a JSON file (to share between
  projects). On import, presets with a matching name are updated and new ones
  added – re-importing the same file changes nothing.
- **Load Default Presets** – add the bundled default presets (existing presets
  with the same name are set to the default values).

---

## 8. Settings dialog

The **Settings…** button in the footer opens a dialog with the rarely-changed
values. Changes apply live; **Cancel** restores the previous state.

- **Grid** – `Columns`, `Rows`, `Add Greyscale Column` (palette grid).
- **Base Color** – `Saturation`, `Brightness` of the middle row.
- **Tint / Shade** – blending of the top/bottom row toward white/black.
- **Globals** – project-wide material values:
  - **Emission Factor** – a global multiplier on every preset's emission
    (e.g. to brighten/darken all glowing faces together).
  - **Clearcoat Roughness** – project-wide roughness of the clearcoat layer.

---

## 9. Unpainted faces & your own materials

- **Unpainted faces** carry no preset and render Blender's plain default look.
  Newly created geometry is always unpainted at first.
- **Objects with their own materials:** if you paint only some faces, the rest
  keep their original material – the add-on never hijacks foreign materials.
  The preset material is assigned only to the painted faces.
- **Material-less objects:** slot 0 stays empty so unpainted faces keep the
  default look; painted faces move to the shared lpc slot.

---

## 10. Export

In the footer, choose an **export template set** on the left via the dropdown
(currently only **Godot Materials**; other engines can be added) and click the
**Export button (⤓)** on the right. A folder dialog opens – the files are
written into the chosen folder.

For **Godot Materials**, two files are produced:

- `lpc_shader.gdshader` – the shared spatial shader.
- `lpc_material.tres` – the ShaderMaterial that references the shader and sets
  the global values (Emission Factor, Clearcoat Roughness).

The export writes **only** these files. The geometry with its per-face data
reaches Godot separately via the `.blend` import (see the next section).

> If the export reports a **UV warning**, see [Fix UV Maps](#12-fix-uv-maps).

---

## 11. Godot integration

Godot imports the `.blend` directly (via Blender's glTF export). This is how
the look travels across:

1. Place the **export folder** (with `lpc_shader.gdshader` +
   `lpc_material.tres`) and your **`.blend`** into your Godot project.
2. Godot imports the `.blend` as a scene. All painted faces form **one
   surface** (because they share a single material).
3. In the imported mesh, select the surface and set its **Material Override**
   to `lpc_material.tres`.

What travels how:

- **Albedo** travels as a vertex color (`COLOR_0`).
- **Roughness/Metallic** live in the first UV map (`lpc_uv0` → `UV`).
- **Clearcoat / Emission** live in the second UV map (`lpc_uv1` → `UV2`).
- The shader assembles the look from these; emission is **per face** and
  albedo-tinted (`EMISSION = color × emission × emission factor`).

> **Important – UV order:** for the parameters to arrive correctly, `lpc_uv0`
> and `lpc_uv1` must be the **first two** UV maps of the mesh. For freshly
> painted meshes this is automatic. If a mesh already had its own UV maps, the
> order can flip – then use **Fix UV Maps**.

---

## 12. Fix UV Maps

When a painted mesh does not have its lpc UV maps in the first two slots (or
one is missing), the footer shows a warning box **"UV maps need fixing"** with
a **Fix button**. The export warns additionally.

**When does this happen?** In practice only when you paint a mesh that
**already had its own UV maps** – the lpc maps then get appended at the end.

**What does "Fix UV Maps" do?** Across all painted meshes:

1. recreate missing lpc UV maps,
2. sort them into the first two slots,
3. rewrite the preset values into them.

Your own UV maps are preserved – they just move behind the lpc maps.

> **Note:** Fix UV Maps only runs in **Object Mode** (reordering UV maps is not
> possible in Edit Mode). Switch to Object Mode briefly and click again if
> needed.

---

## 13. Tips & pitfalls

- **Select a preset first, then pick.** A pick without an active preset paints
  nothing – the "No preset selected" hint warns about this.
- **Use live assign:** changing the selection and simply picking a cell again
  is often faster than the Assign button.
- **One preset, many colors:** you don't need a preset per color. Use e.g. a
  "Solid" preset and pick different palette colors.
- **Change preset values centrally:** moving a slider changes *all* faces of
  that preset at once – ideal for adjusting the look project-wide.
- **Greyscale column:** with the greyscale column enabled, `X = 0` is always
  the white-to-black ramp; the hues start at `X = 1`.

---

## 14. Troubleshooting

**The small swatch in the panel looks "wrong" / too dark.**
Blender draws UI color fields through the view transform (AgX by default), so
e.g. linear white appears grey. The stored value is correct (hover shows it),
and the **picker overlay** shows the true colors.

**"Assign" is greyed out.**
Nothing is selected. Select an object (Object Mode) or faces (Edit Mode).

**"Sample" is greyed out.**
Sample needs a **uniform** selection: exactly one painted color + one preset.
With a mixed selection the button stays locked.

**A preset cannot be deleted.**
It is still used by faces (refcount > 0). Re-color those faces first (assign a
different preset), then deletion is unlocked.

**In Godot, roughness/metallic/clearcoat/emission are wrong.**
Most likely the UV order slipped – run **Fix UV Maps** in Object Mode and
export/import again. Also check that the surface's **Material Override** is set
to `lpc_material.tres`.

**Freshly added geometry is "unpainted".**
This is intentional: new faces carry no preset and render the default look
until you paint them.

---

*Licenses: see [LICENSE.md](LICENSE.md).*
