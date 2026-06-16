# SPDX-License-Identifier: GPL-3.0-or-later

"""Per-face source of truth (attribute + UV redesign 2026-06-16).

Per face there are now these native, export-friendly facts:

    lpc_color       FLOAT_COLOR  CORNER ("vertex colour") -- albedo, SOURCE
    lpc_index       INT          FACE   -- which preset (its uid), SOURCE
    lpc_uv0 / lpc_uv1 (UV maps)         -- the preset's PBR params, DERIVED
    material_index  (built-in)          -- painted? (the shared lpc slot)

`lpc_index` (the preset's stable `uid`, 0 = unpainted) is the SOURCE that
ties a face to a preset; the two UV maps carry that preset's PBR parameters
so the ONE shared material can drive Roughness/Metallic/Coat/Emission per
face (WYSIWYG) and Godot can read them through stock glTF (UV0/UV1 ->
TEXCOORD_0/1; custom attributes do NOT survive glTF, UVs do):

    lpc_uv0 = (roughness, metallic)
    lpc_uv1 = (clearcoat, emission)        # raw 0..1 per preset

The UVs are derived from the preset and flow in ONE direction (preset ->
faces). Editing a preset rescatters them onto every face carrying that uid
(`scatter_preset`); they are rebuildable from the presets at any time and are
never read back as a source.

`lpc_color` is CORNER (per face-corner), not FACE: only POINT / CORNER colour
attributes are real "vertex colours" that the glTF exporter emits as COLOR_0.
CORNER keeps the flat low-poly look. The UV values are likewise written to
every corner of a face identically, so they interpolate flat per face.

Mesh access convention (ARCHITECTURE.md): meshes in Edit Mode via their edit BMesh
(the datablock attributes are EMPTY there), everything else via
`mesh.attributes` / `mesh.uv_layers` + foreach_get/foreach_set.
"""

try:
    import bpy
    import bmesh
except ModuleNotFoundError:  # plain-python tests without Blender
    bpy = None

from . import presets as model_presets

try:
    from .. import constants
except ImportError:  # plain-python tests put the addon dir on sys.path
    import constants

# The per-face data names (the contract with the shared material's nodes and
# with the Godot import). All share the add-on namespace prefix.
COLOR_ATTRIBUTE = constants.PREFIX + "color"   # CORNER FLOAT_COLOR, albedo
INDEX_ATTRIBUTE = constants.PREFIX + "index"   # FACE INT, preset uid
UV0_NAME = constants.PREFIX + "uv0"            # (roughness, metallic)
UV1_NAME = constants.PREFIX + "uv1"            # (clearcoat, emission)

# Neutral albedo fill for freshly created corners (defined once in
# model/presets.py). Unpainted faces carry no lpc material, so this is just
# the attribute's initial value, not a rendered "default brush".
NEUTRAL_COLOR = model_presets.NEUTRAL_COLOR

UNASSIGNED = model_presets.UNASSIGNED


# --------------------------------------------------------------------------
# bpy layer
# --------------------------------------------------------------------------

if bpy is not None:

    # -- colour attribute plumbing -------------------------------------

    def ensure_color_attribute(mesh):
        """The CORNER FLOAT_COLOR `lpc_color` on an Object-Mode mesh, created
        (neutral-filled) if missing. A leftover FACE-domain attribute from an
        older layout is replaced."""
        attr = mesh.attributes.get(COLOR_ATTRIBUTE)
        if attr is not None and (
            attr.domain != "CORNER" or attr.data_type != "FLOAT_COLOR"
        ):
            mesh.attributes.remove(attr)
            attr = None
        if attr is None:
            attr = mesh.attributes.new(COLOR_ATTRIBUTE, "FLOAT_COLOR", "CORNER")
            attr.data.foreach_set("color", list(NEUTRAL_COLOR) * len(attr.data))
        return attr

    def ensure_index_attribute(mesh):
        """The FACE INT `lpc_index` on an Object-Mode mesh, created (0 =
        unpainted) if missing. A leftover non-FACE/non-INT attribute under the
        name is replaced."""
        attr = mesh.attributes.get(INDEX_ATTRIBUTE)
        if attr is not None and (
            attr.domain != "FACE" or attr.data_type != "INT"
        ):
            mesh.attributes.remove(attr)
            attr = None
        if attr is None:
            attr = mesh.attributes.new(INDEX_ATTRIBUTE, "INT", "FACE")
        return attr

    def ensure_uv_layers(mesh):
        """The two param UV maps on an Object-Mode mesh, created if missing.
        Returns (uv0, uv1)."""
        uv0 = mesh.uv_layers.get(UV0_NAME) or mesh.uv_layers.new(name=UV0_NAME)
        uv1 = mesh.uv_layers.get(UV1_NAME) or mesh.uv_layers.new(name=UV1_NAME)
        return uv0, uv1

    def _bmesh_color_layer(bm):
        """The edit BMesh's CORNER colour layer, created (neutral) if missing.
        CORNER colours live on loops."""
        layer = bm.loops.layers.float_color.get(COLOR_ATTRIBUTE)
        if layer is None:
            layer = bm.loops.layers.float_color.new(COLOR_ATTRIBUTE)
            for face in bm.faces:
                for loop in face.loops:
                    loop[layer] = NEUTRAL_COLOR
        return layer

    def _bmesh_index_layer(bm):
        layer = bm.faces.layers.int.get(INDEX_ATTRIBUTE)
        if layer is None:
            layer = bm.faces.layers.int.new(INDEX_ATTRIBUTE)
        return layer

    def _bmesh_uv_layers(bm):
        u0 = bm.loops.layers.uv.get(UV0_NAME) or bm.loops.layers.uv.new(UV0_NAME)
        u1 = bm.loops.layers.uv.get(UV1_NAME) or bm.loops.layers.uv.new(UV1_NAME)
        return u0, u1

    def face_color(face, color_layer):
        """A face's albedo as RGB -- read from its first corner (all corners
        of a painted face share one colour)."""
        for loop in face.loops:
            return tuple(loop[color_layer][:3])
        return NEUTRAL_COLOR[:3]

    # -- assign (colour + index + UV params + slot, atomically) ---------

    def assign_selected_faces(mesh, rgb, uid, uv0, uv1, slot_index):
        """Paint the SELECTED faces of an Edit-Mode mesh in one step: every
        corner's colour, the face's preset `uid`, the param UVs (`uv0` =
        (R,M), `uv1` = (C,E)) on every corner, and the face's `material_index`
        (the shared lpc slot). Returns the number of painted faces."""
        bm = bmesh.from_edit_mesh(mesh)
        clayer = _bmesh_color_layer(bm)
        ilayer = _bmesh_index_layer(bm)
        u0, u1 = _bmesh_uv_layers(bm)
        color = (*rgb, 1.0)
        painted = 0
        for face in bm.faces:
            if face.select:
                for loop in face.loops:
                    loop[clayer] = color
                    loop[u0].uv = uv0
                    loop[u1].uv = uv1
                face[ilayer] = uid
                face.material_index = slot_index
                painted += 1
        if painted:
            bmesh.update_edit_mesh(mesh)
        return painted

    def assign_whole_mesh(mesh, rgb, uid, uv0, uv1, slot_index):
        """Paint every face of an Object-Mode mesh: all corners `rgb`, every
        face's `uid`, the param UVs on every corner, all faces bound to
        `slot_index`."""
        cattr = ensure_color_attribute(mesh)
        iattr = ensure_index_attribute(mesh)
        l0, l1 = ensure_uv_layers(mesh)

        nloops = len(cattr.data)
        npoly = len(mesh.polygons)
        cattr.data.foreach_set("color", [*rgb, 1.0] * nloops)
        iattr.data.foreach_set("value", [uid] * npoly)
        l0.data.foreach_set("uv", list(uv0) * nloops)
        l1.data.foreach_set("uv", list(uv1) * nloops)
        mesh.polygons.foreach_set("material_index", [slot_index] * npoly)
        mesh.update()

    # -- scatter: push a preset's params onto every face carrying its uid ---

    def scatter_preset(uid, uv0, uv1):
        """Rewrite the param UVs (`uv0`=(R,M), `uv1`=(C,E)) on every face that
        carries `uid`, across ALL meshes (Edit Mode via BMesh, Object Mode via
        attribute data). One-directional: preset -> faces. Called from the
        preset value-change callback so an edit propagates to every face using
        the preset."""
        if uid == UNASSIGNED:
            return
        for mesh in bpy.data.meshes:
            if mesh.is_editmode:
                _scatter_edit(mesh, uid, uv0, uv1)
            else:
                _scatter_object(mesh, uid, uv0, uv1)

    def _scatter_edit(mesh, uid, uv0, uv1):
        bm = bmesh.from_edit_mesh(mesh)
        ilayer = bm.faces.layers.int.get(INDEX_ATTRIBUTE)
        u0 = bm.loops.layers.uv.get(UV0_NAME)
        u1 = bm.loops.layers.uv.get(UV1_NAME)
        if ilayer is None or u0 is None or u1 is None:
            return
        changed = False
        for face in bm.faces:
            if face[ilayer] == uid:
                for loop in face.loops:
                    loop[u0].uv = uv0
                    loop[u1].uv = uv1
                changed = True
        if changed:
            bmesh.update_edit_mesh(mesh)

    def _scatter_object(mesh, uid, uv0, uv1):
        iattr = mesh.attributes.get(INDEX_ATTRIBUTE)
        l0 = mesh.uv_layers.get(UV0_NAME)
        l1 = mesh.uv_layers.get(UV1_NAME)
        if iattr is None or l0 is None or l1 is None:
            return
        npoly = len(mesh.polygons)
        indices = [0] * npoly
        iattr.data.foreach_get("value", indices)
        if uid not in indices:
            return
        nloops = len(mesh.loops)
        b0 = [0.0] * (2 * nloops)
        b1 = [0.0] * (2 * nloops)
        l0.data.foreach_get("uv", b0)
        l1.data.foreach_get("uv", b1)
        starts = [0] * npoly
        totals = [0] * npoly
        mesh.polygons.foreach_get("loop_start", starts)
        mesh.polygons.foreach_get("loop_total", totals)
        for p in range(npoly):
            if indices[p] != uid:
                continue
            for li in range(starts[p], starts[p] + totals[p]):
                b0[2 * li], b0[2 * li + 1] = uv0
                b1[2 * li], b1[2 * li + 1] = uv1
        l0.data.foreach_set("uv", b0)
        l1.data.foreach_set("uv", b1)
        mesh.update()

    # -- UV map order (Godot maps TEXCOORD_0/1 -> UV/UV2 by order) ------

    def param_uvs_status(mesh):
        """Presence + order of the param UV maps, name-only (safe in any mode):
        'absent'     -- neither lpc UV map present
        'incomplete' -- only one of the two present
        'misordered' -- both present but not the leading two layers (so they
                        would NOT import as TEXCOORD_0/1 = UV/UV2 in Godot)
        'ok'         -- lpc_uv0, lpc_uv1 are exactly the first two layers
        Whether the mesh is actually painted is the caller's call (a non-lpc
        mesh is simply 'absent')."""
        names = [layer.name for layer in mesh.uv_layers]
        has0, has1 = UV0_NAME in names, UV1_NAME in names
        if not has0 and not has1:
            return "absent"
        if not (has0 and has1):
            return "incomplete"
        if names[:2] == [UV0_NAME, UV1_NAME]:
            return "ok"
        return "misordered"

    def reorder_param_uvs_first(mesh):
        """Move lpc_uv0 / lpc_uv1 to the front of the mesh's uv layers. UV
        layers have no move API, so rebuild the collection in the desired
        order, preserving each layer's data and its active-render flag.
        Returns True if the order changed. OBJECT MODE only (edit-mode uv data
        is not reachable via foreach)."""
        layers = mesh.uv_layers
        current = [layer.name for layer in layers]
        leading = [n for n in (UV0_NAME, UV1_NAME) if n in current]
        if not leading:
            return False
        desired = leading + [n for n in current if n not in leading]
        if desired == current:
            return False

        nloops = len(mesh.loops)
        data = {}
        active_render = None
        for layer in layers:
            buf = [0.0] * (2 * nloops)
            layer.data.foreach_get("uv", buf)
            data[layer.name] = buf
            if layer.active_render:
                active_render = layer.name

        while len(layers) > 0:
            layers.remove(layers[0])
        for name in desired:
            new = layers.new(name=name, do_init=False)
            new.data.foreach_set("uv", data[name])
        if active_render is not None:
            restored = layers.get(active_render)
            if restored is not None:
                restored.active_render = True
        mesh.update()
        return True

    # -- refcount source: which preset uid each face carries ------------

    def iter_face_indices_per_mesh():
        """Per-face preset uid, one list per mesh -- the input for the lazy
        preset refcounts (decision #4). Unpainted faces yield 0."""
        for mesh in bpy.data.meshes:
            if mesh.is_editmode:
                bm = bmesh.from_edit_mesh(mesh)
                ilayer = bm.faces.layers.int.get(INDEX_ATTRIBUTE)
                if ilayer is None:
                    yield [UNASSIGNED] * len(bm.faces)
                else:
                    yield [f[ilayer] for f in bm.faces]
            else:
                iattr = mesh.attributes.get(INDEX_ATTRIBUTE)
                npoly = len(mesh.polygons)
                if iattr is None:
                    yield [UNASSIGNED] * npoly
                else:
                    buffer = [0] * npoly
                    iattr.data.foreach_get("value", buffer)
                    yield buffer
