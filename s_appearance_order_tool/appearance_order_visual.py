import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math

# Configuration variables
POSSIBILITY_ID = 1  # Change this to visualize different combinations

def visualize_appearance_order(actors, first_frames, possibility_id):
    """
    Visualize the appearance order of four actors in 3D space
    
    Args:
        actors: List of actor data (pandas Series)
        first_frames: List of first appearance frames for each actor
        possibility_id: ID of the possibility being visualized
    """
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Define colors for appearance order
    colors = ['red', 'orange', 'green', 'blue']
    
    # Calculate the bounds of all objects to set proper axis limits
    all_bounds = [get_actor_bounds(actor) for actor in actors]
    x_min = min(bound[0] for bound in all_bounds)
    x_max = max(bound[1] for bound in all_bounds)
    y_min = min(bound[2] for bound in all_bounds)
    y_max = max(bound[3] for bound in all_bounds)
    z_min = min(bound[4] for bound in all_bounds)
    z_max = max(bound[5] for bound in all_bounds)
    
    # Also consider camera positions for axis limits
    camera_positions = []
    for actor in actors:
        if 'CamX' in actor and not pd.isna(actor['CamX']):
            camera_positions.append([actor['CamX'], actor['CamY'], actor['CamZ']])
            x_min = min(x_min, actor['CamX'] - 0.5)
            x_max = max(x_max, actor['CamX'] + 0.5)
            y_min = min(y_min, actor['CamY'] - 0.5)
            y_max = max(y_max, actor['CamY'] + 0.5)
            z_min = min(z_min, actor['CamZ'] - 0.5)
            z_max = max(z_max, actor['CamZ'] + 0.5)
    
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
    
    # Function to plot camera with orientation
    def plot_camera(actor, color, label):
        # Check if camera data exists
        if ('CamX' not in actor or pd.isna(actor['CamX']) or 
            'CamY' not in actor or pd.isna(actor['CamY']) or 
            'CamZ' not in actor or pd.isna(actor['CamZ'])):
            print(f"Warning: Camera data missing for {actor['ActorName']}")
            return None
            
        # Camera position
        cam_pos = np.array([actor['CamX'], actor['CamY'], actor['CamZ']])
        
        # Plot camera position as a sphere
        ax.scatter(cam_pos[0], cam_pos[1], cam_pos[2], color=color, s=100, marker='o', 
                  label=f"Camera for {label}")
        
        # Calculate camera direction vectors based on pitch, yaw, roll
        # Convert degrees to radians
        if 'CamPitch' in actor and 'CamYaw' in actor and not pd.isna(actor['CamPitch']) and not pd.isna(actor['CamYaw']):
            pitch_rad = math.radians(actor['CamPitch'])
            yaw_rad = math.radians(actor['CamYaw'])
            
            # Calculate direction vector (simplified - ignoring roll)
            # In Unreal Engine: X is forward, Y is right, Z is up
            # Pitch rotates around Y axis, Yaw rotates around Z axis
            # Calculate direction vector components
            dx = math.cos(yaw_rad) * math.cos(pitch_rad)
            dy = math.sin(yaw_rad) * math.cos(pitch_rad)
            dz = math.sin(pitch_rad)
            
            # Scale the direction vector
            direction_length = 0.5  # Length of the direction arrow
            direction = np.array([dx, dy, dz]) * direction_length
            
            # Draw direction arrow
            ax.quiver(cam_pos[0], cam_pos[1], cam_pos[2], 
                     direction[0], direction[1], direction[2],
                     color=color, arrow_length_ratio=0.2)
            
            # Draw a simplified camera frustum
            frustum_length = 0.3
            frustum_width = 0.2
            frustum_height = 0.15
            
            # Calculate frustum corners based on direction
            # We'll create a simplified frustum with 4 points at the far end
            # First, create basis vectors for the camera's coordinate system
            forward = np.array([dx, dy, dz])
            forward = forward / np.linalg.norm(forward)  # Normalize
            
            # Up vector (we'll use world up and adjust)
            world_up = np.array([0, 0, 1])
            right = np.cross(forward, world_up)
            right = right / np.linalg.norm(right)  # Normalize
            
            # Recalculate up to ensure orthogonality
            up = np.cross(right, forward)
            up = up / np.linalg.norm(up)  # Normalize
            
            # Calculate frustum corners
            frustum_end = cam_pos + forward * frustum_length
            top_right = frustum_end + up * frustum_height/2 + right * frustum_width/2
            top_left = frustum_end + up * frustum_height/2 - right * frustum_width/2
            bottom_right = frustum_end - up * frustum_height/2 + right * frustum_width/2
            bottom_left = frustum_end - up * frustum_height/2 - right * frustum_width/2
            
            # Draw frustum lines
            for end_point in [top_right, top_left, bottom_right, bottom_left]:
                ax.plot3D([cam_pos[0], end_point[0]], 
                         [cam_pos[1], end_point[1]], 
                         [cam_pos[2], end_point[2]], 
                         color=color, linestyle='-', alpha=0.7)
            
            # Draw frustum end rectangle
            ax.plot3D([top_right[0], top_left[0], bottom_left[0], bottom_right[0], top_right[0]],
                     [top_right[1], top_left[1], bottom_left[1], bottom_right[1], top_right[1]],
                     [top_right[2], top_left[2], bottom_left[2], bottom_right[2], top_right[2]],
                     color=color, linestyle='-', alpha=0.7)
        
        return cam_pos
    
    # Plot each actor with its appearance order color
    camera_positions = []
    camera_labels = []
    
    for i, (actor, frame) in enumerate(zip(actors, first_frames)):
        bounds = get_actor_bounds(actor)
        color = colors[i]
        plot_3d_box(bounds, color, actor['ActorName'])
        
        # Add label with appearance order
        order_label = ["1st", "2nd", "3rd", "4th"][i]
        ax.text(actor['WorldX'], actor['WorldY'], actor['WorldZ'] + 0.2,
                f"{actor['ActorName']}\n({order_label}: Frame {frame})",
                horizontalalignment='center',
                verticalalignment='bottom',
                color=color,
                fontweight='bold')
        
        # Plot camera for this actor and store its position
        cam_pos = plot_camera(actor, color, f"{order_label} appearance")
        if cam_pos is not None:
            camera_positions.append(cam_pos)
            camera_labels.append(f"{order_label} (Frame {frame})")
    
    # Draw dotted lines connecting cameras in temporal order
    if len(camera_positions) > 1:
        # Extract x, y, z coordinates for the line
        x_coords = [pos[0] for pos in camera_positions]
        y_coords = [pos[1] for pos in camera_positions]
        z_coords = [pos[2] for pos in camera_positions]
        
        # Plot the dotted line connecting cameras in temporal order
        ax.plot(x_coords, y_coords, z_coords, 'k--', alpha=0.7, linewidth=1.5, label="Camera Path")
        
        # Add small labels at each camera position showing the order
        for i, (pos, label) in enumerate(zip(camera_positions, camera_labels)):
            ax.text(pos[0], pos[1], pos[2] + 0.15, 
                   label,
                   horizontalalignment='center',
                   verticalalignment='bottom',
                   fontsize=8,
                   bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))
    
    # Set title with appearance order
    title = f"Appearance Order Visualization (Possibility {possibility_id})\n"
    title += "Order: "
    actor_texts = []
    for i, (actor, frame) in enumerate(zip(actors, first_frames)):
        order_label = ["1st", "2nd", "3rd", "4th"][i]
        color_name = ["Red", "Orange", "Green", "Blue"][i]
        actor_texts.append(f"{actor['ActorName']} ({order_label}: Frame {frame}, {color_name})")
    title += ", ".join(actor_texts)
    
    ax.set_title(title)
    ax.set_xlabel('World X')
    ax.set_ylabel('World Y')
    ax.set_zlabel('World Z')
    ax.legend()
    
    # Make the plot more viewable
    ax.view_init(elev=30, azim=45)
    
    # Save visualization
    output_dir = ensure_output_directory()
    plt.savefig(os.path.join(output_dir, f'appearance_order_visual.png'), 
                dpi=300, bbox_inches='tight', 
                pad_inches=0.5)  # Add some padding around the plot
    plt.show()
    plt.close()

def get_actor_bounds(actor):
    """Calculate the bounding box coordinates for an actor"""
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
    project_root = os.path.dirname(script_dir) # This assumes the script is one level down from project root

    # Construct relative paths to the CSV files
    actors_csv_path = os.path.join(project_root, '0_data_cleanup_tool', 'output', 'ranked_unique_actor_anno.csv')
    appearance_csv_path = os.path.join(script_dir, 'output', 'appearance_order_all.csv')

    # Read the CSV files
    df_actors = pd.read_csv(actors_csv_path)
    df_appearance = pd.read_csv(appearance_csv_path)
    
    # Get data for the specified possibility
    result = df_appearance[df_appearance['Possibility'] == POSSIBILITY_ID].iloc[0]
    
    # Get actor data and first frames
    actors = []
    first_frames = []
    
    # Get all four actors in order of appearance
    actor_names = []
    actor_frames = []
    
    # Extract actor names and frames
    for i in range(1, 5):
        actor_name = result[f'Actor{i}']
        actor_frame = result[f'Actor{i}_FirstFrame']
        actor_names.append(actor_name)
        actor_frames.append(actor_frame)
    
    # Sort actors by first frame
    sorted_indices = sorted(range(len(actor_frames)), key=lambda k: actor_frames[k])
    
    # Get actors in order of appearance
    for idx in sorted_indices:
        actor = df_actors[df_actors['ActorName'] == actor_names[idx]].iloc[0]
        actors.append(actor)
        first_frames.append(actor_frames[idx])
    
    # Visualize
    visualize_appearance_order(actors, first_frames, POSSIBILITY_ID)
    
    # Print information
    print(f"Visualizing appearance order for possibility {POSSIBILITY_ID}:")
    for i, (actor, frame) in enumerate(zip(actors, first_frames)):
        order_label = ["1st", "2nd", "3rd", "4th"][i]
        color_name = ["Red", "Orange", "Green", "Blue"][i]
        print(f"{order_label} ({color_name}): {actor['ActorName']} (Frame {frame})")
        
        # Print camera information if available
        if 'CamX' in actor and not pd.isna(actor['CamX']):
            print(f"  Camera position: ({actor['CamX']:.2f}, {actor['CamY']:.2f}, {actor['CamZ']:.2f})")
            if 'CamPitch' in actor and not pd.isna(actor['CamPitch']):
                print(f"  Camera orientation: Pitch={actor['CamPitch']:.2f}°, Yaw={actor['CamYaw']:.2f}°, Roll={actor['CamRoll']:.2f}°")

if __name__ == "__main__":
    main()