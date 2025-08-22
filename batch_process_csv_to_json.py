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
import time
import json

class BatchProcessor:
    def __init__(self, data_root: str, parallel: int = 1):
        self.data_root = Path(data_root)
        # 串行处理，不再使用并行
        self.parallel = 1
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
            print(f"[404] 数据根目录不存在(Data root not found): {self.data_root}")
            return []
        
        folders = []
        try:
            items = list(self.data_root.iterdir())
        except Exception as e:
            print(f"[405] 无法读取数据根目录内容(Cannot list directory): {self.data_root} -> {e}")
            return []
        
        for item in items:
            if item.is_dir():
                # 检查是否包含必要的文件
                if self._has_required_files(item):
                    folders.append(item.name)
                else:
                    print(f"[403] 跳过 {item.name}：缺少必要文件(Screenshot_summary.csv)")
        
        return folders

    def _has_required_files(self, folder_path: Path) -> bool:
        """检查文件夹是否包含必要的文件"""
        required_files = ["Screenshot_summary.csv"]
        
        for file_name in required_files:
            p = folder_path / file_name
            try:
                if not p.exists():
                    print(f"[406] 必需文件缺失(Missing): {p}")
                    return False
            except Exception as e:
                print(f"[407] 无法访问必需文件(Cannot access): {p} -> {e}")
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
        print(f"\n====================")
        print(f"开始处理数据包: {data_folder} (Processing folder)")
        start_time = time.time()
        
        results = {
            "folder": data_folder,
            "success": True,
            "scripts_run": 0,
            "scripts_failed": 0,
            "errors": []
        }
        
        # 最多尝试两轮：首轮 + 失败/不完整时重试一轮
        max_attempts = 2
        attempt = 1
        while attempt <= max_attempts:
            if attempt > 1:
                print(f"重试第 {attempt} 次: {data_folder} ... (Retry)")
            
            round_success = True
            # 按依赖顺序运行脚本
            for script in self.processing_scripts:
                print(f"  -> 正在执行脚本: {script}")
                dependencies = self.dependencies.get(script, [])
                for dep in dependencies:
                    if not self._check_dependency_success(dep, data_folder):
                        error_msg = f"依赖未满足(Dependency failed): {dep}"
                        print(f"     !! {error_msg}")
                        results["errors"].append(error_msg)
                        results["success"] = False
                        round_success = False
                        break
                else:
                    if self.run_script(script, data_folder):
                        results["scripts_run"] += 1
                    else:
                        results["scripts_failed"] += 1
                        err = f"脚本失败(Script failed): {script}"
                        print(f"     !! {err}")
                        results["errors"].append(err)
                        if script in ["0_data_cleanup_tool/anno_extraction.py"]:
                            results["success"] = False
                            round_success = False
                            break
                if not round_success:
                    break

            if not round_success:
                attempt += 1
                continue
        
            # 生成JSON文件
            try:
                json_result = subprocess.run(
                    [sys.executable, "create_simplified_vqa_dataset.py"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if json_result.returncode == 0:
                    print(f"✓ 已生成JSON: {data_folder} (Generated)")
                else:
                    print(f"✗ 生成JSON失败(Failed) -> {data_folder}")
                    results["errors"].append("JSON generation failed")
                    round_success = False
            except Exception as e:
                print(f"✗ 生成JSON异常(Error) {data_folder}: {str(e)}")
                results["errors"].append(f"JSON generation error: {str(e)}")
                round_success = False

            # 检查输出完整性
            if round_success:
                if not self._verify_outputs(data_folder):
                    print(f"!! 输出不完整(Incomplete) -> {data_folder}，将重试…")
                    round_success = False
                else:
                    print(f"✓ 输出校验通过(Verified) -> {data_folder}")

            if round_success:
                break
            attempt += 1

        elapsed_time = time.time() - start_time
        results["elapsed_time"] = elapsed_time
        
        print(f"完成数据包: {data_folder}，耗时 {elapsed_time:.2f}s (Completed)")
        return results

    def _check_dependency_success(self, script: str, data_folder: str) -> bool:
        """检查依赖脚本是否成功运行"""
        # 这里可以添加更复杂的依赖检查逻辑
        # 目前简单返回True，因为脚本会按顺序运行
        return True

    def process_all_folders(self) -> list:
        """处理所有数据文件夹（串行）"""
        data_folders = self.get_data_folders()
        
        if not data_folders:
            print("No data folders found to process")
            return []
        
        print(f"发现 {len(data_folders)} 个数据包(Found): {data_folders}")
        all_results = []
        for data_folder in data_folders:
            result = self.process_single_folder(data_folder)
            all_results.append(result)
        
        return all_results

    def _verify_outputs(self, data_folder: str) -> bool:
        """校验当前数据包的输出完整性：CSV 是否齐全且非空，JSON 是否存在且包含 qa_pairs。"""
        required_csv = [
            "ranked_unique_actor_anno.csv",
            "absolute_distances_all.csv",
            "object_size_all.csv",
            "room_size_all.csv",
            "object_count_all.csv",
            "relative_direction_all.csv",
            "relative_distance_all.csv",
            "route_plan_all.csv",
            "appearance_order_all.csv",
        ]
        csv_root = self.project_root / "output_csv" / data_folder
        ok = True
        # 目录检查
        try:
            if not csv_root.exists():
                print(f"  [404] 输出目录不存在(Output folder not found): {csv_root}")
                ok = False
        except Exception as e:
            print(f"  [405] 无法访问输出目录(Cannot access folder): {csv_root} -> {e}")
            ok = False
        
        for name in required_csv:
            path = csv_root / name
            try:
                if not path.exists():
                    print(f"  [404] CSV 不存在(Not found): {path}")
                    ok = False
                else:
                    try:
                        size = path.stat().st_size
                        if size <= 0:
                            print(f"  [405] CSV 大小为0(Unreadable/empty): {path}")
                            ok = False
                    except Exception as e:
                        print(f"  [405] 无法读取CSV属性(Cannot stat CSV): {path} -> {e}")
                        ok = False
            except Exception as e:
                print(f"  [405] 无法检查CSV(Cannot check CSV): {path} -> {e}")
                ok = False

        json_path = self.project_root / "output_json" / f"{data_folder}.json"
        try:
            if not json_path.exists():
                print(f"  [404] JSON 不存在(Not found): {json_path}")
                ok = False
            else:
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    qa_pairs = data.get('qa_pairs', [])
                    if not isinstance(qa_pairs, list) or len(qa_pairs) == 0:
                        print(f"  [405] JSON qa_pairs 为空(Empty): {json_path}")
                        ok = False
                except Exception as e:
                    print(f"  [405] JSON 无法解析(Parse error): {json_path} -> {e}")
                    ok = False
        except Exception as e:
            print(f"  [405] 无法检查JSON(Cannot check JSON): {json_path} -> {e}")
            ok = False

        return ok

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
    # 并行已禁用，保留参数兼容但不生效
    parser.add_argument("--parallel", type=int, default=1, help="(已忽略) 并行处理数量")
    
    args = parser.parse_args()
    
    processor = BatchProcessor(args.data_root, 1)
    results = processor.process_all_folders()
    processor.print_summary(results)

if __name__ == "__main__":
    main()
