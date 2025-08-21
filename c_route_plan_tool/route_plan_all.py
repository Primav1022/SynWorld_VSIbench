import pandas as pd
import itertools
import math
import os
import numpy as np # Added for vector math
import random # Added for shuffling options

# Configuration Variables
MIN_END_DISTANCE = 1  # Minimum distance between begin_at and end_at in meters
NEIGHBOR_DISTANCE = 2  # Default maximum distance to search for a valid facing_at actor in meters

# Define input and output file paths
# Assuming the script is in c_route_plan_tool and other files are in their respective locations as per the structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTOR_ANNO_FILE = os.path.join(BASE_DIR, '0_data_cleanup_tool', 'output', 'ranked_unique_actor_anno.csv')
ABSOLUTE_DISTANCE_FILE = os.path.join(BASE_DIR, 'm_absolute_distance_tool', 'output', 'absolute_distances_all.csv')
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'route_plan_all.csv')

# Ensure output directory exists
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output'), exist_ok=True)

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
    # Calculate XY bounding box for actor1
    min_x1, max_x1 = actor1_details['x'] - actor1_details['size_x']/2, actor1_details['x'] + actor1_details['size_x']/2
    min_y1, max_y1 = actor1_details['y'] - actor1_details['size_y']/2, actor1_details['y'] + actor1_details['size_y']/2

    # Calculate XY bounding box for actor2
    min_x2, max_x2 = actor2_details['x'] - actor2_details['size_x']/2, actor2_details['x'] + actor2_details['size_x']/2
    min_y2, max_y2 = actor2_details['y'] - actor2_details['size_y']/2, actor2_details['y'] + actor2_details['size_y']/2

    # Check for overlap on X and Y axes
    overlap_x = (min_x1 < max_x2) and (max_x1 > min_x2)
    overlap_y = (min_y1 < max_y2) and (max_y1 > min_y2)

    return overlap_x and overlap_y

def check_aabb_overlap(actor1, actor2):
    """Checks if the 3D Axis-Aligned Bounding Boxes (AABB) of two actors overlap.

    Args:
        actor1 (dict): Details of the first actor (from get_actor_details).
        actor2 (dict): Details of the second actor (from get_actor_details).

    Returns:
        bool: True if their AABBs overlap in 3D space, False otherwise.
    """
    # Calculate 3D bounding box for actor1
    min_x1, max_x1 = actor1['x'] - actor1['size_x']/2, actor1['x'] + actor1['size_x']/2
    min_y1, max_y1 = actor1['y'] - actor1['size_y']/2, actor1['y'] + actor1['size_y']/2
    min_z1, max_z1 = actor1['z'] - actor1['size_z']/2, actor1['z'] + actor1['size_z']/2

    # Calculate 3D bounding box for actor2
    min_x2, max_x2 = actor2['x'] - actor2['size_x']/2, actor2['x'] + actor2['size_x']/2
    min_y2, max_y2 = actor2['y'] - actor2['size_y']/2, actor2['y'] + actor2['size_y']/2
    min_z2, max_z2 = actor2['z'] - actor2['size_z']/2, actor2['z'] + actor2['size_z']/2

    # Check for overlap on each axis (X, Y, Z)
    overlap_x = (min_x1 < max_x2) and (max_x1 > min_x2)
    overlap_y = (min_y1 < max_y2) and (max_y1 > min_y2)
    overlap_z = (min_z1 < max_z2) and (max_z1 > min_z2)

    return overlap_x and overlap_y and overlap_z

def get_vector(actor_from_details, actor_to_details):
    """Calculates the 2D vector (on the XY plane) from a starting actor to a target actor.

    Args:
        actor_from_details (dict): Details of the starting actor.
        actor_to_details (dict): Details of the target actor.

    Returns:
        np.array: A 2D numpy array representing the vector [dx, dy].
    """
    return np.array([actor_to_details['x'] - actor_from_details['x'], 
                     actor_to_details['y'] - actor_from_details['y']])

def calculate_angle_and_turn(vec_facing, vec_to_target):
    """Calculates the signed angle from the current facing vector to the target vector
    and determines the corresponding turn command ('Turn Left', 'Turn Right', 'Turn Back', or 'discard_ambiguous_turn').

    Args:
        vec_facing (np.array): The current 2D facing direction vector.
        vec_to_target (np.array): The 2D vector from the current position to the target.

    Returns:
        tuple: (float, str) containing the angle in degrees and the turn command.
    """
    # Normalize vectors to ensure angle calculation is based purely on direction
    norm_vec_facing = vec_facing / np.linalg.norm(vec_facing)
    norm_vec_to_target = vec_to_target / np.linalg.norm(vec_to_target)

    # Calculate the signed angle using atan2, result is in radians (-pi to pi)
    angle_rad = np.arctan2(norm_vec_to_target[1], norm_vec_to_target[0]) - np.arctan2(norm_vec_facing[1], norm_vec_facing[0])

    # Normalize angle to be strictly between -pi and pi
    if angle_rad > np.pi:
        angle_rad -= 2 * np.pi
    elif angle_rad < -np.pi:
        angle_rad += 2 * np.pi

    angle_deg = np.degrees(angle_rad) # Convert angle to degrees

    # Determine turn command based on angle thresholds:
    # ±20°: Ambiguous turn, discard the route.
    # Left (CCW, positive angle, +20° to +135°): Turn left.
    # Right (CW, negative angle, -135° to -20°): Turn right.
    # Outside ±135° (i.e., > +135° or < -135°): Turn back.
    if -30 <= angle_deg <= 30:
        return angle_deg, "discard_ambiguous_turn"
    elif 30 < angle_deg <= 135: # Positive angle (CCW) is turn left
        return angle_deg, "Turn Left"
    elif -135 <= angle_deg < -30: # Negative angle (CW) is turn right
        return angle_deg, "Turn Right"
    else: # angle_deg > 135 or angle_deg < -135
        return angle_deg, "Turn Back"

def process_routes(all_actors, actor_df, distance_df):
    """Main function to process actors and generate route plan questions.
    This involves several steps:
    1. Select Begin and End Actors based on minimum distance.
    2. Choose a Facing Actor for the Begin Actor.
    3. Find Intermediate Go-To Candidates between Begin and End.
    4. Generate All Go-To Combinations (routes with 0-4 intermediate stops).
    5. Validate Paths for Obstruction (ensure no actor blocks line of sight between waypoints).
    6. Build Instruction Blocks (generate turn and go-forward instructions).
    7. Finalize Output (save valid questions to CSV).
    """
    print(f"Found {len(all_actors)} unique actors.")

    # Step 1: Select Begin and End Actors
    # Filters pairs of actors that are at least MIN_END_DISTANCE apart.
    print("\nStep 1: Selecting Begin and End Actors...")
    potential_begin_end_pairs = []
    for begin_actor_name, end_actor_name in itertools.combinations(all_actors, 2):
        dist = get_distance(begin_actor_name, end_actor_name, distance_df)
        if dist is not None and dist >= MIN_END_DISTANCE: # Check if dist is not None
            potential_begin_end_pairs.append((begin_actor_name, end_actor_name, dist))
    
    print(f"Found {len(potential_begin_end_pairs)} potential begin-end pairs with distance >= {MIN_END_DISTANCE}m.")
    if not potential_begin_end_pairs:
        print("No potential begin-end pairs found. Exiting.")
        return

    # Step 2: Choose Facing Actor
    # For each begin actor, find a nearby 'facing_at' actor.
    # If no actor is found within NEIGHBOR_DISTANCE, the search radius is doubled.
    print("\nStep 2: Choosing Facing Actors...")
    begin_end_facing_triplets_raw = []
    for begin_actor_name, end_actor_name, dist_to_end in potential_begin_end_pairs:
        current_neighbor_distance = NEIGHBOR_DISTANCE
        found_facing_actors_for_current_begin = []
        
        # Initial search for facing actors
        for other_actor_name in all_actors:
            if other_actor_name == begin_actor_name or other_actor_name == end_actor_name:
                continue # Cannot face self or the end actor initially
            dist_to_other = get_distance(begin_actor_name, other_actor_name, distance_df)
            if dist_to_other is not None and dist_to_other <= current_neighbor_distance: # Check if dist_to_other is not None
                found_facing_actors_for_current_begin.append(other_actor_name)
        
        # If no facing actor found, double the search distance and try again
        if not found_facing_actors_for_current_begin:
            current_neighbor_distance *= 2
            print(f"  LOG: No facing actor found for {begin_actor_name} within {NEIGHBOR_DISTANCE}m. Expanding search to {current_neighbor_distance}m.") # Log event
            for other_actor_name in all_actors:
                if other_actor_name == begin_actor_name or other_actor_name == end_actor_name:
                    continue
                dist_to_other = get_distance(begin_actor_name, other_actor_name, distance_df)
                if dist_to_other is not None and dist_to_other <= current_neighbor_distance: # Check if dist_to_other is not None
                    found_facing_actors_for_current_begin.append(other_actor_name)
            
        # Store all found (begin, facing, end) triplets
        for facing_actor_name in found_facing_actors_for_current_begin:
            begin_end_facing_triplets_raw.append({
                'begin_actor_name': begin_actor_name, 
                'facing_actor_name': facing_actor_name, 
                'end_actor_name': end_actor_name, 
                'dist_begin_to_end': dist_to_end
            })

    print(f"Found {len(begin_end_facing_triplets_raw)} potential (begin, facing, end) name triplets.")
    if not begin_end_facing_triplets_raw:
        print("No potential (begin, facing, end) triplets found. Exiting.")
        return

    # Convert actor names in triplets to full actor details for easier access
    begin_end_facing_triplets = []
    for trip_names in begin_end_facing_triplets_raw:
        try:
            begin_details = get_actor_details(trip_names['begin_actor_name'], actor_df)
            facing_details = get_actor_details(trip_names['facing_actor_name'], actor_df)
            end_details = get_actor_details(trip_names['end_actor_name'], actor_df)
            begin_end_facing_triplets.append({
                'begin_actor': begin_details,
                'facing_actor': facing_details,
                'end_actor': end_details,
                'dist_begin_to_end': trip_names['dist_begin_to_end']
            })
        except IndexError:
            # This might happen if an actor name from distance_df is not in actor_df
            print(f"Warning: Could not find details for one of the actors in triplet: {trip_names}. Skipping this triplet.")
            continue
    
    print(f"Successfully fetched details for {len(begin_end_facing_triplets)} triplets.")
    if not begin_end_facing_triplets:
        print("No triplets with full details found. Exiting.")
        return

    # Step 3: Find Intermediate Go-To Candidates
    # Identifies potential intermediate stops between the begin and end actors.
    # Candidates must be in front of the begin actor (positive projection on begin-to-end vector)
    # and closer to the begin actor than the end actor.
    # Overlapping candidates on XY plane are filtered, keeping the one with largest volume.
    print("\nStep 3: Finding Intermediate Go-To Candidates...")
    intermediate_candidates_per_triplet = []
    for triplet_info in begin_end_facing_triplets:
        begin_actor_details = triplet_info['begin_actor']
        end_actor_details = triplet_info['end_actor']
        dist_begin_to_end_val = triplet_info['dist_begin_to_end']

        # Define the local coordinate system based on begin and end actors
        begin_coords = np.array([begin_actor_details['x'], begin_actor_details['y']])
        end_coords = np.array([end_actor_details['x'], end_actor_details['y']])

        vec_begin_to_end = end_coords - begin_coords
        if np.linalg.norm(vec_begin_to_end) < 1e-6: # Avoid issues with zero-length vector
            # print(f"Warning: Begin and End actors {begin_actor_details['name']}, {end_actor_details['name']} are at the same XY location. Skipping triplet.")
            continue
        
        unit_y_axis = vec_begin_to_end / np.linalg.norm(vec_begin_to_end) # Local Y-axis

        # Find potential intermediate candidates
        potential_intermediate_candidates_with_proj = []
        for candidate_actor_name_loop in all_actors:
            # Candidate cannot be the begin, facing, or end actor of the current triplet
            if candidate_actor_name_loop in [begin_actor_details['name'], triplet_info['facing_actor']['name'], end_actor_details['name']]:
                continue
            
            candidate_detail = get_actor_details(candidate_actor_name_loop, actor_df)
            candidate_coords_world = np.array([candidate_detail['x'], candidate_detail['y']])
            vec_begin_to_candidate_world = candidate_coords_world - begin_coords

            # Project candidate onto the local Y-axis (direction from begin to end)
            y_new = np.dot(vec_begin_to_candidate_world, unit_y_axis)

            # Candidate must be 'in front' of begin_actor (positive y_new)
            # and closer to begin_actor than end_actor is.
            if y_new > 1e-6: # Small epsilon to avoid floating point issues with 'directly on'
                dist_begin_to_candidate_val = get_distance(begin_actor_details['name'], candidate_actor_name_loop, distance_df)
                if dist_begin_to_candidate_val is not None and dist_begin_to_candidate_val < dist_begin_to_end_val: # Check if dist_begin_to_candidate_val is not None
                    potential_intermediate_candidates_with_proj.append({'details': candidate_detail, 'y_proj': y_new})
        
        # Filter out smaller overlapping actors on the XY plane
        filtered_intermediate_candidates = [] # Stores actor detail dicts
        # Iterate through candidates, usually sorted by some criteria (e.g., y_proj or volume)
        # For simplicity here, we iterate and build the filtered list dynamically.
        for cand_data in potential_intermediate_candidates_with_proj: # cand_data is {'details': ..., 'y_proj': ...}
            current_cand_details = cand_data['details']
            is_current_dominated = False # Flag if current_cand is overlapped by a larger existing one
            
            # Temporary list to hold candidates that are not dominated by current_cand
            next_filtered_list = [] 
            
            for existing_cand_details in filtered_intermediate_candidates:
                if check_xy_overlap(current_cand_details, existing_cand_details):
                    if current_cand_details['volume'] > existing_cand_details['volume']:
                        # Current is larger and overlaps existing; existing is removed (by not adding to next_filtered_list)
                        continue # Don't add existing_cand_details to next_filtered_list
                    else:
                        # Existing is larger or equal and overlaps current; current is dominated
                        is_current_dominated = True
                        break # Current candidate will not be added
                next_filtered_list.append(existing_cand_details) # Keep non-overlapping or larger existing ones
            
            if not is_current_dominated:
                next_filtered_list.append(current_cand_details) # Add current if it's not dominated
                filtered_intermediate_candidates = next_filtered_list # Update main filtered list
            # If current_cand was dominated, filtered_intermediate_candidates remains unchanged from previous iteration for this cand_data

        # Sort the final list of unique, largest candidates by their projection on the y-axis (y_proj)
        # This requires re-associating y_proj with the details in filtered_intermediate_candidates.
        candidates_to_sort_final = []
        for cand_detail_final in filtered_intermediate_candidates:
            # Find original y_proj for this candidate_detail from the initial list
            original_y_proj = 0 # Default or find it
            for p_cand in potential_intermediate_candidates_with_proj:
                if p_cand['details']['name'] == cand_detail_final['name']:
                    original_y_proj = p_cand['y_proj']
                    break
            candidates_to_sort_final.append({'details': cand_detail_final, 'y_proj': original_y_proj})

        sorted_intermediate_candidates = sorted(candidates_to_sort_final, key=lambda c: c['y_proj'])
        
        intermediate_candidates_per_triplet.append({
            'begin_actor': begin_actor_details,
            'end_actor': end_actor_details,
            'facing_actor': triplet_info['facing_actor'],
            'candidates': [c['details'] for c in sorted_intermediate_candidates] # Store only details, now sorted
        })

    print(f"Processed {len(intermediate_candidates_per_triplet)} triplets for intermediate candidates.")

    # Step 4: Generate All Go-To Combinations
    # Creates all possible routes with 0 to 4 intermediate stops from the candidates found in Step 3.
    print("\nStep 4: Generating All Go-To Combinations...")
    potential_routes = []
    for item in intermediate_candidates_per_triplet:
        begin_actor = item['begin_actor']
        end_actor = item['end_actor']
        facing_actor = item['facing_actor']
        candidates_details_list = item['candidates'] # List of actor detail dicts, sorted by y_proj

        # Add route with 0 intermediate stops
        potential_routes.append({
            'begin_actor': begin_actor,
            'end_actor': end_actor,
            'facing_actor': facing_actor,
            'intermediate_stops': [] 
        })

        # Add routes with 1 to max 4 intermediate stops
        # The number of stops 'i' goes from 1 up to min(number_of_available_candidates, 4)
        for i in range(1, min(len(candidates_details_list), 4) + 1): 
            for combo_details in itertools.combinations(candidates_details_list, i):
                # combo_details is a tuple of actor detail dicts
                potential_routes.append({
                    'begin_actor': begin_actor,
                    'end_actor': end_actor,
                    'facing_actor': facing_actor,
                    'intermediate_stops': list(combo_details) 
                })

    print(f"Generated {len(potential_routes)} potential routes.")

    # Step 5: Validate Path for Obstruction
    # Checks each segment of a potential route for obstruction by other actors not part of the route.
    # An obstruction occurs if the AABB of a segment's start or end actor overlaps with a non-path actor's AABB.
    # This is a simplified check; true line-of-sight or pathfinding would be more complex.
    print("\nStep 5: Validating Paths for Obstruction...")
    valid_routes_after_obstruction_check = []
    all_actor_details_map = {name: get_actor_details(name, actor_df) for name in all_actors}

    for route_info in potential_routes:
        is_obstructed = False
        # Create a set of names of actors involved in the current path for quick lookup
        path_actors_names_set = {route_info['begin_actor']['name']} \
                               | {s['name'] for s in route_info['intermediate_stops']} \
                               | {route_info['end_actor']['name']}

        # Define the full sequence of actors (waypoints) in the current path
        current_path_for_route_segments = [route_info['begin_actor']] + route_info['intermediate_stops'] + [route_info['end_actor']]
        
        # Check each segment of the path for obstruction
        for i in range(len(current_path_for_route_segments) - 1):
            seg_start_actor_details = current_path_for_route_segments[i]
            seg_end_actor_details = current_path_for_route_segments[i+1]
            if is_obstructed: break # If already found obstruction, no need to check further segments

            # Check against all other actors in the scene
            for other_actor_name_check in all_actors:
                if other_actor_name_check in path_actors_names_set: 
                    continue # Don't check for obstruction against actors that are part of the path itself
                
                other_actor_details_check = all_actor_details_map[other_actor_name_check]

                # Simplified obstruction: if start or end of segment overlaps with another actor's AABB.
                # This doesn't check the path *between* segment start/end, only the waypoints themselves.
                if check_aabb_overlap(seg_start_actor_details, other_actor_details_check) or \
                   check_aabb_overlap(seg_end_actor_details, other_actor_details_check):
                    # print(f"Obstruction: Segment {seg_start_actor_details['name']} to {seg_end_actor_details['name']} is obstructed by {other_actor_details_check['name']}")
                    is_obstructed = True
                    break # Obstruction found for this segment
            if is_obstructed: break # Move to next route if current segment is obstructed
        
        if not is_obstructed:
            valid_routes_after_obstruction_check.append(route_info)

    print(f"Found {len(valid_routes_after_obstruction_check)} routes after obstruction validation.")
    if not valid_routes_after_obstruction_check:
        print("No routes passed obstruction check. Exiting.")
        return

    # Step 6: Build the Instruction Block & Step 7: Finalize Output
    # For each valid route, generate a sequence of turn and go-forward instructions.
    # Calculates initial turn based on begin and facing actors.
    # Calculates subsequent turns based on the vector of the last movement and the vector to the next target.
    # Formats the question string and saves all valid questions to a CSV file.
    print("\nStep 6 & 7: Building Instruction Blocks and Finalizing Output...")
    generated_questions_list = []

    for route_data in valid_routes_after_obstruction_check:
        current_instructions_for_route = []
        current_answers_for_route = [] # Stores the correct turn commands for the 'Answer' column
        valid_current_route = True # Flag to track if the current route remains valid during instruction generation

        begin_actor_d = route_data['begin_actor']
        facing_actor_d = route_data['facing_actor']
        end_actor_d = route_data['end_actor']
        intermediate_stops_d_list = route_data['intermediate_stops']
        
        # Initial state for navigation
        current_pos_actor_d = begin_actor_d # Robot starts at the begin_actor
        # Initial facing direction is from the robot's current position (begin_actor) towards the facing_actor
        vec_current_facing_dir = get_vector(current_pos_actor_d, facing_actor_d)
        if np.linalg.norm(vec_current_facing_dir) < 1e-6: # Facing self or same point (e.g. begin_actor == facing_actor)
            # print(f"Warning: Initial facing vector for route starting at {begin_actor_d['name']} towards {facing_actor_d['name']} is zero. Skipping route.")
            continue # This route is problematic

        # The full sequence of actors the robot needs to GO TO.
        go_to_sequence_d = intermediate_stops_d_list + [end_actor_d]

        # Iterate through each target in the go-to sequence to generate instructions
        for idx, target_actor_d in enumerate(go_to_sequence_d):
            # Check if current position is already the target (should not happen with distinct stops)
            if current_pos_actor_d['name'] == target_actor_d['name']:
                # This case might occur if, e.g., an intermediate stop is identical to the end_actor and listed consecutively,
                # or if begin_actor is the first target and also the facing_actor.
                if idx == 0 and facing_actor_d['name'] == target_actor_d['name']:
                    # Special case: If first target is the facing actor, it means "go forward to the actor you are already facing".
                    current_instructions_for_route.append(f"{len(current_instructions_for_route) + 1}. Go forward until the {target_actor_d['display_name']}")
                    # No turn answer is recorded for this direct "go forward".
                    current_pos_actor_d = target_actor_d # Update current position
                    # The facing direction for the *next* turn will be from the *previous* stop to this *current* stop.
                    # This is handled before the next turn calculation.
                    continue # Move to the next target in go_to_sequence_d
                else:
                    # print(f"Warning: current_pos_actor {current_pos_actor_d['display_name']} is same as target {target_actor_d['display_name']} in an unexpected way. Invalidating route.")
                    valid_current_route = False; break # Mark route as invalid and stop processing this route
            
            # Vector from current robot position to the current target actor
            vec_to_target_actor = get_vector(current_pos_actor_d, target_actor_d)
            if np.linalg.norm(vec_to_target_actor) < 1e-6: # Target is effectively at the current location
                # print(f"Warning: Target actor {target_actor_d['display_name']} is at the same location as current position {current_pos_actor_d['display_name']}. Invalidating route.")
                valid_current_route = False; break # Invalid route

            # Calculate the turn required to face the target_actor_d
            # vec_current_facing_dir is from previous_pos to current_pos (or initial facing for the first step)
            angle_deg, turn_cmd = calculate_angle_and_turn(vec_current_facing_dir, vec_to_target_actor)

            if turn_cmd == "discard_ambiguous_turn":
                # print(f"Route discarded due to ambiguous turn from {current_pos_actor_d['display_name']} to {target_actor_d['display_name']}.")
                valid_current_route = False; break # Ambiguous turn, route is invalid
            
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
                    continue # Skip this question if correct answer isn't in options
            
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
                    continue # Skip this question
            else:
                # Should not happen if current_answers_for_route is populated and valid_current_route is True
                continue

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

    # After processing all valid routes:
    if generated_questions_list:
        output_df = pd.DataFrame(generated_questions_list)
        # Insert 'Possibility' ID column at the beginning
        output_df.insert(0, 'Possibility', range(1, 1 + len(output_df))) 
        output_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully generated {len(generated_questions_list)} route plan questions to {OUTPUT_FILE}")
    else:
        print("No valid route plan questions were generated after instruction building.")

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