import bpy
import random
from . import nodes
from . import vegetation

def generateInfiniteWorld(masterSeed, chunksToGenerate, mountainStrength, treeDensity):
	tree = nodes.buildChunkNodeTree() 
	treeObj = vegetation.custom_tree_generate()

	parent_name = f"Terrain_Generation_{masterSeed}"
	parent_empty = bpy.data.objects.new(parent_name, None)
	bpy.context.collection.objects.link(parent_empty)

	if "Tree Object" in tree.interface.items_tree:
		tree.interface.items_tree["Tree Object"].default_value = treeObj

	for cx, cy in chunksToGenerate:
		chunkName = f"Chunk_{cx}_{cy}"

		mesh = bpy.data.meshes.new(chunkName + "_Mesh")
		obj = bpy.data.objects.new(chunkName, mesh)
		obj.parent = parent_empty
		bpy.context.collection.objects.link(obj)
		
		mod = obj.modifiers.new(name="Terrain", type='NODES')
		mod.node_group = tree 

		values_to_set = {
			"Master Seed": masterSeed,
			"Chunk X": float(cx),
			"Chunk Y": float(cy),
			"Tree Object": treeObj,
			"Mountain Strength": float(mountainStrength),
			"Tree Density": float(treeDensity)
		}

		for item in tree.interface.items_tree:
			if item.name in values_to_set:
				socket_attr = item.identifier 
				value = values_to_set[item.name]
				getattr(mod.properties.inputs, socket_attr).value = value

	bpy.context.view_layer.update()