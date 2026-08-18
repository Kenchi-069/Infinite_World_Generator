import random as rd
import bpy
import json
import os
import math

ter = bpy.data.objects["terrain"]

size = 3 #change size
seed = rd.randint(0, 1000)
mnt_strength = rd.uniform(0.5, 1)
tree_density = rd.uniform(1, 3) * 10000

node_group = bpy.data.node_groups["Geometry Nodes"]
node_group.nodes["Value"].outputs[0].default_value = size
node_group.nodes["Value.002"].outputs[0].default_value = tree_density  # tree density
node_group.nodes["Value.003"].outputs[0].default_value = seed          # seed
node_group.nodes["Value.004"].outputs[0].default_value = mnt_strength  # i'll let you figure this one out

print(f"seed: {seed}")
print(f"mountain strength: {mnt_strength}")
print(f"tree density: {tree_density}")


def report_chunk_heights(obj, grid_size, seed, mnt_strength, tree_density, output_path=None):
    """
    Evaluates the object's Geometry Nodes output, buckets vertices into
    1x1 world-space chunks, prints the average height per chunk across a
    grid_size x grid_size area, and saves everything to JSON.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated_object = obj.evaluated_get(depsgraph)
    eval_mesh = evaluated_object.to_mesh()

    # to_mesh() returns LOCAL coordinates, so convert to world space
    # to match the object's actual placement/scale in the scene
    world_matrix = obj.matrix_world
    chunk_z_values = {}

    for v in eval_mesh.vertices:
        world_co = world_matrix @ v.co
        cx = int(math.floor(world_co.x))
        cy = int(math.floor(world_co.y))
        chunk_z_values.setdefault((cx, cy), []).append(world_co.z)

    evaluated_object.to_mesh_clear()  # free temp mesh - avoid leaking memory

    chunk_averages = {}
    print(f"\nGrid Size: {grid_size} x {grid_size}\n")

    for cy in range(grid_size):
        for cx in range(grid_size):
            z_values = chunk_z_values.get((cx, cy), [])
            avg_height = sum(z_values) / len(z_values) if z_values else 0.0
            chunk_averages[f"{cx},{cy}"] = round(avg_height, 3)

            print(f"Chunk ({cx},{cy})")
            print(f"Average Height: {round(avg_height, 2)}\n")

    if output_path is None:
        base_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.path.expanduser("~")
        output_path = os.path.join(base_dir, f"chunk_report_seed_{seed}.json")

    data_to_save = {
        "seed": seed,
        "mnt_strength": mnt_strength,
        "tree_density": tree_density,
        "grid_size": grid_size,
        "chunks": chunk_averages,
    }

    try:
        with open(output_path, "w") as f:
            json.dump(data_to_save, f, indent=2)
        print(f"Saved chunk report -> {output_path}")
    except OSError as e:
        import tempfile
        fallback = os.path.join(tempfile.gettempdir(), os.path.basename(output_path))
        print(f"Could not write to '{output_path}' ({e}). Saving to '{fallback}' instead.")
        with open(fallback, "w") as f:
            json.dump(data_to_save, f, indent=2)

    return chunk_averages


report_chunk_heights(ter, grid_size=size, seed=seed, mnt_strength=mnt_strength, tree_density=tree_density)


