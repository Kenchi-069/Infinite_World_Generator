bl_info = {
	"name": "Infinite World Generator",
	"author": "Raghav Aggarwal",
	"version": (1, 0),
	"blender": (5, 2, 0),
	"location": "View3D > Sidebar > World Gen",
	"description": "Procedural terrain and world generation.",
	"category": "Object",
}

# doing all this fancy stuff for easier debugging
if "bpy" in locals():
	import importlib
	importlib.reload(properties)
	importlib.reload(operators)
	importlib.reload(panel)
	importlib.reload(generator)
	importlib.reload(nodes)
	importlib.reload(vegetation)
else:
	import bpy

# Import the files after checking local cache
from . import properties
from . import operators
from . import panel
from . import generator
from . import nodes
from . import vegetation

classes = (
	properties.WorldGenProperties,
	operators.WORLDGEN_OT_generate,
	operators.WORLDGEN_OT_randomize_seed,
	panel.WORLDGEN_PT_main_panel,
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.Scene.worldgen_props = bpy.props.PointerProperty(type=properties.WorldGenProperties)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.worldgen_props

if __name__ == "__main__":
	register()