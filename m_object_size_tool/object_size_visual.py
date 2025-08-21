import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Configuration variables
POSSIBILITY_ID = 1  # Change this to visualize different actors

def visualize_object_size(actor, actor_bounds, longest_dim, possibility_id):
    """
    Visualize an actor's 3D bounding box with the longest dimension highlighted in red
    
    Args:
        actor: Actor data (pandas Series)
        actor_bounds: Bounding box coordinates [x_min, x_max, y_min, y_max, z_min, z_max]
        longest_dim: String indicating the longest dimension ('length (X)', 'width (Y)', or 'height (Z)')
        possibility_id: ID of the possibility being visualized
    """
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Calculate padding for axis limits
    padding = 0.5  # 0.5 meters padding
    x_min = actor_bounds[0] - padding
    x_max = actor_bounds[1] + padding
    y_min = actor_bounds[2] - padding
    y_max = actor_bounds[3] + padding
    z_min = actor_bounds[4] - padding
    z_max = actor_bounds[5] + padding
    
    # Set axis limits
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_zlim(z_min, z_max)
    
    # Make the aspect ratio equal
    ax.set_box_aspect([(x_max-x_min), (y_max-y_min), (z_max-z_min)])
    
    # Plot bounding box with longest dimension highlighted
    plot_3d_box_with_highlight(ax, actor_bounds, actor['ActorName'], longest_dim)
    
    # Plot center point
    ax.scatter(actor['WorldX'], actor['WorldY'], actor['WorldZ'], color='blue', s=100, label='Actor Center')
    
    # Add label for actor
    ax.text(actor['WorldX'], actor['WorldY'], actor['WorldZ'] + 0.2,
            f'{actor["ActorName"]}\n{actor["ShortActorName"]}',
            horizontalalignment='center',
            verticalalignment='bottom',
            color='blue')
    
    # Add dimension information
    dimensions = {
        'length (X)': actor['WorldSizeX'],
        'width (Y)': actor['WorldSizeY'],
        'height (Z)': actor['WorldSizeZ']
    }
    
    # Set title with object information
    title = f"Object Size Visualization (Possibility {possibility_id})\n"
    title += f"Object: {actor['ActorName']} ({actor['ShortActorName']})\n"
    title += f"Dimensions: "
    
    # Add dimensions to title, highlighting the longest one
    dim_texts = []
    for dim_name, dim_value in dimensions.items():
        if dim_name == longest_dim:
            dim_texts.append(f"{dim_name}: {dim_value:.2f}m ({dim_value*100:.1f}cm) [LONGEST]")
        else:
            dim_texts.append(f"{dim_name}: {dim_value:.2f}m ({dim_value*100:.1f}cm)")
    
    title += ", ".join(dim_texts)
    
    ax.set_title(title)
    ax.set_xlabel('World X (m)')
    ax.set_ylabel('World Y (m)')
    ax.set_zlabel('World Z (m)')
    
    # Make the plot more viewable
    ax.view_init(elev=30, azim=45)
    
    # Save visualization
    output_dir = ensure_output_directory()
    plt.savefig(os.path.join(output_dir, f'object_size_visual.png'), 
                dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()

def plot_3d_box_with_highlight(ax, bounds, label, longest_dim):
    """
    Plot a 3D bounding box with the longest dimension highlighted in red
    
    Args:
        ax: Matplotlib 3D axis
        bounds: Bounding box coordinates [x_min, x_max, y_min, y_max, z_min, z_max]
        label: Label for the box
        longest_dim: String indicating the longest dimension ('length (X)', 'width (Y)', or 'height (Z)')
    """
    # Plot edges - complete box outline
    vertices = np.array([
        [bounds[0], bounds[2], bounds[4]],  # front bottom left (0)
        [bounds[1], bounds[2], bounds[4]],  # front bottom right (1)
        [bounds[1], bounds[3], bounds[4]],  # back bottom right (2)
        [bounds[0], bounds[3], bounds[4]],  # back bottom left (3)
        [bounds[0], bounds[2], bounds[5]],  # front top left (4)
        [bounds[1], bounds[2], bounds[5]],  # front top right (5)
        [bounds[1], bounds[3], bounds[5]],  # back top right (6)
        [bounds[0], bounds[3], bounds[5]]   # back top left (7)
    ])
    
    # Define edges by connecting vertices
    # X-direction edges (4 edges)
    x_edges = [[0, 1], [3, 2], [4, 5], [7, 6]]
    
    # Y-direction edges (4 edges)
    y_edges = [[0, 3], [1, 2], [4, 7], [5, 6]]
    
    # Z-direction edges (4 edges)
    z_edges = [[0, 4], [1, 5], [2, 6], [3, 7]]
    
    # Calculate dimensions
    x_length = bounds[1] - bounds[0]
    y_length = bounds[3] - bounds[2]
    z_length = bounds[5] - bounds[4]
    
    # Determine which edges to highlight based on longest dimension
    if longest_dim == 'length (X)':
        highlight_edges = x_edges
        normal_edges = y_edges + z_edges
    elif longest_dim == 'width (Y)':
        highlight_edges = y_edges
        normal_edges = x_edges + z_edges
    else:  # 'height (Z)'
        highlight_edges = z_edges
        normal_edges = x_edges + y_edges
    
    # Plot highlighted edges in red
    for edge in highlight_edges:
        ax.plot3D(vertices[edge, 0], vertices[edge, 1], vertices[edge, 2], 
                 color='red', linewidth=3, label=f"{label} - {longest_dim}" if edge == highlight_edges[0] else "")
    
    # Plot normal edges in grey
    for edge in normal_edges:
        ax.plot3D(vertices[edge, 0], vertices[edge, 1], vertices[edge, 2], 
                 color='grey', label=label if edge == normal_edges[0] else "")
    
    # Add dimension labels
    # X dimension (length)
    midpoint_x = (vertices[0] + vertices[1]) / 2
    ax.text(midpoint_x[0], midpoint_x[1], midpoint_x[2] - 0.1,
            f'{x_length*100:.1f}cm', 
            color='red' if longest_dim == 'length (X)' else 'grey',
            horizontalalignment='center',
            verticalalignment='top')
    
    # Y dimension (width)
    midpoint_y = (vertices[0] + vertices[3]) / 2
    ax.text(midpoint_y[0], midpoint_y[1], midpoint_y[2] - 0.1,
            f'{y_length*100:.1f}cm',
            color='red' if longest_dim == 'width (Y)' else 'grey',
            horizontalalignment='center',
            verticalalignment='top')
    
    # Z dimension (height)
    midpoint_z = (vertices[0] + vertices[4]) / 2
    ax.text(midpoint_z[0], midpoint_z[1], midpoint_z[2],
            f'{z_length*100:.1f}cm',
            color='red' if longest_dim == 'height (Z)' else 'grey',
            horizontalalignment='right',
            verticalalignment='center')
    
    # Add translucent surfaces
    # Bottom face
    xx, yy = np.meshgrid([bounds[0], bounds[1]], [bounds[2], bounds[3]])
    zz = np.full_like(xx, bounds[4])
    ax.plot_surface(xx, yy, zz, color='grey', alpha=0.1)
    
    # Top face
    zz = np.full_like(xx, bounds[5])
    ax.plot_surface(xx, yy, zz, color='grey', alpha=0.1)
    
    # Front face
    xx, zz = np.meshgrid([bounds[0], bounds[1]], [bounds[4], bounds[5]])
    yy = np.full_like(xx, bounds[2])
    ax.plot_surface(xx, yy, zz, color='grey', alpha=0.1)
    
    # Back face
    yy = np.full_like(xx, bounds[3])
    ax.plot_surface(xx, yy, zz, color='grey', alpha=0.1)
    
    # Left face
    yy, zz = np.meshgrid([bounds[2], bounds[3]], [bounds[4], bounds[5]])
    xx = np.full_like(yy, bounds[0])
    ax.plot_surface(xx, yy, zz, color='grey', alpha=0.1)
    
    # Right face
    xx = np.full_like(yy, bounds[1])
    ax.plot_surface(xx, yy, zz, color='grey', alpha=0.1)

def get_actor_bounds(actor):
    """
    Calculate the bounding box coordinates for an actor
    
    Args:
        actor: Actor data (pandas Series)
    
    Returns:
        List of coordinates [x_min, x_max, y_min, y_max, z_min, z_max]
    """
    x_min = actor['WorldX'] - actor['WorldSizeX']/2
    x_max = actor['WorldX'] + actor['WorldSizeX']/2
    y_min = actor['WorldY'] - actor['WorldSizeY']/2
    y_max = actor['WorldY'] + actor['WorldSizeY']/2
    z_min = actor['WorldZ'] - actor['WorldSizeZ']/2
    z_max = actor['WorldZ'] + actor['WorldSizeZ']/2
    return [x_min, x_max, y_min, y_max, z_min, z_max]

def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def main():
    # Determine the project root directory and script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Assumes this script is one level down from project root
    
    # Construct paths to the CSV files
    actors_csv_path = os.path.join(project_root, '0_data_cleanup_tool', 'output', 'ranked_unique_actor_anno.csv')
    object_size_csv_path = os.path.join(script_dir, 'output', 'object_size_all.csv')
    
    # Read the CSV files
    df_actors = pd.read_csv(actors_csv_path)
    df_object_size = pd.read_csv(object_size_csv_path)
    
    # Get data for the specified possibility
    result = df_object_size[df_object_size['Possibility'] == POSSIBILITY_ID]
    
    if len(result) == 0:
        print(f"No data found for possibility {POSSIBILITY_ID}")
        return
    
    result = result.iloc[0]
    
    # Get actor data
    actor_name = result['ActorName']
    actor = df_actors[df_actors['ActorName'] == actor_name].iloc[0]
    
    # Calculate bounds
    actor_bounds = get_actor_bounds(actor)
    
    # Get longest dimension
    longest_dim = result['LongestDimension']
    
    # Visualize
    visualize_object_size(actor, actor_bounds, longest_dim, POSSIBILITY_ID)
    
    # Print information
    print(f"Visualizing object size for possibility {POSSIBILITY_ID}:")
    print(f"Actor: {actor_name} ({actor['ShortActorName']})")
    print(f"Longest dimension: {longest_dim} = {result['LongestDimension_m']:.2f}m ({result['LongestDimension_cm']:.1f}cm)")
    print(f"All dimensions:")
    print(f"  Length (X): {actor['WorldSizeX']:.2f}m ({actor['WorldSizeX']*100:.1f}cm)")
    print(f"  Width (Y): {actor['WorldSizeY']:.2f}m ({actor['WorldSizeY']*100:.1f}cm)")
    print(f"  Height (Z): {actor['WorldSizeZ']:.2f}m ({actor['WorldSizeZ']*100:.1f}cm)")

if __name__ == "__main__":
    main()