
import bpy
import random
from bpy.props import IntProperty, FloatProperty
from bpy.types import PropertyGroup, Operator, Panel
from .generator import execute_world_generation

class WorldGeneratorProperties(PropertyGroup):
    seed: IntProperty(name="Master Seed", default=2025, min=0, max=999999)
    grid_size_x: IntProperty(name="Grid X", default=3, min=1)
    grid_size_y: IntProperty(name="Grid Y", default=3, min=1)
    
    subdivisions: IntProperty(name="Subdivisions", description="Mesh subdivision level", default=0, min=0, max=6)
    
    chunk_size: FloatProperty(name="Terrain Size", default=25.0, min=10.0, max=100.0)
    mountain_strength: FloatProperty(name="Mountain Strength", default=10.0, min=0.1, max=30.0)
    snow_level: FloatProperty(name="Snow Level", default=8.0, min=0.0, max=50.0)
    tree_density: FloatProperty(name="Tree Density", default=15.0, min=0.0, max=100.0)
    rock_density: FloatProperty(name="Rock Density", default=25.0, min=0.0, max=100.0)

class WORLDGEN_OT_randomize_seed(Operator):
    bl_idname = "worldgen.randomize_seed"
    bl_label = "Randomize Seed"

    def execute(self, context):
        context.scene.world_gen_props.seed = random.randint(0, 999999)
        return {'FINISHED'}

class WORLDGEN_OT_generate(Operator):
    bl_idname = "worldgen.generate"
    bl_label = "Generate World"

    def execute(self, context):
        props = context.scene.world_gen_props
        execute_world_generation(props)
        self.report({'INFO'}, f"Infinite World Generated (Seed: {props.seed})")
        return {'FINISHED'}

class WORLDGEN_PT_panel(Panel):
    bl_label = "Infinite World Generator"
    bl_idname = "WORLDGEN_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'World Gen' 

    def draw(self, context):
        layout = self.layout
        props = context.scene.world_gen_props

        box = layout.box()
        box.label(text="Core Settings:", icon='WORLD')
        box.prop(props, "seed")
        row = box.row()
        row.prop(props, "grid_size_x")
        row.prop(props, "grid_size_y")
        box.prop(props, "subdivisions") 
        
        box = layout.box()
        box.label(text="Biome Settings:", icon='MESH_ICOSPHERE')
        box.prop(props, "chunk_size")
        box.prop(props, "mountain_strength")
        box.prop(props, "snow_level")
        box.prop(props, "tree_density")
        box.prop(props, "rock_density")

        layout.separator()
        row = layout.row()
        row.scale_y = 1.5 
        row.operator("worldgen.generate", icon='PLAY')
        layout.operator("worldgen.randomize_seed", icon='FILE_REFRESH', text="")