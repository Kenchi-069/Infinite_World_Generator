bl_info = {
    "name": "Infinite World Generator",
    "author": "Bhanu Charan",
    "version": (1, 0, 0), # Add-on version
    "blender": (5, 1, 0), # Minimum Blender version required
    "location": "View3D > Sidebar", # Self explanatory, where the add-on will appear in Blender's UI
    "description": "Procedural Infinite World Generator", # Just to fill in the description field, not used anywhere else
    "category": "Object", # Category under which the add-on will be listed in Blender's add-on preferences
} # Conventional Blender add-on metadata

import bpy
from bpy.props import PointerProperty

from .properties import WorldGeneratorProperties
from .operators import (
    WORLDGEN_OT_generate,
    WORLDGEN_OT_randomize,
)
from .panel import WORLDGEN_PT_panel # Importing all the classes defined in the other files so they can be registered with Blender when the add-on is enabled.


classes = (
    WorldGeneratorProperties,
    WORLDGEN_OT_generate,
    WORLDGEN_OT_randomize,
    WORLDGEN_PT_panel,
)


def register(): # Runs when the add-on is enabled in Blender's preferences
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.world_generator = PointerProperty(
        type=WorldGeneratorProperties
    ) # Adds a new property to the Scene type in Blender, allowing us to store our WorldGeneratorProperties object in the scene. This is how we can access the settings from the UI and operators.


def unregister(): # Runs when the add-on is disabled in Blender's preferences
    del bpy.types.Scene.world_generator

    for cls in reversed(classes): # Unregisters the classes in reverse order to avoid dependency issues. For example, if a panel depends on an operator, we need to unregister the panel first before the operator.
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register() # Not strictly necessary, but allows the script to be run directly from Blender's text editor for testing purposes.