import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# Configuration variables
POSSIBILITY_ID = 1  # Change this to visualize different combinations

def find_closest_points_3d(bounds1, bounds2, actor1, actor2):
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

def visualize_distance(primary_obj, option_objs, primary_bounds, option_bounds, distances, possibility_id):
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Calculate the bounds of all objects to set proper axis limits
    all_bounds = [primary_bounds] + option_bounds
    x_min = min(bound[0] for bound in all_bounds)
    x_max = max(bound[1] for bound in all_bounds)
    y_min = min(bound[2] for bound in all_bounds)
    y_max = max(bound[3] for bound in all_bounds)
    z_min = min(bound[4] for bound in all_bounds)
    z_max = max(bound[5] for bound in all_bounds)
    
    # Add some padding
    padding = 0.5  # 0.5 meters padding
    x_min -= padding
    x_max += padding
    y_min -= padding
    y_max += padding
    z_min -= padding
    z_max += padding
    
    # Set axis limits
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_zlim(z_min, z_max)
    
    # Make the aspect ratio equal
    ax.set_box_aspect([(x_max-x_min), (y_max-y_min), (z_max-z_min)])
    
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
    
    # Plot primary object in blue
    plot_3d_box(primary_bounds, 'blue', primary_obj['ActorName'])
    # Add label for primary object
    ax.text(primary_obj['WorldX'], primary_obj['WorldY'], primary_obj['WorldZ'] + 0.2,
            f'{primary_obj["ActorName"]}\n(primary)',
            horizontalalignment='center',
            verticalalignment='bottom',
            color='blue')
    
    # Plot option objects (closest in red, others in grey)
    colors = ['red'] + ['grey'] * 3  # First object (closest) in red, rest in grey
    for i, (option, bounds) in enumerate(zip(option_objs, option_bounds)):
        plot_3d_box(bounds, colors[i], option['ActorName'])
        # Add (closest) label for the red box
        if i == 0:
            ax.text(option['WorldX'], option['WorldY'], option['WorldZ'] + 0.2,
                   f'{option["ActorName"]}\n(closest)\n{distances[i]:.2f}m',
                   horizontalalignment='center',
                   verticalalignment='bottom',
                   color='red')
    
    # Plot closest points and distance lines for all options
    for i, (option, bounds, distance) in enumerate(zip(option_objs, option_bounds, distances)):
        x1, y1, z1, x2, y2, z2 = find_closest_points_3d(primary_bounds, bounds, primary_obj, option)
        
        # Plot distance line (red for closest, grey for others)
        line_color = 'red' if i == 0 else 'grey'
        ax.plot([x1, x2], [y1, y2], [z1, z2], '--', 
                color=line_color, 
                label=f'Distance to {option["ActorName"]}: {distance:.2f}m')
        
        # Add distance label at the closest point of the option object (except for closest one as it's already labeled)
        if i > 0:
            ax.text(x2, y2, z2 + 0.2, 
                    f'{option["ActorName"]}\n{distance:.2f}m',
                    horizontalalignment='center',
                    verticalalignment='bottom',
                    color='grey')
    
    # Set title with primary object and option order
    title = f"Relative Distance (Possibility {possibility_id})\n"
    title += f"Primary: {primary_obj['ActorName']}\n"
    title += "Options: "
    options_text = [f"{i+1}. {option['ActorName']} ({distance:.2f}m)" 
                   for i, (option, distance) in enumerate(zip(option_objs, distances))]
    title += ", ".join(options_text)
    
    ax.set_title(title)
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
    plt.savefig(os.path.join(output_dir, f'relative_distance_visual.png'), 
                dpi=300, bbox_inches='tight', 
                pad_inches=0.5)  # Add some padding around the plot
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
    relative_csv_path = os.path.join(script_dir, 'output', 'relative_distance_all.csv')

    # Read the CSV files
    df_actors = pd.read_csv(actors_csv_path)
    df_relative = pd.read_csv(relative_csv_path)
    
    # Get data for the specified possibility
    result = df_relative[df_relative['Possibility'] == POSSIBILITY_ID].iloc[0]
    
    # Get primary object data
    primary_obj = df_actors[df_actors['ActorName'] == result['PrimaryObject']].iloc[0]
    
    # Get option objects data
    option_objs = []
    distances = []
    
    # Get all four option objects in order
    for i in range(1, 5):
        option = df_actors[df_actors['ActorName'] == result[f'OptionObject{i}']].iloc[0]
        option_objs.append(option)
        distances.append(result[f'Distance{i}'])
    
    # Calculate bounds
    primary_bounds = get_actor_bounds(primary_obj)
    option_bounds = [get_actor_bounds(obj) for obj in option_objs]
    
    # Visualize
    visualize_distance(primary_obj, option_objs, primary_bounds, option_bounds, distances, POSSIBILITY_ID)

if __name__ == "__main__":
    main()