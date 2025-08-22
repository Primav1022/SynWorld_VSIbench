import os
import subprocess
import sys

# 脚本执行开关
ENABLE_VISUALIZATIONS = True  # 设为 False 可跳过所有可视化脚本
ENABLE_FRAME_EXTRACTION = True  # 设为 False 可跳过帧抽取脚本
ENABLE_INFERENCE_SCRIPTS = True # 设为 False 可跳过推理脚本

# 统一的数据子目录配置
DEFAULT_DATA_SUBDIR = "data"  # 可改为你的目标数据文件夹

def run_script(script_path):
    """运行指定 Python 脚本并检查错误"""
    print(f"\nRunning: {os.path.basename(script_path)}")
    print("-" * 50)

    # Prepare environment variables to pass to the script
    env = os.environ.copy()
    if DEFAULT_DATA_SUBDIR:
        env['DEFAULT_DATA_SUBDIR'] = DEFAULT_DATA_SUBDIR

    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        print(f"Error running {script_path}:")
        print(result.stderr)
        return False
    
    print(result.stdout)
    return True

def main():
    # 项目根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 帧抽取脚本（可选）
    frame_extraction_script = "0_original_ue_anno/frame_extraction.py"
    
    # 按类别组织要执行的脚本
    data_cleanup_scripts = [
        "0_data_cleanup_tool/anno_extraction.py",
        "0_data_cleanup_tool/actor_visual_description.py",
    ]
    
    # 主处理脚本清单（合并版）
    main_processing_scripts = [
        # 测量类脚本
        "m_absolute_distance_tool/absolute_distance_all.py",
        "m_object_size_tool/object_size_all.py",
        "m_room_size_tool/room_size_all.py",
        # 配置/关系类脚本
        "c_object_count_tool/object_count_all.py",
        "c_relative_direction_tool/relative_direction_all.py",
        "c_relative_distance_tool/relative_distance_all.py",
        "c_route_plan_tool/route_plan_all.py",
        # 时空类脚本
        "s_appearance_order_tool/appearance_order_all.py"
    ]
    
    # 按执行顺序组合所有数据处理脚本
    data_scripts = (
        data_cleanup_scripts +
        main_processing_scripts + # 使用合并后的清单
        ["0_infer_and_score/qa_all.py"] # 将 qa_all.py 追加到数据处理末尾
    )
    
    visualization_scripts = [
        # 数据清洗可视化
        "0_data_cleanup_tool/2d_anno_visualization.py",
        "0_data_cleanup_tool/3d_anno_visualization.py",
        # 测量类可视化
        "m_absolute_distance_tool/absolute_distance_visual.py",
        "m_object_size_tool/object_size_visual.py",
        # 配置/关系类可视化
        "c_relative_direction_tool/relative_direction_visual.py",
        "c_relative_distance_tool/relative_distance_visual.py",
        "c_route_plan_tool/route_plan_visual.py",
        # 时空类可视化
        "s_appearance_order_tool/appearance_order_visual.py"
    ]
    
    inference_scripts = [
        "0_infer_and_score/infer_all.py" # 推理阶段仅保留 infer_all.py
    ]
    
    print("Starting to run data processing scripts...")
    
    # 若启用则运行帧抽取脚本
    if ENABLE_FRAME_EXTRACTION:
        frame_extraction_path = os.path.join(base_dir, frame_extraction_script)
        if not os.path.exists(frame_extraction_path):
            print(f"Error: Frame extraction script not found: {frame_extraction_path}")
        else:
            print("\nRunning frame extraction script...")
            success = run_script(frame_extraction_path)
            if not success:
                print(f"\nExecution stopped due to error in {frame_extraction_script}")
                return
    else:
        print("\nSkipping frame extraction script (ENABLE_FRAME_EXTRACTION is False)")
    
    # 运行数据处理脚本
    for script in data_scripts:
        script_path = os.path.join(base_dir, script)
        if not os.path.exists(script_path):
            print(f"Error: Script not found: {script_path}")
            continue
            
        success = run_script(script_path)
        if not success:
            print(f"\nExecution stopped due to error in {script}")
            return
    
    # 若启用则运行可视化脚本
    if ENABLE_VISUALIZATIONS:
        print("\nStarting to run visualization scripts...")
        for script in visualization_scripts:
            script_path = os.path.join(base_dir, script)
            if not os.path.exists(script_path):
                print(f"Error: Script not found: {script_path}")
                continue
                
            success = run_script(script_path)
            if not success:
                print(f"\nExecution stopped due to error in {script}")
                return
    else:
        print("\nSkipping visualization scripts (ENABLE_VISUALIZATIONS is False)")
    
    # 若启用则运行推理脚本
    if ENABLE_INFERENCE_SCRIPTS:
        print("\nStarting to run inference scripts...")
        for script in inference_scripts:
            script_path = os.path.join(base_dir, script)
            if not os.path.exists(script_path):
                print(f"Error: Script not found: {script_path}")
                continue
            
            success = run_script(script_path)
            if not success:
                print(f"\nExecution stopped due to error in {script}")
                return
    else:
        print("\nSkipping inference scripts (ENABLE_INFERENCE_SCRIPTS is False)")
    
    print("\nAll scripts execution completed!")

if __name__ == "__main__":
    main()