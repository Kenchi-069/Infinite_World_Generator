import bpy

class WORLDGEN_PT_main_panel(bpy.types.Panel):
	bl_label = "Infinite World Generator"
	bl_idname = "WORLDGEN_PT_main_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'World Gen'

	def draw(self, context):
		layout = self.layout
		props = context.scene.worldgen_props

		box = layout.box()
		box.label(text="Core Settings:", icon='WORLD')
		box.prop(props, "seed")
		row = box.row()
		row.prop(props, "grid_size_x")
		row.prop(props, "grid_size_y")
		
		box = layout.box()
		box.label(text="Biome Tweaks:", icon='MESH_ICOSPHERE')
		box.prop(props, "mountain_strength")
		box.prop(props, "tree_density")

		layout.separator()

		row = layout.row()
		row.scale_y = 1.5 
		row.operator("worldgen.generate", icon='PLAY')
		layout.operator("worldgen.randomize_seed", icon='FILE_REFRESH')