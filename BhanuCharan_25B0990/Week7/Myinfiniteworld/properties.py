import bpy
from bpy.types import PropertyGroup
from bpy.props import IntProperty, FloatProperty
# PropertyGroup bundles related settings into one object instead of adding them to bpy.types.Scene individually. 
# IntProperty/FloatProperty create Blender UI properties that panels can draw automatically.

class WorldGeneratorProperties(PropertyGroup):

    seed: IntProperty(
        name="Seed", # Everything self explanatory
        description="Seed used for procedural generation",
        default=990,
        min=0,
    )

    terrain_size: IntProperty(
        name="Terrain Size",
        description="Physical size of the terrain mesh",
        default=2,
        min=1,
        max=10,
    )

    mountain_strength: FloatProperty(
        name="Mountain Strength",
        description="Controls terrain height",
        default=0.7,
        min=0.0,
        max=20.0,
    )

    tree_density: FloatProperty(
        name="Tree Density",
        description="Density of scattered trees",
        default=0.5,
        min=0.0,
        max=1.0,
    )