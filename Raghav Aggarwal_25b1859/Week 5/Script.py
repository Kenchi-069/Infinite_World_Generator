"""
Firstly a tree is created via python code. Then if no mesh was selected, we create a plane which will act as the base for the terrain.
This also triggers the creation of a default preset of basic geo nodes setup for a simple mountainous terrain.
In case a mesh was selected, and did not have a modifier named "Terrain_Generator", we also add on top of any other existing modifiers,
a the same default preset. In the case that there was a modifier with that name, the script just randomizes the values of the parameters.

The seed can be fixed by changing the value of the MASTER_SEED variable.
"""

MASTER_SEED = None # Change 'None' to an integer to lock the seed
SIZE = 3

import bpy
import random
import bpy.types as typ

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

    final_tree.location = (10, 10, 0)
    
    return final_tree

def generate_terrain_preset(master_seed=None):
    # Generate random terrain settings
    if master_seed is not None:
        random.seed(master_seed)
    
    # Generate varied configurations within controlled limits
    preset = {
        "Seed": random.randint(1000, 9999),
        "Mountain Strength": round(random.uniform(0.5, 1.7), 1),
        "Terrain Scale": round(random.uniform(0.8, 2.0), 1),
        "Tree Density": round(random.uniform(3.0, 10.0), 2)
    }
    
    return preset

def modify_color_ramp(ramp_node : typ.ShaderNodeValToRGB):
    # Verify it exists and is actually a Color Ramp (internal type: 'VALTORGB')
    if ramp_node and ramp_node.type == 'VALTORGB':
        cr = ramp_node.color_ramp

        # Options: 'LINEAR', 'EASE', 'CONSTANT', 'B_SPLINE', 'CARDINAL'
        cr.interpolation = 'LINEAR'

        cr.elements[0].position = 0.444
        cr.elements[0].color = (0.0, 0.0, 0.0, 1.0) # (Red, Green, Blue, Alpha)

        cr.elements[1].position = 1.0
        cr.elements[1].color = (1.0, 1.0, 1.0, 1.0)

        # .new() inserts a flag at the given position and returns the new element
        try:
            new_stop = cr.elements.new(position=0.755)
            new_stop.color = (0.735, 0.735, 0.735, 1.0)
        except ValueError:
            # Blender throws a ValueError if a stop already exists at exactly 0.5
            print("A stop already exists at this position.")

node_x = -180
nodeDelta = 200

def newNode(node_tree : typ.GeometryNodeTree, type_name : str, loc_y=0, delta=nodeDelta):
    global node_x
    _node_new = node_tree.nodes.new(type=type_name)
    _node_new.location.x = node_x
    _node_new.location.y = loc_y
    node_x += delta
    return _node_new

def apply_preset_to_modifier(obj, preset, treeObject, planeCreated=False):
    """Modifies the active object by updating its Geometry Nodes parameters."""
    mod_name = "Terrain_Generator"
    
    # only add if modifier doesnt exist
    if mod_name not in obj.modifiers:
        mod = obj.modifiers.new(name=mod_name, type='NODES')
    else:
        mod = obj.modifiers[mod_name]
    
    # if there is no node tree attached, make a new basic one
    if not mod.node_group:
        tree = bpy.data.node_groups.new(name=mod_name, type='GeometryNodeTree')
        mod.node_group = tree
        
        tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        
        # create sockets that match our presets
        tree.interface.new_socket(name="Seed", in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket(name="Mountain Strength", in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket(name="Terrain Scale", in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket(name="Tree Density", in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket(name="Tree Object", in_out='INPUT', socket_type='NodeSocketObject')

        input = newNode(tree, 'NodeGroupInput')
        noise = newNode(tree, 'ShaderNodeTexNoise', -200)
        if planeCreated: subdivide = newNode(tree, 'GeometryNodeSubdivideMesh')
        colorRamp = newNode(tree, 'ShaderNodeValToRGB', -200, 280)
        combine = newNode(tree, 'ShaderNodeCombineXYZ', -200, 0)
        math1 = newNode(tree, 'ShaderNodeMath', -200, 0)
        setPos = newNode(tree, 'GeometryNodeSetPosition')
        distPoints = newNode(tree, 'GeometryNodeDistributePointsOnFaces', -200, 0)
        objInfo = newNode(tree, 'GeometryNodeObjectInfo', -400)
        instPoints = newNode(tree, 'GeometryNodeInstanceOnPoints', -200)
        join1 = newNode(tree, 'GeometryNodeJoinGeometry')
        setSmooth = newNode(tree, 'GeometryNodeSetShadeSmooth')
        output = newNode(tree, 'NodeGroupOutput')
        
        input.outputs["Tree Object"].default_value = treeObject
        if planeCreated: subdivide.inputs["Level"].default_value = 7
        noise.noise_dimensions = '4D'
        noise.inputs["Scale"].default_value = 1.3
        noise.inputs["Detail"].default_value = 1.6
        noise.inputs["Roughness"].default_value = 0.654
        noise.inputs["Lacunarity"].default_value = 1.8
        noise.inputs["Distortion"].default_value = 0.4
        modify_color_ramp(colorRamp)
        math1.operation = 'MULTIPLY'
        instPoints.inputs['Scale'].default_value = (0.02,0.02,0.02)
        
        lks = tree.links
        if planeCreated:
            lks.new(input.outputs["Geometry"], subdivide.inputs["Mesh"])
            lks.new(subdivide.outputs["Mesh"], setPos.inputs["Geometry"])
        else:
            lks.new(input.outputs["Geometry"], setPos.inputs["Geometry"])
            
        lks.new(input.outputs["Seed"], noise.inputs["W"])
        lks.new(input.outputs["Mountain Strength"], math1.inputs[1])
        lks.new(input.outputs["Terrain Scale"], noise.inputs["Scale"])
        lks.new(input.outputs["Seed"], noise.inputs["W"])
        lks.new(noise.outputs["Factor"], colorRamp.inputs["Factor"])
        lks.new(colorRamp.outputs["Color"], math1.inputs[0])
        lks.new(math1.outputs[0], combine.inputs["Z"])
        lks.new(combine.outputs["Vector"], setPos.inputs["Offset"])
        lks.new(setPos.outputs[0], distPoints.inputs["Mesh"])
        lks.new(input.outputs["Tree Density"], distPoints.inputs["Density"])
        lks.new(input.outputs["Seed"], distPoints.inputs["Seed"])
        lks.new(input.outputs["Tree Object"], objInfo.inputs["Object"])
        lks.new(distPoints.outputs["Points"], instPoints.inputs["Points"])
        lks.new(objInfo.outputs["Geometry"], instPoints.inputs["Instance"])
        lks.new(setPos.outputs[0], join1.inputs[0])
        lks.new(instPoints.outputs[0], join1.inputs[0])
        lks.new(join1.outputs[0], setSmooth.inputs["Mesh"])
        lks.new(setSmooth.outputs[0], output.inputs["Geometry"])
        

    # If a node group is attached, map the names to the backend socket identifiers
    if mod.node_group:
        inputs = getattr(mod.node_group, "interface", mod.node_group).items_tree if hasattr(mod.node_group, "interface") else mod.node_group.inputs
        
        for item in inputs:
            # Check if the interface item is one of our preset keys
            if hasattr(item, "name") and item.name in preset:
                # Assign the randomized value directly to the modifier's exposed socket
                mod[item.identifier] = preset[item.name]
            if item.name == "Tree Object" and mod.get(item.identifier) is None:
                mod[item.identifier] = treeObject
    
    obj.data.update_tag()
    mod.show_viewport = False
    mod.show_viewport = True
    bpy.context.view_layer.update()

def main():
    # create a tree, which will be scattered in the default terrain
    customTree = custom_tree_generate()
    
    # targets the currently selected object in the viewport
    currentObj = bpy.context.active_object
    
    planeCreated = False
    # if nothing is selected, create a plane
    if currentObj is None or currentObj.type != 'MESH':
        bpy.ops.mesh.primitive_plane_add(size=SIZE, location=(0,0,0))
        currentObj = bpy.context.active_object
        currentObj.name = "Base Terrain"
        planeCreated = True

    presetData = generate_terrain_preset(MASTER_SEED) 
    
    # Apply the data to the object's modifier
    apply_preset_to_modifier(currentObj, presetData, customTree, planeCreated)

    print("\n--- New Procedural World Preset ---")
    for key, value in presetData.items():
        print(f"{key}: {value}")
    print("-----------------------------------\n")

if __name__ == "__main__":
    main()