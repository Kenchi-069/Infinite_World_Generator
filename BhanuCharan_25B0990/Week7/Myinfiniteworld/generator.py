import bpy
import os


def asset_file():
    # Returns the path to WorldAssets.blend file
    return os.path.join(
        os.path.dirname(__file__),
        "assets",
        "WorldAssets.blend"
    ) # Joins the directory of the current file with the assets folder and WorldAssets.blend to get the full path.


def append_node_group():
    # Copies the "InfiniteWorldGenerator" geometry nodes group out of WorldAssets.blend into the current file, so it can be assigned to a modifier.
    if "InfiniteWorldGenerator" in bpy.data.node_groups:
        return  # To avoid duplicates

    with bpy.data.libraries.load(asset_file(), link=False) as (data_from, data_to): # link=false means the data is copied and not just referenced 
        data_to.node_groups = ["InfiniteWorldGenerator"] # what this does is it loads the node group from the asset file into the current Blender file


def append_tree_collection():
    # Copies the "Trees" collection. Objects, meshes, and their materials all come along automatically.
    if "Trees" in bpy.data.collections:
        return

    with bpy.data.libraries.load(asset_file(), link=False) as (data_from, data_to):
        data_to.collections = ["Trees"]


def append_terrain_material():
    # The Grass material isn't referenced inside the node group, so it has to be appended seperately
    if "Grass" in bpy.data.materials:
        return

    with bpy.data.libraries.load(asset_file(), link=False) as (data_from, data_to):
        data_to.materials = ["Grass"]


def _remove_object(obj): # _ before the function name means it's a private function, not meant to be used outside this file.
    # Deletes an object and its mesh data, freeing the mesh only if no other object still uses it.
    mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True) # do_unlink=True means the object is removed from the scene and its data is unlinked from Blender's data blocks, allowing it to be deleted if no other objects reference it.
    if mesh and mesh.users == 0: # If no users of the mesh exist, it means no other object is using it, so we can safely remove it from Blender's data blocks.
        bpy.data.meshes.remove(mesh)

def _socket_identifiers(node_group): # Another private function
    # Maps input socket display names ("Seed") to their real identifiers ("Socket_2")
    return {
        item.name: item.identifier
        for item in node_group.interface.items_tree
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT'
    } # Creates a dictionary with display names as keys and identifiers as values


def create_terrain(settings): # Settings is the WorldGeneratorProperties object that contains the user-defined parameters for terrain generation.

    old = bpy.data.objects.get("Terrain")
    if old:
        _remove_object(old) # Removes the old terrain if exists

    default_cube = bpy.data.objects.get("Cube")
    if default_cube:
        _remove_object(default_cube) # Removes the default cube if exists

    size = settings.terrain_size # Self explanatory, gets the terrain size from the settings

    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions = 64,
        y_subdivisions = 64,
        size=size,
        location=(0, 0, 0),
    )

    terrain = bpy.context.active_object # The grid is the active object after creationy
    terrain.name = "Terrain" 

    terrain.data.materials.clear() # Clearing any existing materials from the terrain mesh, so we can assign our own material.
    terrain.data.materials.append(bpy.data.materials["Grass"]) # Self explanatory, assigns the Grass material to the terrain mesh.

    modifier = terrain.modifiers.new(name="GeometryNodes", type='NODES') 
    modifier.node_group = bpy.data.node_groups["InfiniteWorldGenerator"] # Assigns the InfiniteWorldGenerator node group
    sockets = _socket_identifiers(modifier.node_group) # dictionary mapping socket display names to their identifiers

    modifier[sockets["Seed"]] = settings.seed # All self explanatory
    modifier[sockets["Mountain Strength"]] = settings.mountain_strength
    modifier[sockets["Tree Density"]] = settings.tree_density
    # IMPORTANT: Terrain size is not passed to the node group, because the grid's physical size is already set by the primitive_grid_add operator above.

    modifier.node_group.interface_update(bpy.context) # These three lines just update the node group interface to reflect the new values set above
    terrain.data.update()
    bpy.context.view_layer.update()

    return terrain


def generate_world(settings):
    # Called when the "Generate World" button is clicked
    append_node_group() # Appends all the necessary assets
    append_tree_collection()
    append_terrain_material()

    create_terrain(settings)