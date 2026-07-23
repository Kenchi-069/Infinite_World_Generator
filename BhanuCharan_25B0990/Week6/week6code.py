import bpy
from mathutils import noise
import json
import os

Seed = 990
# Size of the grid
Chunk_Size = 2
# Just in case if someone wanted larger mountains
height_scale = 1
noise.seed_set(Seed) # Not really required as we are using seed as argument in the noise parts of the code
filepath = os.path.join(bpy.path.abspath("//"),"chunk_data.json") # The bpy.path.abspath("//") gives the absolute path of the folder in which our blend file is present
# So adding chunk_data.json at the end is gonna give the path of the JSON file which is used both in creation of the file and also dumping new outputs into it

# Making the material for snow
snow = bpy.data.materials.get("Snow")

# To make sure that duplicates are not created
if snow is None:
    snow = bpy.data.materials.new("Snow")
    snow.use_nodes = True #To be able to use nodes like principled bsdf

# Changing some values in the Principled BSDF node to get a white color
bsdf = snow.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.99,0.99,0.99,1)
bsdf.inputs["Roughness"].default_value = 0.9
bsdf.inputs["Specular IOR Level"].default_value = 0.15

# Similarly for Rock
rock = bpy.data.materials.get("Rock")

if rock is None:
    rock = bpy.data.materials.new("Rock")
    rock.use_nodes = True

bsdf = rock.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.12,0.08,0.04,1)
bsdf.inputs["Roughness"].default_value = 0.95
bsdf.inputs["Specular IOR Level"].default_value = 0.1

# This part is only needed if there are objects which we want to delete or transform into our 9 chunk terrain. Like if there is a default cube or something.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Adding our sun
bpy.ops.object.light_add(
    type = 'SUN',
    location = (0,0,100)
)

# Changing the energy of our sun
sun = bpy.context.active_object
sun.data.energy = 3

# Function which creates a grid taking the coordinates of center of the grid as arguments
def chunkmaker(x,y):
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions = 128,
        y_subdivisions = 128,
        size = Chunk_Size,
        calc_uvs = True, # Generates UV coordinates for the mesh, used for mapping image textures into mesh usually
        enter_editmode = False, # Stays in object mode
        align = 'WORLD', # Tells blender to use world coordinate system
        location = (x,y,0.0),
        rotation = (0.0,0.0,0.0),
        scale = (1.0,1.0,1.0)
    )
    chunk = bpy.context.active_object # Created chunk automatically becomes the active object
    bpy.ops.object.select_all(action='DESELECT') # Safety measure
    return chunk 

# This function is our custom made noise function which is trying to imitate what a fBM mode in noise texture node does
def fbm(x,y,seed,layers=6,roughness=0.5,lacunarity=2.1):
    height = 0 # Final terrain height storing variable, initially zero
    coefficient = 1 # How much the current layer matters
    frequency = 1 # Low frequency gives large smooth hills, while high frequency gives tiny bumps. This will be clear after seeing where it is used in the loop
    
    for i in range(layers): # So we add few layers of noise. Each differing in the frequency, coefficient, giving a more detailed terrain.
        height += coefficient*noise.noise((x*frequency,y*frequency,seed+i)) # We add the new noise layer to the past ones, seed + i isn't necessary. It just feels better for some reason
        coefficient *= roughness # So if roughness is more, the later layers also matter more
        frequency *= lacunarity # Similar explanation
        
    return height

chunks = {} # This is the dictionary that stores the generated chunk info
for i in range(-1,2): # These are the chunk coordinates, not the coordinates of the center of the chunk
    for j in range(-1,2):
        x = i*Chunk_Size # Making them into the world coordinates
        y = j*Chunk_Size
        chunk = chunkmaker(x,y)
        chunk.data.materials.append(snow) # This stores snow as material 0 and rock as material 1
        chunk.data.materials.append(rock)
        mesh = chunk.data
        total_height = 0
        for vertex in mesh.vertices: # Going over each vertex
            X = x + vertex.co.x # Usually vertex.co.x gives coordinates wrt to that chunk center, so we change this into the world coordinates
            Y = y + vertex.co.y
            details = fbm(
                X*0.8,
                Y*0.8,
                Seed,
                6,
                0.41,
                2.1
            )
            base = noise.noise((X*0.02,Y*0.02,Seed)) # Our fbm noise creates rough small hills everywhere, but this is a very low frequency noise which gives large smooth hills
            height = base*4 + details + 0.3 # As the names suggest, doing this uses the base noise as the base and adding our fbm noise as detail on top, the coefficients and frequency is just decided after me playing with it for a long time
            if height < 0: 
                height = height*0.05 # Our noise combo produces very deep valleys, so deep that they look like inverted mountains. So i scaled those down.
            # The reason why i added 0.3 to the height is just me deciding how deep my valleys should go
            vertex.co.z = height*height_scale # Changing z coord of the vertex
            total_height += height*height_scale # Used to calculate the average height
        
        avg_height = total_height/len(mesh.vertices) # Average height of the current chunk
        chunks[(i,j)] = {
            "average_height":avg_height
        } # Storing the average height of the chunk(another dictionary with a key and a value) with the chunk coordinates being the key
        bpy.ops.object.shade_smooth() # Just making out chunk look smoother
        mesh.update() # Updating the mesh because we would use the changed mesh data next
        for poly in mesh.polygons: # mesh.polygons is really just the list of faces of the chunk mesh
            slope = 1 - poly.normal.z 
            if slope < 0.25: # If the face is low sloped, not very steep, then we will add snow, whose material index is 0
                poly.material_index = 0
            else: # Otherwise rock
                poly.material_index = 1
        
data = {
    "seed":Seed,
    "chunks":{}
} # This is for the JSON part, but this is also a dictionary that stores chunk info

for key,value in chunks.items():
    data["chunks"][str(key)] = value # In chunks dictionary, we had chunk coordinates as keys and the value is another dictionary which effectively stores the average height of the chunk
    # Now we just store that same dictionary here. Its effectively just storing chunks dictionary as the value of chunks key of data dictionary
    
with open(filepath,"w") as f: # Opening the file in the filepath and entering into write mode
    json.dump(data,f,indent=4) # Converting data dictionary into JSON format and writing it into the file and indent = 4 is just gives a nicer formatting




        
    


