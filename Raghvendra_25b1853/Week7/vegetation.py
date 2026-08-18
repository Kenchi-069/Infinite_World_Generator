import bpy
import math
from .utils import new_node

def build_vegetation_node_group():
    group_name = "WG_Vegetation_Scatter"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]
        
    tree = bpy.data.node_groups.new(name=group_name, type='GeometryNodeTree')
    
    tree.interface.new_socket(name="Terrain", in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name="Chunk Seed", in_out='INPUT', socket_type='NodeSocketInt')
    
    tree.interface.new_socket(name="Tree Object", in_out='INPUT', socket_type='NodeSocketObject')
    tree.interface.new_socket(name="Tree Density", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Tree Mask", in_out='INPUT', socket_type='NodeSocketBool')
    
    tree.interface.new_socket(name="Rock Object", in_out='INPUT', socket_type='NodeSocketObject')
    tree.interface.new_socket(name="Rock Density", in_out='INPUT', socket_type='NodeSocketFloat')

    tree.interface.new_socket(name="Vegetated Terrain", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    IN = new_node(tree, 'NodeGroupInput', -800, 0)
    
    seed_offset = new_node(tree, 'ShaderNodeMath', -600, -200)
    seed_offset.operation = 'ADD'
    seed_offset.inputs[1].default_value = 42.0

    dist_trees = new_node(tree, 'GeometryNodeDistributePointsOnFaces', -400, 200)
    dist_trees.distribute_method = 'POISSON'
    dist_trees.inputs['Distance Min'].default_value = 1.5 
    
    dist_rocks = new_node(tree, 'GeometryNodeDistributePointsOnFaces', -400, -200)
    dist_rocks.distribute_method = 'POISSON'
    dist_rocks.inputs['Distance Min'].default_value = 0.5 

    tree_info = new_node(tree, 'GeometryNodeObjectInfo', -400, 400)
    rock_info = new_node(tree, 'GeometryNodeObjectInfo', -400, -400)

    rand_rot = new_node(tree, 'FunctionNodeRandomValue', -200, 600)
    rand_rot.data_type = 'FLOAT_VECTOR'
    rand_rot.inputs['Max'].default_value = (0.0, 0.0, math.pi * 2) 
    
    rand_scale = new_node(tree, 'FunctionNodeRandomValue', -200, 800)
    rand_scale.data_type = 'FLOAT'
    rand_scale.inputs['Min'].default_value = 0.6 
    rand_scale.inputs['Max'].default_value = 1.4 

    math_scale_t = new_node(tree, 'ShaderNodeVectorMath', 0, 400)
    math_scale_t.operation = 'SCALE'
    math_scale_t.inputs[0].default_value = (0.25, 0.25, 0.25)
    
    math_scale_r = new_node(tree, 'ShaderNodeVectorMath', 0, -400)
    math_scale_r.operation = 'SCALE'
    math_scale_r.inputs[0].default_value = (0.15, 0.15, 0.15) 

    inst_trees = new_node(tree, 'GeometryNodeInstanceOnPoints', 200, 200)
    inst_rocks = new_node(tree, 'GeometryNodeInstanceOnPoints', 200, -200)

    join1 = new_node(tree, 'GeometryNodeJoinGeometry', 500, 0)
    OUT = new_node(tree, 'NodeGroupOutput', 700, 0)

    lks = tree.links
    
    lks.new(IN.outputs["Chunk Seed"], dist_trees.inputs["Seed"])
    lks.new(IN.outputs["Chunk Seed"], seed_offset.inputs[0])
    lks.new(seed_offset.outputs[0], dist_rocks.inputs["Seed"])

    lks.new(IN.outputs["Terrain"], dist_trees.inputs["Mesh"])
    lks.new(IN.outputs["Tree Mask"], dist_trees.inputs["Selection"])  
    lks.new(IN.outputs["Tree Density"], dist_trees.inputs["Density Max"])
    
    lks.new(IN.outputs["Terrain"], dist_rocks.inputs["Mesh"])

    lks.new(IN.outputs["Rock Density"], dist_rocks.inputs["Density Max"])

    lks.new(IN.outputs["Tree Object"], tree_info.inputs["Object"])
    lks.new(IN.outputs["Rock Object"], rock_info.inputs["Object"])
    
    lks.new(rand_rot.outputs[0], inst_trees.inputs["Rotation"])
    lks.new(rand_rot.outputs[0], inst_rocks.inputs["Rotation"])
    
    lks.new(rand_scale.outputs["Value"], math_scale_t.inputs[3])
    lks.new(math_scale_t.outputs[0], inst_trees.inputs["Scale"])
    
    lks.new(rand_scale.outputs["Value"], math_scale_r.inputs[3])
    lks.new(math_scale_r.outputs[0], inst_rocks.inputs["Scale"])

    lks.new(dist_trees.outputs["Points"], inst_trees.inputs["Points"])
    lks.new(tree_info.outputs["Geometry"], inst_trees.inputs["Instance"])
    
    lks.new(dist_rocks.outputs["Points"], inst_rocks.inputs["Points"])
    lks.new(rock_info.outputs["Geometry"], inst_rocks.inputs["Instance"])

    lks.new(IN.outputs["Terrain"], join1.inputs[0])
    lks.new(inst_trees.outputs[0], join1.inputs[0])
    lks.new(inst_rocks.outputs[0], join1.inputs[0])
    lks.new(join1.outputs[0], OUT.inputs["Vegetated Terrain"])

    return tree