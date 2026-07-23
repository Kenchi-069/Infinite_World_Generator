import bpy
import os
import json
import random

from .utils import new_node, get_or_create_material
from .terrain import build_terrain_node_group
from .vegetation import build_vegetation_node_group

def generate_pine_tree():
    name = "Procedural_Pine"
    if name in bpy.data.objects: return bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT')
    wood = get_or_create_material("Mat_Wood", (0.1, 0.05, 0.02, 1.0))
    leaf = get_or_create_material("Mat_Leaves", (0.05, 0.2, 0.08, 1.0))
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.2, depth=1.5, location=(0, 0, 0.75))
    trunk = bpy.context.active_object
    trunk.data.materials.append(wood)
    parts.append(trunk)
    z_heights, radii = [2.0, 3.0, 4.0], [1.2, 0.9, 0.6]
    for i in range(3):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=radii[i], depth=2.0-(i*0.2), location=(0, 0, z_heights[i]))
        layer = bpy.context.active_object
        layer.data.materials.append(leaf)
        parts.append(layer)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
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
    if name in bpy.data.objects: return bpy.data.objects[name]
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

class TerrainDataGenerator:
    def __init__(self, seed):
        self.seed = seed
        self.world_data = {} 

    def get_elevation(self, world_x, world_y):
        random.seed(f"{self.seed}_{world_x}_{world_y}")
        return random.uniform(0.0, 50.0)

    def generate_chunk_data(self, chunk_x, chunk_y, grid_resolution=16):
        chunk_key = f"{chunk_x},{chunk_y}"
        if chunk_key in self.world_data: return self.world_data[chunk_key]
        total_height = 0.0
        for local_x in range(grid_resolution):
            for local_y in range(grid_resolution):
                total_height += self.get_elevation((chunk_x * grid_resolution) + local_x, (chunk_y * grid_resolution) + local_y)
        chunk_data = {
            "chunk_coords": [chunk_x, chunk_y],
            "average_height": round(total_height / (grid_resolution**2), 1)
        }
        self.world_data[chunk_key] = chunk_data
        return chunk_data

    def save_world_to_json(self, filename):
        with open(filename, 'w') as f: json.dump(self.world_data, f, indent=4)
        print(f"World Data saved to: {filename}")

def build_master_pipeline(chunk_size):
    tree_name = "WG_Master_Pipeline"
    if tree_name in bpy.data.node_groups: 
        return bpy.data.node_groups[tree_name]
        
    tree = bpy.data.node_groups.new(name=tree_name, type='GeometryNodeTree')
    
    tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name="Master Seed", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Chunk Seed", in_out='INPUT', socket_type='NodeSocketInt')
    tree.interface.new_socket(name="Chunk X", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Chunk Y", in_out='INPUT', socket_type='NodeSocketFloat')
    
    tree.interface.new_socket(name="Subdivisions", in_out='INPUT', socket_type='NodeSocketInt')
    
    tree.interface.new_socket(name="Mountain Strength", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Snow Level", in_out='INPUT', socket_type='NodeSocketFloat')
    
    tree.interface.new_socket(name="Tree Object", in_out='INPUT', socket_type='NodeSocketObject')
    tree.interface.new_socket(name="Tree Density", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Rock Object", in_out='INPUT', socket_type='NodeSocketObject')
    tree.interface.new_socket(name="Rock Density", in_out='INPUT', socket_type='NodeSocketFloat')
    
    tree.interface.new_socket(name="Snow Material", in_out='INPUT', socket_type='NodeSocketMaterial')
    tree.interface.new_socket(name="Ground Material", in_out='INPUT', socket_type='NodeSocketMaterial')
    
    tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    IN = new_node(tree, 'NodeGroupInput', -800, 0)
    OUT = new_node(tree, 'NodeGroupOutput', 1200, 0)

    grid = new_node(tree, 'GeometryNodeMeshGrid', -400, 200)
    grid.inputs['Size X'].default_value = chunk_size
    grid.inputs['Size Y'].default_value = chunk_size
    grid.inputs['Vertices X'].default_value = 64
    grid.inputs['Vertices Y'].default_value = 64

    subdivide = new_node(tree, 'GeometryNodeSubdivideMesh', -200, 200)

    math_x = new_node(tree, 'ShaderNodeMath', -600, -100)
    math_y = new_node(tree, 'ShaderNodeMath', -600, -300)
    math_x.operation, math_y.operation = 'MULTIPLY', 'MULTIPLY'
    math_x.inputs[1].default_value, math_y.inputs[1].default_value = chunk_size, chunk_size
    
    comb_offset = new_node(tree, 'ShaderNodeCombineXYZ', -400, -200)
    pos_node = new_node(tree, 'GeometryNodeInputPosition', -400, -400)
    add_global_pos = new_node(tree, 'ShaderNodeVectorMath', -200, -300)
    add_global_pos.operation = 'ADD'

    grp_terrain = new_node(tree, 'GeometryNodeGroup', 0, 0)
    grp_terrain.node_tree = build_terrain_node_group()
    if "Ground Level" in grp_terrain.inputs: grp_terrain.inputs["Ground Level"].default_value = 2.0
    
    grp_veg = new_node(tree, 'GeometryNodeGroup', 300, 0)
    grp_veg.node_tree = build_vegetation_node_group()

    transform = new_node(tree, 'GeometryNodeTransform', 600, 0)
    shade_smooth = new_node(tree, 'GeometryNodeSetShadeSmooth', 900, 0)

    lks = tree.links
    
    lks.new(grid.outputs["Mesh"], subdivide.inputs["Mesh"])
    lks.new(IN.outputs["Subdivisions"], subdivide.inputs["Level"])
    lks.new(subdivide.outputs["Mesh"], grp_terrain.inputs["Grid"])
    
    lks.new(IN.outputs["Chunk X"], math_x.inputs[0])
    lks.new(IN.outputs["Chunk Y"], math_y.inputs[0])
    lks.new(math_x.outputs[0], comb_offset.inputs["X"])
    lks.new(math_y.outputs[0], comb_offset.inputs["Y"])
    lks.new(pos_node.outputs[0], add_global_pos.inputs[0])
    lks.new(comb_offset.outputs[0], add_global_pos.inputs[1])

    lks.new(add_global_pos.outputs[0], grp_terrain.inputs["Global Position"])
    lks.new(IN.outputs["Master Seed"], grp_terrain.inputs["Master Seed"])
    lks.new(IN.outputs["Mountain Strength"], grp_terrain.inputs["Mountain Strength"])
    lks.new(IN.outputs["Snow Level"], grp_terrain.inputs["Snow Level"])
    lks.new(IN.outputs["Snow Material"], grp_terrain.inputs["Snow Material"])
    lks.new(IN.outputs["Ground Material"], grp_terrain.inputs["Ground Material"])

    lks.new(grp_terrain.outputs["Terrain"], grp_veg.inputs["Terrain"])
    lks.new(IN.outputs["Chunk Seed"], grp_veg.inputs["Chunk Seed"])
    lks.new(IN.outputs["Tree Object"], grp_veg.inputs["Tree Object"])
    lks.new(IN.outputs["Tree Density"], grp_veg.inputs["Tree Density"])
    lks.new(IN.outputs["Rock Object"], grp_veg.inputs["Rock Object"])
    lks.new(IN.outputs["Rock Density"], grp_veg.inputs["Rock Density"])
    
    lks.new(grp_terrain.outputs["Is Ground"], grp_veg.inputs["Tree Mask"])

    lks.new(grp_veg.outputs["Vegetated Terrain"], transform.inputs["Geometry"])
    lks.new(comb_offset.outputs[0], transform.inputs["Translation"])
    
    lks.new(transform.outputs[0], shade_smooth.inputs["Geometry"])
    lks.new(shade_smooth.outputs[0], OUT.inputs["Geometry"])

    return tree

def execute_world_generation(props):
    for obj in bpy.data.objects:
        if obj.name.startswith("Chunk_") or obj.name.startswith("Terrain_Generation_") or obj.name.startswith("Procedural_"):
            bpy.data.objects.remove(obj, do_unlink=True)
            
    data_gen = TerrainDataGenerator(seed=props.seed)
    master_tree = build_master_pipeline(props.chunk_size)
    
    tree_obj = generate_pine_tree()
    rock_obj = generate_rock()
    mat_s = get_or_create_material("Mat_Snow", (0.9, 0.9, 0.95, 1.0))
    mat_g = get_or_create_material("Mat_Grass", (0.35, 0.5, 0.25, 1.0))

    parent_name = f"Terrain_Generation_{props.seed}"
    parent_empty = bpy.data.objects.new(parent_name, None)
    bpy.context.collection.objects.link(parent_empty)

    half_x = props.grid_size_x // 2
    half_y = props.grid_size_y // 2

    for cx in range(-half_x, props.grid_size_x - half_x):
        for cy in range(-half_y, props.grid_size_y - half_y):
            data_gen.generate_chunk_data(cx, cy)
            
            chunk_name = f"Chunk_{cx}_{cy}"
            chunk_obj = bpy.data.objects.new(chunk_name, bpy.data.meshes.new(chunk_name + "_Mesh"))
            
            chunk_obj.parent = parent_empty
            bpy.context.collection.objects.link(chunk_obj)
            
            mod = chunk_obj.modifiers.new(name="World_Generator", type='NODES')
            mod.node_group = master_tree
            
            random.seed(f"{props.seed}_{cx}_{cy}")
            
            values_to_set = {
                "Master Seed": float(props.seed),
                "Chunk Seed": int(random.uniform(0, 10000)),
                "Chunk X": float(cx),
                "Chunk Y": float(cy),
                "Subdivisions": props.subdivisions,
                "Mountain Strength": props.mountain_strength,
                "Snow Level": props.snow_level,
                "Tree Object": tree_obj,
                "Tree Density": props.tree_density,
                "Rock Object": rock_obj,
                "Rock Density": props.rock_density,
                "Snow Material": mat_s,
                "Ground Material": mat_g
            }

            for item in master_tree.interface.items_tree:
                if item.name in values_to_set:
                    socket_attr = item.identifier 
                    val = values_to_set[item.name]
                    getattr(mod.properties.inputs, socket_attr).value = val

    save_dir = os.path.dirname(bpy.data.filepath) if bpy.data.is_saved else os.path.expanduser("~")
    data_gen.save_world_to_json(os.path.join(save_dir, "procedural_world.json"))
    
    bpy.context.view_layer.update()