import bpy

def new_node(tree, type_name, loc_x, loc_y):
    """Helper function to spawn and position nodes in the editor."""
    n = tree.nodes.new(type=type_name)
    n.location.x = loc_x
    n.location.y = loc_y
    return n

def get_or_create_material(name, color):
    """Retrieves or creates a basic color material."""
    if name not in bpy.data.materials:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf: 
            bsdf.inputs["Base Color"].default_value = color
    return bpy.data.materials[name]