import bpy

class WorldGenProperties(bpy.types.PropertyGroup):
	seed: bpy.props.IntProperty(
		name="Seed",
		description="Master seed for procedural generation",
		default=1859,
		min=0
	)
	grid_size_x: bpy.props.IntProperty(
		name="Grid X",
		description="Number of chunks in the X direction",
		default=3,
		min=1
	)
	
	grid_size_y: bpy.props.IntProperty(
		name="Grid Y",
		description="Number of chunks in the Y direction",
		default=3,
		min=1
	)
	mountain_strength: bpy.props.FloatProperty(
		name="Mountain Strength",
		description="Vertical displacement scale (Z-axis)",
		default=12.0,
		min=0.0,
		step=10.0
	)
	tree_density: bpy.props.FloatProperty(
		name="Tree Density",
		description="Amount of vegetation scattered on the mesh",
		default=0.05,
		min=0.0,
		max=1.0,
		step=1
	)