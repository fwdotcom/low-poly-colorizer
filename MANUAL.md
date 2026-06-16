# Low Poly Colorizer – Handbuch

Ein Blender-Add-on zum Bemalen von Mesh-**Faces** mit PBR-Materialwerten
(Farbe, Roughness, Metallic, Emission, Clearcoat) über eine generierte
Farbpalette – mit sofortiger WYSIWYG-Vorschau im Viewport und einem
Export für Game-Engines (aktuell Godot).

> Dieses Dokument richtet sich an **Anwender**. Die technische Architektur
> (Datenmodell, Invarianten) steht in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Inhalt

1. [Grundidee](#1-grundidee)
2. [Installation](#2-installation)
3. [Das Bedienfeld im Überblick](#3-das-bedienfeld-im-überblick)
4. [Schnellstart](#4-schnellstart)
5. [Die Palette & der Picker](#5-die-palette--der-picker)
6. [Bemalen im Detail](#6-bemalen-im-detail)
7. [Presets verwalten](#7-presets-verwalten)
8. [Einstellungen-Dialog](#8-einstellungen-dialog)
9. [Unbemalte Faces & eigene Materialien](#9-unbemalte-faces--eigene-materialien)
10. [Export](#10-export)
11. [Godot-Integration](#11-godot-integration)
12. [Fix UV Maps](#12-fix-uv-maps)
13. [Tipps & Stolperfallen](#13-tipps--stolperfallen)
14. [Problembehebung](#14-problembehebung)

---

## 1. Grundidee

Statt für jede Farbvariante ein eigenes Material zu bauen, malst du **pro
Face** zwei Dinge:

- **Farbe (Albedo)** – kommt aus einer Zelle der generierten Palette und wird
  als **Vertex Color** auf die Face geschrieben. So kann *eine* Face jede
  beliebige Farbe tragen.
- **Material-Look (Preset)** – Roughness, Metallic, Emission und Clearcoat,
  zusammengefasst in einem benannten **Preset**. Mehrere Faces (mit
  unterschiedlichen Farben) können dasselbe Preset nutzen.

Im Hintergrund teilen sich alle bemalten Faces **ein einziges Material**. Die
Per-Face-Unterschiede stecken in den Mesh-Daten (Vertex Color + zwei
UV-Maps), nicht in vielen Materialien. Das hält die Szene schlank und sorgt
beim Export für **eine** Surface statt vieler.

„Bemalt" heißt: Die Face trägt ein Preset. Faces, die du nie bemalt hast,
behalten Blenders schlichten Standard-Look.

---

## 2. Installation

Voraussetzung: **Blender 4.2 oder neuer** (das Add-on ist eine Extension).

1. Das Add-on als ZIP bauen bzw. besorgen
   (`python build_addon.py` legt `dist/low-poly-colorizer-<version>-<branch>.zip` an).
2. In Blender: **Edit ▸ Preferences ▸ Add-ons ▸ Install from Disk…** und die
   ZIP wählen (oder die ZIP per Drag & Drop ins Blender-Fenster ziehen).
3. Das Add-on aktivieren.
4. Im 3D-Viewport die **N-Leiste** öffnen (Taste `N`) und den Reiter **LPC**
   wählen.

Eine frische Datei wird automatisch mit einem Satz Standard-Presets
befüllt, damit du sofort loslegen kannst.

---

## 3. Das Bedienfeld im Überblick

Der gesamte Workflow lebt im N-Panel **LPC ▸ LPC Palette**:

```
┌─ LPC Palette ─────────────────────────────┐
│ [Farbfeld] [X] [Y]            [🎨 Picker]  │  ← aktuelle Farbe + Zelle
│ 3 faces in 1 object selected               │  ← Auswahl-Hinweis
│                                            │
│ ┌ Preset-Liste ─────────────┐  [+]         │
│ │ Solid                  0   │  [-]         │  ← Presets, refcount rechts
│ │ Metallic               12  │  [▾ Menü]    │
│ │ Emission               0   │              │
│ └───────────────────────────┘              │
│                                            │
│ Roughness  ▓▓▓▓▓░░░░                        │  ← Werte des aktiven Presets
│ Metallic   ░░░░░░░░░                        │
│ Emission   ░░░░░░░░░                        │
│ Clearcoat  ░░░░░░░░░                        │
│                                            │
│ [👁 Sample]            [🖌 Assign]          │
│ [Select]              [Deselect]           │  ← nur im Edit Mode
│                                            │
│ Export   [Godot Materials ▾]      [⤓]      │  ← Footer
│ [Settings…]                                │
└────────────────────────────────────────────┘
```

- **Farbfeld / X / Y / Picker** – die aktuell gewählte Palettenzelle. Das
  Farbfeld zeigt ihre Farbe, `X`/`Y` die Spalte/Zeile (direkt editierbar),
  der Picker-Knopf öffnet die Palette als Overlay.
- **Auswahl-Hinweis** – was ein Pinselstrich treffen würde (Anzahl Faces bzw.
  Objekte). Warnt auch, wenn kein Preset gewählt ist.
- **Preset-Liste** – deine Presets. Die Zahl rechts ist der **Refcount**
  (wie viele Faces das Preset nutzen). `+`/`-` legen an/löschen, das
  `▾`-Menü hält Duplizieren, JSON-Im/Export und Standard-Presets.
- **Werte-Slider** – Roughness/Metallic/Emission/Clearcoat des **aktiven**
  Presets. Änderungen wirken sofort auf alle Faces, die das Preset nutzen.
- **Sample / Assign** – Werkzeug-Buttons (siehe unten).
- **Select / Deselect** – nur im Edit Mode sichtbar.
- **Footer** – Export-Auswahl + Button und der Einstellungen-Dialog.

---

## 4. Schnellstart

So bemalst du in unter einer Minute deine ersten Faces:

1. Wähle ein Objekt aus (Object Mode) **oder** gehe in den Edit Mode und
   selektiere ein paar Faces.
2. Wähle in der **Preset-Liste** ein Preset (z. B. „Solid").
3. Klicke auf den **🎨 Picker** rechts neben dem Farbfeld. Die Palette
   erscheint als Overlay im Viewport.
4. **Klicke auf eine Farbzelle.** Der Picker schließt sich, und die
   Auswahl wird sofort bemalt (Farbe + Preset in einem Schritt).

Das war's. Die bemalten Faces zeigen die Farbe mit dem Material-Look des
Presets direkt im Viewport.

> **Live-Assign:** Ein Klick auf eine Zelle bemalt die aktuelle Auswahl
> sofort – du musst „Assign" nicht extra drücken. „Assign" brauchst du, um
> nach einer geänderten Auswahl dieselbe Farbe/Preset-Kombination erneut
> aufzutragen.

---

## 5. Die Palette & der Picker

### Der Picker (Overlay)

Ein Klick auf den 🎨-Knopf öffnet die Palette mittig im Viewport. Steuerung:

| Aktion | Ergebnis |
|--------|----------|
| **Linksklick auf eine Zelle** | wählt sie, bemalt die Auswahl sofort, schließt |
| **Mausrad** | Zoom (auf den Cursor zentriert) |
| **Mittlere Maustaste + ziehen** | verschieben (Pan) |
| **Rechtsklick / Esc / Klick außerhalb** | abbrechen (nichts ändert sich) |

Die Zelle unter dem Mauszeiger wird weiß umrandet. Das Picker-Overlay zeigt
die **echten** Farben (im Gegensatz zum kleinen Farbfeld im Panel, siehe
[Problembehebung](#14-problembehebung)).

### Aufbau der Palette

Die Palette wird vollständig aus Parametern berechnet (im
[Einstellungen-Dialog](#8-einstellungen-dialog) anpassbar):

- **Columns** – Anzahl der **Farbton**-Spalten (Hue).
- **Add Greyscale Column** – stellt links eine zusätzliche Spalte mit einem
  reinen Weiß-zu-Schwarz-Verlauf voran (Spalte `X = 0`). Die Farbton-Spalten
  beginnen dann bei `X = 1`.
- **Rows** – Anzahl der Zeilen. Die **mittlere** Zeile zeigt den Grundton
  (volle Sättigung/Helligkeit), nach oben wird Richtung Weiß, nach unten
  Richtung Schwarz gemischt.
- **Saturation / Brightness** – Sättigung/Helligkeit der mittleren Zeile.
- **Tint** – wie stark die obere Zeile Richtung Weiß geht.
- **Shade** – wie stark die untere Zeile Richtung Schwarz geht.

Die Palette selbst wird nicht in der Datei gespeichert, sondern jederzeit aus
diesen Parametern neu erzeugt. Die **Parameter** dagegen werden pro Szene im
`.blend` gespeichert.

---

## 6. Bemalen im Detail

### Object Mode vs. Edit Mode

- **Object Mode:** Ein Pinselstrich bemalt **alle** Faces der ausgewählten
  Objekte.
- **Edit Mode:** Nur die **selektierten** Faces werden bemalt.

### Die Werkzeuge

- **🖌 Assign** – trägt den aktuellen Pinsel (gewählte Farbe + aktives
  Preset) auf die Auswahl auf. Deaktiviert, wenn nichts ausgewählt ist.
- **👁 Sample** *(Edit Mode)* – „pipettiert" eine bemalte Face zurück in die
  UI: setzt das passende Preset und die nächstgelegene Palettenzelle als
  aktuellen Pinsel. Funktioniert nur bei einer Auswahl, die einheitlich
  *eine* Farbe + *ein* Preset trägt.
- **Select / Deselect** *(Edit Mode)* – wählt alle Faces, die exakt dem
  aktuellen Pinsel entsprechen (gleiche Farbe **und** gleiches Preset), zur
  Selektion hinzu bzw. ab. Praktisch, um nachträglich gezielt umzufärben.

> **Der „Pinsel"** ist immer das Paar *(gewählte Farbe, aktives Preset)*.
> Assign, Sample, Select und Deselect beziehen sich alle auf dieses Paar.

---

## 7. Presets verwalten

Ein **Preset** bündelt die vier Material-Werte unter einem Namen.

- **Anlegen** `+` – neues Preset mit neutralen Werten.
- **Löschen** `-` – nur möglich, wenn **kein** Face das Preset nutzt
  (Refcount 0). Solange es benutzt wird, ist der Button gesperrt und die
  Liste zeigt die Anzahl mit einem Schild-Symbol.
- **Umbenennen** – Doppelklick auf den Namen in der Liste.
- **Werte ändern** – die Slider unter der Liste wirken auf das **aktive**
  Preset und propagieren **sofort** auf alle Faces, die es nutzen.

Über das **`▾`-Menü** neben der Liste:

- **Duplicate** – aktives Preset kopieren.
- **Import / Export** – Presets als JSON-Datei laden/sichern (zum Teilen
  zwischen Projekten). Beim Import werden gleichnamige Presets aktualisiert,
  neue ergänzt – ein erneuter Import derselben Datei ändert nichts.
- **Load Default Presets** – die mitgelieferten Standard-Presets ergänzen
  (vorhandene gleichnamige werden auf die Standardwerte gesetzt).

---

## 8. Einstellungen-Dialog

Der **Settings…**-Knopf im Footer öffnet einen Dialog mit den selten
geänderten Werten. Änderungen wirken live; **Abbrechen** stellt den vorherigen
Zustand wieder her.

- **Grid** – `Columns`, `Rows`, `Add Greyscale Column` (Palettenraster).
- **Base Color** – `Saturation`, `Brightness` der mittleren Zeile.
- **Tint / Shade** – Mischung der oberen/unteren Zeile Richtung Weiß/Schwarz.
- **Globals** – projektweite Material-Werte:
  - **Emission Factor** – globaler Multiplikator auf die Emission jedes
    Presets (z. B. um alle leuchtenden Flächen gemeinsam heller/dunkler zu
    stellen).
  - **Clearcoat Roughness** – projektweite Rauheit der Klarlack-Schicht.

---

## 9. Unbemalte Faces & eigene Materialien

- **Unbemalte Faces** tragen kein Preset und rendern Blenders schlichten
  Standard-Look. Neu erzeugte Geometrie ist immer zunächst unbemalt.
- **Objekte mit eigenen Materialien:** Bemalst du nur einzelne Faces, bleiben
  die übrigen Faces auf ihrem ursprünglichen Material – das Add-on kapert
  keine fremden Materialien. Das Preset-Material wird nur den bemalten Faces
  zugewiesen.
- **Materiallose Objekte:** Slot 0 bleibt leer, damit unbemalte Faces den
  Standard-Look behalten; bemalte Faces wandern auf den geteilten lpc-Slot.

---

## 10. Export

Im Footer wählst du links über das Dropdown ein **Export-Templateset** (aktuell
nur **Godot Materials**, weitere Engines können ergänzt werden) und klickst
rechts auf den **Export-Knopf (⤓)**. Es öffnet sich ein Ordner-Dialog – die
Dateien werden in den gewählten Ordner geschrieben.

Für **Godot Materials** entstehen zwei Dateien:

- `lpc_shader.gdshader` – der geteilte Spatial-Shader.
- `lpc_material.tres` – das ShaderMaterial, das den Shader referenziert und
  die globalen Werte (Emission Factor, Clearcoat Roughness) setzt.

Der Export schreibt **nur** diese Dateien. Die Geometrie samt Per-Face-Daten
kommt separat über den `.blend`-Import nach Godot (siehe nächster Abschnitt).

> Meldet der Export eine **UV-Warnung**, siehe [Fix UV Maps](#12-fix-uv-maps).

---

## 11. Godot-Integration

Godot importiert das `.blend` direkt (über Blenders glTF-Export). So kommt
der Look hinüber:

1. Lege den **Export-Ordner** (mit `lpc_shader.gdshader` + `lpc_material.tres`)
   und dein **`.blend`** in dein Godot-Projekt.
2. Godot importiert das `.blend` als Szene. Alle bemalten Faces bilden **eine
   Surface** (weil sie ein gemeinsames Material teilen).
3. Wähle im importierten Mesh die Surface und setze ihr **Material Override**
   auf `lpc_material.tres`.

Was wie transportiert wird:

- **Albedo** reist als Vertex Color (`COLOR_0`).
- **Roughness/Metallic** liegen in der ersten UV-Map (`lpc_uv0` → `UV`).
- **Clearcoat / Emission** liegen in der zweiten UV-Map (`lpc_uv1` → `UV2`).
- Der Shader setzt daraus den Look zusammen; Emission ist **pro Face**
  albedo-getönt (`EMISSION = Farbe × Emission × Emission Factor`).

> **Wichtig – UV-Reihenfolge:** Damit die Parameter korrekt ankommen, müssen
> `lpc_uv0` und `lpc_uv1` die **ersten beiden** UV-Maps des Meshes sein. Bei
> frisch bemalten Meshes ist das automatisch der Fall. Hattest du auf einer
> Mesh schon eigene UV-Maps, kann die Reihenfolge kippen – dann hilft
> **Fix UV Maps**.

---

## 12. Fix UV Maps

Wenn eine bemalte Mesh ihre lpc-UV-Maps nicht an den ersten beiden Plätzen
hat (oder eine fehlt), erscheint im Footer eine Warnbox **„UV maps need
fixing"** mit einem **Fix-Button**. Der Export warnt zusätzlich.

**Wann passiert das?** Praktisch nur, wenn du eine Mesh bemalst, die **schon
vorher eigene UV-Maps** hatte – die lpc-Maps hängen sich dann hinten an.

**Was tut „Fix UV Maps"?** Über alle bemalten Meshes:

1. fehlende lpc-UV-Maps neu anlegen,
2. sie an die ersten beiden Plätze sortieren,
3. die Preset-Werte wieder hineinschreiben.

Deine eigenen UV-Maps bleiben erhalten – sie rücken nur hinter die lpc-Maps.

> **Hinweis:** Fix UV Maps läuft nur im **Object Mode** (das Umsortieren von
> UV-Maps ist im Edit Mode technisch nicht möglich). Wechsle ggf. kurz in den
> Object Mode und klicke erneut.

---

## 13. Tipps & Stolperfallen

- **Erst Preset wählen, dann picken.** Ein Pick ohne aktives Preset bemalt
  nichts – der Hinweis „No preset selected" warnt davor.
- **Live-Assign nutzen:** Auswahl ändern und einfach erneut eine Zelle picken
  ist oft schneller als der Assign-Knopf.
- **Ein Preset, viele Farben:** Du brauchst nicht pro Farbe ein Preset. Nimm
  z. B. ein „Solid"-Preset und picke unterschiedliche Palettenfarben.
- **Preset-Werte zentral ändern:** Verschiebst du einen Slider, ändern sich
  *alle* Faces dieses Presets gleichzeitig – ideal, um den Look projektweit
  nachzujustieren.
- **Greyscale-Spalte:** Mit aktivierter Grauwertspalte ist `X = 0` immer der
  Weiß-Schwarz-Verlauf; die Farbtöne starten bei `X = 1`.

---

## 14. Problembehebung

**Das kleine Farbfeld im Panel sieht „falsch" / zu dunkel aus.**
Blender zeichnet UI-Farbfelder durch die Ansichts-Transformation (standardmäßig
AgX), daher wirkt z. B. lineares Weiß grau. Der gespeicherte Wert ist korrekt
(Hover zeigt ihn), und das **Picker-Overlay** zeigt die echten Farben.

**„Assign" ist ausgegraut.**
Es ist nichts ausgewählt. Wähle ein Objekt (Object Mode) oder Faces
(Edit Mode).

**„Sample" ist ausgegraut.**
Sample braucht eine **einheitliche** Auswahl: genau eine bemalte Farbe + ein
Preset. Bei gemischter Auswahl bleibt der Knopf gesperrt.

**Ein Preset lässt sich nicht löschen.**
Es wird noch von Faces genutzt (Refcount > 0). Färbe diese Faces erst um
(anderes Preset zuweisen), dann ist das Löschen frei.

**In Godot stimmen Roughness/Metallic/Clearcoat/Emission nicht.**
Mit hoher Wahrscheinlichkeit ist die UV-Reihenfolge verrutscht – führe
**Fix UV Maps** im Object Mode aus und exportiere/importiere erneut. Prüfe
außerdem, dass das **Material Override** der Surface auf `lpc_material.tres`
gesetzt ist.

**Frisch hinzugefügte Geometrie ist „nicht bemalt".**
Das ist beabsichtigt: Neue Faces tragen kein Preset und rendern den
Standard-Look, bis du sie bemalst.

---

*Lizenzen: siehe [LICENSE.md](LICENSE.md).*
