import bpy
import math
import random
import mathutils
import json
import os


def sgn(x):
    return (x > 0) - (x < 0)


def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def lerp(t, a, b):
    return a + t * (b - a)


def smoothstep(edge0, edge1, x):
    if edge0 == edge1:
        return 0.0 if x < edge0 else 1.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def seeded_random_vector(seed: int, x: int, y: int):
    """
    Generates a deterministic random vector by hashing a tuple containing the seed and spatial coordinates. The resulting hash code is applied as the seed for a pseudo-random number generator, guaranteeing reproducible values for given coordinates.
    """
    hash_code = hash((seed, x, y))

    random.seed(hash_code)

    # Returns a random number between -1 and 1
    vector_x = random.random() * 2 - 1
    vector_y = math.sqrt(1 - vector_x**2) * random.choice([1, -1])

    return vector_x, vector_y


def perlin_noise(seed: int, x, y, no_of_segments_per_meter=64):
    """
    Generates a random vector at each grid point and uses dot product with the position vector to smmoth noise.
    """
    segment_length = 1.0 / no_of_segments_per_meter
    x_cell = math.floor(x / segment_length)
    y_cell = math.floor(y / segment_length)

    x0 = math.floor(x / segment_length) * segment_length
    x1 = x0 + segment_length
    y0 = math.floor(y / segment_length) * segment_length
    y1 = y0 + segment_length

    vector_1 = seeded_random_vector(seed, x_cell, y_cell)
    vector_2 = seeded_random_vector(seed, x_cell + 1, y_cell)
    vector_3 = seeded_random_vector(seed, x_cell, y_cell + 1)
    vector_4 = seeded_random_vector(seed, x_cell + 1, y_cell + 1)

    d1 = (x - x0) / segment_length, (y - y0) / segment_length
    d2 = (x - x1) / segment_length, (y - y0) / segment_length
    d3 = (x - x0) / segment_length, (y - y1) / segment_length
    d4 = (x - x1) / segment_length, (y - y1) / segment_length

    dot_1 = vector_1[0] * d1[0] + vector_1[1] * d1[1]
    dot_2 = vector_2[0] * d2[0] + vector_2[1] * d2[1]
    dot_3 = vector_3[0] * d3[0] + vector_3[1] * d3[1]
    dot_4 = vector_4[0] * d4[0] + vector_4[1] * d4[1]

    u = fade((x - x0) / segment_length)
    v = fade((y - y0) / segment_length)

    nx0 = lerp(u, dot_1, dot_2)
    nx1 = lerp(u, dot_3, dot_4)

    return lerp(v, nx0, nx1)


def fbm(
    seed: int,
    x,
    y,
    octaves=4,
    damping_factor=0.5,
    lacuranity=2,
    no_of_segments_per_meter=64,
):
    """
    Adds multiple perlin noise maps at decreasing amplitudes and increasing frequencies
    to improve detail and smoothness of the terrain.
    """
    total = 0.0
    amplitude = 1.0
    frequency = 1.0
    max_amplitude = 0.0

    for i in range(octaves):
        total += amplitude * perlin_noise(
            seed + i * 100, x * frequency, y * frequency, no_of_segments_per_meter
        )
        max_amplitude += amplitude
        amplitude *= damping_factor
        frequency *= lacuranity

    return total / max_amplitude


def transform_noise_to_biomes(noise):
    """
    Filters the noise to form different biomes, with smooth transitions between lake / plains / mountain.
    """
    lake_level = 0
    mountain_level = 0.7
    threshold = 0.15

    def plains_height(n):
        return n * 0.5

    def mountain_height(n):
        base_height = mountain_level * 0.5
        return base_height + (n - mountain_level) * 2.5

    if noise <= lake_level - threshold:
        return lake_level

    if noise < lake_level + threshold:
        t = smoothstep(lake_level - threshold, lake_level + threshold, noise)
        return lerp(t, lake_level, plains_height(noise))

    if noise < mountain_level - threshold:
        return plains_height(noise)

    if noise < mountain_level + threshold:
        t = smoothstep(mountain_level - threshold, mountain_level + threshold, noise)
        return lerp(t, plains_height(noise), mountain_height(noise))

    return mountain_height(noise)


def chunk_mean_height(mesh: bpy.types.Mesh):
    return sum(vertex.co.z for vertex in mesh.vertices) / len(mesh.vertices)


def chunk_std(mesh: bpy.types.Mesh):
    mean = chunk_mean_height(mesh)
    return sum((vertex.co.z - mean) ** 2 for vertex in mesh.vertices) / len(
        mesh.vertices
    )


def maximum_elevation(mesh: bpy.types.Mesh):
    return max(vertex.co.z for vertex in mesh.vertices)


def maximum_slope(mesh: bpy.types.Mesh):
    min_z = min(polygon.normal.z for polygon in mesh.polygons)
    return math.acos(abs(min_z)) * 180 / math.pi


def get_output_path(filename: str) -> str:
    if bpy.data.filepath:
        directory = os.path.dirname(bpy.data.filepath)
    else:
        import tempfile

        directory = tempfile.gettempdir()
        print(
            "Warning: .blend file has not been saved, writing output to "
            f"temp directory instead: {directory}"
        )

    return os.path.join(directory, filename)


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


def create_terrain_mesh(seed: int, X=2, Y=2, number_of_cuts=191) -> dict:
    """Generates a flat, subdivided 3m x 3m plane with its center positioned at (x - 0.5 * sgn(x), y - 0.5 * sgn(y)). The global space is partitioned into 1m x 1m chunks, where each chunk is assigned the (x, y) coordinate of the corner most distant from the world origin. So all the chunks sharing an edge or a vertex with the marked chunk are also generated."""
    center_x = X - 0.5 * sgn(X)
    center_y = Y - 0.5 * sgn(Y)
    center_z = 0

    bpy.ops.mesh.primitive_plane_add(
        size=3,
        enter_editmode=False,
        align="WORLD",
        location=(center_x, center_y, center_z),
        scale=(1, 1, 1),
    )
    TERRAIN = bpy.context.active_object
    MESH = TERRAIN.data

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=number_of_cuts)
    bpy.ops.object.mode_set(mode="OBJECT")
    matrix_world = TERRAIN.matrix_world

    for vertex in MESH.vertices:
        world_pos = matrix_world @ vertex.co

        noise = fbm(seed, world_pos.x * 0.005, world_pos.y * 0.005)

        detail = fbm(seed + 1000, world_pos.x * 0.1, world_pos.y * 0.1, octaves=3)

        vertex.co.z = transform_noise_to_biomes(noise) * 20 + detail * 0.05

    MESH.update()

    bpy.ops.object.shade_smooth()

    chunk_data = {
        "seed": seed,
        "chunk_x_coordinate": X,
        "chunk_y_coordinate": Y,
        "mean_height": chunk_mean_height(MESH),
        "std_height": chunk_std(MESH),
        "maximum_elevation": maximum_elevation(MESH),
        "maximum_slope": maximum_slope(MESH),
    }

    return chunk_data


def main():
    clear_scene()
    seed = random.randint(1,10000)
    data = [
        create_terrain_mesh(seed=seed, X=2, Y=2),
    ]
    output_path = get_output_path("data.json")

    with open(output_path, "w") as file:
        json.dump(data, file, indent=2)


if __name__ == "__main__":
    main()
