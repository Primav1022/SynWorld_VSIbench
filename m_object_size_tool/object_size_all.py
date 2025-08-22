import pandas as pd
import numpy as np
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
    """Create output directory if it doesn't exist"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_folder_name = get_data_folder_name()
    output_dir = os.path.join(project_root, "output_csv", data_folder_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def find_longest_dimension(actor_row):
    """
    Find the longest dimension (X, Y, or Z) of an actor
    Returns the dimension name, value in meters, and value in centimeters
    """
    # Get the dimensions
    dimensions = {
        'length (X)': actor_row['WorldSizeX'],
        'width (Y)': actor_row['WorldSizeY'], 
        'height (Z)': actor_row['WorldSizeZ']
    }
    
    # Find the longest dimension
    longest_dim_name = max(dimensions, key=dimensions.get)
    longest_dim_value_meters = dimensions[longest_dim_name]
    
    # Convert to centimeters (multiply by 100)
    longest_dim_value_cm = longest_dim_value_meters * 100
    
    return longest_dim_name, longest_dim_value_meters, longest_dim_value_cm

def main():
    # Determine the project root directory and script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Assumes this script is one level down from project root
    
    # 修改输入路径以读取新的CSV文件位置
    data_folder_name = get_data_folder_name()
    input_csv_path = os.path.join(project_root, 'output_csv', data_folder_name, 'ranked_unique_actor_anno.csv')
    
    if not os.path.exists(input_csv_path):
        print(f"Error: Input CSV file not found at {input_csv_path}")
        return
    
    # Read the CSV file
    df = pd.read_csv(input_csv_path)
    
    # Get unique actor names
    actor_names = df['ActorName'].unique()
    output_dir = ensure_output_directory()
    
    # Process all actors
    all_results = []
    possibility_counter = 1
    
    for actor_name in actor_names:
        try:
            # Get actor data
            actor_row = df[df['ActorName'] == actor_name].iloc[0]
            
            # Get display name
            actor_desc = actor_row.get('ActorDescription')
            display_name = actor_desc if pd.notna(actor_desc) and str(actor_desc).strip() else actor_row['ShortActorName']
            
            # Find the longest dimension
            longest_dim_name, longest_dim_meters, longest_dim_cm = find_longest_dimension(actor_row)
            
            # Create question
            question = f"What is the length of the longest dimension (length, width, or height) of the {display_name}, measured in centimeters?"
            
            # Round the answer to 1 decimal place
            answer = round(longest_dim_cm, 1)
            
            # Record results - with simplified columns
            all_results.append({
                'Possibility': possibility_counter,
                'ActorName': actor_name,
                'LongestDimension': longest_dim_name,
                'LongestDimension_m': longest_dim_meters,
                'LongestDimension_cm': longest_dim_cm,
                'Question': question,
                'Answer': answer
            })
            
            possibility_counter += 1
            
        except Exception as e:
            print(f"Error processing actor {actor_name}")
            print(f"Error message: {str(e)}")
            continue
    
    # Save all results to CSV
    if all_results:
        output_df = pd.DataFrame(all_results)
        output_csv_path = os.path.join(output_dir, 'object_size_all.csv')
        output_df.to_csv(output_csv_path, index=False)
        print(f"Successfully processed {len(all_results)} actors")
        print(f"Output saved to: {output_csv_path}")
        
if __name__ == "__main__":
    main()