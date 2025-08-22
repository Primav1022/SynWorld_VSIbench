#!/usr/bin/env python3
"""
批量处理脚本：处理多个数据文件夹，生成所有CSV文件并转换为简化的JSON格式

使用方法：
python batch_process_csv_to_json.py --data_root data --parallel 4
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

class BatchProcessor:
    def __init__(self, data_root: str, parallel: int = 1):
        self.data_root = Path(data_root)
        self.parallel = parallel
        self.project_root = Path(__file__).parent
        
        # 定义需要运行的脚本列表
        self.processing_scripts = [
            "0_data_cleanup_tool/anno_extraction.py",
            "m_absolute_distance_tool/absolute_distance_all.py",
            "m_object_size_tool/object_size_all.py",
            "m_room_size_tool/room_size_all.py",
            "c_object_count_tool/object_count_all.py",
            "c_relative_direction_tool/relative_direction_all.py",
            "c_relative_distance_tool/relative_distance_all.py",
            "c_route_plan_tool/route_plan_all.py",
            "s_appearance_order_tool/appearance_order_all.py"
        ]
        
        # 定义脚本依赖关系
        self.dependencies = {
            "0_data_cleanup_tool/anno_extraction.py": [],
            "m_absolute_distance_tool/absolute_distance_all.py": ["0_data_cleanup_tool/anno_extraction.py"],
            "m_object_size_tool/object_size_all.py": ["0_data_cleanup_tool/anno_extraction.py"],
            "m_room_size_tool/room_size_all.py": ["0_data_cleanup_tool/anno_extraction.py"],
            "c_object_count_tool/object_count_all.py": ["0_data_cleanup_tool/anno_extraction.py"],
            "c_relative_direction_tool/relative_direction_all.py": ["0_data_cleanup_tool/anno_extraction.py", "m_room_size_tool/room_size_all.py"],
            "c_relative_distance_tool/relative_distance_all.py": ["0_data_cleanup_tool/anno_extraction.py", "m_absolute_distance_tool/absolute_distance_all.py", "m_room_size_tool/room_size_all.py"],
            "c_route_plan_tool/route_plan_all.py": ["0_data_cleanup_tool/anno_extraction.py", "m_absolute_distance_tool/absolute_distance_all.py"],
            "s_appearance_order_tool/appearance_order_all.py": ["0_data_cleanup_tool/anno_extraction.py"]
        }

    def get_data_folders(self) -> list:
        """获取所有数据文件夹"""
        if not self.data_root.exists():
            print(f"Error: Data root directory not found: {self.data_root}")
            return []
        
        folders = []
        for item in self.data_root.iterdir():
            if item.is_dir():
                # 检查是否包含必要的文件
                if self._has_required_files(item):
                    folders.append(item.name)
                else:
                    print(f"Warning: Skipping {item.name} - missing required files")
        
        return folders

    def _has_required_files(self, folder_path: Path) -> bool:
        """检查文件夹是否包含必要的文件"""
        required_files = ["Screenshot_summary.csv"]
        
        for file_name in required_files:
            if not (folder_path / file_name).exists():
                return False
        
        return True

    def run_script(self, script_path: str, data_folder: str) -> bool:
        """运行单个脚本"""
        script_full_path = self.project_root / script_path
        
        if not script_full_path.exists():
            print(f"Error: Script not found: {script_full_path}")
            return False
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['DEFAULT_DATA_SUBDIR'] = data_folder
            
            # 运行脚本
            result = subprocess.run(
                [sys.executable, str(script_full_path), "--data_subdir", data_folder],
                cwd=self.project_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print(f"✓ {script_path} for {data_folder}")
                return True
            else:
                print(f"✗ {script_path} for {data_folder}")
                print(f"  Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"✗ {script_path} for {data_folder} - Timeout")
            return False
        except Exception as e:
            print(f"✗ {script_path} for {data_folder} - {str(e)}")
            return False

    def process_single_folder(self, data_folder: str) -> dict:
        """处理单个数据文件夹"""
        print(f"\nProcessing folder: {data_folder}")
        start_time = time.time()
        
        results = {
            "folder": data_folder,
            "success": True,
            "scripts_run": 0,
            "scripts_failed": 0,
            "errors": []
        }
        
        # 按依赖顺序运行脚本
        for script in self.processing_scripts:
            # 检查依赖
            dependencies = self.dependencies.get(script, [])
            for dep in dependencies:
                if not self._check_dependency_success(dep, data_folder):
                    error_msg = f"Dependency failed: {dep}"
                    results["errors"].append(error_msg)
                    results["success"] = False
                    break
            else:
                # 所有依赖都成功，运行当前脚本
                if self.run_script(script, data_folder):
                    results["scripts_run"] += 1
                else:
                    results["scripts_failed"] += 1
                    results["errors"].append(f"Script failed: {script}")
                    # 对于关键脚本，如果失败就停止处理
                    if script in ["0_data_cleanup_tool/anno_extraction.py"]:
                        results["success"] = False
                        break
        
        # 生成JSON文件
        if results["success"]:
            try:
                json_result = subprocess.run(
                    [sys.executable, "create_simplified_vqa_dataset.py"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if json_result.returncode == 0:
                    print(f"✓ Generated JSON for {data_folder}")
                else:
                    print(f"✗ Failed to generate JSON for {data_folder}")
                    results["errors"].append("JSON generation failed")
            except Exception as e:
                print(f"✗ JSON generation error for {data_folder}: {str(e)}")
                results["errors"].append(f"JSON generation error: {str(e)}")
        
        elapsed_time = time.time() - start_time
        results["elapsed_time"] = elapsed_time
        
        print(f"Completed {data_folder} in {elapsed_time:.2f}s")
        return results

    def _check_dependency_success(self, script: str, data_folder: str) -> bool:
        """检查依赖脚本是否成功运行"""
        # 这里可以添加更复杂的依赖检查逻辑
        # 目前简单返回True，因为脚本会按顺序运行
        return True

    def process_all_folders(self) -> list:
        """处理所有数据文件夹"""
        data_folders = self.get_data_folders()
        
        if not data_folders:
            print("No data folders found to process")
            return []
        
        print(f"Found {len(data_folders)} data folders to process: {data_folders}")
        
        all_results = []
        
        if self.parallel == 1:
            # 串行处理
            for data_folder in data_folders:
                result = self.process_single_folder(data_folder)
                all_results.append(result)
        else:
            # 并行处理
            with ProcessPoolExecutor(max_workers=self.parallel) as executor:
                # 提交所有任务
                future_to_folder = {
                    executor.submit(self.process_single_folder, folder): folder 
                    for folder in data_folders
                }
                
                # 收集结果
                for future in as_completed(future_to_folder):
                    folder = future_to_folder[future]
                    try:
                        result = future.result()
                        all_results.append(result)
                    except Exception as e:
                        print(f"Error processing {folder}: {str(e)}")
                        all_results.append({
                            "folder": folder,
                            "success": False,
                            "scripts_run": 0,
                            "scripts_failed": 0,
                            "errors": [str(e)],
                            "elapsed_time": 0
                        })
        
        return all_results

    def print_summary(self, results: list):
        """打印处理摘要"""
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        
        total_folders = len(results)
        successful_folders = sum(1 for r in results if r["success"])
        failed_folders = total_folders - successful_folders
        
        total_scripts_run = sum(r["scripts_run"] for r in results)
        total_scripts_failed = sum(r["scripts_failed"] for r in results)
        total_time = sum(r["elapsed_time"] for r in results)
        
        print(f"Total folders processed: {total_folders}")
        print(f"Successful: {successful_folders}")
        print(f"Failed: {failed_folders}")
        print(f"Total scripts run: {total_scripts_run}")
        print(f"Total scripts failed: {total_scripts_failed}")
        print(f"Total processing time: {total_time:.2f}s")
        
        if failed_folders > 0:
            print("\nFailed folders:")
            for result in results:
                if not result["success"]:
                    print(f"  - {result['folder']}: {', '.join(result['errors'])}")

def main():
    parser = argparse.ArgumentParser(description="批量处理数据文件夹，生成CSV和JSON文件")
    parser.add_argument("--data_root", default="data", help="数据根目录")
    parser.add_argument("--parallel", type=int, default=1, help="并行处理数量")
    
    args = parser.parse_args()
    
    processor = BatchProcessor(args.data_root, args.parallel)
    results = processor.process_all_folders()
    processor.print_summary(results)

if __name__ == "__main__":
    main()
