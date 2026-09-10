# Engine Export and Integration

Low Poly Colorizer is engineered from the ground up for maximum rendering performance in real-time game engines. The export process translates Blender scene data into lightweight, optimized textures and shaders.

## One-Click Export to Godot

To prepare your assets for Godot, click the **Export button** in the N-Panel (next to the *Godot Materials* dropdown). LPC generates three files:

* **`lpc_palette.png`**: Palette texture storing all albedo and emission colors.
* **`lpc_preset_lut.png`**: Compact lookup table defining roughness, metallic, clearcoat, and emission parameters.
* **`lpc_shader.tres`**: Production-ready Godot shader that automatically binds both textures using dedicated UV sets.
* **Dirty Flag Tracking**: The export button illuminates in red whenever unsaved changes exist and resets to neutral once synchronized.

## Procedural Workflows with Geometry Nodes

For procedural meshes, generate the `lpc_set_material` node group via the preset menu (**▾**) by selecting **Create Geometry Node Group**:

1. LPC constructs the node group and attaches it as a Geometry Nodes modifier to the active object.
2. In the Node Editor, drive palette coordinates $(X, Y)$ and material preset procedurally through input sockets. The shared `lpc_multicolor` material handles shading automatically.

![The lpc_set_material node group in the Geometry Node Editor](images/geo_nodes_lpc_set_material.png)

## Maintenance: Repairing UV Maps (*Fix UV Maps*)

Low Poly Colorizer utilizes two designated UV channels: `lpc_uv0` (palette color coordinates) and `lpc_uv1` (preset LUT coordinates).

When meshes are joined (`Ctrl + J`), cut with Boolean operations, or imported from external sources, UV layers can become swapped or omitted. In this case, LPC automatically displays a highlighted warning box at the bottom of the N-Panel:

> [!WARNING]
> **UV maps need fixing:** Clicking **Fix UV Maps** repairs mesh attributes, restores the correct `lpc_uv0` / `lpc_uv1` layer ordering, and ensures seamless import into Godot.

## Troubleshooting Checklist

| Problem | Cause | Solution |
|:---|:---|:---|
| **No colors in viewport** | 3D Viewport is set to *Wireframe* or *Solid* mode without texture preview enabled. | Press `Z` and switch shading mode to **Material Preview** or **Rendered**. |
| **Faces do not color** | In Edit Mode, no faces are selected, or no preset is selected in the list. | Select faces with `A` or `L` and ensure a preset is highlighted in the list. |
| **Minus button (`-`) disabled** | The selected preset is currently used by mesh faces (refcount > 0). | Use *Select* to locate referencing faces and assign them a different preset. |
| **Exported look differs in Godot** | Textures were not re-exported after modifying presets (red export button). | Click the red **Export button** in the N-Panel to update texture assets. |
