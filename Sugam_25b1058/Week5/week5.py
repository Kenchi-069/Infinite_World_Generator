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

# Making our own simplistic(very) rock with default parameter name as Rock
def create_rock(name="Rock"):
    
    # To avoid making duplicates
    if name in bpy.data.objects:
        return
    # Making the base shape of the rock using icosphere (same low-poly approach as the tree leaves)
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1,
        radius=0.3,
        location=(0, 0, 0.15) # Roughly half the radius so it sits on the ground properly
    )
    rock = bpy.context.active_object # Just referencing the selected or 'active' object
    
    # Randomizing the scale on each axis so it doesn't look like a plain sphere
    rock.scale.x = random.uniform(0.7, 1.3)
    rock.scale.y = random.uniform(0.7, 1.3)
    rock.scale.z = random.uniform(0.5, 0.9) # Squashing it a bit vertically so it looks more like a rock and less like a boulder-ball
    
    # Randomizing rotation too, for variety when scattered
    rock.rotation_euler = (
        random.uniform(0, 6.28),
        random.uniform(0, 6.28),
        random.uniform(0, 6.28)
    )
    
    # Going into edit mode briefly to randomize vertices a little (gives it that jagged low-poly rock look)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.vertex_random(offset=0.05, uniform=0.0, normal=0.0, seed=random.randint(0, 1000))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Creating material for the rock
    rockmat = bpy.data.materials.new(name="rock") # Creating a new material
    rockmat.use_nodes = True # Enables usage of nodes
    rockmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.4,0.4,0.42,1) # Greyish rock color in RGBA terms
    rockmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9 # Rocks shouldn't be shiny
    rock.data.materials.append(rockmat) # To apply the created material to the rock
    
    rock.name = name # Using argument of the function as the name
    
    # Setting the origin of our rock to the bottom because it is essential in scattering it on the face
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

create_tree() # Creating the tree
create_rock() # Creating the rock

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