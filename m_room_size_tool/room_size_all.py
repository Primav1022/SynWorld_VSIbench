import pandas as pd
import os
import json

def ensure_output_directory():
    """Create output directory if it doesn't exist and return its path."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    return output_dir

def main():
    """
    Main function to extract room dimensions, calculate area, generate QA pairs,
    and save them to a CSV file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Navigates to SynVSI_anno_gen

    # Configurable timestamp folder
    TIMESTAMP_FOLDER = os.environ.get('DEFAULT_DATA_SUBDIR', "20250527-145925")  # You can change this value as needed

    # Path to the directory containing the JSON file
    json_dir_path = os.path.join(project_root, '0_original_ue_anno', TIMESTAMP_FOLDER)

    # Find the JSON file starting with "result" in the timestamp folder
    json_file_name = None
    if os.path.exists(json_dir_path):
        for f_name in os.listdir(json_dir_path):
            if f_name.startswith('result') and f_name.endswith('.json'):
                json_file_name = f_name
                break # Use the first matching file
    
    if not json_file_name:
        print(f"Error: No JSON file starting with 'result' found in {json_dir_path}")
        return

    json_file_path = os.path.join(json_dir_path, json_file_name)

    output_dir = ensure_output_directory()
    all_results = []
    possibility_counter = 1

    if not os.path.exists(json_file_path):
        print(f"Error: JSON file not found at {json_file_path}")
        return

    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        # Extract dimensions from room_status.transforms.size
        # Assuming size is [width, height, depth] and we need width and depth for floor area
        if (
            'room_status' not in data or 
            not isinstance(data['room_status'], list) or 
            len(data['room_status']) == 0 or
            'transforms' not in data['room_status'][0] or
            not isinstance(data['room_status'][0]['transforms'], list) or
            len(data['room_status'][0]['transforms']) == 0 or
            'size' not in data['room_status'][0]['transforms'][0] or
            not isinstance(data['room_status'][0]['transforms'][0]['size'], list) or
            len(data['room_status'][0]['transforms'][0]['size']) < 3
        ):
            print(f"Error: 'room_status[0].transforms[0].size' not found or invalid in {json_file_path}")
            return

        room_dimensions_cm = data['room_status'][0]['transforms'][0]['size']
        width_cm = room_dimensions_cm[0]
        depth_cm = room_dimensions_cm[2] # Using the third element as depth for floor area

        # Convert dimensions from centimeters to meters
        # 1 meter = 100 centimeters
        width_m = width_cm / 100.0
        depth_m = depth_cm / 100.0

        # Calculate area in square meters
        area_sq_m = width_m * depth_m

        question = "What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space."
        answer = round(area_sq_m, 2) # Round to 2 decimal places for readability

        all_results.append({
            'Possibility': possibility_counter,
            'RoomWidth_cm': width_cm,
            'RoomDepth_cm': depth_cm,
            'RoomWidth_m': width_m,
            'RoomDepth_m': depth_m,
            'Question': question,
            'Answer': answer
        })

        # Save all results to CSV
        output_csv_path = os.path.join(output_dir, 'room_size_all.csv')
        output_df = pd.DataFrame(all_results)
        output_df.to_csv(output_csv_path, index=False)
        print(f"Successfully processed room size from {json_file_name}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {json_file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()