import bpy
import random

# Making our own simplistic(very) tree with default parameter name as Tree
def create_tree(name="Tree"):
    
    # To avoid making duplicates
    if name in bpy.data.objects:
        return

    # Making the trunk of the tree
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=6, # low-poly :)
        radius=0.1,
        depth=1.5,
        location=(0, 0, 0.75) # So that the bottom of the trunk is at origin
    )
    trunk = bpy.context.active_object # Just referencing the selected or 'active' object

    # Making leaves using icosohedron which is usually the most used way for low-poly trees
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1,
        radius=0.5,
        location=(0, 0, 1.8) # This puts the bottom of the leaves portion at Z=1.3, which means there is an intentional 0.2 overlap which makes it look better
    )
    leaves = bpy.context.active_object # Same
    
    # Creating materials for trunk and leaves
    trumat = bpy.data.materials.new(name="trunk") # Creating a new material
    trumat.use_nodes = True # Enables usage of nodes
    trumat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35,0.18,0.05,1) # Just inputting the Base color in RGBA terms 
    leafmat = bpy.data.materials.new(name="leaf") # Same for leaves
    leafmat.use_nodes = True
    leafmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05,0.30,0.05,1)
    trunk.data.materials.append(trumat) # To apply the created material to the trunk
    leaves.data.materials.append(leafmat) # Same for leaves

    # Joining trunk and leaves
    bpy.ops.object.select_all(action='DESELECT') # Deselecting everything first
    trunk.select_set(True) 
    leaves.select_set(True) # Selecting both trunk and leaves at once
    bpy.context.view_layer.objects.active = trunk # Setting trunk as the active object (leaves get merged into this) 
    bpy.ops.object.join() # Just joins the selected object into one
    tree = bpy.context.active_object
    tree.name = name # Using argument of the function as the name
    
    # Setting the origin of our tree to the bottom because it is essential in scattering it on the face
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

create_tree() # Creating the tree

# Next few lines are just assigning random values to the geometry nodes parameters which we wanted to change
mountain_strength = round(random.uniform(0.7, 1), 2)
seed = random.randint(0, 1000)
terrain_scale = round(random.uniform(1.0, 3), 2)
tree_seed = random.randint(0, 1000)
tree_density = round(random.uniform(0.2, 2.0), 2)
terrain = bpy.data.objects["Grid"] # Referencing the terrain
modifier= terrain.modifiers["GeometryNodes"] # Referencing the geometry nodes modifier
modifier["Socket_2"] = mountain_strength # Assigning the random values actually into the sockets
modifier["Socket_3"] = seed
modifier["Socket_4"] = terrain_scale
modifier["Socket_5"] = tree_seed
modifier["Socket_6"] = tree_density
terrain.data.update() # Updating the data
bpy.context.view_layer.update() # Updating the visuals

# Just printing the values assigned
print("\n=====================\n")
print(f"Mountain Strength:{mountain_strength}")
print(f"Seed:{seed}")
print(f"Terrain Scale:{terrain_scale}")
print(f"Tree Seed:{tree_seed}")
print(f"Tree Density:{tree_density}")

# So basically what i did was, i already created a terrain before hand with few variable parameters. Then i used this code to assign random values to them ofc.
# But first i created a tree, so i ran this code first, and in geometry node editor i will input the created "Tree" object in object info node.
# Then i will basically hide the tree to get the final terrain.

