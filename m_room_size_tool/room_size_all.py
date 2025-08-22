import pandas as pd
import os
import json

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
    
    output_dir = ensure_output_directory()
    all_results = []
    possibility_counter = 1

    # 如果找不到JSON文件，使用默认房间大小
    if not json_file_name:
        print(f"Warning: No JSON file starting with 'result' found in {json_dir_path}")
        print("Using default room size based on object positions...")
        
        # 从清理后的数据中估算房间大小
        data_folder_name = get_data_folder_name()
        input_csv_path = os.path.join(project_root, 'output_csv', data_folder_name, 'ranked_unique_actor_anno.csv')
        
        if os.path.exists(input_csv_path):
            try:
                df = pd.read_csv(input_csv_path)
                
                # 计算对象的边界框来估算房间大小
                if 'WorldX' in df.columns and 'WorldY' in df.columns:
                    min_x, max_x = df['WorldX'].min(), df['WorldX'].max()
                    min_y, max_y = df['WorldY'].min(), df['WorldY'].max()
                    
                    # 添加一些边距
                    width_m = (max_x - min_x) + 2.0  # 添加2米边距
                    depth_m = (max_y - min_y) + 2.0  # 添加2米边距
                    
                    # 确保最小房间大小
                    width_m = max(width_m, 5.0)
                    depth_m = max(depth_m, 5.0)
                    
                    area_sq_m = width_m * depth_m
                    
                    question = "What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space."
                    answer = round(area_sq_m, 2)
                    
                    all_results.append({
                        'Possibility': possibility_counter,
                        'RoomWidth_cm': width_m * 100,  # 转换为厘米
                        'RoomDepth_cm': depth_m * 100,  # 转换为厘米
                        'RoomWidth_m': width_m,
                        'RoomDepth_m': depth_m,
                        'Question': question,
                        'Answer': answer,
                        'Method': 'Estimated from object positions'
                    })
                    
                    print(f"Estimated room size: {width_m:.2f}m x {depth_m:.2f}m = {area_sq_m:.2f} sq m")
                else:
                    print("Error: WorldX and WorldY columns not found in input CSV")
                    return
                    
            except Exception as e:
                print(f"Error reading input CSV: {e}")
                return
        else:
            print(f"Error: Input CSV file not found at {input_csv_path}")
            return
    else:
        # 使用JSON文件中的房间大小
        json_file_path = os.path.join(json_dir_path, json_file_name)

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
                'Answer': answer,
                'Method': 'From JSON file'
            })

            print(f"Successfully processed room size from {json_file_name}")

        except Exception as e:
            print(f"Error processing JSON file: {e}")
            return

    # Save all results to CSV
    if all_results:
        output_csv_path = os.path.join(output_dir, 'room_size_all.csv')
        output_df = pd.DataFrame(all_results)
        output_df.to_csv(output_csv_path, index=False)
        print(f"Successfully saved room size data to {output_csv_path}")
    else:
        print("No room size data to save.")

if __name__ == "__main__":
    main()