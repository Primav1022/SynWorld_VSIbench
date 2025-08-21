import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches # Added for bounding boxes and arcs
import ast

# Configuration variables
POSSIBILITY_ID_TO_VISUALIZE = 8  # Change this to visualize different combinations

# Define input file paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'route_plan_all.csv')
ACTOR_ANNO_FILE = os.path.join(BASE_DIR, '0_data_cleanup_tool', 'output', 'ranked_unique_actor_anno.csv')

def load_data():
    """Loads route plan and actor annotation data from CSV files."""
    try:
        route_df = pd.read_csv(ROUTES_FILE)
        actor_df = pd.read_csv(ACTOR_ANNO_FILE)
        print(f"Successfully loaded {ROUTES_FILE}")
        print(f"Successfully loaded {ACTOR_ANNO_FILE}")
        return route_df, actor_df
    except FileNotFoundError as e:
        print(f"Error loading data: {e}. Please ensure input files are in the correct locations.")
        return None, None

def get_actor_details(actor_name, actor_df):
    """Retrieves detailed information for a given actor."""
    actor_info = actor_df[actor_df['ActorName'] == actor_name]
    if actor_info.empty:
        print(f"Warning: Actor '{actor_name}' not found in annotation file.")
        return None
    actor_info = actor_info.iloc[0]
    # 兼容没有 ActorDescription 列或为空的情况
    description = None
    if 'ActorDescription' in actor_info.index:
        description = actor_info['ActorDescription']
    short_name = actor_info['ShortActorName']
    display_name = description if pd.notna(description) and description.strip() != "" else short_name
    return {
        'name': actor_name,
        'display_name': display_name,
        'x': actor_info['WorldX'],
        'y': actor_info['WorldY'],
        'z': actor_info['WorldZ'],
        'size_x': actor_info['WorldSizeX'], # Added
        'size_y': actor_info['WorldSizeY']  # Added
    }

def plot_actor(ax, actor_details, color, label_prefix="", marker='o', size=100):
    """Plots a single actor on the given axes with its bounding box."""
    if actor_details:
        # Plot bounding box
        rect = patches.Rectangle(
            (actor_details['x'] - actor_details['size_x'] / 2, actor_details['y'] - actor_details['size_y'] / 2),
            actor_details['size_x'],
            actor_details['size_y'],
            linewidth=1,
            edgecolor=color,
            facecolor=color, # Use the base color for facecolor
            alpha=0.33,      # Set transparency using the alpha parameter
            label=f"{label_prefix}{actor_details['display_name']}" if marker == 'o' else None, # Avoid duplicate labels for facing actor
            zorder=4
        )
        ax.add_patch(rect)
        # Plot center marker
        ax.scatter(actor_details['x'], actor_details['y'], color=color, s=size/5, marker=marker, zorder=5) # Smaller marker for center
        ax.text(actor_details['x'] + 0.1, actor_details['y'] + 0.1, actor_details['display_name'], fontsize=9, zorder=6)


def calculate_angle_degrees(v1, v2):
    """Calculates the angle in degrees between two vectors v1 and v2."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0 # Avoid division by zero
    cos_angle = dot_product / (norm_v1 * norm_v2)
    angle_rad = np.arccos(np.clip(cos_angle, -1.0, 1.0)) # Clip for numerical stability
    angle_deg = np.degrees(angle_rad)

    # Determine sign of the angle (for left/right turn)
    cross_product_z = v1[0] * v2[1] - v1[1] * v2[0]
    if cross_product_z < 0:
        angle_deg = -angle_deg # Clockwise turn
    return angle_deg


def plot_turn_arc(ax, center_pos, prev_vec, next_vec, turn_command):
    """Plots an arc representing the turn."""
    if not center_pos or prev_vec is None or next_vec is None:
        return

    # Normalize vectors for angle calculation and consistent arc radius
    prev_vec_norm = prev_vec / np.linalg.norm(prev_vec) if np.linalg.norm(prev_vec) > 0 else np.array([0,1])
    next_vec_norm = next_vec / np.linalg.norm(next_vec) if np.linalg.norm(next_vec) > 0 else np.array([0,1])

    angle_prev_rad = np.arctan2(prev_vec_norm[1], prev_vec_norm[0])
    angle_next_rad = np.arctan2(next_vec_norm[1], next_vec_norm[0])

    angle_prev_deg = np.degrees(angle_prev_rad)
    angle_next_deg = np.degrees(angle_next_rad)

    # Adjust angles to be in [0, 360)
    if angle_prev_deg < 0: angle_prev_deg += 360
    if angle_next_deg < 0: angle_next_deg += 360

    # Determine the sweep angle and direction
    turn_angle_deg = calculate_angle_degrees(prev_vec_norm, next_vec_norm)

    arc_radius = 0.5 # Adjust as needed for visibility
    arc_color = 'purple'

    # Theta1 is the start angle of the arc, Theta2 is the end angle
    # For positive turn_angle_deg (left), arc goes from prev_vec to next_vec counter-clockwise
    # For negative turn_angle_deg (right), arc goes from prev_vec to next_vec clockwise
    # matplotlib Arc takes angles in degrees, counter-clockwise from positive x-axis

    theta1 = angle_prev_deg
    theta2 = angle_prev_deg + turn_angle_deg # This will be correct due to signed turn_angle_deg

    # Ensure theta2 is correctly representing the sweep
    # If turn_angle_deg is large, theta2 might wrap around. Matplotlib handles this.

    arc = patches.Arc((center_pos['x'], center_pos['y']), 
                      width=arc_radius*2, height=arc_radius*2, 
                      angle=0, # Rotation of ellipse, 0 for circle
                      theta1=min(theta1, theta2) if turn_angle_deg !=0 else theta1, 
                      theta2=max(theta1, theta2) if turn_angle_deg !=0 else theta2, 
                      color=arc_color, linewidth=1.5, linestyle='-', zorder=7)
    ax.add_patch(arc)

    # Add arrow to indicate direction of turn at the end of the arc
    # Calculate the midpoint of the arc for the arrow
    mid_angle_rad = np.deg2rad(theta1 + turn_angle_deg / 2)
    arrow_dx = np.cos(mid_angle_rad) * 0.05 # Small offset for arrow head
    arrow_dy = np.sin(mid_angle_rad) * 0.05

    # Position the arrow head at the end of the arc segment
    end_arc_point_x = center_pos['x'] + arc_radius * np.cos(np.deg2rad(theta2))
    end_arc_point_y = center_pos['y'] + arc_radius * np.sin(np.deg2rad(theta2))

    # Direction of the arrow (tangent at the end of the arc)
    # If turning left (positive angle), tangent is perpendicular to radius vector, pointing CCW
    # If turning right (negative angle), tangent is perpendicular, pointing CW
    tangent_angle_rad = np.deg2rad(theta2) + (np.pi/2 if turn_angle_deg > 0 else -np.pi/2)
    
    # For simplicity, just place a text label for now, precise arrowheads on arcs are tricky
    # ax.text(end_arc_point_x, end_arc_point_y, '>', color=arc_color, zorder=8, 
    #         horizontalalignment='center', verticalalignment='center', 
    #         rotation=np.degrees(tangent_angle_rad))


def visualize_route(possibility_id, route_data, actor_df):
    """Visualizes a single route plan."""
    if route_data.empty:
        print(f"No data found for Possibility ID: {possibility_id}")
        return

    fig, ax = plt.subplots(figsize=(12, 8))

    # Get actor details
    begin_actor_name = route_data['BeginActor'].iloc[0]
    facing_actor_name = route_data['FacingActor'].iloc[0]
    end_actor_name = route_data['EndActor'].iloc[0]
    intermediate_stops_str = route_data['IntermediateStops'].iloc[0]

    begin_actor_d = get_actor_details(begin_actor_name, actor_df)
    facing_actor_d = get_actor_details(facing_actor_name, actor_df)
    end_actor_d = get_actor_details(end_actor_name, actor_df)

    intermediate_actors_d = []
    if pd.notna(intermediate_stops_str) and intermediate_stops_str:
        intermediate_actor_names = [name.strip() for name in intermediate_stops_str.split(',')]
        for name in intermediate_actor_names:
            detail = get_actor_details(name, actor_df)
            if detail:
                intermediate_actors_d.append(detail)

    # Plot actors
    plot_actor(ax, begin_actor_d, 'blue', "Begin: ")
    # For facing actor, use a different marker and smaller size, no redundant label from bounding box
    if facing_actor_d:
        rect = patches.Rectangle(
            (facing_actor_d['x'] - facing_actor_d['size_x'] / 2, facing_actor_d['y'] - facing_actor_d['size_y'] / 2),
            facing_actor_d['size_x'],
            facing_actor_d['size_y'],
            linewidth=1,
            edgecolor='cyan',
            facecolor='cyan', # Use the base color for facecolor
            alpha=0.33,       # Set transparency using the alpha parameter
            zorder=4
        )
        ax.add_patch(rect)
        ax.scatter(facing_actor_d['x'], facing_actor_d['y'], color='cyan', s=70/5, marker='x', label="Facing: " + facing_actor_d['display_name'], zorder=5)
        ax.text(facing_actor_d['x'] + 0.1, facing_actor_d['y'] + 0.1, facing_actor_d['display_name'], fontsize=9, zorder=6)

    plot_actor(ax, end_actor_d, 'red', "End: ")
    for i, inter_actor_d in enumerate(intermediate_actors_d):
        plot_actor(ax, inter_actor_d, 'green', f"Stop {i+1}: ")

    # Plot path and facing lines
    path_points_x = [begin_actor_d['x']]
    path_points_y = [begin_actor_d['y']]

    # Initial facing vector
    if begin_actor_d and facing_actor_d:
        vec_initial_facing = np.array([facing_actor_d['x'] - begin_actor_d['x'], facing_actor_d['y'] - begin_actor_d['y']])
        ax.arrow(begin_actor_d['x'], begin_actor_d['y'], 
                 vec_initial_facing[0], 
                 vec_initial_facing[1], 
                 head_width=0.15, head_length=0.2, fc='cyan', ec='cyan', linestyle='--', label="Initial Facing Dir", zorder=3)
    else:
        vec_initial_facing = np.array([0, 1]) # Default if facing actor is missing

    current_pos_details = begin_actor_d
    current_facing_vec = vec_initial_facing
    route_sequence = intermediate_actors_d + [end_actor_d]

    # Define turns here, before it's used in the loop
    # MODIFICATION START: Update how 'turns' are derived from 'Options' and 'Answer'
    options_str = route_data['Options'].iloc[0]
    correct_answer_letter = route_data['Answer'].iloc[0]
    turns = [] # Initialize turns as an empty list

    if pd.notna(options_str) and options_str and pd.notna(correct_answer_letter) and correct_answer_letter:
        try:
            options_list = ast.literal_eval(options_str) # ast.literal_eval is safer
            correct_option_full_string = ""
            for option_item in options_list:
                # option_item is like "A. Turn Left" or "B. Turn Right, Turn Back"
                if option_item.strip().startswith(correct_answer_letter + "."):
                    correct_option_full_string = option_item.strip()
                    break
            
            if correct_option_full_string:
                # Remove "X. " part, e.g., "A. "
                # Ensure there's a space after the dot before splitting
                if ". " in correct_option_full_string:
                    actual_turns_sequence_str = correct_option_full_string.split('. ', 1)[1]
                    # Split by comma to get individual turn commands
                    turns = [t.strip() for t in actual_turns_sequence_str.split(',') if t.strip()]
                else: # Handle cases like "A.Turn Left" if that occurs
                    actual_turns_sequence_str = correct_option_full_string.split('.', 1)[1]
                    turns = [t.strip() for t in actual_turns_sequence_str.split(',') if t.strip()]

            else:
                print(f"Warning: Correct answer letter '{correct_answer_letter}' not found in options: {options_list} for Possibility ID {possibility_id}")
        except (ValueError, SyntaxError) as e:
            print(f"Warning: Could not parse options string: '{options_str}'. Error: {e} for Possibility ID {possibility_id}")
            turns = [] # Ensure turns is empty if parsing fails
    else:
        print(f"Warning: 'Options' or 'Answer' data is missing or invalid for Possibility ID {possibility_id}.")
    # MODIFICATION END

    path_points_x = [begin_actor_d['x']]
    path_points_y = [begin_actor_d['y']]

    for i, target_actor_details in enumerate(route_sequence):
        if current_pos_details and target_actor_details:
            ax.plot([current_pos_details['x'], target_actor_details['x']], [current_pos_details['y'], target_actor_details['y']], 'k--', zorder=2) # Path segment
            path_points_x.append(target_actor_details['x'])
            path_points_y.append(target_actor_details['y'])

            # Calculate and plot turn arc
            vec_to_target = np.array([target_actor_details['x'] - current_pos_details['x'], target_actor_details['y'] - current_pos_details['y']])
            if np.linalg.norm(current_facing_vec) > 0 and np.linalg.norm(vec_to_target) > 0:
                turn_command_from_csv = ""
                if i < len(turns): # Check against length of turns list
                    turn_command_from_csv = turns[i]
                # Pass the actual turn command string to plot_turn_arc
                plot_turn_arc(ax, current_pos_details, current_facing_vec, vec_to_target, turn_command_from_csv)
            
            # Update for next iteration
            current_facing_vec = vec_to_target
            current_pos_details = target_actor_details
    
    ax.plot(path_points_x, path_points_y, 'ko-', label="Route Path", zorder=1) # Full path with markers

    # Annotate turns (Text labels)
    # 'turns' is already defined above
    turn_visualization_points = [begin_actor_d] + intermediate_actors_d

    for i, turn_cmd in enumerate(turns):
        if i < len(turn_visualization_points) and turn_visualization_points[i]:
            actor_name_for_size = turn_visualization_points[i]['name']
            actor_size_y = 0
            if actor_df is not None and not actor_df[actor_df['ActorName'] == actor_name_for_size].empty:
                 actor_size_y = actor_df.loc[actor_df['ActorName'] == actor_name_for_size, 'WorldSizeY'].iloc[0]
            
            ax.annotate(f"{turn_cmd.split()[0].capitalize()} {turn_cmd.split()[1] if len(turn_cmd.split()) > 1 else ''}", 
                        (turn_visualization_points[i]['x'], turn_visualization_points[i]['y']), 
                        textcoords="offset points", xytext=(0,15 + actor_size_y * 5),
                        ha='center', color='purple', zorder=7,
                        bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.3'))

    # Set plot properties
    all_x = [d['x'] for d in [begin_actor_d, facing_actor_d, end_actor_d] + intermediate_actors_d if d]
    all_y = [d['y'] for d in [begin_actor_d, facing_actor_d, end_actor_d] + intermediate_actors_d if d]
    if not all_x or not all_y: # handle case where no actors could be plotted
        print("Error: No actor coordinates available to set plot limits.")
        plt.close(fig)
        return
        
    ax.set_xlabel("World X Coordinate")
    ax.set_ylabel("World Y Coordinate")
    ax.set_title(f"Route Plan Visualization - Possibility ID: {possibility_id}")
    ax.legend(loc='best')
    ax.grid(True)
    ax.axis('equal') # Ensure X and Y scales are the same for correct angle representation
    
    # Determine plot limits with padding
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    x_range = x_max - x_min if x_max > x_min else 1.0
    y_range = y_max - y_min if y_max > y_min else 1.0
    padding = max(x_range, y_range) * 0.1 # 10% padding

    ax.set_xlim(x_min - padding, x_max + padding)
    ax.set_ylim(y_min - padding, y_max + padding)

    plt.tight_layout() # Adjust layout to fit screen better

    # Define output path for the plot
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plot_filename = os.path.join(output_dir, 'route_plan_visual.png')
    
    try:
        plt.savefig(plot_filename)
        print(f"Plot saved to {plot_filename}")
    except Exception as e:
        print(f"Error saving plot: {e}")

    plt.show()

if __name__ == '__main__':
    route_df, actor_df = load_data()
    if route_df is not None and actor_df is not None:
        # Ensure output directory exists (moved here for earlier check, though visualize_route also checks)
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
            
        selected_route_data = route_df[route_df['Possibility'] == POSSIBILITY_ID_TO_VISUALIZE]
        if not selected_route_data.empty:
            visualize_route(POSSIBILITY_ID_TO_VISUALIZE, selected_route_data, actor_df)
        else:
            print(f"Possibility ID {POSSIBILITY_ID_TO_VISUALIZE} not found in {ROUTES_FILE}.")
    else:
        print("Failed to load data. Visualization script will not run.")