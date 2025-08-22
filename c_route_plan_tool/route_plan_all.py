import pandas as pd
import itertools
import math
import os
import numpy as np # Added for vector math
import random # Added for shuffling options

def get_data_folder_name():
    """
    从output_csv目录中找到数据文件夹名称
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_csv_root = os.path.join(project_root, "output_csv")
    
    if os.path.exists(output_csv_root):
        for item in os.listdir(output_csv_root):
            item_path = os.path.join(output_csv_root, item)
            if os.path.isdir(item_path):
                return item
    return "default"

# Configuration Variables
MIN_END_DISTANCE = 1  # Minimum distance between begin_at and end_at in meters
NEIGHBOR_DISTANCE = 2  # Default maximum distance to search for a valid facing_at actor in meters

# Define input and output file paths
# Assuming the script is in c_route_plan_tool and other files are in their respective locations as per the structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_folder_name = get_data_folder_name()
ACTOR_ANNO_FILE = os.path.join(BASE_DIR, 'output_csv', data_folder_name, 'ranked_unique_actor_anno.csv')
ABSOLUTE_DISTANCE_FILE = os.path.join(BASE_DIR, 'output_csv', data_folder_name, 'absolute_distances_all.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'output_csv', data_folder_name, 'route_plan_all.csv')

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

def load_data():
    """Loads actor annotation and absolute distance data from CSV files."""
    try:
        actor_df = pd.read_csv(ACTOR_ANNO_FILE)
        distance_df = pd.read_csv(ABSOLUTE_DISTANCE_FILE)
        print(f"Successfully loaded {ACTOR_ANNO_FILE}")
        print(f"Successfully loaded {ABSOLUTE_DISTANCE_FILE}")
        return actor_df, distance_df
    except FileNotFoundError as e:
        print(f"Error loading data: {e}. Please ensure input files are in the correct locations.")
        return None, None

def get_actor_details(actor_name, actor_df):
    """Retrieves detailed information for a given actor from the actor dataframe.

    Args:
        actor_name (str): The name of the actor.
        actor_df (pd.DataFrame): DataFrame containing actor annotations.

    Returns:
        dict: A dictionary containing the actor's details (name, display_name, coordinates, size, volume).
    """
    actor_info = actor_df[actor_df['ActorName'] == actor_name].iloc[0]
    # 兼容缺失的 ActorDescription 列，回退到 ShortActorName
    description = actor_info.get('ActorDescription', None)
    short_name = actor_info.get('ShortActorName', actor_name)
    # Use ActorDescription if available and not NaN/empty, otherwise use ShortActorName
    display_name = description if (description is not None and pd.notna(description) and str(description).strip() != "") else short_name
    return {
        'name': actor_name,
        'display_name': display_name,
        'x': actor_info['WorldX'],
        'y': actor_info['WorldY'],
        'z': actor_info['WorldZ'],
        'size_x': actor_info['WorldSizeX'],
        'size_y': actor_info['WorldSizeY'],
        'size_z': actor_info['WorldSizeZ'],
        'volume': actor_info['Volume']  # Added volume
    }

def get_distance(actor1_name, actor2_name, distance_df):
    """Gets the pre-calculated distance between two actors from the distance dataframe.

    Args:
        actor1_name (str): Name of the first actor.
        actor2_name (str): Name of the second actor.
        distance_df (pd.DataFrame): DataFrame containing pairwise actor distances.

    Returns:
        float or None: The distance between the two actors, or None if not found.
    """
    # Check for (actor1, actor2) or (actor2, actor1) as distance is symmetric
    dist_row = distance_df[
        ((distance_df['Actor1'] == actor1_name) & (distance_df['Actor2'] == actor2_name)) |
        ((distance_df['Actor1'] == actor2_name) & (distance_df['Actor2'] == actor1_name))
    ]
    if not dist_row.empty:
        return dist_row['Answer'].iloc[0]
    # If distance is not found, return None. Calling code should handle this.
    return None

def get_actor_coords(actor_name, actor_df):
    """Retrieves world coordinates (x, y) for a given actor.
    DEPRECATED: get_actor_details provides more comprehensive info including coordinates.
    Kept for now if any specific part of the code relies on this exact output format.
    """
    actor_info = actor_df[actor_df['ActorName'] == actor_name].iloc[0]
    return np.array([actor_info['WorldX'], actor_info['WorldY']])

def check_xy_overlap(actor1_details, actor2_details):
    """Checks if the XY projections of two actors' Axis-Aligned Bounding Boxes (AABBs) overlap.

    Args:
        actor1_details (dict): Details of the first actor (from get_actor_details).
        actor2_details (dict): Details of the second actor (from get_actor_details).

    Returns:
        bool: True if their XY projections overlap, False otherwise.
    """
    # Calculate bounding box corners for actor1
    actor1_x_min = actor1_details['x'] - actor1_details['size_x']/2
    actor1_x_max = actor1_details['x'] + actor1_details['size_x']/2
    actor1_y_min = actor1_details['y'] - actor1_details['size_y']/2
    actor1_y_max = actor1_details['y'] + actor1_details['size_y']/2
    
    # Calculate bounding box corners for actor2
    actor2_x_min = actor2_details['x'] - actor2_details['size_x']/2
    actor2_x_max = actor2_details['x'] + actor2_details['size_x']/2
    actor2_y_min = actor2_details['y'] - actor2_details['size_y']/2
    actor2_y_max = actor2_details['y'] + actor2_details['size_y']/2
    
    # Check for overlap
    overlap_x = (actor1_x_min <= actor2_x_max and actor1_x_max >= actor2_x_min)
    overlap_y = (actor1_y_min <= actor2_y_max and actor1_y_max >= actor2_y_min)

    return overlap_x and overlap_y

def find_nearest_actor(current_actor_details, candidate_actors_list, actor_df, distance_df, max_distance=NEIGHBOR_DISTANCE):
    """Finds the nearest actor within a specified maximum distance from the current actor.

    Args:
        current_actor_details (dict): Details of the current actor (from get_actor_details).
        candidate_actors_list (list): List of actor names to consider as candidates.
        actor_df (pd.DataFrame): DataFrame containing actor annotations.
        distance_df (pd.DataFrame): DataFrame containing pairwise actor distances.
        max_distance (float): Maximum distance to consider for finding neighbors.

    Returns:
        dict or None: Details of the nearest actor within max_distance, or None if no suitable actor found.
    """
    nearest_actor = None
    min_distance = float('inf')
    
    for candidate_actor_name in candidate_actors_list:
        if candidate_actor_name == current_actor_details['name']:
            continue  # Skip self
        
        distance = get_distance(current_actor_details['name'], candidate_actor_name, distance_df)
        if distance is not None and distance <= max_distance and distance < min_distance:
            min_distance = distance
            nearest_actor = get_actor_details(candidate_actor_name, actor_df)
    
    return nearest_actor

def calculate_turn_direction(current_facing_vector, target_vector):
    """Calculates the turn direction needed to face the target from the current facing direction.

    Args:
        current_facing_vector (np.array): Current facing direction vector.
        target_vector (np.array): Vector pointing to the target.

    Returns:
        str: Turn direction ('Turn Left', 'Turn Right', or 'Turn Back').
    """
    # Normalize vectors
    current_facing_norm = current_facing_vector / np.linalg.norm(current_facing_vector)
    target_norm = target_vector / np.linalg.norm(target_vector)
    
    # Calculate cross product to determine turn direction
    cross_product = np.cross(current_facing_norm, target_norm)
    
    # Calculate dot product to determine if we need to turn back
    dot_product = np.dot(current_facing_norm, target_norm)
    
    # Determine turn direction based on cross product and dot product
    if abs(dot_product) < 0.1:  # Nearly perpendicular
        if cross_product > 0:
            return 'Turn Left'
        else:
            return 'Turn Right'
    elif dot_product < -0.5:  # Need to turn back
        return 'Turn Back'
    elif cross_product > 0:
        return 'Turn Left'
    else:
        return 'Turn Right'

def process_routes(unique_actors_list, actor_df, distance_df):
    """Main function to process all possible routes and generate questions.

    Args:
        unique_actors_list (list): List of all unique actor names.
        actor_df (pd.DataFrame): DataFrame containing actor annotations.
        distance_df (pd.DataFrame): DataFrame containing pairwise actor distances.
    """
    generated_questions_list = []
    
    # Generate all possible combinations of begin_at, facing_at, and end_at actors
    for begin_at, facing_at, end_at in itertools.permutations(unique_actors_list, 3):
        # Skip if begin_at and end_at are the same
        if begin_at == end_at:
            continue
        
        # Get actor details
        begin_actor_d = get_actor_details(begin_at, actor_df)
        facing_actor_d = get_actor_details(facing_at, actor_df)
        end_actor_d = get_actor_details(end_at, actor_df)
        
        # Check if begin_at and end_at are far enough apart
        end_distance = get_distance(begin_at, end_at, distance_df)
        if end_distance is None or end_distance < MIN_END_DISTANCE:
            continue
    
        # Check if facing_at is close enough to begin_at to be a reasonable starting direction
        facing_distance = get_distance(begin_at, facing_at, distance_df)
        if facing_distance is None or facing_distance > NEIGHBOR_DISTANCE:
            continue
        
        # Generate route with intermediate stops
        route_sequences = generate_route_sequences(begin_actor_d, facing_actor_d, end_actor_d, unique_actors_list, actor_df, distance_df)
        
        # Process each route sequence
        for route_sequence in route_sequences:
            process_single_route(begin_actor_d, facing_actor_d, end_actor_d, route_sequence, generated_questions_list, actor_df)
    
    # Save results
    if generated_questions_list:
        output_df = pd.DataFrame(generated_questions_list)
        # Insert 'Possibility' ID column at the beginning
        output_df.insert(0, 'Possibility', range(1, 1 + len(output_df))) 
        output_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully generated {len(generated_questions_list)} route plan questions to {OUTPUT_FILE}")
    else:
        print("No valid route plan questions were generated after instruction building.")

def generate_route_sequences(begin_actor_d, facing_actor_d, end_actor_d, unique_actors_list, actor_df, distance_df):
    """Generates possible route sequences with intermediate stops.

    Args:
        begin_actor_d (dict): Details of the beginning actor.
        facing_actor_d (dict): Details of the facing actor.
        end_actor_d (dict): Details of the end actor.
        unique_actors_list (list): List of all unique actor names.
        actor_df (pd.DataFrame): DataFrame containing actor annotations.
        distance_df (pd.DataFrame): DataFrame containing pairwise actor distances.

    Returns:
        list: List of route sequences, where each sequence is a list of intermediate stops.
    """
    route_sequences = [[]]  # Start with no intermediate stops
    
    # Add sequences with 1 intermediate stop
    for intermediate_actor in unique_actors_list:
        if (intermediate_actor != begin_actor_d['name'] and 
            intermediate_actor != facing_actor_d['name'] and 
            intermediate_actor != end_actor_d['name']):
            
            # Check if intermediate actor is reachable from begin_at and can reach end_at
            begin_to_intermediate = get_distance(begin_actor_d['name'], intermediate_actor, distance_df)
            intermediate_to_end = get_distance(intermediate_actor, end_actor_d['name'], distance_df)
            
            if (begin_to_intermediate is not None and intermediate_to_end is not None and
                begin_to_intermediate <= NEIGHBOR_DISTANCE and intermediate_to_end <= NEIGHBOR_DISTANCE):
                
                route_sequences.append([intermediate_actor])
    
    return route_sequences

def process_single_route(begin_actor_d, facing_actor_d, end_actor_d, intermediate_stops_list, generated_questions_list, actor_df):
    """Processes a single route and generates questions.

    Args:
        begin_actor_d (dict): Details of the beginning actor.
        facing_actor_d (dict): Details of the facing actor.
        end_actor_d (dict): Details of the end actor.
        intermediate_stops_list (list): List of intermediate stop actor names.
        generated_questions_list (list): List to append generated questions to.
    """
    # Get details for intermediate stops
    intermediate_stops_d_list = []
    for stop_actor_name in intermediate_stops_list:
        stop_actor_d = get_actor_details(stop_actor_name, actor_df)
        intermediate_stops_d_list.append(stop_actor_d)
    
    # Build the complete route sequence
    route_sequence = [begin_actor_d] + intermediate_stops_d_list + [end_actor_d]
    
    # Generate instructions for this route
    current_instructions_for_route = []
    current_answers_for_route = []
    valid_current_route = True
    
    # Start at the beginning actor, facing the facing actor
    current_pos_actor_d = begin_actor_d
    vec_current_facing_dir = np.array([facing_actor_d['x'] - begin_actor_d['x'], 
                                      facing_actor_d['y'] - begin_actor_d['y']])
    
    # Process each segment of the route
    for i in range(len(route_sequence) - 1):
        target_actor_d = route_sequence[i + 1]
        
        # Calculate vector to target
        vec_to_target_actor = np.array([target_actor_d['x'] - current_pos_actor_d['x'], 
                                       target_actor_d['y'] - current_pos_actor_d['y']])
        
        # Calculate turn direction
        turn_cmd = calculate_turn_direction(vec_current_facing_dir, vec_to_target_actor)
        
        # Check for ambiguous turns (if turn direction is unclear)
        if turn_cmd == 'Turn Back':
                # print(f"Route discarded due to ambiguous turn from {current_pos_actor_d['display_name']} to {target_actor_d['display_name']}.")
            valid_current_route = False
            break # Ambiguous turn, route is invalid
            
            # Add turn instruction
            current_instructions_for_route.append(f"{len(current_instructions_for_route) + 1}. [please fill in]")
            current_answers_for_route.append(turn_cmd) # Record the correct turn
            # Add go forward instruction
            current_instructions_for_route.append(f"{len(current_instructions_for_route) + 1}. Go forward until the {target_actor_d['display_name']}.")
            
            # Update state for the next iteration / next segment of the path:
            # The new facing direction is the direction of the movement just made.
            vec_current_facing_dir = vec_to_target_actor 
            # The new current position is the target actor just reached.
            current_pos_actor_d = target_actor_d       

        # After processing all targets in the sequence for this route:
        if valid_current_route and current_answers_for_route:
            instruction_block_str = " ".join(current_instructions_for_route)
            # Construct the full question string
            question_str = (
                f"You are a robot beginning at the {begin_actor_d['display_name']} facing the {facing_actor_d['display_name']}. "
                f"You want to navigate to the {end_actor_d['display_name']}. "
                f"You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' or 'turn right.'): "
                f"{instruction_block_str} "
                f"You have reached the final destination."
            )

            # Generate multiple choice options
            options = []
            answer_letter = ''
            possible_turns = ['Turn Left', 'Turn Right', 'Turn Back']

            if len(current_answers_for_route) == 1:
                correct_answer_str = current_answers_for_route[0]
                # Options are always the three basic turns, shuffled
                mc_options = possible_turns[:]
                random.shuffle(mc_options)
                options = [f"{chr(65+i)}. {opt}" for i, opt in enumerate(mc_options)]
                try:
                    answer_letter = chr(65 + mc_options.index(correct_answer_str))
                except ValueError:
                    # print(f"Warning: Correct answer '{correct_answer_str}' not in mc_options. Skipping.")
                    return # Skip this question if correct answer isn't in options
            
            elif len(current_answers_for_route) >= 2:
                correct_answer_str = ', '.join(current_answers_for_route)
                num_turns = len(current_answers_for_route)
                all_mc_options_text = {correct_answer_str} # Use a set to store unique option strings

                # Generate 3 unique incorrect options
                while len(all_mc_options_text) < 4:
                    incorrect_sequence = []
                    for _ in range(num_turns):
                        incorrect_sequence.append(random.choice(possible_turns))
                    incorrect_sequence_str = ', '.join(incorrect_sequence)
                    all_mc_options_text.add(incorrect_sequence_str)
                
                mc_options_list = list(all_mc_options_text)
                random.shuffle(mc_options_list)
                options = [f"{chr(65+i)}. {opt}" for i, opt in enumerate(mc_options_list)]
                try:
                    answer_letter = chr(65 + mc_options_list.index(correct_answer_str))
                except ValueError:
                    # print(f"Warning: Correct answer sequence '{correct_answer_str}' not in generated mc_options_list. Skipping.")
                    return # Skip this question
            else:
                # Should not happen if current_answers_for_route is populated and valid_current_route is True
                return

            # Store the generated question and its details
            generated_questions_list.append({
                'BeginActor': begin_actor_d['name'],
                'FacingActor': facing_actor_d['name'],
                'EndActor': end_actor_d['name'],
                'IntermediateStops': ', '.join(s['name'] for s in intermediate_stops_d_list) if intermediate_stops_d_list else '',
                'Question': question_str,
                'Answer': answer_letter, # Updated to be the letter
                'Options': options # New field for multiple choice options
            })

if __name__ == '__main__':
    # Load actor and distance data
    actor_data_df, distance_data_df = load_data()
    if actor_data_df is not None and distance_data_df is not None:
        # Get a list of all unique actor names
        unique_actors_list = actor_data_df['ActorName'].unique().tolist()
        # Start the route processing logic
        process_routes(unique_actors_list, actor_data_df, distance_data_df)
    else:
        print("Failed to load data. Exiting script.")