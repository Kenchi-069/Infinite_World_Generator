# import bpy
import numpy as np

# Generate random preset for procedural generation
Seed = np.random.randint(0, 3000)
MountainStrength = np.random.normal(8,5)
TerrainScale = np.random.normal(15,5)
TreeDensity = np.random.normal(1,0.5)

# Print the generated presets
print(Seed, MountainStrength, TerrainScale, TreeDensity)
