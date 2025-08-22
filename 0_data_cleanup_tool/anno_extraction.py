import pandas as pd
import os
import argparse
import re # Added import

# Configuration variables
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Navigate up to SynVSI_anno_gen

# Default values
# 优先从 data/ 目录读取；允许通过环境变量或参数传入 data 的子目录名
DEFAULT_DATA_SUBDIRECTORY = os.environ.get('DEFAULT_DATA_SUBDIR', "")
MIN_FRAME_COUNT = 5  # Minimum number of frames an actor must appear in
MIN_VOLUME = 0.005   # Minimum volume in cubic meters

# Input/Output paths
# 改为在项目根 data/ 目录下查找输入 CSV
DATA_ROOT = os.path.join(project_root, "data")
# 修改输出路径到根目录的output_csv/对应数据文件名/
OUTPUT_DATA_ROOT = os.path.join(project_root, "output_csv")

def _resolve_screenshot_summary_csv(data_subdir: str) -> str:
    """
    在 data/ 根目录下解析 Screenshot_summary.csv 的真实路径。
    查找顺序：
      1) data/Screenshot_summary.csv
      2) 若提供 data_subdir，则 data/<data_subdir>/Screenshot_summary.csv
      3) 递归遍历 data/，返回找到的第一个 Screenshot_summary.csv
    若均未找到，返回空字符串。
    """
    # 1) 直接在 data/ 根目录
    direct_path = os.path.join(DATA_ROOT, "Screenshot_summary.csv")
    if os.path.exists(direct_path):
        return direct_path

    # 2) 指定 data 子目录
    if data_subdir:
        candidate = os.path.join(DATA_ROOT, data_subdir, "Screenshot_summary.csv")
        if os.path.exists(candidate):
            return candidate

    # 3) 递归兜底
    for current_dir, _, files in os.walk(DATA_ROOT):
        if "Screenshot_summary.csv" in files:
            return os.path.join(current_dir, "Screenshot_summary.csv")

    return ""

def _get_data_folder_name(data_subdir: str) -> str:
    """
    根据data_subdir确定数据文件夹名称，用于输出目录
    """
    if data_subdir:
        return data_subdir
    else:
        # 如果没有指定data_subdir，尝试从data目录中找到第一个文件夹
        if os.path.exists(DATA_ROOT):
            for item in os.listdir(DATA_ROOT):
                item_path = os.path.join(DATA_ROOT, item)
                if os.path.isdir(item_path):
                    return item
        return "default"

# --- Add the new function here ---
def _determine_short_actor_name(actor_name: str, cleaned_actor_name: str) -> str:
    """
    Determines a shorter, more readable actor name for VLM prompting.
    It extracts the second to last part of the underscore-separated actor name,
    formats it by splitting camel case, and converts it to lowercase.
    Acronyms (e.g., 'TV') are kept together.
    """
    parts = actor_name.split('_')
    
    # Use the second to last part as the base for the short name.
    # If there are less than 2 parts, use the whole name.
    if len(parts) >= 2:
        # The second to last part is usually the most descriptive name.
        raw_name = parts[-2]
    else:
        raw_name = actor_name

    # Add a space before any uppercase letter that is preceded by a lowercase letter.
    # This correctly handles 'WashingMachine' -> 'Washing Machine' and 'MyTV' -> 'MyTV'.
    spaced_name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', raw_name)
    
    # Convert to lowercase
    short_actor_name = spaced_name.lower()
    
    return short_actor_name
# --- End of new function ---

def extract_ranked_actor_info(data_subdir=DEFAULT_DATA_SUBDIRECTORY, min_frame_count=MIN_FRAME_COUNT, min_volume=MIN_VOLUME):
    """
    Extract unique actor information with first appearance frame and world data
    Args:
        data_subdir: Data subdirectory name containing the input data
        min_frame_count: Minimum number of frames an actor must appear in
        min_volume: Minimum volume in cubic meters
    """
    # 解析 data/ 下的 Screenshot_summary.csv
    input_csv = _resolve_screenshot_summary_csv(data_subdir)

    if not input_csv:
        print(f"Error: Could not find 'Screenshot_summary.csv' under data root: {DATA_ROOT}")
        return

    # Read the input CSV file
    df = pd.read_csv(input_csv)

    # Count frame appearances for each actor
    frame_counts = df.groupby(['ActorName', 'ActorClass'])['FrameNumber'].nunique().reset_index()
    frame_counts = frame_counts.rename(columns={'FrameNumber': 'FrameCount'})
    
    # Filter actors that appear in more than min_frame_count frames
    qualified_actors = frame_counts[frame_counts['FrameCount'] >= min_frame_count]

    # Get first appearance frame for each actor
    first_appearance = df.groupby(['ActorName', 'ActorClass'])['FrameNumber'].min().reset_index()
    first_appearance = first_appearance.rename(columns={'FrameNumber': 'FirstFrame'})

    # Get world coordinates and sizes for each actor (using the first appearance frame)
    actor_info = []
    for _, row in first_appearance.iterrows():
        actor_name = row['ActorName']
        actor_class = row['ActorClass']
        first_frame = row['FirstFrame']
        
        # Get the data for this actor from the first frame they appear in
        frame_data = df[(df['ActorName'] == actor_name) & (df['FrameNumber'] == first_frame)]
        
        if not frame_data.empty:
            actor_row = frame_data.iloc[0]
            actor_info.append({
                'ActorName': actor_name,
                'ActorClass': actor_class,
                'WorldX': actor_row['WorldX'],
                'WorldY': actor_row['WorldY'],
                'WorldZ': actor_row['WorldZ'],
                'WorldSizeX': actor_row['WorldSizeX'],
                'WorldSizeY': actor_row['WorldSizeY'],
                'WorldSizeZ': actor_row['WorldSizeZ'],
                'ActorDescription': actor_row.get('ActorDescription', '')
            })

    actor_info = pd.DataFrame(actor_info)

    # Convert world coordinates and sizes from centimeters to meters
    # Apply transformation: X -> -X for WorldX
    actor_info['WorldX'] = - (actor_info['WorldX'] / 100.0)
    # actor_info['WorldX'] = (actor_info['WorldX'] / 100.0)
    actor_info['WorldY'] = actor_info['WorldY'] / 100.0
    actor_info['WorldZ'] = actor_info['WorldZ'] / 100.0
    
    size_columns = ['WorldSizeX', 'WorldSizeY', 'WorldSizeZ']
    actor_info[size_columns] = actor_info[size_columns] / 100.0

    # Calculate volume in cubic meters
    actor_info['Volume'] = actor_info['WorldSizeX'] * actor_info['WorldSizeY'] * actor_info['WorldSizeZ']
    
    # Filter by minimum volume
    actor_info = actor_info[actor_info['Volume'] >= min_volume]

    # Merge the information and sort by first appearance
    merged_info = pd.merge(first_appearance, actor_info, on=['ActorName', 'ActorClass'])
    # Add frame count information
    merged_info = pd.merge(merged_info, qualified_actors[['ActorName', 'FrameCount']], on='ActorName')
    
    # Generate ShortActorName
    # Pass actor_name for both arguments as CleanedActorName is not separately generated here.
    merged_info['ShortActorName'] = merged_info.apply(
        lambda row: _determine_short_actor_name(row['ActorName'], row['ActorName']), axis=1
    )

    # Extract camera information for each actor's first appearance frame
    camera_columns = ['CamX', 'CamY', 'CamZ', 'CamPitch', 'CamYaw', 'CamRoll']
    
    # Create a dictionary to store camera data for each actor
    camera_data = {}
    
    # For each actor, get the camera data from its first appearance frame
    for _, row in merged_info.iterrows():
        actor_name = row['ActorName']
        first_frame = row['FirstFrame']
        
        # Get the camera data from the first frame this actor appears in
        frame_data = df[(df['ActorName'] == actor_name) & (df['FrameNumber'] == first_frame)]
        
        if not frame_data.empty and all(col in frame_data.columns for col in camera_columns):
            camera_row = frame_data.iloc[0]
            camera_data[actor_name] = {
                'CamX': - (camera_row['CamX'] / 100.0),  # Convert to meters and apply transformation X -> -X
                'CamY': camera_row['CamY'] / 100.0,   # Convert to meters
                'CamZ': camera_row['CamZ'] / 100.0,   # Convert to meters
                'CamPitch': camera_row['CamPitch'],
                'CamYaw': camera_row['CamYaw'],
                'CamRoll': camera_row['CamRoll']
            }
        else:
            # If camera data is missing, use NaN values
            camera_data[actor_name] = {col: float('nan') for col in camera_columns}
    
    # Add camera data to the merged info dataframe
    for col in camera_columns:
        merged_info[col] = merged_info['ActorName'].apply(lambda x: camera_data[x][col])
    
    # Sort by first appearance
    merged_info = merged_info.sort_values('FirstFrame')
    
    # Ensure column order with FirstFrame, FrameCount, Volume and Camera data
    column_order = ['FirstFrame', 'FrameCount', 'ActorName', 'ActorClass', 'ShortActorName',
                    'WorldX', 'WorldY', 'WorldZ', 'WorldSizeX', 'WorldSizeY', 'WorldSizeZ', 'Volume',
                    'CamX', 'CamY', 'CamZ', 'CamPitch', 'CamYaw', 'CamRoll']
    merged_info = merged_info[column_order]

    # 确定输出目录
    data_folder_name = _get_data_folder_name(data_subdir)
    output_dir = os.path.join(OUTPUT_DATA_ROOT, data_folder_name)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save to output CSV in the new directory structure
    output_csv = os.path.join(output_dir, "ranked_unique_actor_anno.csv")
    merged_info.to_csv(output_csv, index=False)

    # print(f"Ranked actor information has been saved to {output_csv}")
    print(f"Unique actors:")
    print(f"1. Appear in {min_frame_count} or more frames")
    print(f"2. Have a volume greater than {min_volume} cubic meters")
    print(f"Output saved to: {output_csv}")
    # print("Note: All world coordinates and sizes have been converted from centimeters to meters")
    # print("Note: Camera position data (CamX, CamY, CamZ) has also been converted to meters")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract and rank actor information from Screenshot_summary.csv (searched under data/)')
    parser.add_argument('--data_subdir', type=str, default=DEFAULT_DATA_SUBDIRECTORY,
                      help='Optional subdirectory under data/ to search; if empty, will check data/ then recurse')
    parser.add_argument('--min_frames', type=int, default=MIN_FRAME_COUNT,
                      help='Minimum number of frames an actor must appear in')
    parser.add_argument('--min_volume', type=float, default=MIN_VOLUME,
                      help='Minimum volume in cubic meters')
    
    args = parser.parse_args()
    
    extract_ranked_actor_info(
        data_subdir=args.data_subdir,
        min_frame_count=args.min_frames,
        min_volume=args.min_volume
    )