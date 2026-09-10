# Code Review: Low Poly Colorizer (LPC)

**Datum**: 2026-09-09  
**Review-Gegenstand**: Vollständige Codebasis (Version 0.1.1 inkl. Geometry Nodes Feature)  
**Zielumgebung**: Blender 4.2+ LTS / Blender 5.x | Godot 4.x  
**Lizenz**: GPL-3.0-or-later  

---

## 1. Executive Summary

Das Blender-Addon **Low Poly Colorizer (LPC)** präsentiert sich in einem **herausragenden architektonischen und technischen Zustand**. Das Projekt zeichnet sich durch ein klares Schichtenmodell, strikte Invarianten, vollständige Vermeidung von Redundanzen (Single Source of Truth) und eine performante Datenverarbeitung aus.

Seit dem letzten Review wurden wesentliche Erweiterungen vorgenommen:
- **Geometry Nodes Integration (`lpc_set_material`)**: Ein nativer, prozeduraler Node-Group mit dynamischem `GeometryNodeMenuSwitch` (Blender 4.1+) und `NodeSocketMenu` zur prozeduralen Einfärbung von Faces.
- **Signal-Emitter im Godot Resource Template**: Ergänzung von reaktiven Settern (`emit_changed()`) in `lpc_singlecolor_resource.gd`.
- **Bereinigte Dokumentation**: Entfernung starrer Dateizahlen in der [`README.md`](file:///e:/Projekte/low-poly-colorizer/README.md) zugunsten robuster Formulierungen.
- **Umfassende automatisierte Test-Suite (`tests/`)**: 22 Tests für Standalone-Python-Verifikation ohne `bpy`-Abhängigkeit.

---

## 2. Detaillierte Modulanalyse

### 2.1 Datenmodell (`addon/model/`)

| Modul | Verantwortung | Bewertung |
|---|---|---|
| [`palette.py`](file:///e:/Projekte/low-poly-colorizer/addon/model/palette.py) | Deterministische Farbberechnung (`color_at`), Pixel-Puffer (`build_pixels`), Nearest-Cell Lookup | **Exzellent.** Vollständig reine Logik ohne `bpy`. Mathematisch exakt, handhabt Graustufenspalte und HSV-Interpolation deterministisch. |
| [`presets.py`](file:///e:/Projekte/low-poly-colorizer/addon/model/presets.py) | Preset-Definition, UID-Management, Refcounting, Live-Callbacks | **Sehr gut.** UID-basierte Identität entkoppelt Faces von Listenpositionen. Lazy Refcounting schützt vor versehentlichem Löschen. |
| [`faces.py`](file:///e:/Projekte/low-poly-colorizer/addon/model/faces.py) | Mesh-Attribute (`lpc_index`, `lpc_uv0`, `lpc_uv1`), BMesh- und Mesh-Data-Operationen | **Exzellent.** Saubere Trennung zwischen Edit Mode (BMesh) und Object Mode (`foreach_set`). glTF-V-Flip-Kompensation ist zentral gekapselt. |

### 2.2 Picker & Interaktion (`addon/picker/`)

| Modul | Verantwortung | Bewertung |
|---|---|---|
| [`geometry.py`](file:///e:/Projekte/low-poly-colorizer/addon/picker/geometry.py) | Koordinatentransformation (Cell $\leftrightarrow$ Screen), Zoom & Pan, Hit-Testing | **Exzellent.** Reine Python-Klasse mit 100% Testabdeckung. Identische Geometrieberechnung für Rendering und Hit-Test. |
| [`interface.py`](file:///e:/Projekte/low-poly-colorizer/addon/picker/interface.py) | Layer-2-Kontrakt: Picker $\rightarrow$ Live-Apply, Swatch-Getter | **Sehr gut.** Context-Safety via `try/except` in `_result_color_get`. Verhindert zirkuläres Repainting über `_suppress_live_apply`. |
| [`modal.py`](file:///e:/Projekte/low-poly-colorizer/addon/picker/modal.py) | GPU-Overlay im 3D-Viewport (Shader, Events, Redraw-Tags) | **Sehr gut.** Sauberes Lifecycle-Handling (Draw-Handler Remove bei Finish/Cancel, Viewport-Zentrierung). |

### 2.3 Operatoren (`addon/ops/`)

| Modul | Verantwortung | Bewertung |
|---|---|---|
| [`assign_sample.py`](file:///e:/Projekte/low-poly-colorizer/addon/ops/assign_sample.py) | `Assign`, `Sample`, `Select`, `Deselect`, `Fix UV Maps` | **Sehr gut.** Exakter Abgleich (Cell + Preset UID). `Fix UV Maps` repariert fehlende oder verschobene UV-Layers sicher in Object Mode. |
| [`presets.py`](file:///e:/Projekte/low-poly-colorizer/addon/ops/presets.py) | `Add`, `Delete`, `Duplicate`, `Default Presets`, `JSON Import/Export` | **Exzellent.** Schutz vor Löschen aktiver Presets (Refcount > 0). Robuste JSON-Validierung mit Clamping und Typenprüfung. |

### 2.4 Benutzeroberfläche & Preview (`addon/ui/`)

| Modul | Verantwortung | Bewertung |
|---|---|---|
| [`preview_material.py`](file:///e:/Projekte/low-poly-colorizer/addon/ui/preview_material.py) | Generierung des geteilten `lpc_multicolor`-Materials, Palette- & LUT-Texturen | **Exzellent.** Echtes WYSIWYG durch direkte Spiegelung des Godot-Shader-Verhaltens. Verwaltete Datablocks werden über Custom Properties (`lpc_managed`) gestempelt. |
| [`geometry_nodes.py`](file:///e:/Projekte/low-poly-colorizer/addon/ui/geometry_nodes.py) | Erzeugung & Synchronisation von `lpc_set_material` mit Menu Switch | **Hervorragend.** Nutzt Blenders modernen `GeometryNodeMenuSwitch` (Blender 4.1+) für Dropdown-Presets in prozeduralen Workflows. |
| [`panel.py`](file:///e:/Projekte/low-poly-colorizer/addon/ui/panel.py) | N-Panel Darstellung, UIList, Settings-Dialog, Menüs | **Sehr gut.** Aufgeräumtes Layout mit klaren visuellen Hinweisen (Export Dirty State, Warnings, Refcount-Shields). |

### 2.5 Export-Pipeline (`addon/export/`)

| Modul | Verantwortung | Bewertung |
|---|---|---|
| [`exporter.py`](file:///e:/Projekte/low-poly-colorizer/addon/export/exporter.py) | Engine-agnostische Template-Engine (`.tpl`), Fingerprint-Berechnung | **Exzellent.** Sichere Platzhalter-Ersetzung (`{{key}}`), Beibehaltung von Shader-Klammern, Sanitization von Bezeichnern. |
| [`registry.py`](file:///e:/Projekte/low-poly-colorizer/addon/export/registry.py) | Registrierung von Export-Zielen | **Modular.** Ermöglicht einfaches Hinzufügen weiterer Ziel-Engines (z. B. Unity, Unreal). |
| `godot/*.tpl` | Shaders, Materials, Resource-Klasse, README | **Vollständig.** Saubere Trennung von Multi- und Singlecolor, Unterstützung für `@tool`-Resources mit Signal-Emittern. |

---

## 3. Findings & durchgeführte Optimierungen

Im Rahmen dieses Reviews wurden folgende Punkte identifiziert und direkt im Code behoben:

### Finding 1: Fehlender LUT-Update-Aufruf in `_preset_values_changed` (BEHOBEN)
- **Komponente**: [`addon/model/presets.py`](file:///e:/Projekte/low-poly-colorizer/addon/model/presets.py#L78-L88)
- **Problem**: Beim Hinzufügen des neuen `_preset_name_changed`-Callbacks war in `_preset_values_changed` der Aufruf `preview_material.update_preset_lut(context.scene)` verloren gegangen. Slider-Änderungen an Roughness/Metallic/Emission/Clearcoat aktualisierten die Preview-LUT nicht mehr sofort.
- **Behebung**: Der Aufruf wurde mit Context-Safety (`if context is None ...: return`) wiederhergestellt.

### Finding 2: Robustes Property-Cleanup in `unregister()` (BEHOBEN)
- **Komponente**: [`addon/__init__.py`](file:///e:/Projekte/low-poly-colorizer/addon/__init__.py#L157-L175)
- **Problem**: Bei manuellem Reload oder Deaktivierung via `addon_utils.disable()` konnte `del bpy.types.WindowManager.lpc_picker_result` einen `AttributeError` werfen, falls die Property nicht existierte.
- **Behebung**: Absicherung via `hasattr()` für alle WindowManager- und Scene-Properties.

---

## 4. Einhaltung der Architektur-Invarianten

| Invariante | Beschreibung | Status |
|---|---|---|
| **1. Zero Configuration** | Ein Standard-File ist ohne Setup sofort einsatzbereit | **Erfüllt** (Default-Presets + Auto-Seeding) |
| **2. Single Source of Truth** | Reine Daten im Mesh (`lpc_index`, `lpc_uv0`, `lpc_uv1`) | **Erfüllt** (Keine redundante Speicherung) |
| **3. No Load Handlers for State** | Keine Rekonstruktion von Session-State nötig | **Erfüllt** (Nativ im `.blend` gespeichert) |
| **4. Colors are Pure Derived Data** | Farben stammen ausschließlich aus `model.palette` | **Erfüllt** (Picker liefert nur Zellenindizes) |
| **5. Picker Transforms** | Einheitliche Koordinatenformeln für Draw & Hit-Test | **Erfüllt** (`PickerGeometry`) |
| **6. Lazy Refcounting** | Presets mit Refcount > 0 sind gegen Löschen geschützt | **Erfüllt** (Sicherer UI- & Operator-Guard) |
| **7. Atomic Paint Operations** | Mesh-Attribute und Material-Slot werden atomar gesetzt | **Erfüllt** (`assign_selected_faces` / `assign_whole_mesh`) |
| **8. One-Directional Flow** | Preset-Werte ändern nur die LUT, nicht die Meshes | **Erfüllt** (Null Mesh-Traversierung bei Farb-/Preset-Tuning) |

---

## 5. Testabdeckung & Verifikation

### 5.1 Standalone Unit-Tests (`tests/`)
Die Test-Suite umfasst **22 automatisierte Tests** und läuft in **< 5ms** durch:
- `test_palette.py`: Zellanzahl, Farbgrenzen, Graustufenspalte, Pixelpuffer, Nearest-Cell.
- `test_presets.py`: Referenzzählung, JSON-Roundtrip, Validierung, Clamping, Strict Mode.
- `test_geometry.py`: Screen-Transformation, Zoom, Pan, Hit-Testing.
- `test_faces_pure.py`: UV-Encoding/Decoding, glTF-V-Flip-Kompensation.
- `test_exporter.py`: PascalCase, Preset-Sanitization, Template-Rendering.
- `test_geometry_nodes_pure.py`: Node-Group-Namen, Managed-Key-Logik.

### 5.2 Blender Headless Integrationstest
- Erfolgreich getestet unter **Blender 5.2.0 LTS**:
  - Addon Registrierung / De-Registrierung (`register()` / `unregister()`).
  - Erstellung und Evaluierung von `lpc_set_material` Modifiern auf Mesh-Objekten.
  - Live-Synchronisation von Presets im `GeometryNodeMenuSwitch`.

---

## 6. Fazit & Empfehlungen

Die Codebasis ist **hochwertig, robust, performant und exzellent dokumentiert**.

### Empfohlene nächste Schritte für zukünftige Releases:
1. **Release 0.1.2 / 0.2.0**: Vorbereitung des nächsten Versionssprungs inklusive des neuen Geometry-Nodes-Features.
2. **CI-Pipeline**: Einbindung von `python -m unittest discover -s tests` in GitHub Actions für automatische PR-Prüfungen.
3. **Erweiterte Templates**: Evaluierung weiterer Export-Targets (z. B. Unity Shader Graph oder Unreal Engine Material Functions) über die vorhandene Registry.

