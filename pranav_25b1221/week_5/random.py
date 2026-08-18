import random as rd
import bpy

seed = rd.randint(0, 1000)
mnt_strength = rd.uniform(0.5, 1)
tree_density = rd.uniform(1, 3)*10000

bpy.data.node_groups["Geometry Nodes"].nodes["Value.002"].outputs[0].default_value = tree_density #changes tree density

bpy.data.node_groups["Geometry Nodes"].nodes["Value.003"].outputs[0].default_value = seed #changes seed

bpy.data.node_groups["Geometry Nodes"].nodes["Value.004"].outputs[0].default_value = mnt_strength #i'll let you figure this one out

print(f"seed: {seed}")
print(f"mountian strength: {mnt_strength}")
print(f"tree density: {tree_density}")


