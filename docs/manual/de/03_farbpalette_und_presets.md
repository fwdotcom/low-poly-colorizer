# Farbpalette und PBR-Presets

In Low Poly Colorizer werden Farbgebung (Albedo) und Oberflächenbeschaffenheit (PBR-Werte) getrennt gesteuert und erst beim Rendern bzw. Shading miteinander kombiniert.

---

## Der interaktive Modal Palette Picker

Klicken Sie im N-Panel auf den **Paletten-Button** (Farbwähler), öffnet sich die Farbpalette als hardwarebeschleunigtes GPU-Overlay direkt im 3D-Viewport.

![Der interaktive GPU-Palette-Picker](images/palette_picker_annotated.png)

| Bereich | Beschreibung |
|:---:|:---|
| **Ⓐ** | **Graustufenspalte (Spalte 0)**: Reine Graustufen von Schwarz (oben) bis Weiß (unten) für monochrome Flächen oder neutrale Schattierungen. |
| **Ⓑ** | **Farbton-Spektrum (Spalten 1–16)**: Der vollständige HSV-Farbkreis von Rot über Gelb, Grün, Cyan, Blau bis Magenta horizontal aufgefächert. |
| **Ⓒ** | **Helligkeits- & Sättigungsverlauf (Zeilen 0–7)**: Vertikale Abstufung von tiefdunklen Schatten (oben) über satte Farben bis hin zu hellen Pastelltönen (unten). |
| **Ⓓ** | **Aktive Zelle & Selektionsrahmen**: Zweifarbiger Markierungsrahmen um die momentan gewählte Palettenzelle $(X, Y)$ mit direkter Zuweisung per Klick. |

### Steuerung im Picker-Overlay

* **Auswählen & Zuweisen**: Klicken Sie mit der **linken Maustaste** auf die gewünschte Zelle. Die Zelle wird gespeichert, der aktuellen Auswahl zugewiesen und das Overlay schließt sich.
* **Zoomen**: Drehen Sie das **Mausrad**, um stufenlos in die Palette hinein- oder herauszuzoomen (0.25× bis 4.0×).
* **Verschieben (Pan)**: Halten Sie die **mittlere Maustaste (MMB)** gedrückt und ziehen Sie die Maus, um das Palettenfenster im Viewport zu bewegen.
* **Abbrechen**: Mit **Rechtsklick**, **Escape** oder einem Linksklick außerhalb der Palette schließen Sie das Overlay, ohne die bisherige Farbauswahl zu verändern.

---

## PBR-Presets: Materialeigenschaften steuern

Jedes Preset bündelt vier standardisierte physikalische Materialparameter:

* **Roughness (0.0 – 1.0)**: Oberflächen-Rauheit. Niedrige Werte erzeugen spiegelnde Oberflächen, hohe Werte ein mattes Finish.
* **Metallic (0.0 – 1.0)**: Metallischer Anteil. 0.0 entspricht Dielektrika (Plastik, Holz, Stein), 1.0 echtem Metall.
* **Emission (0.0 – 10.0)**: Eigenleuchtkraft der Fläche. Die Albedo-Farbe der Palettenzelle wird als Leuchtfarbe herangezogen.
* **Clearcoat (0.0 – 1.0)**: Klarlack-Schicht (z. B. für Autolacke, polierte Oberflächen oder nasse Optiken).

> [!IMPORTANT]
> **Live-Scatter-Prinzip:** Die Preset-Regler modifizieren keine individuellen Meshes, sondern die zentrale Lookup-Tabelle. Ändern Sie beispielsweise die *Roughness* des Presets *Solid*, aktualisieren sich **augenblicklich alle bereits bemalten Flächen im gesamten Projekt**.

### Preset-Zusatzfunktionen (Menü `▾`)

* **Duplicate**: Erstellt eine 1:1-Kopie des aktiven Presets, um rasch Variationen zu erzeugen.
* **Import / Export JSON**: Ermöglicht das Speichern und Laden von Preset-Sets als handliche Textdateien – ideal zur Wiederverwendung in anderen Projekten.
* **Load Default Presets**: Stellt die vier mitgelieferten Werks-Presets (*Solid*, *Metallic*, *Clearcoat*, *Emission*) wieder her.

---

## Globale Einstellungen (*Settings…*)

Über den Button **Settings…** im N-Panel öffnen Sie das Konfigurationsfenster für projektspezifische Paletten- und Shader-Parameter:

![Die globalen LPC-Einstellungen](images/settings_annotated.png)

| Bereich | Beschreibung |
|:---:|:---|
| **①** | **Grid**: Spalten- (*Columns*) und Zeilenanzahl (*Rows*) des Rasters sowie Umschalter für die monochrome Graustufenspalte (*Add Greyscale Column*). |
| **②** | **Base Color**: Grundsättigung (*Saturation*) und Basishelligkeit (*Brightness*) aller Farbtöne im Farbkreis. |
| **③** | **Tint / Shade**: Intensität der vertikalen Abstufungen (Aufhellung durch *Tint*, Abdunklung durch *Shade*). |
| **④** | **Globals**: Projektweite Parameter wie der globale Emissions-Skalierungsfaktor (*Emission Factor*) und die Grund-Rauheit für Klarlack (*Clearcoat Roughness*). |

