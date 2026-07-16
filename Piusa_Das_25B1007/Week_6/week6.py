import bpy
import math
import json
import os
from mathutils import noise

def clear_scene():

    #delete unused objects
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    #remove unused data
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)

    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)

    for camera in list(bpy.data.cameras):
        bpy.data.cameras.remove(camera)

    for node_group in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(node_group)
        
def setup_materials():

    #water material
    water=bpy.data.materials.get("Water")

    if water is None:
        water=bpy.data.materials.new("Water")
        water.use_nodes=True

    bsdf=water.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value=(0.05, 0.25, 0.8, 1)
    bsdf.inputs["Roughness"].default_value=0.08
    bsdf.inputs["Specular IOR Level"].default_value=0.5

    #grass material
    grass=bpy.data.materials.get("Grass")

    if grass is None:
        grass=bpy.data.materials.new("Grass")
        grass.use_nodes=True

    bsdf=grass.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value=(0.18, 0.45, 0.12, 1)
    bsdf.inputs["Roughness"].default_value=0.9
    bsdf.inputs["Specular IOR Level"].default_value=0.15

    #rock material
    rock=bpy.data.materials.get("Rock")

    if rock is None:
        rock=bpy.data.materials.new("Rock")
        rock.use_nodes=True

    bsdf=rock.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value=(0.28, 0.25, 0.23, 1)
    bsdf.inputs["Roughness"].default_value=0.95
    bsdf.inputs["Specular IOR Level"].default_value=0.1

    return water, grass, rock

def fbm(x, y, seed, octaves=5, persistence=0.5, lacunarity=2.0):

    #terrain height, amplitude, frequency
    height=0.0
    amplitude=1.0
    frequency=1.0
    max_amplitude=0.0

    #generate multiple octaves of noise
    for i in range(octaves):

        value=noise.noise(
            (
                x*frequency,
                y*frequency,
                seed+i
            )
        )

        height+=value*amplitude
        max_amplitude+=amplitude

        amplitude*=persistence
        frequency*=lacunarity

    #normalize the result
    return height/max_amplitude

def calculate_chunk_statistics(mesh):

    #stores the height of every vertex
    heights=[vertex.co.z for vertex in mesh.vertices]
    average_height=sum(heights)/len(heights)

    #lowest and highest points
    minimum_height=min(heights)
    maximum_height=max(heights)

    #standard deviation
    variance=sum(
        (height-average_height)**2
        for height in heights
    )/len(heights)

    standard_deviation=math.sqrt(variance)

    return {
        "average_height": average_height,
        "minimum_height": minimum_height,
        "maximum_height": maximum_height,
        "height_variation": standard_deviation
    }
    
def assign_materials(mesh):

    for face in mesh.polygons:

        #calculate average height of face
        average_height=0

        for vertex_index in face.vertices:
            average_height+=mesh.vertices[vertex_index].co.z

        average_height/=len(face.vertices)

        #calculate slope of face
        slope=1-face.normal.z

        #water
        if average_height<0:
            face.material_index=0

        #rock
        elif slope>0.30:
            face.material_index=2

        #grass
        else:
            face.material_index=1
            
def generate_chunk(chunk_x, chunk_y, seed,
                   water, grass, rock,
                   chunk_size=2,
                   subdivisions=128):

    #world position of chunk
    world_x=chunk_x*chunk_size
    world_y=chunk_y*chunk_size

    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=subdivisions,
        y_subdivisions=subdivisions,
        size=chunk_size,
        location=(world_x, world_y, 0),
        enter_editmode=False
    )

    chunk=bpy.context.active_object
    mesh=chunk.data

    mesh.materials.append(water)
    mesh.materials.append(grass)
    mesh.materials.append(rock)

    for vertex in mesh.vertices:

        x=world_x+vertex.co.x
        y=world_y+vertex.co.y

        base=fbm(
            x*0.3,
            y*0.3,
            seed,
            octaves=5
        )

        detail=fbm(
            x*0.25,
            y*0.25,
            seed+100,
            octaves=3
        )

        height=base*4 + detail*0.5

        #flatten seas
        if height<0:
            height*=0.15

        vertex.co.z=height

    mesh.update()

    bpy.context.view_layer.objects.active=chunk
    chunk.select_set(True)
    bpy.ops.object.shade_smooth()

    assign_materials(mesh)

    statistics=calculate_chunk_statistics(mesh)

    return chunk, statistics

def generate_world(world_size, seed):

    world_data={}
    
    water, grass, rock=setup_materials()

    for chunk_x in range(-world_size, world_size+1):
        for chunk_y in range(-world_size, world_size+1):

            #generate a chunk
            chunk, statistics=generate_chunk(
                chunk_x,
                chunk_y,
                seed,
                water,
                grass,
                rock
            )

            world_data[(chunk_x, chunk_y)]=statistics

    return world_data

def save_json(world_data, seed, chunk_size, world_size,
              filename="chunk_data.json"):

    data={
        "seed": seed,
        "chunk_size": chunk_size,
        "world_size": world_size,
        "chunks": {}
    }

    for coordinates, statistics in world_data.items():
        data["chunks"][str(coordinates)]=statistics

    filepath=os.path.join(
        bpy.path.abspath("//"),
        filename
    )

    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)

    return filepath
    
def main():

    #parameters
    SEED=6967
    CHUNK_SIZE=2
    WORLD_SIZE=1
    
    #seed noise generator
    noise.seed_set(SEED)

    clear_scene()
    setup_materials()

    world_data=generate_world(
        world_size=WORLD_SIZE,
        seed=SEED
    )
    filepath=save_json(
        world_data=world_data,
        seed=SEED,
        chunk_size=CHUNK_SIZE,
        world_size=WORLD_SIZE
    )

if __name__ == "__main__":
    main()
