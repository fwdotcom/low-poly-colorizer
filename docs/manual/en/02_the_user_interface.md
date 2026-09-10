# The User Interface

All controls in Low Poly Colorizer are organized within a compact sidebar panel in the 3D Viewport (**N-Panel ▸ LPC**).

---

## The N-Panel at a Glance

![The Low Poly Colorizer N-Panel with Legend](images/n_panel_annotated.png)

| No. | Section | Description |
|:---:|:---|:---|
| **①** | **Color Selection & Picker** | Displays the color and coordinates $(X, Y)$ of the active palette cell. Clicking the **Palette button** (color picker) opens the interactive modal picker in the viewport. Coordinates can also be edited numerically. |
| **②** | **Selection Status** | Dynamically reports the target selection (*“14 faces in 1 object selected”* or *“1 object selected”*). Displays a warning if no preset is selected. |
| **③** | **Preset List & Actions** | Lists all material presets. The number on the right indicates the **refcount** (how many faces currently use this preset). Includes buttons to add (`+`), delete (`-`), and access the actions menu (`▾`). |
| **④** | **PBR Properties** | Controls the physical material properties (*Roughness*, *Metallic*, *Emission*, *Clearcoat*) of the **currently active preset**. Changes propagate instantly to all faces using this preset. |
| **⑤** | **Tools** | **Assign**: Assigns the active brush (color + preset) to the selection.<br>**Sample**: Eyedropper tool to pick color and preset from an existing face.<br>**Select / Deselect**: *(Edit Mode only)* Selects or deselects all faces sharing identical color and preset. |
| **⑥** | **Export & Settings** | Target format selection (default: *Godot Materials*), **Export button** with automatic dirty tracking (glows red when unsaved changes exist), and button to open **Settings…**. |

---

## Protection & Feedback Mechanisms

* **Refcount Protection**: A preset cannot be deleted while its reference counter is greater than 0, preventing accidental broken mesh references.
* **Visual Dirty Tracking**: Whenever presets, colors, or face assignments change, the Export button highlights in vibrant **red**. After a successful export, it returns to neutral.
* **Color & Preset Matching**: *Select* and *Deselect* use strict logical AND matching: only faces that share **both the exact palette cell and the same preset** are affected.

---

## Shortcuts & Workflow Hotkeys

| Key | Context | Function |
|:---|:---|:---|
| `N` | 3D Viewport | Toggle sidebar containing the LPC panel |
| `Tab` | 3D Viewport | Toggle between Object Mode (paint whole object) and Edit Mode |
| `1` / `2` / `3` | Edit Mode | Switch between Vertex, Edge, and Face selection modes |
| `L` | Edit Mode (cursor over face) | Select linked geometry island |
| `A` / `Alt + A` | 3D Viewport | Select all / Deselect all |
