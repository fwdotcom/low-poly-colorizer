# SPDX-License-Identifier: GPL-3.0-or-later

"""Presets + globals (attribute + UV redesign 2026-06-16).

A **Preset** is a NAMED parameter combination (R, M, E, C). Faces reference a
preset by carrying its `uid` in the `lpc_index` face attribute; the preset's
PBR parameters are scattered onto those faces' param UV maps (model/faces.py)
so the ONE shared material can render them per face. `uid` (0 = UNASSIGNED) is
the stable identity tying a face to its preset.

Editing a preset rescatters its parameters onto every face carrying its uid
(one-directional, preset -> faces). There is one shared material for the
whole project (ui/preview_material.py), not one per preset.

Lifecycle (Invariant 6): refcounts are lazy (decision #4), computed on demand
by counting faces whose `lpc_index` is the preset's uid across all meshes.
Delete is allowed at refcount 0 only.

The pure counting logic is bpy-free and testable; only the PropertyGroup
layer below needs `bpy`.
"""

try:
    import bpy
except ModuleNotFoundError:  # plain-python tests without Blender
    bpy = None

try:
    from .. import constants
except ImportError:  # plain-python tests put the addon dir on sys.path
    import constants

# Immutable "no preset" uid sentinel. Real preset uids start at 1
# (lpc_preset_next_uid) so they never collide with it.
UNASSIGNED = 0

# Preset parameter keys + neutral defaults. The single definition of the
# parameter list: the UI sliders, the JSON logic (ops/presets.py) and the
# default-preset validation all derive from these keys.
# (No occlusion: invisible in a Principled preview. No alpha: transparency
# is a material-level property -- a per-face alpha < 1 would force the
# material out of opaque mode.)
PRESET_VALUE_KEYS = ("roughness", "metallic", "emission", "clearcoat")
PRESET_VALUE_DEFAULTS = {
    "roughness": 0.8, "metallic": 0.0, "emission": 0.0, "clearcoat": 0.0,
}

# Neutral albedo fill for a newly created lpc_color attribute (model/faces).
NEUTRAL_COLOR = (0.8, 0.8, 0.8, 1.0)


# --------------------------------------------------------------------------
# Pure logic (no bpy)
# --------------------------------------------------------------------------

def reference_counts(keys, referenced_keys):
    """Reference count per key (aligned with `keys`) from an iterable of
    referenced keys. `None` keys and unknown references are ignored --
    degrade gracefully on foreign data."""
    counts = [0] * len(keys)
    index_by_key = {k: i for i, k in enumerate(keys) if k is not None}
    for key in referenced_keys:
        i = index_by_key.get(key)
        if i is not None:
            counts[i] += 1
    return counts


def preset_param_uvs(preset):
    """The preset's PBR parameters packed into the two param UV pairs:
    (roughness, metallic) and (clearcoat, emission). The single encoding of
    which value goes into which UV channel -- shared by paint and scatter."""
    return (
        (preset.roughness, preset.metallic),
        (preset.clearcoat, preset.emission),
    )


# --------------------------------------------------------------------------
# bpy layer
# --------------------------------------------------------------------------

if bpy is not None:

    def _preset_values_changed(self, context):
        """A preset's parameters changed -> rescatter them onto the param UVs
        of every face carrying this preset's uid (Invariant 8: one-directional
        preset -> faces). Lazy import: model must not import faces at load
        time as a sibling cycle."""
        from . import faces as model_faces

        uv0, uv1 = preset_param_uvs(self)
        model_faces.scatter_preset(self.uid, uv0, uv1)

    class LPC_Preset(bpy.types.PropertyGroup):
        """One named parameter combination. `uid` is set once by `new_preset`
        and never changes; it is the identity faces reference via `lpc_index`.
        The name is purely cosmetic (a readable label / Godot surface hint)."""

        name: bpy.props.StringProperty(name="Name", default="Preset")
        uid: bpy.props.IntProperty(
            name="UID", default=UNASSIGNED,
            description="Immutable preset identity",
        )
        roughness: bpy.props.FloatProperty(
            name="Roughness", default=0.8, min=0.0, max=1.0,
            description="Roughness (R)", update=_preset_values_changed,
        )
        metallic: bpy.props.FloatProperty(
            name="Metallic", default=0.0, min=0.0, max=1.0,
            description="Metallic (M)", update=_preset_values_changed,
        )
        emission: bpy.props.FloatProperty(
            name="Emission", default=0.0, min=0.0, max=1.0,
            description="Emission strength (E), scaled by the global "
            "emission factor", update=_preset_values_changed,
        )
        clearcoat: bpy.props.FloatProperty(
            name="Clearcoat", default=0.0, min=0.0, max=1.0,
            description="Clearcoat intensity (C)", update=_preset_values_changed,
        )

    def _globals_changed(self, context):
        # Globals live as value nodes / uniforms on the ONE shared material
        # (emission factor multiplies the per-face emission, coat roughness is
        # a project-wide constant). A globals edit updates that material only
        # -- no per-face rescatter needed.
        from ..ui import preview_material

        preview_material.update_globals(context.scene)

    class LPC_Globals(bpy.types.PropertyGroup):
        """Global material values -- project-wide constants applied to the one
        shared material (Invariant 8)."""

        emission_factor: bpy.props.FloatProperty(
            name="Emission Factor", default=constants.DEFAULT_EMISSION_FACTOR,
            min=0.0, soft_max=16.0,
            description="Global multiplier on every preset's emission",
            update=_globals_changed,
        )
        clearcoat_roughness: bpy.props.FloatProperty(
            name="Clearcoat Roughness",
            default=constants.DEFAULT_CLEARCOAT_ROUGHNESS, min=0.0, max=1.0,
            description="Project-wide constant clearcoat roughness",
            update=_globals_changed,
        )

    def new_preset(scene, name=""):
        """Append a preset with a fresh uid (the ONLY place uids are
        assigned). The shared material is created lazily on first paint."""
        preset = scene.lpc_presets.add()
        preset.uid = scene.lpc_preset_next_uid
        scene.lpc_preset_next_uid += 1
        if name:
            preset.name = name
        return preset

    def preset_for_uid(scene, uid):
        """The preset with `uid`, or None (Sample / Select: uid -> preset)."""
        if uid == UNASSIGNED:
            return None
        for preset in scene.lpc_presets:
            if preset.uid == uid:
                return preset
        return None

    def preset_refcounts(scene):
        """Lazy refcount per preset (aligned with `scene.lpc_presets`): how
        many faces across ALL meshes carry the preset's uid (decision #4)."""
        from . import faces

        keys = [preset.uid for preset in scene.lpc_presets]
        return reference_counts(
            keys,
            (
                uid
                for mesh_indices in faces.iter_face_indices_per_mesh()
                for uid in mesh_indices
                if uid != UNASSIGNED
            ),
        )
