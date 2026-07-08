import bpy
import json
import random
import os
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
    """Function to modify the color ramp to specific values"""
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

def custom_tree_generate(tree_name="Tree"):
    """Generates a low-poly tree"""
    
    # 1. Check if the tree already exists so we don't spawn duplicates
    if tree_name in bpy.data.objects:
        print(f"{tree_name} already exists. Skipping creation.")
        return bpy.data.objects[tree_name]
        
    # Deselect everything in the scene to avoid accidental joining
    bpy.ops.object.select_all(action='DESELECT')
    
    # 2. Build the Trunk
    # We use a 6-sided cylinder to keep the polygon count very low for scattering
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=6, 
        radius=0.25, 
        depth=2.0, 
        location=(0, 0, 1.0) # We spawn it 1m up so the bottom rests exactly at Z=0
    )
    trunk = bpy.context.active_object
    
    # 3. Build the Canopy (Leaves)
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=2, 
        radius=1.5, 
        location=(0, 0, 2.5) # Spawned resting on top of the trunk
    )
    canopy = bpy.context.active_object
    
    # 4. Make it Organic (Random Vertex Displacement)
    # We switch to edit mode and scramble the vertices slightly so it isn't a perfect sphere
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.vertex_random(offset=0.3)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 5. Join them into a single object
    trunk.select_set(True)
    canopy.select_set(True)
    bpy.context.view_layer.objects.active = trunk
    bpy.ops.object.join()
    
    # Rename the final joined object
    final_tree = bpy.context.active_object
    final_tree.name = tree_name
    
    # 6. Set the Origin to the absolute bottom
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    final_tree.location = (48, 48, 0)
    final_tree.hide_set(True)
    
    return final_tree

def buildChunkNodeTree(treeName="Chunk_Generator_Tree"):
    global nodeX
    nodeX = -1200  
    
    if treeName in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[treeName])
        
    tree = bpy.data.node_groups.new(name=treeName, type='GeometryNodeTree')
    
    tree.interface.new_socket(name="Master Seed", in_out='INPUT', socket_type='NodeSocketInt')
    tree.interface.new_socket(name="Chunk X", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Chunk Y", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Tree Object", in_out='INPUT', socket_type='NodeSocketObject')
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

def generateInfiniteWorld(masterSeed, chunksToGenerate, chunkSize=16):
    tree = buildChunkNodeTree() # node tree
    treeObj = custom_tree_generate() # make a low  poly tree which will instanced in the terrain
    worldData = {}
    
    for cx, cy in chunksToGenerate:
        chunkName = f"Chunk_{cx}_{cy}"
        
        mesh = bpy.data.meshes.new(chunkName + "_Mesh")
        obj = bpy.data.objects.new(chunkName, mesh)
        bpy.context.collection.objects.link(obj)
        
        mod = obj.modifiers.new(name="Terrain", type='NODES')
        mod.node_group = tree # Give every chunk the same node tree (like exactly same) to save space and optimize
        
        inputs = tree.interface.items_tree
        for item in inputs:
            if item.name == "Master Seed":
                mod[item.identifier] = masterSeed
            elif item.name == "Chunk X":
                mod[item.identifier] = float(cx)
            elif item.name == "Chunk Y":
                mod[item.identifier] = float(cy)
            elif item.name == "Tree Object":
                mod[item.identifier] = treeObj
                
        chunkSeed = hash((masterSeed, cx, cy))
        rng = random.Random(chunkSeed)
        
        heights = [[round(rng.uniform(0.0, 15.0), 2) for _ in range(chunkSize)] for _ in range(chunkSize)]
        avgHeight = sum(sum(row) for row in heights) / (chunkSize * chunkSize)
        
        worldData[f"{cx},{cy}"] = {
            "coordinates": [cx, cy],
            "average_height": round(avgHeight, 2),
            "height_map": heights
        }
        
    blendPath = bpy.data.filepath
    if not blendPath:
        blendPath = os.path.expanduser("~") 
    else:
        blendPath = os.path.dirname(blendPath)
        
    jsonPath = os.path.join(blendPath, "procedural_world_data.json") # Writing data to this json file
    
    outputJson = {
        "master_seed": masterSeed,
        "chunk_size": chunkSize,
        "chunks": worldData
    }
    
    with open(jsonPath, 'w') as f:
        json.dump(outputJson, f, indent=4)
    
    bpy.context.view_layer.update()

if __name__ == "__main__":
#    seed = 1859 # Use this for set seed
    seed = random.randint(0, 999999) # Use this for random seed
    
    # Using only 9 chunks here, but easily scalable
    chunkGrid = [
        (0, 0), (1, 0), (2, 0),
        (0, 1), (1, 1), (2, 1),
        (0, 2), (1, 2), (2, 2)
    ]
    
    generateInfiniteWorld(masterSeed=seed, chunksToGenerate=chunkGrid)