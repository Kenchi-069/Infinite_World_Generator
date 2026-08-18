
bl_info = {
    "name": "Infinite World Generator",
    "author": "Raghvendra Ubarhande",
    "version": (1, 2, 1),
    "blender": (5, 2, 0),
    "location": "View3D > Sidebar > World Gen",
    "description": "Generates a modular procedural chunk-based world.",
    "category": "Object",
}

if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(terrain)
    importlib.reload(vegetation)
    importlib.reload(generator)
    importlib.reload(panel)
else:
    from . import utils
    from . import terrain
    from . import vegetation
    from . import generator
    from . import panel

import bpy

classes = (
    panel.WorldGeneratorProperties,
    panel.WORLDGEN_OT_randomize_seed,
    panel.WORLDGEN_OT_generate,
    panel.WORLDGEN_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.world_gen_props = bpy.props.PointerProperty(type=panel.WorldGeneratorProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.world_gen_props

if __name__ == "__main__":
    register()