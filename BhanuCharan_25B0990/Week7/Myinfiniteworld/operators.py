import bpy
import random
import traceback

from .generator import generate_world


class WORLDGEN_OT_generate(bpy.types.Operator): # Named WORLDGEN_OT_generate to follow Blender's naming convention for operators. The "OT" stands for "Operator Type".
    # Runs the full generation pipeline when "Generate World" is clicked.

    bl_idname = "world.generate" # Named "world.generate" to follow Blender's naming convention for operators. The first part is the category, the second part is the operator name.
    bl_label = "Generate World"

    def execute(self, context):
        settings = context.scene.world_generator

        try:
            generate_world(settings)
        except Exception as e:
            # Operators should never let a raw exception reach Blender. This turns it into a clean UI error message instead of a silent or confusing failure.
            traceback.print_exc()
            self.report({'ERROR'}, f"World generation failed: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}


class WORLDGEN_OT_randomize(bpy.types.Operator): # Again, named to follow conventions
    # Picks a new random seed. Doesn't regenerate the terrain by itself. IMPORTANT: Generate World still needs to be clicked afterward.

    bl_idname = "world.randomize_seed"
    bl_label = "Randomize Seed"

    def execute(self, context):
        settings = context.scene.world_generator
        settings.seed = random.randint(0, 999999)
        return {'FINISHED'}