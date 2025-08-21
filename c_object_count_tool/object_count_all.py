import pandas as pd
import os

def ensure_output_directory():
    """Create output directory if it doesn't exist and return its path."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    return output_dir

def main():
    """
    Main function to count objects by ShortActorName, generate QA pairs,
    and save them to a CSV file.
    """
    # Determine the project root directory and script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Assumes this script is one level down from project root
    
    # Construct path to the input CSV file
    input_csv_path = os.path.join(project_root, '0_data_cleanup_tool', 'output', 'ranked_unique_actor_anno.csv')
    
    # Ensure the input file exists
    if not os.path.exists(input_csv_path):
        print(f"Error: Input CSV file not found at {input_csv_path}")
        return

    # Read the input CSV file
    try:
        df = pd.read_csv(input_csv_path)
    except Exception as e:
        print(f"Error reading CSV file {input_csv_path}: {e}")
        return

    # Ensure 'ShortActorName' column exists
    if 'ShortActorName' not in df.columns:
        print(f"Error: 'ShortActorName' column not found in {input_csv_path}")
        return

    # Count occurrences of each ShortActorName
    actor_counts = df['ShortActorName'].value_counts()
    
    # Filter for actors that appear more than once
    multiple_actors = actor_counts[actor_counts > 1]
    
    output_dir = ensure_output_directory()
    all_results = []
    possibility_counter = 1
    
    if multiple_actors.empty:
        print("No ShortActorName appears more than once. No output file will be generated.")
        return

    print(f"Found {len(multiple_actors)} ShortActorNames appearing more than once.")

    for short_name, count in multiple_actors.items():
        question = f"How many {short_name} are in this room?"
        answer = count  # Numerical count
        
        all_results.append({
            'Possibility': possibility_counter,
            'ShortActorName': short_name,
            'Question': question,
            'Answer': answer
        })
        possibility_counter += 1
        
    # Save all results to CSV
    if all_results:
        output_df = pd.DataFrame(all_results)
        output_csv_path = os.path.join(output_dir, 'object_counts_all.csv')
        try:
            output_df.to_csv(output_csv_path, index=False)
            print(f"Successfully processed {len(all_results)} possibility")

        except Exception as e:
            print(f"Error writing output CSV to {output_csv_path}: {e}")
    else:
        print("No results to save.")

if __name__ == "__main__":
    main()