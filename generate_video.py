#!/usr/bin/env python3
"""
视频生成脚本 - 将PNG图片序列合成为MP4视频
支持单个文件夹处理和批量处理
"""

import os
import argparse
from pathlib import Path
import cv2
import numpy as np
from typing import List
import logging
import time
import json
from concurrent.futures import ProcessPoolExecutor, as_completed

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_sorted_image_files(image_dir: Path) -> List[Path]:
    """获取排序后的图片文件列表"""
    image_files = []
    
    # 支持的图片格式
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    for file_path in image_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)
    
    # 按文件名排序（数字顺序）
    image_files.sort(key=lambda x: int(x.stem.split('_')[-1]) if x.stem.split('_')[-1].isdigit() else 0)
    
    return image_files

def create_video_from_images(image_dir: str, output_path: str, fps: int = 30, 
                           width: int = None, height: int = None, 
                           quality: int = 95) -> bool:
    """
    从图片序列创建MP4视频
    
    Args:
        image_dir: 图片目录路径
        output_path: 输出视频路径
        fps: 帧率
        width: 视频宽度（None表示使用原图宽度）
        height: 视频高度（None表示使用原图高度）
        quality: 视频质量（0-100）
    
    Returns:
        bool: 是否成功
    """
    image_dir_path = Path(image_dir)
    
    if not image_dir_path.exists():
        logger.error(f"图片目录不存在: {image_dir}")
        return False
    
    # 获取排序后的图片文件
    image_files = get_sorted_image_files(image_dir_path)
    
    if not image_files:
        logger.error(f"在目录 {image_dir} 中未找到图片文件")
        return False
    
    logger.info(f"找到 {len(image_files)} 个图片文件")
    
    # 读取第一张图片获取尺寸
    first_image = cv2.imread(str(image_files[0]))
    if first_image is None:
        logger.error(f"无法读取第一张图片: {image_files[0]}")
        return False
    
    # 确定视频尺寸
    if width is None:
        width = first_image.shape[1]
    if height is None:
        height = first_image.shape[0]
    
    logger.info(f"视频尺寸: {width}x{height}, 帧率: {fps} fps")
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        logger.error("无法创建视频写入器")
        return False
    
    try:
        for i, image_file in enumerate(image_files):
            # 读取图片
            img = cv2.imread(str(image_file))
            if img is None:
                logger.warning(f"无法读取图片: {image_file}")
                continue
            
            # 调整图片尺寸
            if img.shape[:2] != (height, width):
                img = cv2.resize(img, (width, height))
            
            # 写入视频
            out.write(img)
            
            # 显示进度
            if (i + 1) % 50 == 0 or i == len(image_files) - 1:
                logger.info(f"处理进度: {i + 1}/{len(image_files)}")
    
    except Exception as e:
        logger.error(f"处理图片时发生错误: {e}")
        return False
    
    finally:
        # 释放资源
        out.release()
    
    logger.info(f"视频生成完成: {output_path}")
    return True

def process_single_video(data_folder: str, output_dir: str, fps: int = 30, 
                        width: int = None, height: int = None) -> dict:
    """处理单个数据文件夹的视频生成"""
    start_time = time.time()
    
    # 构建图片目录路径
    image_dir = f"data/{data_folder}/annotation"
    
    # 构建输出路径
    output_path = Path(output_dir) / f"{data_folder}.mp4"
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        'folder': data_folder,
        'start_time': start_time,
        'success': False,
        'error': None,
        'output_path': str(output_path),
        'file_size_mb': 0
    }
    
    try:
        # 生成视频
        success = create_video_from_images(
            image_dir=image_dir,
            output_path=str(output_path),
            fps=fps,
            width=width,
            height=height
        )
        
        result['success'] = success
        
        if success:
            # 计算文件大小
            if output_path.exists():
                result['file_size_mb'] = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ 成功生成视频: {data_folder} ({result['file_size_mb']:.2f} MB)")
            else:
                result['error'] = "视频文件未生成"
        else:
            result['error'] = "视频生成失败"
            
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"处理文件夹 {data_folder} 时发生错误: {e}")
    
    result['end_time'] = time.time()
    result['duration'] = result['end_time'] - result['start_time']
    
    return result

def find_data_folders(data_root: str) -> List[str]:
    """查找所有包含annotation目录的数据文件夹"""
    data_folders = []
    data_root_path = Path(data_root)
    
    if not data_root_path.exists():
        logger.error(f"数据根目录不存在: {data_root}")
        return data_folders
    
    for item in data_root_path.iterdir():
        if item.is_dir():
            # 检查是否包含annotation目录
            annotation_dir = item / "annotation"
            if annotation_dir.exists():
                data_folders.append(item.name)
                logger.info(f"找到数据文件夹: {item.name}")
    
    logger.info(f"总共找到 {len(data_folders)} 个数据文件夹")
    return data_folders

def batch_generate_videos(data_root: str, output_dir: str, parallel: int = 1, 
                         fps: int = 30, width: int = None, height: int = None) -> List[dict]:
    """批量生成视频"""
    data_folders = find_data_folders(data_root)
    
    if not data_folders:
        logger.error("未找到任何数据文件夹")
        return []
    
    logger.info(f"开始批量生成视频，共 {len(data_folders)} 个文件夹")
    
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    results = []
    
    if parallel == 1:
        # 串行处理
        for folder in data_folders:
            result = process_single_video(folder, output_dir, fps, width, height)
            results.append(result)
    else:
        # 并行处理
        with ProcessPoolExecutor(max_workers=parallel) as executor:
            # 提交所有任务
            future_to_folder = {
                executor.submit(process_single_video, folder, output_dir, fps, width, height): folder 
                for folder in data_folders
            }
            
            # 收集结果
            for future in as_completed(future_to_folder):
                folder = future_to_folder[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"处理文件夹 {folder} 时发生异常: {e}")
                    results.append({
                        'folder': folder,
                        'success': False,
                        'error': str(e)
                    })
    
    # 保存处理结果
    save_batch_results(results, output_dir)
    
    # 打印统计信息
    print_batch_statistics(results)
    
    return results

def save_batch_results(results: List[dict], output_dir: str):
    """保存批量处理结果"""
    results_file = Path(output_dir) / "video_generation_results.json"
    
    # 转换时间戳为字符串以便JSON序列化
    serializable_results = []
    for result in results:
        serializable_result = result.copy()
        if 'start_time' in serializable_result:
            serializable_result['start_time'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(serializable_result['start_time'])
            )
        if 'end_time' in serializable_result:
            serializable_result['end_time'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(serializable_result['end_time'])
            )
        serializable_results.append(serializable_result)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"处理结果已保存到: {results_file}")

def print_batch_statistics(results: List[dict]):
    """打印批量处理统计信息"""
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    total_time = sum(r.get('duration', 0) for r in results)
    avg_time = total_time / total if total > 0 else 0
    
    total_size = sum(r.get('file_size_mb', 0) for r in results)
    
    logger.info("=" * 50)
    logger.info("批量视频生成统计信息:")
    logger.info(f"总文件夹数: {total}")
    logger.info(f"成功生成: {successful}")
    logger.info(f"生成失败: {failed}")
    logger.info(f"成功率: {successful/total*100:.1f}%")
    logger.info(f"总耗时: {total_time:.2f}秒")
    logger.info(f"平均耗时: {avg_time:.2f}秒/文件夹")
    logger.info(f"总文件大小: {total_size:.2f} MB")
    
    if failed > 0:
        logger.info("\n失败的文件夹:")
        for result in results:
            if not result['success']:
                logger.info(f"  - {result['folder']}: {result.get('error', '未知错误')}")
    
    logger.info("=" * 50)

def main():
    parser = argparse.ArgumentParser(description="从图片序列生成MP4视频")
    parser.add_argument("--mode", choices=['single', 'batch'], default='single', 
                       help="处理模式：single(单个文件夹) 或 batch(批量处理)")
    parser.add_argument("--data_folder", help="单个数据文件夹名称（如：20250820-151238）")
    parser.add_argument("--data_root", default="data", help="数据根目录（批量模式使用）")
    parser.add_argument("--output_dir", default="output_video", help="输出目录")
    parser.add_argument("--fps", type=int, default=30, help="视频帧率（默认：30）")
    parser.add_argument("--width", type=int, help="视频宽度（默认：使用原图宽度）")
    parser.add_argument("--height", type=int, help="视频高度（默认：使用原图高度）")
    parser.add_argument("--parallel", type=int, default=1, help="并行处理数量（批量模式使用）")
    
    args = parser.parse_args()
    
    if args.mode == 'single':
        if not args.data_folder:
            logger.error("单个模式需要指定 --data_folder 参数")
            return 1
        
        # 确保输出目录存在
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 处理单个文件夹
        result = process_single_video(
            data_folder=args.data_folder,
            output_dir=args.output_dir,
            fps=args.fps,
            width=args.width,
            height=args.height
        )
        
        if result['success']:
            logger.info("🎉 视频生成成功！")
            return 0
        else:
            logger.error("💥 视频生成失败！")
            return 1
    
    elif args.mode == 'batch':
        # 批量处理
        results = batch_generate_videos(
            data_root=args.data_root,
            output_dir=args.output_dir,
            parallel=args.parallel,
            fps=args.fps,
            width=args.width,
            height=args.height
        )
        
        successful = sum(1 for r in results if r['success'])
        if successful > 0:
            logger.info("🎉 批量视频生成完成！")
            return 0
        else:
            logger.error("💥 批量视频生成失败！")
            return 1

if __name__ == "__main__":
    exit(main())
