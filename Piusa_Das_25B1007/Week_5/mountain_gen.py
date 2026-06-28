import bpy
from math import pi

so=bpy.data.objects.get("Mountain")
if so is None:
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=512,
        y_subdivisions=512,
        size=2,
        enter_editmode=False,
        align='WORLD',
        location=(0, 0, 0),
        scale=(1, 1, 1)
        )
    so=bpy.context.active_object
    so.name="Mountain"

else:
    bpy.context.view_layer.objects.active=so
    so.select_set(True)

geo=so.modifiers.get("GeometryNodes")

if geo is None:
    geo=so.modifiers.new("GeometryNodes", "NODES")

if geo.node_group is None:
    geo.node_group=bpy.data.node_groups.new(
        "TerrainNodes",
        "GeometryNodeTree"
    )

    tree=geo.node_group

    tree.interface.new_socket(
        name="Geometry",
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )

    tree.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

tree=geo.node_group
    
mat=bpy.data.materials.get("TerrainMaterial")

if mat is None:
    mat=bpy.data.materials.new("TerrainMaterial")
    mat.use_nodes=True
    so.data.materials.clear()
    so.data.materials.append(mat)
else:
    if len(so.data.materials):
        so.data.materials[0]=mat
    else:
        so.data.materials.append(mat)

tree=geo.node_group

mat.use_nodes=True
nodes=mat.node_tree.nodes
links=mat.node_tree.links
nodes.clear()

#helper functions

#to make node of a type and set its location
def node(node_type, x=0, y=0):
    n = tree.nodes.new(node_type)
    n.location = (x, y)
    return n

#to make links between output of first node and input of second node
def link(out_node, out_socket, in_node, in_socket):
    tree.links.new(
        out_node.outputs[out_socket],
        in_node.inputs[in_socket]
    )

#to generate masks with different settings    
def make_mask(x, y, axis, from_min, from_max, to_min, to_max):
    pos=node("GeometryNodeInputPosition", x-100, y)
    sep=node("ShaderNodeSeparateXYZ", x, y)
    map_range=node("ShaderNodeMapRange", x+100, y)
    map_range.inputs[1].default_value=from_min
    map_range.inputs[2].default_value=from_max
    map_range.inputs[3].default_value=to_min
    map_range.inputs[4].default_value=to_max
    link(pos, "Position", sep, "Vector")
    link(sep, axis, map_range, "Value")
    return map_range
            
#to multiply two nodes
def multiply_nodes(node1, socket1, node2, socket2, x, y):
    mul = node("ShaderNodeMath", x, y)
    mul.operation = "MULTIPLY"
    link(node1, socket1, mul, 0)
    link(node2, socket2, mul, 1)
    return mul

#remove original nodes and links
tree.nodes.clear()
tree.links.clear()

#add group input and group output
tree.interface.new_socket(
    name="Geometry",
    in_out='INPUT',
    socket_type='NodeSocketGeometry'
)

tree.interface.new_socket(
    name="Geometry",
    in_out='OUTPUT',
    socket_type='NodeSocketGeometry'
)
group_input=tree.nodes.new("NodeGroupInput")
group_output=tree.nodes.new("NodeGroupOutput")

group_input.location=(-1200, 0)
group_output.location=(1200, 0)

#add set position node
set_position = node("GeometryNodeSetPosition", -100, 0)

#add noise texture node
noise_tex=node("ShaderNodeTexNoise", -750, -80)
noise_tex.noise_dimensions="4D"
noise_tex.inputs[1].default_value=0.0 #property
noise_tex.inputs[2].default_value=2.5 #property
noise_tex.inputs[3].default_value=5.0
noise_tex.inputs[4].default_value=0.25 #property

#add combine xyz node
comb_xyz=node("ShaderNodeCombineXYZ", -250,-70)

#add map nodes
map_y_left=make_mask(-300, 400, "Y", -1, 0, 0, 1)
map_y_right=make_mask(-300, 0, "Y", 0, 1, 1, 0)
y_mul=multiply_nodes(map_y_left, 0, map_y_right, 0, -200, 200)

map_x_left=make_mask(-300, -400, "X", -1, 0, 0, 1)
map_x_right=make_mask(-300, -800, "X", 0, 1, 1, 0)
x_mul=multiply_nodes(map_x_left, 0, map_x_right, 0, -200, -600)

#create final map
final_map=multiply_nodes(y_mul, 0, x_mul, 0, -100, -200)
        
#multiply with noise texture
final_noise=multiply_nodes(final_map, 0, noise_tex, 0, -100, -500)
        
#multiply with height
height=node("ShaderNodeValue", -100, 400)
height.outputs[0].default_value=1.0 #property
last_one=multiply_nodes(final_noise, 0, height, 0, -100, 250)

#add shade smooth node
shade_smo=node("GeometryNodeSetShadeSmooth")

#adding tree nodes
dist_points=node("GeometryNodeDistributePointsOnFaces")
dist_points.distribute_method='POISSON'
dist_points.inputs[2].default_value=0.001
dist_points.inputs[3].default_value=100.0 #property
dist_points.inputs[6].default_value=0 #property
link(shade_smo, 0, dist_points, "Mesh")

instance=node("GeometryNodeInstanceOnPoints")

link(dist_points, "Points", instance, "Points")

obj=node("GeometryNodeObjectInfo")
obj.inputs[0].default_value=bpy.data.objects["tree_hp_01"]
obj.inputs["As Instance"].default_value=True
link(obj, "Geometry", instance, "Instance")

join=node("GeometryNodeJoinGeometry")
link(instance, "Instances", join, "Geometry")
link(shade_smo, 0, join, 0)
link(join, 0, group_output, 0)

#editing trees to appear random in scale and rotation
scale=node("FunctionNodeRandomValue")
scale.inputs[2].default_value=0.001
scale.inputs[3].default_value=0.005
combine=node("ShaderNodeCombineXYZ")
for i in range(0,3):
    link(scale, "Value", combine, i)
link(combine, "Vector", instance, "Scale")

rotation=node("FunctionNodeRandomValue")
rotation.data_type='FLOAT_VECTOR'
rotation.inputs[1].default_value[0]=0.1
rotation.inputs[1].default_value[1]=0.1
rotation.inputs[1].default_value[2]=2*pi
link(rotation, 0, instance, "Rotation")

#adding compare node to trees
comp=node("FunctionNodeCompare")
comp.operation='LESS_THAN'
link(last_one, "Value", comp, "A")

multi=node("ShaderNodeMath")
multi.operation='MULTIPLY'
link(height, 0, multi, 0)
multi.inputs[1].default_value=0.25
link(multi, "Value", comp, "B")

link(comp, "Result", dist_points, "Selection")

#connect nodes
link(group_input, "Geometry", set_position, "Geometry")
link(set_position, "Geometry", shade_smo, "Mesh")
link(last_one, "Value", comb_xyz, "Z")
link(comb_xyz, "Vector", set_position, "Offset")

#add material and principled BSDF
principled_bsdf=nodes.new("ShaderNodeBsdfPrincipled")
material_output=nodes.new("ShaderNodeOutputMaterial")
links.new(
    principled_bsdf.outputs["BSDF"],
    material_output.inputs["Surface"]
)

#creating rock image texture nodes
base_color=nodes.new("ShaderNodeTexImage")
roughness=nodes.new("ShaderNodeTexImage")
displacement=nodes.new("ShaderNodeTexImage")
normal=nodes.new("ShaderNodeTexImage")

#creating other rock nodes
normal_map=nodes.new("ShaderNodeNormalMap")
disp_node=nodes.new("ShaderNodeDisplacement")
tex_coord=nodes.new("ShaderNodeTexCoord")
mapping=nodes.new("ShaderNodeMapping")

#loading textures
base_color.image = bpy.data.images.load(r"C:\Users\PIUSA DAS\OneDrive\Desktop\IITB\10_soc_inf_world\Textures\rock_face_03_4k.blend\textures\rock_face_03_diff_4k.jpg")
roughness.image = bpy.data.images.load(r"C:\Users\PIUSA DAS\OneDrive\Desktop\IITB\10_soc_inf_world\Textures\rock_face_03_4k.blend\textures\rock_face_03_rough_4k.exr")
displacement.image = bpy.data.images.load(r"C:\Users\PIUSA DAS\OneDrive\Desktop\IITB\10_soc_inf_world\Textures\rock_face_03_4k.blend\textures\rock_face_03_disp_4k.png")
normal.image = bpy.data.images.load(r"C:\Users\PIUSA DAS\OneDrive\Desktop\IITB\10_soc_inf_world\Textures\rock_face_03_4k.blend\textures\rock_face_03_nor_gl_4k.exr")

#loading images in principled BSDF
links.new(base_color.outputs["Color"], principled_bsdf.inputs["Base Color"])
links.new(roughness.outputs["Color"], principled_bsdf.inputs["Roughness"])
links.new(normal_map.outputs["Normal"], principled_bsdf.inputs["Normal"])
links.new(normal.outputs["Color"], normal_map.inputs["Color"])
links.new(disp_node.outputs["Displacement"], material_output.inputs["Displacement"])
links.new(displacement.outputs["Color"], disp_node.inputs["Height"])

#adding mapping
links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
links.new(mapping.outputs["Vector"], base_color.inputs["Vector"])
links.new(mapping.outputs["Vector"], roughness.inputs["Vector"])
links.new(mapping.outputs["Vector"], displacement.inputs["Vector"])
links.new(mapping.outputs["Vector"], normal.inputs["Vector"])
