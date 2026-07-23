import bpy
from .utils import new_node

def build_terrain_node_group():
    group_name = "WG_Terrain_Biome_Gen"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]
        
    tree = bpy.data.node_groups.new(name=group_name, type='GeometryNodeTree')
    
    tree.interface.new_socket(name="Grid", in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name="Global Position", in_out='INPUT', socket_type='NodeSocketVector')
    tree.interface.new_socket(name="Master Seed", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Mountain Strength", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Ground Level", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Snow Level", in_out='INPUT', socket_type='NodeSocketFloat')
    tree.interface.new_socket(name="Snow Material", in_out='INPUT', socket_type='NodeSocketMaterial')
    tree.interface.new_socket(name="Ground Material", in_out='INPUT', socket_type='NodeSocketMaterial')

    tree.interface.new_socket(name="Terrain", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name="Is Ground", in_out='OUTPUT', socket_type='NodeSocketBool')

    IN = new_node(tree, 'NodeGroupInput', -800, 0)
    
    n1 = new_node(tree, 'ShaderNodeTexNoise', -400, 300)
    m1 = new_node(tree, 'ShaderNodeMapRange', -200, 300)
    s1 = new_node(tree, 'ShaderNodeMath', 0, 300)
    mul1 = new_node(tree, 'ShaderNodeMath', 200, 300)

    n1.noise_dimensions = '4D'
    n1.inputs["Scale"].default_value, n1.inputs["Detail"].default_value = 0.3, 8.0
    m1.interpolation_type, m1.inputs["From Max"].default_value, m1.inputs["To Max"].default_value = 'SMOOTHSTEP', 3.7, 3.9
    s1.operation, s1.inputs[1].default_value = 'SUBTRACT', 0.5
    mul1.operation, mul1.inputs[1].default_value = 'MULTIPLY', 1.2

    n2 = new_node(tree, 'ShaderNodeTexNoise', -400, -100)
    m2 = new_node(tree, 'ShaderNodeMapRange', -200, -100)
    s2 = new_node(tree, 'ShaderNodeMath', 0, -100)
    mul2 = new_node(tree, 'ShaderNodeMath', 200, -100)

    n2.noise_dimensions = '4D'
    n2.inputs["Scale"].default_value, n2.inputs["Detail"].default_value = 0.08, 2.0
    m2.interpolation_type, m2.inputs["From Max"].default_value, m2.inputs["To Max"].default_value = 'SMOOTHSTEP', 1.5, 3.0
    s2.operation, s2.inputs[1].default_value = 'SUBTRACT', 0.5
    mul2.operation = 'MULTIPLY' 

    add_combo = new_node(tree, 'ShaderNodeMath', 400, 100)
    add_combo.operation = 'ADD'
    
    math_max = new_node(tree, 'ShaderNodeMath', 600, 100)
    math_max.operation = 'MAXIMUM'
    
    combine_z = new_node(tree, 'ShaderNodeCombineXYZ', 800, 100)
    set_pos = new_node(tree, 'GeometryNodeSetPosition', 1000, 100)
    
    pos_snow = new_node(tree, 'GeometryNodeInputPosition', 800, -100)
    sep_snow = new_node(tree, 'ShaderNodeSeparateXYZ', 1000, -100)
    comp_snow = new_node(tree, 'ShaderNodeMath', 1200, -100)
    comp_snow.operation = 'GREATER_THAN'
    
    bool_not = new_node(tree, 'FunctionNodeBooleanMath', 1400, -100)
    bool_not.operation = 'NOT'

    mat_ground = new_node(tree, 'GeometryNodeSetMaterial', 1400, 100)
    mat_snow = new_node(tree, 'GeometryNodeSetMaterial', 1600, 100)
    
    OUT = new_node(tree, 'NodeGroupOutput', 1800, 100)

    lks = tree.links
    
    lks.new(IN.outputs["Global Position"], n1.inputs["Vector"])
    lks.new(IN.outputs["Global Position"], n2.inputs["Vector"])
    lks.new(IN.outputs["Master Seed"], n1.inputs["W"])
    lks.new(IN.outputs["Master Seed"], n2.inputs["W"])
    lks.new(IN.outputs["Mountain Strength"], mul2.inputs[1])

    lks.new(n1.outputs["Color"], m1.inputs["Value"])
    lks.new(m1.outputs["Result"], s1.inputs[0])
    lks.new(s1.outputs[0], mul1.inputs[0])

    lks.new(n2.outputs["Color"], m2.inputs["Value"])
    lks.new(m2.outputs["Result"], s2.inputs[0])
    lks.new(s2.outputs[0], mul2.inputs[0])
    
    lks.new(mul1.outputs[0], add_combo.inputs[0])
    lks.new(mul2.outputs[0], add_combo.inputs[1])
    
    lks.new(add_combo.outputs[0], math_max.inputs[0])
    lks.new(IN.outputs["Ground Level"], math_max.inputs[1])
    lks.new(math_max.outputs[0], combine_z.inputs["Z"])
    lks.new(IN.outputs["Grid"], set_pos.inputs["Geometry"])
    lks.new(combine_z.outputs["Vector"], set_pos.inputs["Offset"])
    

    lks.new(pos_snow.outputs[0], sep_snow.inputs[0])
    lks.new(IN.outputs["Snow Level"], comp_snow.inputs[0]) 
    lks.new(sep_snow.outputs["Z"], comp_snow.inputs[1])    
    lks.new(comp_snow.outputs[0], bool_not.inputs[0])
    
    lks.new(set_pos.outputs[0], mat_ground.inputs["Geometry"])
    lks.new(IN.outputs["Ground Material"], mat_ground.inputs["Material"])
    
    lks.new(mat_ground.outputs[0], mat_snow.inputs["Geometry"])
    lks.new(bool_not.outputs[0], mat_snow.inputs["Selection"]) 
    lks.new(IN.outputs["Snow Material"], mat_snow.inputs["Material"])

    lks.new(mat_snow.outputs[0], OUT.inputs["Terrain"])
    lks.new(comp_snow.outputs[0], OUT.inputs["Is Ground"]) 

    return tree