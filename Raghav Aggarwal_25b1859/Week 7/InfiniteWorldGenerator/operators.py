import bpy
import random
from . import generator

class WORLDGEN_OT_generate(bpy.types.Operator):
	bl_idname = "worldgen.generate"
	bl_label = "Generate World"
	bl_description = "Generates the procedural world based on current settings"

	def execute(self, context):
		props = context.scene.worldgen_props

		chunkGrid = []
		half_x = props.grid_size_x // 2
		half_y = props.grid_size_y // 2

		for cx in range(-half_x, props.grid_size_x - half_x):
			for cy in range(-half_y, props.grid_size_y - half_y):
				chunkGrid.append((cx, cy))

		generator.generateInfiniteWorld(
			masterSeed=props.seed,
			chunksToGenerate=chunkGrid,
			mountainStrength=props.mountain_strength,
			treeDensity=props.tree_density
		)

		self.report({'INFO'}, f"World Generated with Seed {props.seed}!")
		return {'FINISHED'}

class WORLDGEN_OT_randomize_seed(bpy.types.Operator):
	bl_idname = "worldgen.randomize_seed"
	bl_label = "Randomize Seed"
	bl_description = "Picks a new random seed"

	def execute(self, context):
		context.scene.worldgen_props.seed = random.randint(0, 9999)
		return {'FINISHED'}