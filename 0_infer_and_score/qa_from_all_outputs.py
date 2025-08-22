import pandas as pd
import os
import json
from pathlib import Path

# 获取数据文件夹名称
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

# 输出目录结构为 output_json/数据文件夹名/各部分json文件
def get_output_dir(data_folder_name):
    """
    获取指定数据文件夹下的输出目录（output_json/数据文件夹名），并确保其存在。
    """
    output_dir = Path("output_json") / data_folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

# 定义要处理的CSV文件和对应的JSON输出文件名
# - output_csv/数据文件夹名称/absolute_distances_all.csv => m_absolute_distance.json
# - output_csv/数据文件夹名称/object_size_all.csv => m_object_size.json
# - output_csv/数据文件夹名称/room_size_all.csv => m_room_size.json （若不存在则跳过）
# - output_csv/数据文件夹名称/object_count_all.csv => c_object_count.json （若不存在则跳过）
# - output_csv/数据文件夹名称/relative_direction_all.csv => c_relative_direction.json
# - output_csv/数据文件夹名称/relative_distance_all.csv => c_relative_distance.json
# - output_csv/数据文件夹名称/route_plan_all.csv => c_route_plan.json
# - output_csv/数据文件夹名称/appearance_order_all.csv => s_appearance_order.json

def process_absolute_distance():
    """处理绝对距离数据"""
    data_folder_name = get_data_folder_name()
    csv_path = f"output_csv/{data_folder_name}/absolute_distances_all.csv"
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return []
    
    df = pd.read_csv(csv_path)
    qa_pairs = []
    
    for index, row in df.iterrows():
        qa_pair = {
            "video_id": data_folder_name,  # 使用数据文件夹名称
            "video_path": f"output_video/{data_folder_name}.mp4",  # 使用对应的视频路径
            "category": "absolute_distance",
            "question_id": f"abs_dist_{index + 1}",
            "question": row.get('Question', ''),
            "answer": row.get('Answer', ''),
            "metadata": {
                "object1": row.get('Object1', ''),
                "object2": row.get('Object2', ''),
                "distance": row.get('Distance', ''),
                "possibility": row.get('Possibility', '')
            }
        }
        qa_pairs.append(qa_pair)
    
    return qa_pairs

def process_object_size():
    """处理对象尺寸数据"""
    data_folder_name = get_data_folder_name()
    csv_path = f"output_csv/{data_folder_name}/object_size_all.csv"
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return []
    
    df = pd.read_csv(csv_path)
    qa_pairs = []
    
    for index, row in df.iterrows():
        qa_pair = {
            "video_id": data_folder_name,
            "video_path": f"output_video/{data_folder_name}.mp4",
            "category": "object_size",
            "question_id": f"obj_size_{index + 1}",
            "question": row.get('Question', ''),
            "answer": row.get('Answer', ''),
            "metadata": {
                "actor_name": row.get('ActorName', ''),
                "longest_dimension": row.get('LongestDimension', ''),
                "possibility": row.get('Possibility', '')
            }
        }
        qa_pairs.append(qa_pair)
    
    return qa_pairs

def process_room_size():
    """处理房间尺寸数据"""
    data_folder_name = get_data_folder_name()
    csv_path = f"output_csv/{data_folder_name}/room_size_all.csv"
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return []
    
    df = pd.read_csv(csv_path)
    qa_pairs = []
    
    for index, row in df.iterrows():
        qa_pair = {
            "video_id": data_folder_name,
            "video_path": f"output_video/{data_folder_name}.mp4",
            "category": "room_size",
            "question_id": f"room_size_{index + 1}",
            "question": row.get('Question', ''),
            "answer": row.get('Answer', ''),
            "metadata": {
                "room_width": row.get('RoomWidth', ''),
                "room_length": row.get('RoomLength', ''),
                "possibility": row.get('Possibility', '')
            }
        }
        qa_pairs.append(qa_pair)
    
    return qa_pairs

def process_object_count():
    """处理对象计数数据"""
    data_folder_name = get_data_folder_name()
    csv_path = f"output_csv/{data_folder_name}/object_count_all.csv"
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return []
    
    df = pd.read_csv(csv_path)
    qa_pairs = []
    
    for index, row in df.iterrows():
        qa_pair = {
            "video_id": data_folder_name,
            "video_path": f"output_video/{data_folder_name}.mp4",
            "category": "object_count",
            "question_id": f"obj_count_{index + 1}",
            "question": row.get('Question', ''),
            "answer": row.get('Answer', ''),
            "metadata": {
                "object_type": row.get('ObjectType', ''),
                "count": row.get('Count', ''),
                "possibility": row.get('Possibility', '')
            }
        }
        qa_pairs.append(qa_pair)
    
    return qa_pairs

def process_relative_direction():
    """处理相对方向数据"""
    data_folder_name = get_data_folder_name()
    csv_path = f"output_csv/{data_folder_name}/relative_direction_all.csv"
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return []
    
    df = pd.read_csv(csv_path)
    qa_pairs = []
    
    for index, row in df.iterrows():
        qa_pair = {
            "video_id": data_folder_name,
            "video_path": f"output_video/{data_folder_name}.mp4",
            "category": "relative_direction",
            "question_id": f"rel_dir_{index + 1}",
            "question": row.get('QuestionHard', ''),  # 使用Hard难度的问题
            "answer": row.get('AnswerHard', ''),
            "metadata": {
                "object1": row.get('Object1', ''),
                "object2": row.get('Object2', ''),
                "direction": row.get('Direction', ''),
                "possibility": row.get('Possibility', '')
            }
        }
        qa_pairs.append(qa_pair)
    
    return qa_pairs

def process_relative_distance():
    """处理相对距离数据"""
    data_folder_name = get_data_folder_name()
    csv_path = f"output_csv/{data_folder_name}/relative_distance_all.csv"
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return []
    
    df = pd.read_csv(csv_path)
    qa_pairs = []
    
    for index, row in df.iterrows():
        qa_pair = {
            "video_id": data_folder_name,
            "video_path": f"output_video/{data_folder_name}.mp4",
            "category": "relative_distance",
            "question_id": f"rel_dist_{index + 1}",
            "question": row.get('Question', ''),
            "answer": row.get('Answer', ''),
            "metadata": {
                "object1": row.get('Object1', ''),
                "object2": row.get('Object2', ''),
                "distance": row.get('Distance', ''),
                "possibility": row.get('Possibility', '')
            }
        }
        qa_pairs.append(qa_pair)
    
    return qa_pairs

def process_route_plan():
    """处理路径规划数据"""
    data_folder_name = get_data_folder_name()
    csv_path = f"output_csv/{data_folder_name}/route_plan_all.csv"
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return []
    
    df = pd.read_csv(csv_path)
    qa_pairs = []
    
    for index, row in df.iterrows():
        qa_pair = {
            "video_id": data_folder_name,
            "video_path": f"output_video/{data_folder_name}.mp4",
            "category": "route_plan",
            "question_id": f"route_{index + 1}",
            "question": row.get('Question', ''),
            "answer": row.get('Answer', ''),
            "metadata": {
                "start_point": row.get('StartPoint', ''),
                "end_point": row.get('EndPoint', ''),
                "turn_direction": row.get('TurnDirection', ''),
                "possibility": row.get('Possibility', '')
            }
        }
        qa_pairs.append(qa_pair)
    
    return qa_pairs

def process_appearance_order():
    """处理出现顺序数据"""
    data_folder_name = get_data_folder_name()
    csv_path = f"output_csv/{data_folder_name}/appearance_order_all.csv"
    if not os.path.exists(csv_path):
        print(f"文件不存在: {csv_path}")
        return []
    
    df = pd.read_csv(csv_path)
    qa_pairs = []
    
    for index, row in df.iterrows():
        qa_pair = {
            "video_id": data_folder_name,
            "video_path": f"output_video/{data_folder_name}.mp4",
            "category": "appearance_order",
            "question_id": f"app_order_{index + 1}",
            "question": row.get('Question', ''),
            "answer": row.get('Answer', ''),
            "metadata": {
                "object_name": row.get('ObjectName', ''),
                "appearance_order": row.get('AppearanceOrder', ''),
                "first_frame": row.get('FirstFrame', ''),
                "possibility": row.get('Possibility', '')
            }
        }
        qa_pairs.append(qa_pair)
    
    return qa_pairs

def main():
    print("开始处理所有输出文件...")
    
    # 获取数据文件夹名称和输出目录
    data_folder_name = get_data_folder_name()
    OUTPUT_DIR = get_output_dir(data_folder_name)
    
    # 定义处理函数和对应的输出文件名
    processors = [
        (process_absolute_distance, "m_absolute_distance.json"),
        (process_object_size, "m_object_size.json"),
        (process_room_size, "m_room_size.json"),
        (process_object_count, "c_object_count.json"),
        (process_relative_direction, "c_relative_direction.json"),
        (process_relative_distance, "c_relative_distance.json"),
        (process_route_plan, "c_route_plan.json"),
        (process_appearance_order, "s_appearance_order.json"),
    ]
    
    total_qa_pairs = 0
    
    for processor, output_filename in processors:
        print(f"\n处理 {output_filename}...")
        qa_pairs = processor()
        
        if qa_pairs:
            output_path = OUTPUT_DIR / output_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 生成 {len(qa_pairs)} 个QA pairs -> {output_path}")
            total_qa_pairs += len(qa_pairs)
        else:
            print(f"⚠️  跳过 {output_filename} (无数据)")
    
    print(f"\n🎉 处理完成！总共生成 {total_qa_pairs} 个QA pairs")
    print(f"输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()


