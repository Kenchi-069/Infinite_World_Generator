"""
================================================================================
PROCEDURAL TERRAIN, TREE, AND ROCK GENERATOR
================================================================================
This script generates a completely procedural low-poly landscape in Blender.
It builds a customized multi-layered pine tree, randomized rocks, and distributes 
them across a mathematically displaced terrain using dual-layered Noise Textures 
via Geometry Nodes. 

Everything is styled with basic colors automatically.
"""

# --- GLOBAL SETTINGS ---
MASTER_SEED = 5800 # Set to match the seed in your image (5.800)
SIZE = 25 # Size of the terrain plane
TREE_DENSITY = 15.0 # Max points for Poisson Disk to pick from
ROCK_DENSITY = 25.0 

import bpy
import random
import math
import bpy.types as typ

# ==============================================================================
# 1. MATERIAL GENERATOR
# ==============================================================================
def get_or_create_material(name, color):
    """Checks if a material exists. If not, it creates it with the given color."""
    if name not in bpy.data.materials:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Colors are RGBA format (Red, Green, Blue, Alpha) ranging from 0.0 to 1.0
            bsdf.inputs["Base Color"].default_value = color
    return bpy.data.materials[name]

# ==============================================================================
# 2. ASSET GENERATORS (TREES & ROCKS)
# ==============================================================================
def generate_pine_tree(name="Procedural_Pine"):
    """Generates a well-made procedural low-poly pine tree with 3 layers of leaves."""
    # Delete old tree if it exists to avoid duplications
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        
    bpy.ops.object.select_all(action='DESELECT')
    
    # Setup Colors
    wood_mat = get_or_create_material("Mat_Wood", (0.1, 0.05, 0.02, 1.0))
    leaf_mat = get_or_create_material("Mat_Leaves", (0.05, 0.2, 0.08, 1.0))
    
    parts = []
    
    # 1. Create the Trunk (Cylinder)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.2, depth=1.5, location=(0, 0, 0.75))
    trunk = bpy.context.active_object
    trunk.data.materials.append(wood_mat)
    parts.append(trunk)
    
    # 2. Create Leaf Layer 1 (Bottom Cone)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.2, depth=2.0, location=(0, 0, 2.0))
    layer1 = bpy.context.active_object
    layer1.data.materials.append(leaf_mat)
    parts.append(layer1)
    
    # 3. Create Leaf Layer 2 (Middle Cone)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.9, depth=1.8, location=(0, 0, 3.0))
    layer2 = bpy.context.active_object
    layer2.data.materials.append(leaf_mat)
    parts.append(layer2)
    
    # 4. Create Leaf Layer 3 (Top Cone)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.6, depth=1.5, location=(0, 0, 4.0))
    layer3 = bpy.context.active_object
    layer3.data.materials.append(leaf_mat)
    parts.append(layer3)
    
    # Join everything into one object
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = trunk
    bpy.ops.object.join()
    
    tree = bpy.context.active_object
    tree.name = name
    
    # Move origin to the very bottom so it sits perfectly on the ground
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    tree.location = (20, 0, 0) # Hide it out of the way
    return tree

def generate_rock(name="Procedural_Rock"):
    """Generates a procedural rock by distorting an icosphere."""
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        
    bpy.ops.object.select_all(action='DESELECT')
    rock_mat = get_or_create_material("Mat_Rock", (0.3, 0.3, 0.3, 1.0))
    
    # Add base icosphere
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.6, location=(0, 0, 0.2))
    rock = bpy.context.active_object
    rock.data.materials.append(rock_mat)
    
    # Enter edit mode and randomize the vertices to make it look organic
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.vertex_random(offset=0.2)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    rock.name = name
    
    # Flatten the bottom slightly so it sits on the ground better
    rock.scale.z = 0.6
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    rock.location = (20, 5, 0) # Hide it out of the way
    return rock

# ==============================================================================
# 3. GEOMETRY NODES SETUP
# ==============================================================================
# Helper to spawn nodes in a readable grid layout
def newNode(node_tree, type_name, loc_x, loc_y):
    _node = node_tree.nodes.new(type=type_name)
    _node.location.x = loc_x
    _node.location.y = loc_y
    return _node

def apply_terrain_nodes(obj, tree_obj, rock_obj, planeCreated=False):
    mod_name = "Landscape_Generator"
    
    if mod_name not in obj.modifiers:
        mod = obj.modifiers.new(name=mod_name, type='NODES')
    else:
        mod = obj.modifiers[mod_name]
    
    # Create the node tree if it doesn't exist
    if not mod.node_group:
        tree = bpy.data.node_groups.new(name=mod_name, type='GeometryNodeTree')
        mod.node_group = tree
        
        # --- 1. SETUP MODIFIER INTERFACE (INPUTS) ---
        tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        tree.interface.new_socket(name="Seed", in_out='INPUT', socket_type='NodeSocketFloat')
        
        tree.interface.new_socket(name="Tree Object", in_out='INPUT', socket_type='NodeSocketObject')
        tree.interface.new_socket(name="Tree Density", in_out='INPUT', socket_type='NodeSocketFloat')
        
        tree.interface.new_socket(name="Rock Object", in_out='INPUT', socket_type='NodeSocketObject')
        tree.interface.new_socket(name="Rock Density", in_out='INPUT', socket_type='NodeSocketFloat')

        # --- 2. SPAWN CORE NODES ---
        input_node = newNode(tree, 'NodeGroupInput', -1000, 0)
        if planeCreated: subdivide = newNode(tree, 'GeometryNodeSubdivideMesh', 400, 200)
        setPos = newNode(tree, 'GeometryNodeSetPosition', 600, 0)
        
        join1 = newNode(tree, 'GeometryNodeJoinGeometry', 1200, 0)
        setSmooth = newNode(tree, 'GeometryNodeSetShadeSmooth', 1400, 0)
        output = newNode(tree, 'NodeGroupOutput', 1600, 0)

        # --- 3. DUAL NOISE TERRAIN MATH (EXACTLY FROM IMAGE) ---
        # Top Branch Nodes (Medium details)
        noise1 = newNode(tree, 'ShaderNodeTexNoise', -600, 300)
        map1 = newNode(tree, 'ShaderNodeMapRange', -400, 300)
        sub1 = newNode(tree, 'ShaderNodeMath', -200, 300)
        mult1 = newNode(tree, 'ShaderNodeMath', 0, 300)

        # Bottom Branch Nodes (Large sweeping mountains)
        noise2 = newNode(tree, 'ShaderNodeTexNoise', -600, -100)
        map2 = newNode(tree, 'ShaderNodeMapRange', -400, -100)
        sub2 = newNode(tree, 'ShaderNodeMath', -200, -100)
        mult2 = newNode(tree, 'ShaderNodeMath', 0, -100)

        # Math Combiners
        add_combo = newNode(tree, 'ShaderNodeMath', 200, 100)
        combine = newNode(tree, 'ShaderNodeCombineXYZ', 400, 100)

        # --- SET IMAGE VALUES ---
        if planeCreated: subdivide.inputs["Level"].default_value = 10
        
        # Top Branch Properties
        noise1.noise_dimensions = '4D'
        if hasattr(noise1, 'normalize'): noise1.normalize = True
        noise1.inputs["Scale"].default_value = 1.200
        noise1.inputs["Detail"].default_value = 8.000
        noise1.inputs["Roughness"].default_value = 0.583
        noise1.inputs["Lacunarity"].default_value = 2.000
        noise1.inputs["Distortion"].default_value = 1.000

        map1.interpolation_type = 'SMOOTHSTEP'
        map1.inputs["From Min"].default_value = 0.000
        map1.inputs["From Max"].default_value = 3.700
        map1.inputs["To Min"].default_value = 0.000
        map1.inputs["To Max"].default_value = 3.900

        sub1.operation = 'SUBTRACT'
        sub1.inputs[1].default_value = 0.500
        mult1.operation = 'MULTIPLY'
        mult1.inputs[1].default_value = 1.400

        # Bottom Branch Properties
        noise2.noise_dimensions = '4D'
        if hasattr(noise2, 'normalize'): noise2.normalize = True
        noise2.inputs["Scale"].default_value = 0.120
        noise2.inputs["Detail"].default_value = 2.000
        noise2.inputs["Roughness"].default_value = 0.500
        noise2.inputs["Lacunarity"].default_value = 0.000
        noise2.inputs["Distortion"].default_value = 0.000

        map2.interpolation_type = 'SMOOTHSTEP'
        map2.inputs["From Min"].default_value = 0.000
        map2.inputs["From Max"].default_value = 1.500
        map2.inputs["To Min"].default_value = 0.000
        map2.inputs["To Max"].default_value = 3.000

        sub2.operation = 'SUBTRACT'
        sub2.inputs[1].default_value = 0.500
        mult2.operation = 'MULTIPLY'
        mult2.inputs[1].default_value = 15.000
        
        add_combo.operation = 'ADD'

        # --- 4. ASSET SCATTERING NODES (POISSON DISK) ---
        # Random Generators for variety
        rand_rot = newNode(tree, 'FunctionNodeRandomValue', 400, -800)
        rand_rot.data_type = 'FLOAT_VECTOR'
        rand_rot.inputs['Min'].default_value = (0.0, 0.0, 0.0)
        rand_rot.inputs['Max'].default_value = (0.0, 0.0, math.pi * 2) # Random Z spin
        
        rand_scale = newNode(tree, 'FunctionNodeRandomValue', 400, -1000)
        rand_scale.data_type = 'FLOAT'
        rand_scale.inputs['Min'].default_value = 0.6 # Minimum asset size
        rand_scale.inputs['Max'].default_value = 1.4 # Maximum asset size

        # Tree Scattering Set
        dist_trees = newNode(tree, 'GeometryNodeDistributePointsOnFaces', 600, -200)
        dist_trees.distribute_method = 'POISSON'
        dist_trees.inputs['Distance Min'].default_value = 1.0 # Trees cant touch
        
        tree_info = newNode(tree, 'GeometryNodeObjectInfo', 600, -400)
        inst_trees = newNode(tree, 'GeometryNodeInstanceOnPoints', 1000, -200)
        
        # Rock Scattering Set
        dist_rocks = newNode(tree, 'GeometryNodeDistributePointsOnFaces', 600, -600)
        dist_rocks.distribute_method = 'POISSON'
        dist_rocks.inputs['Distance Min'].default_value = 0.3 # Rocks can be closer
        
        rock_info = newNode(tree, 'GeometryNodeObjectInfo', 600, -800)
        inst_rocks = newNode(tree, 'GeometryNodeInstanceOnPoints', 1000, -600)
        
        # Scale instances down globally so they fit the scene nicely
        inst_trees.inputs['Scale'].default_value = (0.3, 0.3, 0.3) 
        inst_rocks.inputs['Scale'].default_value = (0.2, 0.2, 0.2)
        
        # --- 5. CONNECT THE WIRES (LINKS) ---
        lks = tree.links
        
        # Terrain Geometry Data
        if planeCreated:
            lks.new(input_node.outputs["Geometry"], subdivide.inputs["Mesh"])
            lks.new(subdivide.outputs["Mesh"], setPos.inputs["Geometry"])
        else:
            lks.new(input_node.outputs["Geometry"], setPos.inputs["Geometry"])
            
        # Wire up Top Math
        lks.new(input_node.outputs["Seed"], noise1.inputs["W"])
        lks.new(noise1.outputs["Color"], map1.inputs["Value"])
        lks.new(map1.outputs["Result"], sub1.inputs[0])
        lks.new(sub1.outputs[0], mult1.inputs[0])

        # Wire up Bottom Math
        lks.new(input_node.outputs["Seed"], noise2.inputs["W"])
        lks.new(noise2.outputs["Color"], map2.inputs["Value"])
        lks.new(map2.outputs["Result"], sub2.inputs[0])
        lks.new(sub2.outputs[0], mult2.inputs[0])

        # Wire up Add/Combine to Set Position
        lks.new(mult1.outputs[0], add_combo.inputs[0])
        lks.new(mult2.outputs[0], add_combo.inputs[1])
        lks.new(add_combo.outputs[0], combine.inputs["Z"])
        lks.new(combine.outputs["Vector"], setPos.inputs["Offset"])
        
        # Wire up Trees
        lks.new(setPos.outputs[0], dist_trees.inputs["Mesh"])
        lks.new(input_node.outputs["Tree Density"], dist_trees.inputs["Density Max"])
        lks.new(input_node.outputs["Seed"], dist_trees.inputs["Seed"])
        lks.new(input_node.outputs["Tree Object"], tree_info.inputs["Object"])
        lks.new(dist_trees.outputs["Points"], inst_trees.inputs["Points"])
        lks.new(tree_info.outputs["Geometry"], inst_trees.inputs["Instance"])
        
        # Wire up Rocks
        lks.new(setPos.outputs[0], dist_rocks.inputs["Mesh"])
        lks.new(input_node.outputs["Rock Density"], dist_rocks.inputs["Density Max"])
        # Give rocks a slightly different seed so they don't spawn exactly under trees
        lks.new(input_node.outputs["Seed"], dist_rocks.inputs["Seed"]) 
        lks.new(input_node.outputs["Rock Object"], rock_info.inputs["Object"])
        lks.new(dist_rocks.outputs["Points"], inst_rocks.inputs["Points"])
        lks.new(rock_info.outputs["Geometry"], inst_rocks.inputs["Instance"])

        # Wire up Randomization to both Instances
        lks.new(rand_rot.outputs[0], inst_trees.inputs["Rotation"])
        lks.new(rand_rot.outputs[0], inst_rocks.inputs["Rotation"])
        
# Multiply our global scale by the random float for varied sizes
        # Spaced nicely between Object Info and Instances

        # 1. Tree Scaling Nodes
        math_scale_t = newNode(tree, 'ShaderNodeVectorMath', 800, -350)
        math_scale_t.operation = 'SCALE'
        math_scale_t.inputs[0].default_value = (0.25, 0.25, 0.25) # base tree scale
        
        lks.new(rand_scale.outputs["Value"], math_scale_t.inputs[3])
        lks.new(math_scale_t.outputs[0], inst_trees.inputs["Scale"])

        # 2. Rock Scaling Nodes
        math_scale_r = newNode(tree, 'ShaderNodeVectorMath', 800, -750)
        math_scale_r.operation = 'SCALE'
        math_scale_r.inputs[0].default_value = (0.15, 0.15, 0.15) # base rock scale
        

        lks.new(rand_scale.outputs["Value"], math_scale_r.inputs[3])
        lks.new(math_scale_r.outputs[0], inst_rocks.inputs["Scale"])

        # Join everything together
        lks.new(setPos.outputs[0], join1.inputs[0])
        lks.new(inst_trees.outputs[0], join1.inputs[0])
        lks.new(inst_rocks.outputs[0], join1.inputs[0])
        
        lks.new(join1.outputs[0], setSmooth.inputs["Mesh"])
        lks.new(setSmooth.outputs[0], output.inputs["Geometry"])

    # Push our default variables into the Modifier's UI on the right panel
    if mod.node_group:
        inputs = getattr(mod.node_group, "interface", mod.node_group).items_tree if hasattr(mod.node_group, "interface") else mod.node_group.inputs
        
        for item in inputs:
            if item.name == "Seed": mod[item.identifier] = MASTER_SEED
            if item.name == "Tree Object": mod[item.identifier] = tree_obj
            if item.name == "Rock Object": mod[item.identifier] = rock_obj
            if item.name == "Tree Density": mod[item.identifier] = TREE_DENSITY
            if item.name == "Rock Density": mod[item.identifier] = ROCK_DENSITY
    
    # Refresh Viewport
    obj.data.update_tag()
    mod.show_viewport = False
    mod.show_viewport = True
    bpy.context.view_layer.update()

# ==============================================================================
# 4. MAIN EXECUTION
# ==============================================================================
def main():
    # 1. Generate our custom assets
    pine_tree = generate_pine_tree()
    rock = generate_rock()
    
    # Deselect assets so they don't get accidentally turned into terrain
    bpy.ops.object.select_all(action='DESELECT')
    
    # 2. Check for or create base terrain
    if "Base Terrain" in bpy.data.objects:
        terrain_obj = bpy.data.objects["Base Terrain"]
        bpy.context.view_layer.objects.active = terrain_obj
        planeCreated = False
    else:
        # Generate a large flat plane
        bpy.ops.mesh.primitive_plane_add(size=SIZE, location=(0,0,0))
        terrain_obj = bpy.context.active_object
        terrain_obj.name = "Base Terrain"
        planeCreated = True

    # 3. Apply a Light Green Material to the terrain
    terrain_mat = get_or_create_material("Mat_Terrain", (0.35, 0.5, 0.25, 1.0)) 
    if len(terrain_obj.data.materials) == 0:
        terrain_obj.data.materials.append(terrain_mat)

    # 4. Apply the Geometry Nodes Modifier
    apply_terrain_nodes(terrain_obj, pine_tree, rock, planeCreated)

    print("\n--- Final Procedural World Generated Successfully ---")

if __name__ == "__main__":
    main()