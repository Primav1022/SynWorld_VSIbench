import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import os # Add os import

# Determine the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct relative paths
actors_csv_path = os.path.join(script_dir, 'output', 'ranked_unique_actor_anno.csv')
output_visualization_path = os.path.join(script_dir, 'output', '3d_anno_visualization.png')

# Read the CSV file
df = pd.read_csv(actors_csv_path)

# Create the figure and 3D axis
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Plot points and boxes
for idx, row in df.iterrows():
    # Plot center point
    ax.scatter(row['WorldX'], row['WorldY'], row['WorldZ'], color='blue', s=50, zorder=2)
    
    # Calculate box vertices
    x = row['WorldX']
    y = row['WorldY']
    z = row['WorldZ']
    dx = row['WorldSizeX'] / 2
    dy = row['WorldSizeY'] / 2
    dz = row['WorldSizeZ'] / 2
    
    # Define the vertices of the box
    vertices = np.array([
        [x-dx, y-dy, z-dz], [x+dx, y-dy, z-dz], [x+dx, y+dy, z-dz], [x-dx, y+dy, z-dz],
        [x-dx, y-dy, z+dz], [x+dx, y-dy, z+dz], [x+dx, y+dy, z+dz], [x-dx, y+dy, z+dz]
    ])
    
    # Define the faces of the box
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],
        [vertices[4], vertices[5], vertices[6], vertices[7]],
        [vertices[0], vertices[1], vertices[5], vertices[4]],
        [vertices[2], vertices[3], vertices[7], vertices[6]],
        [vertices[1], vertices[2], vertices[6], vertices[5]],
        [vertices[0], vertices[3], vertices[7], vertices[4]]
    ]
    
    # Create the 3D box
    box = Poly3DCollection(faces, alpha=0.25, facecolor='red', edgecolor='black')
    ax.add_collection3d(box)
    
    # Add labels
    label = f"{row['ActorName']}\n(Frame: {int(row['FirstFrame'])})"
    ax.text(x, y, z + dz, label,
            horizontalalignment='center',
            verticalalignment='bottom',
            fontsize=7)

# Customize the plot
ax.set_title('Actor Positions with 3D Bounding Boxes')
ax.set_xlabel('World X (cm)')
ax.set_ylabel('World Y (cm)')
ax.set_zlabel('World Z (cm)')

# Set equal aspect ratio
max_range = np.array([
    df['WorldX'].max() - df['WorldX'].min(),
    df['WorldY'].max() - df['WorldY'].min(),
    df['WorldZ'].max() - df['WorldZ'].min()
]).max() / 2.0

mid_x = (df['WorldX'].max() + df['WorldX'].min()) * 0.5
mid_y = (df['WorldY'].max() + df['WorldY'].min()) * 0.5
mid_z = (df['WorldZ'].max() + df['WorldZ'].min()) * 0.5

ax.set_xlim(mid_x - max_range, mid_x + max_range)
ax.set_ylim(mid_y - max_range, mid_y + max_range)
ax.set_zlim(mid_z - max_range, mid_z + max_range)

# Add grid
ax.grid(True)

# Set initial view angle
ax.view_init(elev=30, azim=45)

# Save the plot
plt.savefig(output_visualization_path, dpi=300, bbox_inches='tight')
plt.show()