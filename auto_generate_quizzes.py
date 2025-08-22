#!/usr/bin/env python3
"""
自动为所有数据包生成测验脚本

功能：
1. 扫描 output_json/ 目录下的所有数据包JSON文件
2. 自动为每个数据包生成10题测验
3. 支持自定义随机种子和输出目录

使用方法：
    python auto_generate_quizzes.py                    # 使用默认设置
    python auto_generate_quizzes.py --seed 123        # 指定随机种子
    python auto_generate_quizzes.py --output_dir custom_quizzes  # 指定输出目录
"""

import os
import subprocess
import argparse
from pathlib import Path
from typing import List


def get_data_packages() -> List[str]:
    """获取所有数据包名称（排除测验文件和汇总文件）"""
    output_json_dir = Path("output_json")
    if not output_json_dir.exists():
        print("错误：output_json 目录不存在")
        return []
    
    data_packages = []
    for file_path in output_json_dir.iterdir():
        if file_path.is_file() and file_path.suffix == '.json':
            filename = file_path.name
            # 排除测验文件和汇总文件
            if not filename.endswith('_quiz10.json') and filename != 'summary.json':
                package_name = filename.replace('.json', '')
                data_packages.append(package_name)
    
    return sorted(data_packages)


def generate_quiz_for_package(package_name: str, seed: int, output_dir: str = None) -> bool:
    """为单个数据包生成测验"""
    try:
        cmd = ['python', 'sample_quiz_from_output_json.py', '--video_id', package_name, '--seed', str(seed)]
        
        if output_dir:
            output_path = Path(output_dir) / f"{package_name}_quiz10.json"
            cmd.extend(['--output', str(output_path)])
        
        print(f"正在为 {package_name} 生成测验...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ {package_name} 测验生成成功")
            return True
        else:
            print(f"❌ {package_name} 测验生成失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ {package_name} 测验生成超时")
        return False
    except Exception as e:
        print(f"❌ {package_name} 测验生成出错: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="自动为所有数据包生成测验")
    parser.add_argument("--seed", type=int, default=42, help="随机种子（默认：42）")
    parser.add_argument("--output_dir", help="输出目录（默认：output_json）")
    parser.add_argument("--parallel", type=int, default=1, help="并行处理数量（默认：1）")
    
    args = parser.parse_args()
    
    # 获取所有数据包
    data_packages = get_data_packages()
    
    if not data_packages:
        print("未找到任何数据包文件")
        return
    
    print(f"找到 {len(data_packages)} 个数据包：{data_packages}")
    print(f"使用随机种子：{args.seed}")
    if args.output_dir:
        print(f"输出目录：{args.output_dir}")
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # 生成测验
    success_count = 0
    failed_count = 0
    
    if args.parallel == 1:
        # 串行处理
        for package in data_packages:
            if generate_quiz_for_package(package, args.seed, args.output_dir):
                success_count += 1
            else:
                failed_count += 1
    else:
        # 并行处理
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
            future_to_package = {
                executor.submit(generate_quiz_for_package, package, args.seed, args.output_dir): package
                for package in data_packages
            }
            
            for future in concurrent.futures.as_completed(future_to_package):
                package = future_to_package[future]
                try:
                    if future.result():
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    print(f"❌ {package} 处理异常: {str(e)}")
                    failed_count += 1
    
    # 打印统计信息
    print("\n" + "="*50)
    print("测验生成统计")
    print("="*50)
    print(f"总数据包数：{len(data_packages)}")
    print(f"成功生成：{success_count}")
    print(f"生成失败：{failed_count}")
    print(f"成功率：{success_count/len(data_packages)*100:.1f}%")
    
    if failed_count > 0:
        print("\n失败的数据包可能需要检查：")
        print("- 确保对应的JSON文件存在且格式正确")
        print("- 检查是否有足够的QA对用于生成测验")


if __name__ == "__main__":
    main()
