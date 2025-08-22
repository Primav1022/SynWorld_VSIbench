#!/usr/bin/env python3
"""
专门处理route_plan的批量处理脚本：只执行route_plan_all.py并将结果插入到现有JSON文件中

使用方法：
python batch_process_route_plan.py --data_root data
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import time
import json
import pandas as pd

class RoutePlanProcessor:
    def __init__(self, data_root: str):
        self.data_root = Path(data_root)
        self.project_root = Path(__file__).parent
        
        # 只处理route_plan脚本
        self.route_plan_script = "c_route_plan_tool/route_plan_all.py"

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

    def run_route_plan_script(self, data_folder: str) -> bool:
        """运行route_plan脚本"""
        script_full_path = self.project_root / self.route_plan_script
        
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
                print(f"✓ {self.route_plan_script} for {data_folder}")
                return True
            else:
                print(f"✗ {self.route_plan_script} for {data_folder}")
                print(f"  Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"✗ {self.route_plan_script} for {data_folder} - Timeout")
            return False
        except Exception as e:
            print(f"✗ {self.route_plan_script} for {data_folder} - {str(e)}")
            return False

    def extract_route_plan_qa_pairs(self, data_folder: str) -> list:
        """从route_plan_all.csv中提取QA对"""
        csv_path = self.project_root / "output_csv" / data_folder / "route_plan_all.csv"
        
        if not csv_path.exists():
            print(f"  [404] route_plan_all.csv 不存在: {csv_path}")
            return []
        
        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                print(f"  [405] route_plan_all.csv 为空: {csv_path}")
                return []
            
            qa_pairs = []
            for _, row in df.iterrows():
                qa_pair = {
                    "question": row['Question'],
                    "answer": row['Answer'],
                    "question_type": "c_route_plan",
                    "difficulty": "hard"  # route_plan默认为hard难度
                }
                qa_pairs.append(qa_pair)
            
            print(f"  ✓ 提取了 {len(qa_pairs)} 个route_plan QA对")
            return qa_pairs
            
        except Exception as e:
            print(f"  [405] 无法读取route_plan_all.csv: {csv_path} -> {e}")
            return []

    def update_json_with_route_plan(self, data_folder: str, route_plan_qa_pairs: list) -> bool:
        """将route_plan的QA对插入到现有JSON文件中"""
        json_path = self.project_root / "output_json" / f"{data_folder}.json"
        
        if not json_path.exists():
            print(f"  [404] JSON文件不存在: {json_path}")
            return False
        
        try:
            # 读取现有JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 获取现有的qa_pairs
            existing_qa_pairs = json_data.get('qa_pairs', [])
            
            # 移除现有的c_route_plan类型的QA对（如果存在）
            filtered_qa_pairs = [qa for qa in existing_qa_pairs if qa.get('question_type') != 'c_route_plan']
            
            # 添加新的route_plan QA对
            updated_qa_pairs = filtered_qa_pairs + route_plan_qa_pairs
            
            # 更新JSON数据
            json_data['qa_pairs'] = updated_qa_pairs
            
            # 写回文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"  ✓ 成功更新JSON文件，新增 {len(route_plan_qa_pairs)} 个route_plan QA对")
            return True
            
        except Exception as e:
            print(f"  [405] 无法更新JSON文件: {json_path} -> {e}")
            return False

    def process_single_folder(self, data_folder: str) -> dict:
        """处理单个数据文件夹的route_plan"""
        print(f"\n====================")
        print(f"开始处理route_plan: {data_folder} (Processing route_plan)")
        start_time = time.time()
        
        results = {
            "folder": data_folder,
            "success": True,
            "route_plan_generated": False,
            "qa_pairs_extracted": 0,
            "json_updated": False,
            "errors": []
        }
        
        # 1. 运行route_plan脚本
        print(f"  -> 正在执行脚本: {self.route_plan_script}")
        if self.run_route_plan_script(data_folder):
            results["route_plan_generated"] = True
        else:
            results["success"] = False
            results["errors"].append("route_plan脚本执行失败")
            elapsed_time = time.time() - start_time
            results["elapsed_time"] = elapsed_time
            print(f"完成route_plan处理: {data_folder}，耗时 {elapsed_time:.2f}s (Failed)")
            return results
        
        # 2. 提取QA对
        route_plan_qa_pairs = self.extract_route_plan_qa_pairs(data_folder)
        results["qa_pairs_extracted"] = len(route_plan_qa_pairs)
        
        if not route_plan_qa_pairs:
            results["errors"].append("未提取到route_plan QA对")
            # 即使没有QA对，也认为处理成功（可能是数据本身没有有效路线）
        
        # 3. 更新JSON文件
        if route_plan_qa_pairs:
            if self.update_json_with_route_plan(data_folder, route_plan_qa_pairs):
                results["json_updated"] = True
            else:
                results["success"] = False
                results["errors"].append("JSON文件更新失败")
        
        elapsed_time = time.time() - start_time
        results["elapsed_time"] = elapsed_time
        
        print(f"完成route_plan处理: {data_folder}，耗时 {elapsed_time:.2f}s (Completed)")
        return results

    def process_all_folders(self) -> list:
        """处理所有数据文件夹的route_plan"""
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

    def print_summary(self, results: list):
        """打印处理摘要"""
        print("\n" + "="*60)
        print("ROUTE PLAN PROCESSING SUMMARY")
        print("="*60)
        
        total_folders = len(results)
        successful_folders = sum(1 for r in results if r["success"])
        failed_folders = total_folders - successful_folders
        
        total_route_plans_generated = sum(1 for r in results if r["route_plan_generated"])
        total_qa_pairs_extracted = sum(r["qa_pairs_extracted"] for r in results)
        total_jsons_updated = sum(1 for r in results if r["json_updated"])
        total_time = sum(r["elapsed_time"] for r in results)
        
        print(f"Total folders processed: {total_folders}")
        print(f"Successful: {successful_folders}")
        print(f"Failed: {failed_folders}")
        print(f"Route plans generated: {total_route_plans_generated}")
        print(f"Total QA pairs extracted: {total_qa_pairs_extracted}")
        print(f"JSON files updated: {total_jsons_updated}")
        print(f"Total processing time: {total_time:.2f}s")
        
        if failed_folders > 0:
            print("\nFailed folders:")
            for result in results:
                if not result["success"]:
                    print(f"  - {result['folder']}: {', '.join(result['errors'])}")

def main():
    parser = argparse.ArgumentParser(description="批量处理数据文件夹的route_plan，并更新JSON文件")
    parser.add_argument("--data_root", default="data", help="数据根目录")
    
    args = parser.parse_args()
    
    processor = RoutePlanProcessor(args.data_root)
    results = processor.process_all_folders()
    processor.print_summary(results)

if __name__ == "__main__":
    main()
