# Engine-Export und Integration

Low Poly Colorizer wurde von Grund auf für maximale Render-Performance in Echtzeit-Engines entworfen. Der Export übersetzt die Blender-Szenendaten in leichtgewichtige Texturen und Shader.

## Der 1-Klick Export nach Godot

Um Ihr Modell für Godot vorzubereiten, klicken Sie im N-Panel auf den **Export-Button** (neben dem Dropdown *Godot Materials*). LPC erzeugt drei Dateien:

* **`lpc_palette.png`**: Palettengrafik für Albedo- und Emissionsfarben.
* **`lpc_preset_lut.png`**: Kompakte Lookup-Table für Roughness, Metallic, Clearcoat und Emission.
* **`lpc_shader.tres`**: Fertiger Godot-Shader zur automatischen Bindung beider Texturen an die UVs.
* **Dirty-Flag-Erkennung**: Der Button leuchtet rot bei ungespeicherten Änderungen und neutral im synchronen Zustand.

## Prozedurale Workflows mit Geometry Nodes

Für prozedurale Meshes erzeugen Sie über das Preset-Zusatzmenü (**▾**) mit **Create Geometry Node Group** die Node-Gruppe `lpc_set_material`:

1. LPC erstellt die Node-Gruppe und bindet sie als Geometry-Nodes-Modifier an das aktive Objekt.
2. Im Node-Editor steuern Sie Palettenzelle $(X, Y)$ sowie das Preset prozedural per Eingangs-Socket. Das Material `lpc_multicolor` übernimmt das Shading automatisch.


![Die Node-Gruppe lpc_set_material im Geometry-Nodes-Editor](images/geo_nodes_lpc_set_material.png)

## Wartung: UV-Maps reparieren (*Fix UV Maps*)

Low Poly Colorizer nutzt zwei definierte UV-Kanäle: `lpc_uv0` (Paletten-Farbkoordinaten) und `lpc_uv1` (Preset-LUT-Koordinaten).

Werden Meshes zusammengefügt (`Ctrl + J`), durch Booleans zerschnitten oder importiert, können UV-Kanäle vertauscht sein oder fehlen. LPC blendet in diesem Fall am unteren Rand des N-Panels automatisch eine rot markierte Warnbox ein:

> [!WARNING]
> **UV maps need fixing:** Ein Klick auf den Button **Fix UV Maps** repariert die Mesh-Attribute, stellt die Reihenfolge `lpc_uv0` / `lpc_uv1` wieder her und sichert den sauberen Import in Godot.


## Troubleshooting-Checkliste

| Problem | Ursache | Lösung |
|:---|:---|:---|
| **Keine Farben im Viewport** | 3D-Viewport steht auf *Wireframe* oder *Solid* ohne Texture-Preview. | Schalten Sie mit `Z` in den Shading-Modus **Material Preview** oder **Rendered**. |
| **Flächen färben sich nicht** | Im Edit Mode ist keine Fläche markiert oder kein Preset aktiv. | Flächen mit `A` oder `L` selektieren und sicherstellen, dass in der Liste ein Preset markiert ist. |
| **Minus-Button (`-`) gesperrt** | Das ausgewählte Preset wird noch von Flächen verwendet (Refcount > 0). | Verwenden Sie *Select*, um die Flächen zu finden, und weisen Sie ihnen ein anderes Preset zu. |
| **Exportierter Godot-Look weicht ab** | Texturen wurden nach Preset-Änderungen nicht exportiert (roter Button). | Klicken Sie im N-Panel auf den roten **Export-Button**, um die Texturen zu aktualisieren. |


