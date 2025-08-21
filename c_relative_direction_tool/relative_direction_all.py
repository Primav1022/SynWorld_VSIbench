import pandas as pd
import numpy as np
import os
import random

def determine_quadrant(df, standing_at_name, facing_at_name, locate_at_name):
    """
    Calculate relative direction between three points in 2D space.
    Args:
        df: DataFrame containing actor positions
        standing_at_name: Name of standing position actor
        facing_at_name: Name of facing direction actor
        locate_at_name: Name of object to locate     
    Returns:
        Dictionary containing direction information in three difficulty levels
        and coordinate system transformation details
    """
    # Get world coordinates for each point from the DataFrame
    standing_at = df[df['ActorName'] == standing_at_name][['WorldX', 'WorldY']].values[0]
    facing_at = df[df['ActorName'] == facing_at_name][['WorldX', 'WorldY']].values[0]
    locate_at = df[df['ActorName'] == locate_at_name][['WorldX', 'WorldY']].values[0]
    
    # Create a relative coordinate system where:
    # - Origin is at standing_at point
    # - Y-axis points from standing_at to facing_at (normalized)
    y_axis = facing_at - standing_at
    y_axis = y_axis / np.linalg.norm(y_axis)
    
    # X-axis is perpendicular to y_axis (rotate 90 degrees clockwise)
    # This ensures x-axis is to the right when facing along positive y-axis
    x_axis = np.array([y_axis[1], -y_axis[0]])
    
    # Convert locate_at point to relative coordinates
    locate_at_rel = locate_at - standing_at
    
    # Project locate_at onto the new coordinate axes
    x_coord = np.dot(locate_at_rel, x_axis)  # Right (+) or Left (-)
    y_coord = np.dot(locate_at_rel, y_axis)  # Front (+) or Back (-)
    
    # Calculate angle between locate_at and Y-axis for direction determination
    angle = np.degrees(np.arctan2(x_coord, y_coord))
    
    # Determine direction in three different granularities:
    # 1. Hard: Precise quadrant with front/back + left/right
    # 2. Medium: Uses 135° sectors for back, otherwise left/right
    # 3. Easy: Simple left/right determination
    
    # Hard version (quadrant-based)
    if x_coord >= 0 and y_coord >= 0:
        quadrant_hard = "front-right"
        quadrant_num = "quadrant I"
        quadrant_easy = "right"
    elif x_coord < 0 and y_coord >= 0:
        quadrant_hard = "front-left"
        quadrant_num = "quadrant II"
        quadrant_easy = "left"
    elif x_coord < 0 and y_coord < 0:
        quadrant_hard = "back-left"
        quadrant_num = "quadrant III"
        quadrant_easy = "left"
    else:  # x_coord >= 0 and y_coord < 0
        quadrant_hard = "back-right"
        quadrant_num = "quadrant IV"
        quadrant_easy = "right"
    
    # Medium version (135° sectors)
    if angle > 135 or angle < -135:  # Back sector
        quadrant_medium = "back"
    elif angle >= -135 and angle < 0:  # Left sector
        quadrant_medium = "left"
    else:  # Right sector (angle >= 0 and angle <= 135)
        quadrant_medium = "right"
    
    return {
        'quadrant': quadrant_hard,
        'quadrant_num': quadrant_num,
        'quadrant_medium': quadrant_medium,
        'quadrant_easy': quadrant_easy,
        'new_coords': (x_coord, y_coord),
        'standing_at': standing_at,
        'facing_at': facing_at,
        'locate_at': locate_at,
        'x_axis': x_axis,
        'y_axis': y_axis,
        'angle': angle  # Add angle to the return dictionary
    }

def ensure_output_directory():
    # Create main output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

# Helper function to get ambiguity threshold based on room size
def get_ambiguity_threshold(room_size_csv_path):
    """
    Reads the room size from the CSV and returns the appropriate ambiguity threshold.
    0.3m for room size > 40 sq m, 0.15m otherwise.
    """
    try:
        room_size_df = pd.read_csv(room_size_csv_path)
        if not room_size_df.empty and 'Answer' in room_size_df.columns:
            room_area_sq_m = room_size_df['Answer'].iloc[0]
            if room_area_sq_m > 40:
                return 0.3
            else:
                return 0.15
        else:
            print(f"Warning: 'Answer' column not found or CSV is empty in {room_size_csv_path}. Using default threshold 0.15m.")
            return 0.15
    except FileNotFoundError:
        print(f"Warning: Room size CSV not found at {room_size_csv_path}. Using default threshold 0.15m.")
        return 0.15
    except Exception as e:
        print(f"Error reading room size CSV: {e}. Using default threshold 0.15m.")
        return 0.15

# Helper function to load absolute distances
def load_absolute_distances(file_path):
    """Load absolute distances from CSV file"""
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        print(f"Error: Absolute distances file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading absolute distances: {e}")
        return None

# Helper function to create a distance dictionary
def create_distance_dict(abs_distances_df):
    """Create a dictionary of distances between object pairs"""
    distance_dict = {}
    if abs_distances_df is None:
        return distance_dict
    for _, row in abs_distances_df.iterrows():
        obj1 = row['Actor1']
        obj2 = row['Actor2']
        distance = row['Answer']
        distance_dict[(obj1, obj2)] = distance
        distance_dict[(obj2, obj1)] = distance # Store in both directions
    return distance_dict

def main():
    """
    Main processing function that:
    1. Loads actor position data
    2. Generates all valid combinations of standing/facing/locate points
    3. Calculates relative directions for each combination
    4. Outputs results to CSV with questions and answers at three difficulty levels
    """
    # Determine the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Assumes this script is in a subdirectory of the project root

    # Load actor positions from CSV using a relative path
    csv_path = os.path.join(project_root, '0_data_cleanup_tool', 'output', 'ranked_unique_actor_anno.csv')
    df = pd.read_csv(csv_path)
    actor_names = df['ActorName'].unique()
    output_dir = ensure_output_directory()

    # Paths for ambiguity check
    room_size_csv_path = os.path.join(project_root, "m_room_size_tool", "output", "room_size_all.csv")
    absolute_distances_path = os.path.join(project_root, "m_absolute_distance_tool", "output", "absolute_distances_all.csv")

    # Get ambiguity threshold
    ambiguity_threshold = get_ambiguity_threshold(room_size_csv_path)
    print(f"Using ambiguity threshold: {ambiguity_threshold}m")

    # Load absolute distances and create distance dictionary
    # print(f"Loading absolute distances from {absolute_distances_path}")
    abs_distances_df = load_absolute_distances(absolute_distances_path)
    if abs_distances_df is None:
        print("Cannot proceed without absolute distances. Exiting.")
        return
    distance_dict = create_distance_dict(abs_distances_df)
    if not distance_dict:
        print("Warning: Distance dictionary is empty. Ambiguity check might not work as expected.")

    # Process all valid combinations of three different actors
    all_results = []
    possibility_counter = 1
    
    # Define all possible options for each difficulty level
    POSSIBLE_HARD_OPTIONS = ["front-left", "front-right", "back-left", "back-right"]
    POSSIBLE_MEDIUM_OPTIONS = ["left", "right", "back"]
    POSSIBLE_EASY_OPTIONS = ["left", "right"]

    for standing_at in actor_names:
        for facing_at in actor_names:
            for locate_at in actor_names:
                if standing_at != facing_at and standing_at != locate_at and facing_at != locate_at:
                    # AMBIGUITY CHECK based on distances between the three chosen objects
                    dist_sf = distance_dict.get((standing_at, facing_at), float('inf'))
                    dist_sl = distance_dict.get((standing_at, locate_at), float('inf'))
                    dist_fl = distance_dict.get((facing_at, locate_at), float('inf'))

                    # Check if any distance is infinity (pair not found in distance_dict)
                    if dist_sf == float('inf') or dist_sl == float('inf') or dist_fl == float('inf'):
                        # print(f"Warning: Missing distance for combination: {standing_at}, {facing_at}, {locate_at}. Skipping.")
                        continue
                    
                    is_distance_ambiguous = False
                    if abs(dist_sf - dist_sl) < ambiguity_threshold or \
                       abs(dist_sf - dist_fl) < ambiguity_threshold or \
                       abs(dist_sl - dist_fl) < ambiguity_threshold:
                        is_distance_ambiguous = True
                    
                    if is_distance_ambiguous:
                        # print(f"Skipping ambiguous combination (distances): {standing_at}, {facing_at}, {locate_at} with distances SF:{dist_sf:.2f}m, SL:{dist_sl:.2f}m, FL:{dist_fl:.2f}m. Threshold: {ambiguity_threshold}m")
                        continue
                    # END AMBIGUITY CHECK (distances)

                    try:
                        result = determine_quadrant(df, standing_at, facing_at, locate_at)
                        
                        # Extract angle for angular ambiguity checks
                        angle = result['angle'] # Angle from determine_quadrant is in degrees, -180 to 180

                        # --- Angular Ambiguity Checks for each difficulty level ---
                        is_hard_ambiguous = False
                        is_medium_ambiguous = False
                        is_easy_ambiguous = False

                        # Hard difficulty: proximity to x or y axis (20 degrees threshold)
                        # Y-axis proximity (0 or 180 degrees)
                        if min(abs(angle), abs(abs(angle) - 180)) < 20:
                            is_hard_ambiguous = True
                        # X-axis proximity (90 or -90 degrees)
                        if min(abs(abs(angle) - 90), abs(abs(angle) + 90)) < 20:
                            is_hard_ambiguous = True
                        
                        # Medium difficulty: proximity to 135° sectors boundary lines (30 degrees threshold)
                        # Boundaries are at 0, 135, -135 degrees
                        if abs(angle) < 30 or abs(angle - 135) < 30 or abs(angle + 135) < 30:
                            is_medium_ambiguous = True

                        # Easy difficulty: proximity to y axis (40 degrees threshold)
                        # Y-axis proximity (0 or 180 degrees)
                        if min(abs(angle), abs(abs(angle) - 180)) < 40:
                            is_easy_ambiguous = True

                        # Get display names from the DataFrame
                        standing_row = df[df['ActorName'] == standing_at].iloc[0]
                        facing_row = df[df['ActorName'] == facing_at].iloc[0]
                        locate_row = df[df['ActorName'] == locate_at].iloc[0]

                        standing_desc = standing_row.get('ActorDescription')
                        display_standing = standing_desc if pd.notna(standing_desc) and str(standing_desc).strip() else standing_row['ShortActorName']

                        facing_desc = facing_row.get('ActorDescription')
                        display_facing = facing_desc if pd.notna(facing_desc) and str(facing_desc).strip() else facing_row['ShortActorName']

                        locate_desc = locate_row.get('ActorDescription')
                        display_locate = locate_desc if pd.notna(locate_desc) and str(locate_desc).strip() else locate_row['ShortActorName']
                        
                        # Initialize questions, answers, and options
                        hard_question = ""
                        hard_answer_letter = ""
                        hard_options_formatted = []
                        medium_question = ""
                        medium_answer_letter = ""
                        medium_options_formatted = []
                        easy_question = ""
                        easy_answer_letter = ""
                        easy_options_formatted = []

                        # Assign questions and answers if not ambiguous
                        if not is_hard_ambiguous:
                            hard_question = f"""If I am standing by the {display_standing} and facing the {display_facing}, is the {display_locate} to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis)."""
                            correct_hard_answer_str = result['quadrant']
                            shuffled_hard_options = random.sample(POSSIBLE_HARD_OPTIONS, len(POSSIBLE_HARD_OPTIONS))
                            hard_options_formatted = [f"{chr(65+i)}. {opt}" for i, opt in enumerate(shuffled_hard_options)]
                            try:
                                hard_answer_letter = chr(65 + shuffled_hard_options.index(correct_hard_answer_str))
                            except ValueError: # Should not happen if POSSSIBLE_HARD_OPTIONS is correct
                                print(f"Warning: Correct answer '{correct_hard_answer_str}' not in shuffled hard options for {standing_at}, {facing_at}, {locate_at}")
                                hard_question = "" # Invalidate question if error
                                hard_options_formatted = []


                        if not is_medium_ambiguous:
                            medium_question = f"""If I am standing by the {display_standing} and facing the {display_facing}, is the {display_locate} to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it."""
                            correct_medium_answer_str = result['quadrant_medium']
                            shuffled_medium_options = random.sample(POSSIBLE_MEDIUM_OPTIONS, len(POSSIBLE_MEDIUM_OPTIONS))
                            medium_options_formatted = [f"{chr(65+i)}. {opt}" for i, opt in enumerate(shuffled_medium_options)]
                            try:
                                medium_answer_letter = chr(65 + shuffled_medium_options.index(correct_medium_answer_str))
                            except ValueError:
                                print(f"Warning: Correct answer '{correct_medium_answer_str}' not in shuffled medium options for {standing_at}, {facing_at}, {locate_at}")
                                medium_question = "" # Invalidate question
                                medium_options_formatted = []


                        if not is_easy_ambiguous:
                            easy_question = f"""If I am standing by the {display_standing} and facing the {display_facing}, is the {display_locate} to the left or the right of the {display_standing}?"""
                            correct_easy_answer_str = result['quadrant_easy']
                            shuffled_easy_options = random.sample(POSSIBLE_EASY_OPTIONS, len(POSSIBLE_EASY_OPTIONS))
                            easy_options_formatted = [f"{chr(65+i)}. {opt}" for i, opt in enumerate(shuffled_easy_options)]
                            try:
                                easy_answer_letter = chr(65 + shuffled_easy_options.index(correct_easy_answer_str))
                            except ValueError:
                                print(f"Warning: Correct answer '{correct_easy_answer_str}' not in shuffled easy options for {standing_at}, {facing_at}, {locate_at}")
                                easy_question = "" # Invalidate question
                                easy_options_formatted = []


                        # If all questions are ambiguous (or became invalid), skip this combination entirely
                        if not hard_question and not medium_question and not easy_question:
                            # print(f"Skipping combination {standing_at}, {facing_at}, {locate_at} as all questions are ambiguous or invalid.")
                            continue
                        
                        # Combine all data into one row
                        all_results.append({
                            'Possibility': possibility_counter,
                            'standing_at': standing_at,
                            'standing_at_x': result['standing_at'][0],
                            'standing_at_y': result['standing_at'][1],
                            'facing_at': facing_at,
                            'facing_at_x': result['facing_at'][0],
                            'facing_at_y': result['facing_at'][1],
                            'locate_at': locate_at,
                            'locate_at_x': result['locate_at'][0],
                            'locate_at_y': result['locate_at'][1],
                            'QuadrantNumber': result['quadrant_num'],
                            'QuestionHard': hard_question,
                            'AnswerHard': hard_answer_letter,
                            'OptionsHard': hard_options_formatted,
                            'QuestionMedium': medium_question,
                            'AnswerMedium': medium_answer_letter,
                            'OptionsMedium': medium_options_formatted,
                            'QuestionEasy': easy_question,
                            'AnswerEasy': easy_answer_letter,
                            'OptionsEasy': easy_options_formatted
                        })
                        
                        possibility_counter += 1
                        
                    except Exception as e:
                        print(f"Error processing combination {possibility_counter}: {standing_at}, {facing_at}, {locate_at}")
                        print(f"Error message: {str(e)}")
                        continue
    
    # Save all results to CSV
    if all_results:
        output_df = pd.DataFrame(all_results)
        output_df.to_csv(os.path.join(output_dir, 'relative_direction_all.csv'), index=False)
        print(f"Successfully processed {len(all_results)} possibility")

if __name__ == "__main__":
    main()