import pandas as pd
import os
import random
from itertools import combinations, permutations # Import permutations

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

def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_folder_name = get_data_folder_name()
    output_dir = os.path.join(project_root, "output_csv", data_folder_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def main():
    # Read the CSV file using relative path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Assumes this script is one level down from project root
    
    # 修改输入路径以读取新的CSV文件位置
    data_folder_name = get_data_folder_name()
    input_csv_path = os.path.join(project_root, 'output_csv', data_folder_name, 'ranked_unique_actor_anno.csv')
    
    if not os.path.exists(input_csv_path):
        print(f"Error: Input CSV file not found at {input_csv_path}")
        return
        
    df = pd.read_csv(input_csv_path)

    # Get unique actor names
    actor_names = df['ActorName'].unique()
    print(f"Found {len(actor_names)} unique actors")
    
    # Check if we have enough actors for combinations of 4
    if len(actor_names) < 4:
        print(f"Error: Need at least 4 actors, but only found {len(actor_names)}")
        return
    
    output_dir = ensure_output_directory()
    
    # Process all combinations of 4 different actors
    all_results = []
    possibility_counter = 1
    
    # Generate all combinations of 4 actors (order doesn't matter)
    for actor_combo in combinations(actor_names, 4):
        try:
            # Get the FirstFrame and DisplayName for each actor
            actor_data = []
            for actor_name in actor_combo:
                actor_row = df[df['ActorName'] == actor_name].iloc[0]
                actor_desc = actor_row.get('ActorDescription')
                display_name = actor_desc if pd.notna(actor_desc) and str(actor_desc).strip() else actor_row['ShortActorName']
                actor_data.append({
                    'ActorName': actor_name,
                    'DisplayName': display_name, # Use DisplayName
                    'FirstFrame': int(actor_row['FirstFrame'])
                })
            
            # Sort actors by FirstFrame to determine appearance order
            actor_data.sort(key=lambda x: x['FirstFrame'])
            
            # Create randomized order for question (different from correct order)
            question_order = actor_data.copy()
            while question_order == actor_data:  # Ensure the order is different
                random.shuffle(question_order)
            
            # Create question with randomized order using DisplayName
            question_names = [actor['DisplayName'] for actor in question_order]
            question = f"What will be the first-time appearance order of the following categories in the video: {', '.join(question_names)}?"
            
            # Determine the correct answer sequence using DisplayName
            correct_answer_sequence = [actor['DisplayName'] for actor in actor_data]
            correct_sequence_tuple = tuple(correct_answer_sequence) # Convert to tuple for comparison

            # Generate all permutations of the names presented in the question
            all_permutations_for_options = list(permutations(question_names))
            
            # Ensure the correct sequence is present in the generated permutations.
            if correct_sequence_tuple not in all_permutations_for_options:
                print(f"Warning: Correct sequence {correct_sequence_tuple} not found in permutations of question names {question_names}. Skipping combination.")
                continue # Skip this combination if the correct answer cannot be formed from the question names.

            # Remove the correct sequence from the list of all permutations to get incorrect options
            incorrect_options_raw = [p for p in all_permutations_for_options if p != correct_sequence_tuple]
            
            # Select 3 random incorrect options. If fewer than 3 are available, take all available.
            num_incorrect_to_select = min(3, len(incorrect_options_raw))
            selected_incorrect_options = random.sample(incorrect_options_raw, num_incorrect_to_select)
            
            # Combine the correct option with the selected incorrect options
            all_options_for_display = [correct_sequence_tuple] + selected_incorrect_options
            random.shuffle(all_options_for_display) # Shuffle the order of options A, B, C, D
            
            # Format options as A., B., C., D.
            formatted_options = [f"{chr(65+i)}. {', '.join(opt)}" for i, opt in enumerate(all_options_for_display)]
            
            # Determine the letter of the correct answer
            correct_answer_letter = chr(65 + all_options_for_display.index(correct_sequence_tuple))
            
            # Record results
            all_results.append({
                'Possibility': possibility_counter,
                'Actor1': actor_combo[0],
                'Actor2': actor_combo[1],
                'Actor3': actor_combo[2],
                'Actor4': actor_combo[3],
                'Actor1_FirstFrame': df[df['ActorName'] == actor_combo[0]]['FirstFrame'].iloc[0],
                'Actor2_FirstFrame': df[df['ActorName'] == actor_combo[1]]['FirstFrame'].iloc[0],
                'Actor3_FirstFrame': df[df['ActorName'] == actor_combo[2]]['FirstFrame'].iloc[0],
                'Actor4_FirstFrame': df[df['ActorName'] == actor_combo[3]]['FirstFrame'].iloc[0],
                'Question': question,
                'Answer': correct_answer_letter, # The letter (A, B, C, D)
                'Options': formatted_options # The list of formatted options
            })
            
            possibility_counter += 1
            
        except Exception as e:
            print(f"Error processing combination {possibility_counter}: {actor_combo}")
            print(f"Error message: {str(e)}")
            continue
    
    print(f"Total combinations processed: {len(all_results)}")
    
    # Save all results to CSV
    if all_results:
        output_df = pd.DataFrame(all_results)
        output_csv_path = os.path.join(output_dir, 'appearance_order_all.csv')
        output_df.to_csv(output_csv_path, index=False)
        print(f"Successfully processed {len(all_results)} possibility")
        print(f"Output saved to: {output_csv_path}")
    else:
        print("No valid combinations found.")

if __name__ == "__main__":
    main()