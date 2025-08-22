import pandas as pd
import os

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

def ensure_output_directory():
    """Create output directory if it doesn't exist and return its path."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_folder_name = get_data_folder_name()
    output_dir = os.path.join(project_root, "output_csv", data_folder_name)
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
    
    # 修改输入路径以读取新的CSV文件位置
    data_folder_name = get_data_folder_name()
    input_csv_path = os.path.join(project_root, 'output_csv', data_folder_name, 'ranked_unique_actor_anno.csv')
    
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
        print(f"Available columns: {list(df.columns)}")
        return

    # Count occurrences of each ShortActorName
    actor_counts = df['ShortActorName'].value_counts()
    
    # 修改逻辑：生成所有对象的计数，不仅仅是重复的对象
    output_dir = ensure_output_directory()
    all_results = []
    possibility_counter = 1
    
    print(f"Found {len(actor_counts)} unique ShortActorNames.")

    for short_name, count in actor_counts.items():
        # 为每个对象生成计数问题
        if count == 1:
            question = f"How many {short_name} are in this room?"
            answer = count
        else:
            question = f"How many {short_name} are in this room?"
            answer = count
        
        all_results.append({
            'Possibility': possibility_counter,
            'ShortActorName': short_name,
            'Count': count,
            'Question': question,
            'Answer': answer
        })
        possibility_counter += 1
        
    # Save all results to CSV
    if all_results:
        output_df = pd.DataFrame(all_results)
        output_csv_path = os.path.join(output_dir, 'object_count_all.csv')  # 修正文件名
        try:
            output_df.to_csv(output_csv_path, index=False)
            print(f"Successfully processed {len(all_results)} object types")
            print(f"Saved to: {output_csv_path}")

        except Exception as e:
            print(f"Error writing output CSV to {output_csv_path}: {e}")
    else:
        print("No results to save.")

if __name__ == "__main__":
    main()