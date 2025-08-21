import pandas as pd
import os
import random
from itertools import combinations, permutations # Import permutations

def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def main():
    # Read the CSV file using relative path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Assumes this script is one level down from project root
    input_csv_path = os.path.join(project_root, '0_data_cleanup_tool', 'output', 'ranked_unique_actor_anno.csv')
    df = pd.read_csv(input_csv_path)

    # Get unique actor names
    actor_names = df['ActorName'].unique()
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
            
        # --- Ambiguity Check ---
            is_ambiguous = False
            for i in range(len(actor_data) - 1):
                frame_diff = actor_data[i+1]['FirstFrame'] - actor_data[i]['FirstFrame']
                if frame_diff < 10:
                    is_ambiguous = True
                    break
            
            if is_ambiguous:
                # print(f"Skipping ambiguous combination {possibility_counter} due to close timestamps: {[ad['FirstFrame'] for ad in actor_data]}")
                continue # Discard this combination
            # --- End Ambiguity Check ---

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
    
    # Save all results to CSV
    if all_results:
        output_df = pd.DataFrame(all_results)
        output_df.to_csv(os.path.join(output_dir, 'appearance_order_all.csv'), index=False)
        print(f"Successfully processed {len(all_results)} possibility")

if __name__ == "__main__":
    main()