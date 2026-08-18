import bpy


class WORLDGEN_PT_panel(bpy.types.Panel): # Conventional naming for Blender panels. The "PT" stands for "Panel Type".
    # Draws the "Infinite World Generator" box in the 3D Viewport sidebar.

    bl_label = "Infinite World Generator"
    bl_idname = "WORLDGEN_PT_panel"
    bl_space_type = "VIEW_3D" # the 3D Viewport
    bl_region_type = "UI" # the sidebar opened with the N key
    bl_category = "WorldGen" # sidebar tab name

    def draw(self, context): # Draws the UI elements in the panel. This method is called by Blender automatically when the panel needs to be drawn.
        layout = self.layout
        settings = context.scene.world_generator

        layout.prop(settings, "seed")
        layout.prop(settings, "terrain_size")
        layout.prop(settings, "mountain_strength")
        layout.prop(settings, "tree_density")

        layout.separator() # Adds a visual separator in the UI to make it look cleaner

        layout.operator("world.generate") # Adds the "Generate World" button to the panel
        layout.operator("world.randomize_seed") # Adds the "Randomize Seed" button to the panel