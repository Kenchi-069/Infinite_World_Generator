import bpy
import math
import random


def random_settings_gen(seed: int) -> dict:
    """
    Random terrain settings generated with seeding
    """
    random_seeder = random.Random(seed)
    settings = {
        "seed": seed,
        "mountain_strength": random_seeder.gauss(10, 2),
        "tree_density": random_seeder.uniform(5, 50),
        "terrain_scale": random_seeder.gauss(0.3, 0.1),
        "terrain_detail": random_seeder.uniform(2.0, 8.0),
        "terrain_roughness": random_seeder.uniform(0.3, 0.7),
    }
    return settings


def print_settings(settings: dict) -> None:
    """
    Prints the Settings generated
    """
    print("TERRAIN SETTINGS")
    print(f"Seed:{settings['seed']}")
    print(f"Mountain Strength:{settings['mountain_strength']}")
    print(f"Tree Density:{settings['tree_density']}")
    print(f"Terrain Scale: {settings['terrain_scale']}")
    print(f"Terrain detail:{settings['terrain_detail']}")
    print(f"Terrain_roughness:{settings['terrain_roughness']}")


def clear_scene() -> None:
    """
    Deletes all meshes and materials present on the scene after running the script
    """
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for block in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.node_groups,
        bpy.data.lights,
        bpy.data.cameras,
    ):
        for item in list(block):
            block.remove(item)


def create_terrain_mesh(node_tree: bpy.types.GeometryNodeTree) -> None:
    """
    Adds a Plane in the scene with a geometry nodes modifier
    """
    bpy.ops.mesh.primitive_plane_add(
        size=16,
        enter_editmode=False,
        align="WORLD",
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )
    TERRAIN_PLANE = bpy.context.active_object
    geometry_nodes_modifier = TERRAIN_PLANE.modifiers.new(
        name="TerrainModifier", type="NODES"
    )
    geometry_nodes_modifier.node_group = node_tree


def create_tree_object():
    """
    Create a tree object with a cylinder as a trunk and a cone as the leaves and return the object to use it as an instance in the node network
    """
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.005, depth=0.02, location=(1000, 1000, 0.01)
    )
    trunk = bpy.context.active_object

    bpy.ops.mesh.primitive_cone_add(
        radius1=0.015, depth=0.03, location=(1000, 1000, 0.035)
    )
    leaves = bpy.context.active_object

    bpy.ops.object.select_all(action="DESELECT")
    trunk.select_set(True)
    leaves.select_set(True)
    bpy.context.view_layer.objects.active = trunk
    bpy.ops.object.join()

    trunk.name = "TreeInstance"
    return trunk


def create_node_tree(settings: dict):
    """
    Create a Node Network which generates a terrain based on the generated settings
    """
    node_tree = bpy.data.node_groups.new(type="GeometryNodeTree", name="Terrain")

    node_tree.interface.new_socket(
        name="Size X", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    node_tree.interface.new_socket(
        name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
    )

    # Group Input Node
    GROUP_INPUT = node_tree.nodes.new(type="NodeGroupInput")
    GROUP_INPUT.location = (-200, 0)

    # Group Output Node
    GROUP_OUTPUT = node_tree.nodes.new(type="NodeGroupOutput")
    GROUP_OUTPUT.location = (1450, 160)

    # 16x16 Grid with 512x512 vertices
    Grid_Node = node_tree.nodes.new(type="GeometryNodeMeshGrid")
    Grid_Node.location = (50, 160)
    Grid_Node.inputs["Size X"].default_value = 16.0
    Grid_Node.inputs["Size Y"].default_value = 16.0
    Grid_Node.inputs["Vertices X"].default_value = 512
    Grid_Node.inputs["Vertices Y"].default_value = 512

    # Primary Noise Texture for the major hills and details
    Noise_Texture_1 = node_tree.nodes.new(type="ShaderNodeTexNoise")
    Noise_Texture_1.location = (-350, -140)
    Noise_Texture_1.noise_dimensions = "4D"
    Noise_Texture_1.noise_type = "FBM"
    Noise_Texture_1.normalize = True
    Noise_Texture_1.inputs["W"].default_value = 0.0
    Noise_Texture_1.inputs["Scale"].default_value = settings["terrain_scale"]
    Noise_Texture_1.inputs["Detail"].default_value = settings["terrain_detail"]
    Noise_Texture_1.inputs["Roughness"].default_value = settings["terrain_roughness"]
    Noise_Texture_1.inputs["Lacunarity"].default_value = 1.5
    Noise_Texture_1.inputs["Distortion"].default_value = 0.0

    # Secondary Noise texture for minor bumps on the surface
    Noise_Texture_2 = node_tree.nodes.new(type="ShaderNodeTexNoise")
    Noise_Texture_2.location = (-350, -420)
    Noise_Texture_2.noise_dimensions = "4D"
    Noise_Texture_2.noise_type = "FBM"
    Noise_Texture_2.normalize = True
    Noise_Texture_2.inputs["W"].default_value = 0.0
    Noise_Texture_2.inputs["Scale"].default_value = 0.8
    Noise_Texture_2.inputs["Detail"].default_value = 10
    Noise_Texture_2.inputs["Roughness"].default_value = 0.5
    Noise_Texture_2.inputs["Lacunarity"].default_value = 2.0

    # Color Ramp which modifies the noise generated
    Color_Ramp = node_tree.nodes.new(type="ShaderNodeValToRGB")
    Color_Ramp.location = (50, -140)
    Color_Ramp.color_ramp.interpolation = "LINEAR"
    Color_Ramp.color_ramp.elements[0].position = 0.5
    Color_Ramp.color_ramp.elements[1].position = 1.0
    Color_Ramp.color_ramp.elements.new(
        max(0.5, min(settings["mountain_strength"] * 0.75, 1.0))
    )
    Color_Ramp.color_ramp.elements[1].color = (0.256, 0.256, 0.256, 1)

    # Amplifies the Primary Noise Texture
    Multiply = node_tree.nodes.new(type="ShaderNodeMath")
    Multiply.location = (280, -140)
    Multiply.operation = "MULTIPLY"
    Multiply.use_clamp = False
    Multiply.inputs[1].default_value = 10.0

    Add = node_tree.nodes.new(type="ShaderNodeMath")
    Add.location = (460, -140)
    Add.operation = "ADD"
    Add.use_clamp = False

    Combine_XYZ = node_tree.nodes.new(type="ShaderNodeCombineXYZ")
    Combine_XYZ.location = (640, -140)
    Combine_XYZ.inputs["X"].default_value = 0.0
    Combine_XYZ.inputs["Y"].default_value = 0.0

    # Set the z offset
    Set_Position = node_tree.nodes.new(type="GeometryNodeSetPosition")
    Set_Position.location = (400, 160)

    Set_Shade_Smooth = node_tree.nodes.new(type="GeometryNodeSetShadeSmooth")
    Set_Shade_Smooth.location = (650, 160)
    Set_Shade_Smooth.domain = "FACE"

    Object_Info = node_tree.nodes.new(type="GeometryNodeObjectInfo")
    Object_Info.location = (650, 400)
    if "TreeInstance" in bpy.data.objects:
        Object_Info.inputs["Object"].default_value = bpy.data.objects["TreeInstance"]

    Distribute_Points = node_tree.nodes.new(type="GeometryNodeDistributePointsOnFaces")
    Distribute_Points.location = (850, 160)
    Distribute_Points.inputs["Density"].default_value = settings["tree_density"] * 0.5

    Instance_On_Points = node_tree.nodes.new(type="GeometryNodeInstanceOnPoints")
    Instance_On_Points.location = (1050, 160)

    Join_Geometry = node_tree.nodes.new(type="GeometryNodeJoinGeometry")
    Join_Geometry.location = (1250, 160)

    node_tree.links.new(Grid_Node.outputs["Mesh"], Set_Position.inputs["Geometry"])
    node_tree.links.new(Noise_Texture_1.outputs["Factor"], Color_Ramp.inputs["Fac"])
    node_tree.links.new(Color_Ramp.outputs["Color"], Multiply.inputs[0])
    node_tree.links.new(Multiply.outputs["Value"], Add.inputs[0])
    node_tree.links.new(Noise_Texture_2.outputs["Factor"], Add.inputs[1])
    node_tree.links.new(Add.outputs["Value"], Combine_XYZ.inputs["Z"])
    node_tree.links.new(Combine_XYZ.outputs["Vector"], Set_Position.inputs["Offset"])
    node_tree.links.new(
        Set_Position.outputs["Geometry"], Set_Shade_Smooth.inputs["Geometry"]
    )

    node_tree.links.new(
        Set_Shade_Smooth.outputs["Geometry"], Distribute_Points.inputs["Mesh"]
    )
    node_tree.links.new(
        Distribute_Points.outputs["Points"], Instance_On_Points.inputs["Points"]
    )
    node_tree.links.new(
        Object_Info.outputs["Geometry"], Instance_On_Points.inputs["Instance"]
    )

    node_tree.links.new(
        Set_Shade_Smooth.outputs["Geometry"], Join_Geometry.inputs["Geometry"]
    )
    node_tree.links.new(
        Instance_On_Points.outputs["Instances"], Join_Geometry.inputs["Geometry"]
    )

    node_tree.links.new(
        Join_Geometry.outputs["Geometry"], GROUP_OUTPUT.inputs["Geometry"]
    )

    return node_tree


def main():
    # Modify the seed to choice
    seed = random.randint(1, 10000)

    settings = random_settings_gen(seed)

    clear_scene()
    create_tree_object()

    NODE_TREE = create_node_tree(settings)
    create_terrain_mesh(NODE_TREE)
    print("__________________________________________________________")
    print_settings(settings)
    print("__________________________________________________________")


if __name__ == "__main__":
    main()
