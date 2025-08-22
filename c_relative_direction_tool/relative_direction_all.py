import pandas as pd
import numpy as np
import os
import random

def get_data_folder_name():
    """
    优先使用环境变量 DEFAULT_DATA_SUBDIR；否则回退扫描 output_csv。
    """
    env_subdir = os.environ.get('DEFAULT_DATA_SUBDIR')
    if env_subdir:
        return env_subdir
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_csv_root = os.path.join(project_root, "output_csv")
    if os.path.exists(output_csv_root):
        for item in os.listdir(output_csv_root):
            item_path = os.path.join(output_csv_root, item)
            if os.path.isdir(item_path):
                return item
    return "default"

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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_folder_name = get_data_folder_name()
    output_dir = os.path.join(project_root, "output_csv", data_folder_name)
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

def main():
    # Read the CSV file    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Assumes this script is one level down from project root
    
    # 修改输入路径以读取新的CSV文件位置
    data_folder_name = get_data_folder_name()
    input_csv_path = os.path.join(project_root, 'output_csv', data_folder_name, 'ranked_unique_actor_anno.csv')
    
    if not os.path.exists(input_csv_path):
        print(f"Error: Input CSV file not found at {input_csv_path}")
        return
        
    df = pd.read_csv(input_csv_path)

    actor_names = df['ActorName'].unique()
    output_dir = ensure_output_directory()
    
    # Get room size for ambiguity threshold
    room_size_csv_path = os.path.join(project_root, "output_csv", data_folder_name, "room_size_all.csv")
    ambiguity_threshold = get_ambiguity_threshold(room_size_csv_path)
    
    # Process all valid combinations of three different actors
    all_results = []
    possibility_counter = 1
    
    # Define possible options for each difficulty level
    POSSIBLE_HARD_OPTIONS = ["front-left", "front-right", "back-left", "back-right"]
    POSSIBLE_MEDIUM_OPTIONS = ["left", "right", "back"]
    POSSIBLE_EASY_OPTIONS = ["left", "right"]
    
    # Use combinations to ensure order-independent pairs
    for standing_at in actor_names:
        for facing_at in actor_names:
            if facing_at == standing_at:
                continue
            for locate_at in actor_names:
                if locate_at == standing_at or locate_at == facing_at:
                    continue
                    
                try:
                    # Calculate relative direction
                    result = determine_quadrant(df, standing_at, facing_at, locate_at)
                    
                    # Check for ambiguity based on distance
                    distance = np.linalg.norm(result['new_coords'])
                    
                    # Determine ambiguity for each difficulty level
                    is_hard_ambiguous = distance < ambiguity_threshold
                    is_medium_ambiguous = distance < ambiguity_threshold
                    is_easy_ambiguous = distance < ambiguity_threshold
                    
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
        output_csv_path = os.path.join(output_dir, 'relative_direction_all.csv')
        output_df.to_csv(output_csv_path, index=False)
        print(f"Successfully processed {len(all_results)} possibility")
        print(f"Output saved to: {output_csv_path}")

if __name__ == "__main__":
    main()