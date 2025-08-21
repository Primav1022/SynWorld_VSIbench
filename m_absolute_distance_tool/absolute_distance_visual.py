import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# Configuration variables
POSSIBILITY_ID = 1  # Change this to visualize different actor pairs

def visualize_distance(actor1, actor2, actor1_bounds, actor2_bounds, min_distance, possibility_id):
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot bounding boxes
    def plot_3d_box(bounds, color, label):
        # Plot edges - complete box outline
        vertices = np.array([
            [bounds[0], bounds[2], bounds[4]],  # front bottom left
            [bounds[1], bounds[2], bounds[4]],  # front bottom right
            [bounds[1], bounds[3], bounds[4]],  # back bottom right
            [bounds[0], bounds[3], bounds[4]],  # back bottom left
            [bounds[0], bounds[2], bounds[5]],  # front top left
            [bounds[1], bounds[2], bounds[5]],  # front top right
            [bounds[1], bounds[3], bounds[5]],  # back top right
            [bounds[0], bounds[3], bounds[5]]   # back top left
        ])
        
        # Define edges by connecting vertices
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # bottom face
            [4, 5], [5, 6], [6, 7], [7, 4],  # top face
            [0, 4], [1, 5], [2, 6], [3, 7]   # vertical edges
        ]
        
        # Plot all edges
        for edge in edges:
            ax.plot3D(vertices[edge, 0], vertices[edge, 1], vertices[edge, 2], 
                     color=color, label=label if edge == edges[0] else "")
        
        # Add translucent surfaces
        # Create meshgrid for each face
        def create_face(x, y, z):
            xx, yy = np.meshgrid(x, y)
            return xx, yy, np.full_like(xx, z)
        
        # Bottom face
        xx, yy = np.meshgrid([bounds[0], bounds[1]], [bounds[2], bounds[3]])
        zz = np.full_like(xx, bounds[4])
        ax.plot_surface(xx, yy, zz, color=color, alpha=0.1)
        
        # Top face
        zz = np.full_like(xx, bounds[5])
        ax.plot_surface(xx, yy, zz, color=color, alpha=0.1)
        
        # Front face
        xx, zz = np.meshgrid([bounds[0], bounds[1]], [bounds[4], bounds[5]])
        yy = np.full_like(xx, bounds[2])
        ax.plot_surface(xx, yy, zz, color=color, alpha=0.1)
        
        # Back face
        yy = np.full_like(xx, bounds[3])
        ax.plot_surface(xx, yy, zz, color=color, alpha=0.1)
        
        # Left face
        yy, zz = np.meshgrid([bounds[2], bounds[3]], [bounds[4], bounds[5]])
        xx = np.full_like(yy, bounds[0])
        ax.plot_surface(xx, yy, zz, color=color, alpha=0.1)
        
        # Right face
        xx = np.full_like(yy, bounds[1])
        ax.plot_surface(xx, yy, zz, color=color, alpha=0.1)
    
    plot_3d_box(actor1_bounds, 'blue', actor1['ActorName'])
    plot_3d_box(actor2_bounds, 'red', actor2['ActorName'])
    
    # Plot centers
    ax.scatter(actor1['WorldX'], actor1['WorldY'], actor1['WorldZ'], color='blue', s=100, label='Actor1 Center')
    ax.scatter(actor2['WorldX'], actor2['WorldY'], actor2['WorldZ'], color='red', s=100, label='Actor2 Center')
    
    # Calculate and plot minimum distance line
    def find_closest_points_3d(bounds1, bounds2):
        # Check for overlap in each dimension
        overlap_x = (bounds1[0] <= bounds2[1] and bounds1[1] >= bounds2[0])
        overlap_y = (bounds1[2] <= bounds2[3] and bounds1[3] >= bounds2[2])
        overlap_z = (bounds1[4] <= bounds2[5] and bounds1[5] >= bounds2[4])
        
        if overlap_x and overlap_y and overlap_z:
            # If boxes overlap, use center points
            return (actor1['WorldX'], actor1['WorldY'], actor1['WorldZ'],
                   actor2['WorldX'], actor2['WorldY'], actor2['WorldZ'])
        
        # Find closest points based on signed distances
        x1 = bounds1[0] if bounds1[0] > bounds2[1] else (bounds1[1] if bounds1[1] < bounds2[0] else min(max(actor2['WorldX'], bounds1[0]), bounds1[1]))
        y1 = bounds1[2] if bounds1[2] > bounds2[3] else (bounds1[3] if bounds1[3] < bounds2[2] else min(max(actor2['WorldY'], bounds1[2]), bounds1[3]))
        z1 = bounds1[4] if bounds1[4] > bounds2[5] else (bounds1[5] if bounds1[5] < bounds2[4] else min(max(actor2['WorldZ'], bounds1[4]), bounds1[5]))
        
        x2 = bounds2[1] if bounds1[0] > bounds2[1] else (bounds2[0] if bounds1[1] < bounds2[0] else actor2['WorldX'])
        y2 = bounds2[3] if bounds1[2] > bounds2[3] else (bounds2[2] if bounds1[3] < bounds2[2] else actor2['WorldY'])
        z2 = bounds2[5] if bounds1[4] > bounds2[5] else (bounds2[4] if bounds1[5] < bounds2[4] else actor2['WorldZ'])
        
        return x1, y1, z1, x2, y2, z2
    
    x1, y1, z1, x2, y2, z2 = find_closest_points_3d(actor1_bounds, actor2_bounds)
    ax.plot([x1, x2], [y1, y2], [z1, z2], 'g--', label=f'Min Distance: {min_distance:.2f}')
    
    ax.set_title(f'3D Minimum Distance Visualization (Possibility {possibility_id})')
    ax.set_xlabel('World X')
    ax.set_ylabel('World Y')
    ax.set_zlabel('World Z')
    ax.legend()
    
    # Make the plot more viewable
    ax.view_init(elev=30, azim=45)
    
    # Save visualization
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.savefig(os.path.join(output_dir, 'absolute_distance_visual.png'), dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()

def get_actor_bounds(actor):
    x_min = actor['WorldX'] - actor['WorldSizeX']/2
    x_max = actor['WorldX'] + actor['WorldSizeX']/2
    y_min = actor['WorldY'] - actor['WorldSizeY']/2
    y_max = actor['WorldY'] + actor['WorldSizeY']/2
    z_min = actor['WorldZ'] - actor['WorldSizeZ']/2
    z_max = actor['WorldZ'] + actor['WorldSizeZ']/2
    return [x_min, x_max, y_min, y_max, z_min, z_max]

def main():
    # Determine the project root directory and script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # This assumes the script is one level down from project root

    # Construct relative paths to the CSV files
    actors_csv_path = os.path.join(project_root, '0_data_cleanup_tool', 'output', 'ranked_unique_actor_anno.csv')
    distances_csv_path = os.path.join(script_dir, 'output', 'absolute_distances_all.csv')

    # Read the CSV files
    df_actors = pd.read_csv(actors_csv_path)
    df_distances = pd.read_csv(distances_csv_path)
    
    # Get the specific pair from distances file
    pair = df_distances[df_distances['Possibility'] == POSSIBILITY_ID].iloc[0]
    
    # Get actor data
    actor1 = df_actors[df_actors['ActorName'] == pair['Actor1']].iloc[0]
    actor2 = df_actors[df_actors['ActorName'] == pair['Actor2']].iloc[0]
    
    # Calculate bounds
    bounds1 = get_actor_bounds(actor1)
    bounds2 = get_actor_bounds(actor2)
    
    # Visualize using pre-computed distance from CSV
    visualize_distance(actor1, actor2, bounds1, bounds2, pair['Answer'], POSSIBILITY_ID)
    print(f"Visualizing possibility {POSSIBILITY_ID}:")
    print(f"Actor1: {pair['Actor1']}")
    print(f"Actor2: {pair['Actor2']}")
    print(f"Distance: {pair['Answer']:.2f} meters")

if __name__ == "__main__":
    main()