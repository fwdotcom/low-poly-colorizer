# SPDX-License-Identifier: GPL-3.0-or-later

"""The one shared preview material (Invariant 7, redesign 2026-06-16).

The whole project shares ONE Godot-compatible Principled material. Per-face
variation is driven entirely by mesh data the stock glTF export carries:

    lpc_color (CORNER vertex colour) -> Base Color AND Emission Color
    lpc_uv0.x / .y                   -> Roughness / Metallic
    lpc_uv1.x / .y                   -> Coat Weight / (raw) Emission
    global emission_factor           -> multiplies the emission
    global clearcoat_roughness       -> Coat Roughness

So a painted face's PBR look comes from its param UVs (written by paint /
scatter, model/faces.py), and editing a preset just rescatters those UVs.
There is exactly one material, so all painted faces collapse to ONE surface
in Godot (one Material Override).

There is NO default-brush material: unpainted faces carry no lpc material (an
empty slot 0 on material-less objects, or the user's own material otherwise)
and render the plain default. "Painted" means the face carries a preset uid
(lpc_index != 0); the shared material on its slot just makes that visible.

The material is "lpc-managed" via the `lpc_managed` custom prop, so
`has_real_materials` can tell an object's own materials from ours.
"""

import bpy

from .. import constants
from ..model import faces as model_faces

# The single shared material datablock name.
MATERIAL_NAME = constants.PREFIX + "material"

# Custom-prop stamp on the material we create.
_MANAGED_KEY = constants.PREFIX + "managed"

# Bumped when the node layout changes; ensure_* rebuilds older materials.
_NODES_VERSION = 6
_VERSION_KEY = constants.PREFIX + "nodes_version"

# Node names we look up later (Blender keeps node names unique per tree).
_EMISSION_FACTOR_NODE = constants.PREFIX + "emission_factor"
_COAT_ROUGHNESS_NODE = constants.PREFIX + "clearcoat_roughness"


# --------------------------------------------------------------------------
# Node helpers
# --------------------------------------------------------------------------

def _input(node, *names):
    """First existing input socket among `names` (Blender version drift:
    4.x "Coat Weight" was 3.x "Clearcoat")."""
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            return socket
    return None


def _build_nodes(material):
    """The shared Principled tree: albedo + emission colour from the
    `lpc_color` vertex colour, the scalar PBR params from the two param UV
    maps, the two globals from named value nodes."""
    tree = material.node_tree
    tree.nodes.clear()
    links = tree.links

    output = tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)
    principled = tree.nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (300, 0)
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    # Albedo (+ emission tint) from the per-face vertex colour.
    col = tree.nodes.new("ShaderNodeVertexColor")
    col.layer_name = model_faces.COLOR_ATTRIBUTE
    col.location = (-300, 200)
    links.new(col.outputs["Color"], principled.inputs["Base Color"])
    emission_color = _input(principled, "Emission Color", "Emission")
    if emission_color is not None:
        links.new(col.outputs["Color"], emission_color)

    # Roughness / Metallic from lpc_uv0.
    uv0 = tree.nodes.new("ShaderNodeUVMap")
    uv0.uv_map = model_faces.UV0_NAME
    uv0.location = (-500, -80)
    sep0 = tree.nodes.new("ShaderNodeSeparateXYZ")
    sep0.location = (-300, -80)
    links.new(uv0.outputs["UV"], sep0.inputs["Vector"])
    links.new(sep0.outputs["X"], principled.inputs["Roughness"])
    links.new(sep0.outputs["Y"], principled.inputs["Metallic"])

    # Clearcoat / Emission from lpc_uv1.
    uv1 = tree.nodes.new("ShaderNodeUVMap")
    uv1.uv_map = model_faces.UV1_NAME
    uv1.location = (-500, -320)
    sep1 = tree.nodes.new("ShaderNodeSeparateXYZ")
    sep1.location = (-300, -320)
    links.new(uv1.outputs["UV"], sep1.inputs["Vector"])
    coat = _input(principled, "Coat Weight", "Clearcoat")
    if coat is not None:
        links.new(sep1.outputs["X"], coat)

    # Emission strength = raw emission (uv1.y) * global emission factor.
    factor = tree.nodes.new("ShaderNodeValue")
    factor.name = _EMISSION_FACTOR_NODE
    factor.label = "Emission Factor"
    factor.location = (-300, -520)
    mult = tree.nodes.new("ShaderNodeMath")
    mult.operation = "MULTIPLY"
    mult.location = (0, -400)
    links.new(sep1.outputs["Y"], mult.inputs[0])
    links.new(factor.outputs["Value"], mult.inputs[1])
    strength = _input(principled, "Emission Strength")
    if strength is not None:
        links.new(mult.outputs["Value"], strength)

    # Coat roughness from a global value node.
    coat_rough_node = tree.nodes.new("ShaderNodeValue")
    coat_rough_node.name = _COAT_ROUGHNESS_NODE
    coat_rough_node.label = "Coat Roughness"
    coat_rough_node.location = (0, -640)
    coat_rough = _input(principled, "Coat Roughness", "Clearcoat Roughness")
    if coat_rough is not None:
        links.new(coat_rough_node.outputs["Value"], coat_rough)

    material[_VERSION_KEY] = _NODES_VERSION


# --------------------------------------------------------------------------
# The shared material
# --------------------------------------------------------------------------

def is_lpc_managed(material):
    return material is not None and material.get(_MANAGED_KEY) == 1


def _find_managed_material():
    """The shared lpc material if it exists -- identified by the managed stamp,
    NOT by name (a foreign datablock may squat MATERIAL_NAME). There is only
    ever one; the first managed material wins."""
    for material in bpy.data.materials:
        if is_lpc_managed(material):
            return material
    return None


def update_globals(scene):
    """Push the scene globals onto the shared material's value nodes
    (Invariant 8). No-op if the material does not exist yet."""
    material = _find_managed_material()
    if material is None or not material.use_nodes:
        return
    g = scene.lpc_globals
    tree = material.node_tree
    factor = tree.nodes.get(_EMISSION_FACTOR_NODE)
    if factor is not None:
        factor.outputs["Value"].default_value = g.emission_factor
    coat_rough = tree.nodes.get(_COAT_ROUGHNESS_NODE)
    if coat_rough is not None:
        coat_rough.outputs["Value"].default_value = g.clearcoat_roughness


def ensure_lpc_material(scene):
    """The shared material, identified by its managed stamp (NOT by name, so a
    foreign datablock squatting MATERIAL_NAME never spawns a duplicate),
    created + stamped + fake-user + globals-synced if missing or built by an
    older version. A fresh material is named MATERIAL_NAME (Blender
    auto-suffixes if that name is already taken)."""
    material = _find_managed_material()
    if material is None:
        material = bpy.data.materials.new(MATERIAL_NAME)
    material.use_nodes = True
    if material.get(_VERSION_KEY) != _NODES_VERSION:
        _build_nodes(material)
    material[_MANAGED_KEY] = 1
    material.use_fake_user = True
    update_globals(scene)
    return material


# --------------------------------------------------------------------------
# Slot management (lazy, per object) -- one shared material on a slot
# --------------------------------------------------------------------------

def has_real_materials(mesh):
    """True if the mesh has any slot holding a NON-lpc material -- the user's
    own materials, which unpainted faces keep. A mesh with only the lpc
    material (or empty slots) lets its unpainted faces fall back to slot 0."""
    return any(
        m is not None and not is_lpc_managed(m) for m in mesh.materials
    )


def mesh_is_painted(mesh):
    """True if the mesh carries the shared lpc material in any slot -- i.e. it
    has been painted by us (mode-stable, name-only signal)."""
    return any(is_lpc_managed(m) for m in mesh.materials)


def mesh_needs_uv_fix(mesh):
    """A PAINTED mesh whose param UVs are missing, incomplete, or not the
    leading two layers -- so Godot would not import them as UV/UV2. Fixed by
    the 'Fix UV Maps' operator."""
    return mesh_is_painted(mesh) and model_faces.param_uvs_status(mesh) != "ok"


def _slot_of_material(mesh, material):
    for i, m in enumerate(mesh.materials):
        if m is material:
            return i
    return -1


def ensure_lpc_slot(mesh, scene):
    """Index of the slot holding the shared lpc material on `mesh`, appending
    it if missing (lazy: an object gets the slot only when first painted)."""
    material = ensure_lpc_material(scene)
    idx = _slot_of_material(mesh, material)
    if idx == -1:
        mesh.materials.append(material)
        idx = len(mesh.materials) - 1
    return idx


def ensure_unpainted_front(obj):
    """Keep slot 0 of a material-less object EMPTY so unpainted faces
    (material_index 0, incl. new geometry) never point at the shared material
    -- they render the plain default look instead. No-op on an object with its
    own materials (unpainted faces keep the user's material there).

    Must run before the first ensure_lpc_slot on a fresh object, so the
    reserved empty slot lands at 0 and the lpc material goes to slot >= 1."""
    mesh = obj.data
    if has_real_materials(mesh):
        return
    if len(mesh.materials) == 0:
        mesh.materials.append(None)
