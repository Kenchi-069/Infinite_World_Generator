# Procedural chunk-based world generator
# Passes absolute chunk locations to the modifier to ensure seamless global coordinate math.

import bpy
import random
import math
import json
import os

MASTER_SEED = 2025
CHUNK_SIZE = 25 
TREE_DENSITY = 15.0
ROCK_DENSITY = 25.0 

class TerrainDataGenerator:
    def __init__(self, seed):
        self.seed = seed
        self.world_data = {} 

    def get_elevation(self, world_x, world_y):
        coord_seed = f"{self.seed}_{world_x}_{world_y}"
        random.seed(coord_seed)
        return random.uniform(0.0, 50.0)

    def generate_chunk_data(self, chunk_x, chunk_y):
        chunk_key = f"{chunk_x},{chunk_y}"
        if chunk_key in self.world_data: 
            return self.world_data[chunk_key]

        total_height = 0.0
        grid_resolution = 16 
        for local_x in range(grid_resolution):
            for local_y in range(grid_resolution):
                world_x = (chunk_x * grid_resolution) + local_x
                world_y = (chunk_y * grid_resolution) + local_y
                total_height += self.get_elevation(world_x, world_y)

        avg_height = total_height / (grid_resolution * grid_resolution)

        chunk_data = {
            "chunk_coords": [chunk_x, chunk_y],
            "average_height": round(avg_height, 1)
        }
        self.world_data[chunk_key] = chunk_data
        return chunk_data

    def save_world_to_json(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.world_data, f, indent=4)
        print(f"World Data saved to: {filename}")


def get_or_create_material(name, color):
    if name not in bpy.data.materials:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf: 
            bsdf.inputs["Base Color"].default_value = color
    return bpy.data.materials[name]

def generate_pine_tree():
    name = "Procedural_Pine"
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        
    bpy.ops.object.select_all(action='DESELECT')
    wood_mat = get_or_create_material("Mat_Wood", (0.1, 0.05, 0.02, 1.0))
    leaf_mat = get_or_create_material("Mat_Leaves", (0.05, 0.2, 0.08, 1.0))
    
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.2, depth=1.5, location=(0, 0, 0.75))
    trunk = bpy.context.active_object
    trunk.data.materials.append(wood_mat)
    parts.append(trunk)
    
    z_heights = [2.0, 3.0, 4.0]
    radii = [1.2, 0.9, 0.6]
    for i in range(3):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=radii[i], depth=2.0-(i*0.2), location=(0, 0, z_heights[i]))
        layer = bpy.context.active_object
        layer.data.materials.append(leaf_mat)
        parts.append(layer)
    
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: 
        p.select_set(True)
    bpy.context.view_layer.objects.active = trunk
    bpy.ops.object.join()
    
    tree = bpy.context.active_object
    tree.name = name
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    tree.location = (100, 100, 0)
    return tree

def generate_rock():
    name = "Procedural_Rock"
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        
    bpy.ops.object.select_all(action='DESELECT')
    rock_mat = get_or_create_material("Mat_Rock", (0.3, 0.3, 0.3, 1.0))
    
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.6, location=(0, 0, 0.2))
    rock = bpy.context.active_object
    rock.data.materials.append(rock_mat)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.vertex_random(offset=0.2)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    rock.name = name
    rock.scale.z = 0.6
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    rock.location = (100, 105, 0)
    return rock

def newNode(node_tree, type_name, loc_x, loc_y):
    _node = node_tree.nodes.new(type=type_name)
    _node.location.x = loc_x
    _node.location.y = loc_y
    return _node

def apply_terrain_nodes(obj, tree_obj, rock_obj, master_seed, chunk_seed, chunk_loc):
    mod_name = "Landscape_Generator"
    
    if mod_name not in obj.modifiers:
        mod = obj.modifiers.new(name=mod_name, type='NODES')
    else:
        mod = obj.modifiers[mod_name]
    
    if not mod.node_group:
        tree = bpy.data.node_groups.new(name=mod_name, type='GeometryNodeTree')
        mod.node_group = tree
        
        # Interface setup
        tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        tree.interface.new_socket(name="Master Seed", in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket(name="Chunk Seed", in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket(name="Chunk Location", in_out='INPUT', socket_type='NodeSocketVector')
        tree.interface.new_socket(name="Tree Object", in_out='INPUT', socket_type='NodeSocketObject')
        tree.interface.new_socket(name="Tree Density", in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket(name="Rock Object", in_out='INPUT', socket_type='NodeSocketObject')
        tree.interface.new_socket(name="Rock Density", in_out='INPUT', socket_type='NodeSocketFloat')

        input_node = newNode(tree, 'NodeGroupInput', -1000, 0)
        subdivide = newNode(tree, 'GeometryNodeSubdivideMesh', 400, 200)
        subdivide.inputs["Level"].default_value = 8
        setPos = newNode(tree, 'GeometryNodeSetPosition', 600, 0)
        join1 = newNode(tree, 'GeometryNodeJoinGeometry', 1200, 0)
        setSmooth = newNode(tree, 'GeometryNodeSetShadeSmooth', 1400, 0)
        output = newNode(tree, 'NodeGroupOutput', 1600, 0)

        # Global coordinate offset
        pos_node = newNode(tree, 'GeometryNodeInputPosition', -1000, 450)
        add_pos = newNode(tree, 'ShaderNodeVectorMath', -800, 400)
        add_pos.operation = 'ADD'

        noise1 = newNode(tree, 'ShaderNodeTexNoise', -600, 300)
        map1 = newNode(tree, 'ShaderNodeMapRange', -400, 300)
        sub1 = newNode(tree, 'ShaderNodeMath', -200, 300)
        mult1 = newNode(tree, 'ShaderNodeMath', 0, 300)

        noise2 = newNode(tree, 'ShaderNodeTexNoise', -600, -100)
        map2 = newNode(tree, 'ShaderNodeMapRange', -400, -100)
        sub2 = newNode(tree, 'ShaderNodeMath', -200, -100)
        mult2 = newNode(tree, 'ShaderNodeMath', 0, -100)

        add_combo = newNode(tree, 'ShaderNodeMath', 200, 100)
        combine = newNode(tree, 'ShaderNodeCombineXYZ', 400, 100)

        noise1.noise_dimensions = '4D'
        noise1.inputs["Scale"].default_value = 0.300
        noise1.inputs["Detail"].default_value = 8.000
        noise1.inputs["Roughness"].default_value = 0.583
        noise1.inputs["Lacunarity"].default_value = 2.000
        
        map1.interpolation_type = 'SMOOTHSTEP'
        map1.inputs["From Max"].default_value = 3.700
        map1.inputs["To Max"].default_value = 3.900
        sub1.operation = 'SUBTRACT'
        sub1.inputs[1].default_value = 0.500
        mult1.operation = 'MULTIPLY'
        mult1.inputs[1].default_value = 1.200

        noise2.noise_dimensions = '4D'
        noise2.inputs["Scale"].default_value = 0.080
        noise2.inputs["Detail"].default_value = 2.000
        noise2.inputs["Roughness"].default_value = 0.500
        noise2.inputs["Lacunarity"].default_value = 1.400

        map2.interpolation_type = 'SMOOTHSTEP'
        map2.inputs["From Max"].default_value = 1.500
        map2.inputs["To Max"].default_value = 3.000
        sub2.operation = 'SUBTRACT'
        sub2.inputs[1].default_value = 0.500
        mult2.operation = 'MULTIPLY'
        mult2.inputs[1].default_value = 15.000
        
        add_combo.operation = 'ADD'

        rand_rot = newNode(tree, 'FunctionNodeRandomValue', 400, -800)
        rand_rot.data_type = 'FLOAT_VECTOR'
        rand_rot.inputs['Max'].default_value = (0.0, 0.0, math.pi * 2) 
        
        rand_scale = newNode(tree, 'FunctionNodeRandomValue', 400, -1000)
        rand_scale.data_type = 'FLOAT'
        rand_scale.inputs['Min'].default_value = 0.6 
        rand_scale.inputs['Max'].default_value = 1.4 

        dist_trees = newNode(tree, 'GeometryNodeDistributePointsOnFaces', 600, -200)
        dist_trees.distribute_method = 'POISSON'
        dist_trees.inputs['Distance Min'].default_value = 1.5 
        tree_info = newNode(tree, 'GeometryNodeObjectInfo', 600, -400)
        inst_trees = newNode(tree, 'GeometryNodeInstanceOnPoints', 1000, -200)
        
        dist_rocks = newNode(tree, 'GeometryNodeDistributePointsOnFaces', 600, -600)
        dist_rocks.distribute_method = 'POISSON'
        dist_rocks.inputs['Distance Min'].default_value = 0.5 
        rock_info = newNode(tree, 'GeometryNodeObjectInfo', 600, -800)
        inst_rocks = newNode(tree, 'GeometryNodeInstanceOnPoints', 1000, -600)
        
        math_scale_t = newNode(tree, 'ShaderNodeVectorMath', 800, -350)
        math_scale_t.operation = 'SCALE'
        math_scale_t.inputs[0].default_value = (0.25, 0.25, 0.25)
        
        math_scale_r = newNode(tree, 'ShaderNodeVectorMath', 800, -750)
        math_scale_r.operation = 'SCALE'
        math_scale_r.inputs[0].default_value = (0.15, 0.15, 0.15) 

        # Node connections
        lks = tree.links
        
        lks.new(pos_node.outputs[0], add_pos.inputs[0])
        lks.new(input_node.outputs["Chunk Location"], add_pos.inputs[1])
        
        lks.new(add_pos.outputs[0], noise1.inputs["Vector"])
        lks.new(add_pos.outputs[0], noise2.inputs["Vector"])
        
        lks.new(input_node.outputs["Master Seed"], noise1.inputs["W"])
        lks.new(input_node.outputs["Master Seed"], noise2.inputs["W"])
        lks.new(input_node.outputs["Chunk Seed"], dist_trees.inputs["Seed"])
        lks.new(input_node.outputs["Chunk Seed"], dist_rocks.inputs["Seed"])

        lks.new(input_node.outputs["Geometry"], subdivide.inputs["Mesh"])
        lks.new(subdivide.outputs["Mesh"], setPos.inputs["Geometry"])
            
        lks.new(noise1.outputs["Color"], map1.inputs["Value"])
        lks.new(map1.outputs["Result"], sub1.inputs[0])
        lks.new(sub1.outputs[0], mult1.inputs[0])

        lks.new(noise2.outputs["Color"], map2.inputs["Value"])
        lks.new(map2.outputs["Result"], sub2.inputs[0])
        lks.new(sub2.outputs[0], mult2.inputs[0])

        lks.new(mult1.outputs[0], add_combo.inputs[0])
        lks.new(mult2.outputs[0], add_combo.inputs[1])
        lks.new(add_combo.outputs[0], combine.inputs["Z"])
        lks.new(combine.outputs["Vector"], setPos.inputs["Offset"])
        
        lks.new(setPos.outputs[0], dist_trees.inputs["Mesh"])
        lks.new(input_node.outputs["Tree Density"], dist_trees.inputs["Density Max"])
        lks.new(input_node.outputs["Tree Object"], tree_info.inputs["Object"])
        lks.new(dist_trees.outputs["Points"], inst_trees.inputs["Points"])
        lks.new(tree_info.outputs["Geometry"], inst_trees.inputs["Instance"])
        
        lks.new(setPos.outputs[0], dist_rocks.inputs["Mesh"])
        lks.new(input_node.outputs["Rock Density"], dist_rocks.inputs["Density Max"])
        lks.new(input_node.outputs["Rock Object"], rock_info.inputs["Object"])
        lks.new(dist_rocks.outputs["Points"], inst_rocks.inputs["Points"])
        lks.new(rock_info.outputs["Geometry"], inst_rocks.inputs["Instance"])

        lks.new(rand_rot.outputs[0], inst_trees.inputs["Rotation"])
        lks.new(rand_rot.outputs[0], inst_rocks.inputs["Rotation"])
        lks.new(rand_scale.outputs["Value"], math_scale_t.inputs[3])
        lks.new(math_scale_t.outputs[0], inst_trees.inputs["Scale"])
        lks.new(rand_scale.outputs["Value"], math_scale_r.inputs[3])
        lks.new(math_scale_r.outputs[0], inst_rocks.inputs["Scale"])

        lks.new(setPos.outputs[0], join1.inputs[0])
        lks.new(inst_trees.outputs[0], join1.inputs[0])
        lks.new(inst_rocks.outputs[0], join1.inputs[0])
        lks.new(join1.outputs[0], setSmooth.inputs["Mesh"])
        lks.new(setSmooth.outputs[0], output.inputs["Geometry"])

    # Push parameter values to the modifier
    if mod.node_group:
        inputs = getattr(mod.node_group, "interface", mod.node_group).items_tree if hasattr(mod.node_group, "interface") else mod.node_group.inputs
        for item in inputs:
            if item.name == "Master Seed": mod[item.identifier] = master_seed
            if item.name == "Chunk Seed": mod[item.identifier] = chunk_seed
            if item.name == "Chunk Location": mod[item.identifier] = chunk_loc 
            if item.name == "Tree Object": mod[item.identifier] = tree_obj
            if item.name == "Rock Object": mod[item.identifier] = rock_obj
            if item.name == "Tree Density": mod[item.identifier] = TREE_DENSITY
            if item.name == "Rock Density": mod[item.identifier] = ROCK_DENSITY
    
    obj.data.update_tag()
    bpy.context.view_layer.update()


def clear_old_chunks():
    for obj in bpy.data.objects:
        if obj.name.startswith("Chunk_"):
            bpy.data.objects.remove(obj, do_unlink=True)

def main():
    print(f"\n--- Starting Generation (Seed: {MASTER_SEED}) ---")
    clear_old_chunks()
    
    data_generator = TerrainDataGenerator(seed=MASTER_SEED)
    pine_tree = generate_pine_tree()
    rock = generate_rock()
    terrain_mat = get_or_create_material("Mat_Terrain", (0.35, 0.5, 0.25, 1.0))

    chunks_to_load = [
        (0, 0), (1, 0), (2, 0),(3,0),
        (0, 1), (1, 1), (2, 1),(3,1),
        (0, 2), (1, 2), (2, 2),(3,2),
        (0,3), (1,3), (2,3), 
    ]

    for cx, cy in chunks_to_load:
        chunk_data = data_generator.generate_chunk_data(cx, cy)
        
        x_loc = cx * CHUNK_SIZE
        y_loc = cy * CHUNK_SIZE
        
        random.seed(f"{MASTER_SEED}_{cx}_{cy}")
        chunk_visual_seed = int(random.uniform(0, 10000))

        bpy.ops.mesh.primitive_plane_add(size=CHUNK_SIZE, location=(x_loc, y_loc, 0))
        chunk_plane = bpy.context.active_object
        chunk_plane.name = f"Chunk_{cx}_{cy}"
        
        if len(chunk_plane.data.materials) == 0:
            chunk_plane.data.materials.append(terrain_mat)
            
        apply_terrain_nodes(chunk_plane, pine_tree, rock, MASTER_SEED, chunk_visual_seed, (x_loc, y_loc, 0.0))

    if bpy.data.is_saved:
        save_dir = os.path.dirname(bpy.data.filepath)
    else:
        save_dir = os.path.expanduser("~")
        
    safe_save_path = os.path.join(save_dir, "procedural_world.json")
    data_generator.save_world_to_json(filename=safe_save_path)
    
    print("--- World Generation Complete ---")

if __name__ == "__main__":
    main()