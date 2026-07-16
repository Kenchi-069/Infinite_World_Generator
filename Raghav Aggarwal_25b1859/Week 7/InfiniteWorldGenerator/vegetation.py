import bpy

def custom_tree_generate(tree_name="Tree"):
	if tree_name in bpy.data.objects:
		treeObj = bpy.data.objects[tree_name]
		if treeObj.name not in bpy.context.collection.objects:
			bpy.context.collection.objects.link(treeObj)
		return treeObj

	bpy.ops.object.select_all(action='DESELECT')

	bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.25, depth=2.0, location=(0, 0, 1.0))
	trunk = bpy.context.active_object

	bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.5, location=(0, 0, 2.5))
	canopy = bpy.context.active_object
	canopyMesh = canopy.data

	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.transform.vertex_random(offset=0.3)
	bpy.ops.object.mode_set(mode='OBJECT')

	trunk.select_set(True)
	canopy.select_set(True)
	bpy.context.view_layer.objects.active = trunk
	bpy.ops.object.join()

	bpy.data.meshes.remove(canopyMesh)

	final_tree = bpy.context.active_object
	final_tree.name = tree_name

	bpy.context.scene.cursor.location = (0, 0, 0)
	bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
	final_tree.location = (48, 48, 0)
	final_tree.hide_set(True)

	return final_tree