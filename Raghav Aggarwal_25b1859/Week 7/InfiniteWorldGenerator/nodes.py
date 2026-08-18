import bpy
import bpy.types as typ

nodeX = -1200
nodeDelta = 200

def newNode(nodeTree: typ.GeometryNodeTree, typeName: str, locY=0, delta=nodeDelta):
	global nodeX
	createdNode = nodeTree.nodes.new(type=typeName)
	createdNode.location.x = nodeX
	createdNode.location.y = locY
	nodeX += delta
	return createdNode

def modify_color_ramp(ramp_node: typ.ShaderNodeValToRGB):
	if ramp_node and ramp_node.type == 'VALTORGB':
		cr = ramp_node.color_ramp
		cr.interpolation = 'LINEAR'
		cr.elements[0].position = 0.444
		cr.elements[0].color = (0.0, 0.0, 0.0, 1.0)
		cr.elements[1].position = 1.0
		cr.elements[1].color = (1.0, 1.0, 1.0, 1.0)
		try:
			new_stop = cr.elements.new(position=0.81)
			new_stop.color = (0.735, 0.735, 0.735, 1.0)
		except ValueError:
			pass

def buildChunkNodeTree(treeName="Chunk_Generator_Tree"):
	global nodeX
	nodeX = -1200

	tree = bpy.data.node_groups.new(name=treeName, type='GeometryNodeTree')

	tree.interface.new_socket(name="Master Seed", in_out='INPUT', socket_type='NodeSocketInt')
	tree.interface.new_socket(name="Chunk X", in_out='INPUT', socket_type='NodeSocketFloat')
	tree.interface.new_socket(name="Chunk Y", in_out='INPUT', socket_type='NodeSocketFloat')
	tree.interface.new_socket(name="Tree Object", in_out='INPUT', socket_type='NodeSocketObject')
	tree.interface.new_socket(name="Mountain Strength", in_out='INPUT', socket_type='NodeSocketFloat')
	tree.interface.new_socket(name="Tree Density", in_out='INPUT', socket_type='NodeSocketFloat')
	tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

	groupInput = newNode(tree, 'NodeGroupInput', 0, 0)
	position = newNode(tree, 'GeometryNodeInputPosition', -200, 200)
	mathX = newNode(tree, 'ShaderNodeMath', 200, 0)
	mathY = newNode(tree, 'ShaderNodeMath', 0, 0)
	vectorAdd = newNode(tree, 'ShaderNodeVectorMath', -200, 200)
	grid = newNode(tree, 'GeometryNodeMeshGrid', 400, 0)
	combineOffset = newNode(tree, 'ShaderNodeCombineXYZ', 0, 200)
	noise = newNode(tree, 'ShaderNodeTexNoise', 0, 250)
	colorRamp = newNode(tree, 'ShaderNodeValToRGB', 0, 300)
	mapRange = newNode(tree, 'ShaderNodeMapRange', 0, 0)
	combineZ = newNode(tree, 'ShaderNodeCombineXYZ', -200, 200)
	setPos = newNode(tree, 'GeometryNodeSetPosition', 0, 200)
	distributePoints = newNode(tree, 'GeometryNodeDistributePointsOnFaces', 200, 0)
	objectInfo = newNode(tree, 'GeometryNodeObjectInfo', -200, 200)
	instancePoints = newNode(tree, 'GeometryNodeInstanceOnPoints', 0, 200)
	joinGeometry = newNode(tree, 'GeometryNodeJoinGeometry', 0, 200)
	transform = newNode(tree, 'GeometryNodeTransform', 0, 200)
	smooth = newNode(tree, 'GeometryNodeSetShadeSmooth', 0, 200)
	groupOutput = newNode(tree, 'NodeGroupOutput', 0, 200)

	grid.inputs['Size X'].default_value = 16.0
	grid.inputs['Size Y'].default_value = 16.0
	grid.inputs['Vertices X'].default_value = 32
	grid.inputs['Vertices Y'].default_value = 32
	mathX.operation = 'MULTIPLY'
	mathX.inputs[1].default_value = 16.0
	mathY.operation = 'MULTIPLY'
	mathY.inputs[1].default_value = 16.0
	vectorAdd.operation = 'ADD'
	noise.noise_dimensions = '4D'
	noise.inputs['Scale'].default_value = 0.1
	mapRange.inputs[3].default_value = 0.0
	mapRange.inputs[4].default_value = 12.0
	distributePoints.inputs['Density'].default_value = 0.04 
	instancePoints.inputs['Scale'].default_value = (0.35, 0.35, 0.35)
	modify_color_ramp(colorRamp)

	lks = tree.links
	lks.new(grid.outputs['Mesh'], setPos.inputs['Geometry'])
	lks.new(groupInput.outputs['Chunk X'], mathX.inputs[0])
	lks.new(groupInput.outputs['Chunk Y'], mathY.inputs[0])
	lks.new(groupInput.outputs['Mountain Strength'], mapRange.inputs[4])
	lks.new(groupInput.outputs['Tree Density'], distributePoints.inputs['Density'])
	lks.new(mathX.outputs['Value'], combineOffset.inputs['X'])
	lks.new(mathY.outputs['Value'], combineOffset.inputs['Y'])
	lks.new(position.outputs['Position'], vectorAdd.inputs[0])
	lks.new(combineOffset.outputs['Vector'], vectorAdd.inputs[1])
	lks.new(vectorAdd.outputs['Vector'], noise.inputs['Vector'])
	lks.new(groupInput.outputs['Master Seed'], noise.inputs['W'])
	lks.new(noise.outputs['Fac'], colorRamp.inputs['Factor'])
	lks.new(colorRamp.outputs['Color'], mapRange.inputs['Value'])
	lks.new(mapRange.outputs['Result'], combineZ.inputs['Z'])
	lks.new(combineZ.outputs['Vector'], setPos.inputs['Offset'])
	lks.new(setPos.outputs['Geometry'], distributePoints.inputs['Mesh'])
	lks.new(groupInput.outputs['Tree Object'], objectInfo.inputs['Object'])
	lks.new(distributePoints.outputs['Points'], instancePoints.inputs['Points'])
	lks.new(objectInfo.outputs['Geometry'], instancePoints.inputs['Instance'])
	lks.new(setPos.outputs['Geometry'], joinGeometry.inputs['Geometry'])
	lks.new(instancePoints.outputs['Instances'], joinGeometry.inputs['Geometry'])
	lks.new(joinGeometry.outputs['Geometry'], transform.inputs['Geometry'])
	lks.new(combineOffset.outputs['Vector'], transform.inputs['Translation'])
	lks.new(transform.outputs['Geometry'], smooth.inputs['Geometry'])
	lks.new(smooth.outputs['Geometry'], groupOutput.inputs['Geometry'])

	return tree