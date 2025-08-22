#!/usr/bin/env python3
"""
从 output_json/{video_id}.json 中抽取题目，生成包含10道题的测验JSON：
1) 先对每个 question_type 抽取 1 题（若不足则跳过该类）
2) 智能补充题目以覆盖难度 hard/medium/easy（三种都至少各1道）
3) 若仍不足10题，则从剩余题库随机补足到10题（不重复）

用法：
  python sample_quiz_from_output_json.py --video_id 20250820-151238
  python sample_quiz_from_output_json.py --video_id 20250820-151433 --seed 42 --output output_json/custom_quiz.json
输出：
  默认写入 output_json/{video_id}_quiz10.json
"""

import os
import json
import random
import argparse
from pathlib import Path
from typing import Dict, List


def load_dataset(video_id: str) -> Dict:
    dataset_path = Path("output_json") / f"{video_id}.json"
    if not dataset_path.exists():
        raise FileNotFoundError(f"未找到数据集文件：{dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def group_by_category(qa_pairs: List[Dict]) -> Dict[str, List[Dict]]:
    cat2items: Dict[str, List[Dict]] = {}
    for item in qa_pairs:
        cat = item.get("question_type", "unknown")
        cat2items.setdefault(cat, []).append(item)
    return cat2items


def pick_one_per_category(cat2items: Dict[str, List[Dict]], rng: random.Random) -> List[Dict]:
    picked: List[Dict] = []
    for cat, items in cat2items.items():
        if not items:
            continue
        picked.append(rng.choice(items))
    return picked


def ensure_difficulty_coverage(all_items: List[Dict], current: List[Dict], rng: random.Random) -> List[Dict]:
    """补充题目以覆盖 hard/medium/easy 三种难度，每种至少1道。"""
    need = {"hard", "medium", "easy"}
    have = {q.get("difficulty", "").lower() for q in current}
    missing = [d for d in need if d not in have]
    if not missing:
        return []

    remaining = [q for q in all_items if q not in current]
    rng.shuffle(remaining)

    additions: List[Dict] = []
    for d in missing:
        cand = [q for q in remaining if str(q.get("difficulty", "")).lower() == d and q not in additions]
        if cand:
            additions.append(rng.choice(cand))
    return additions


def top_up_to_ten(all_items: List[Dict], current: List[Dict], rng: random.Random) -> List[Dict]:
    if len(current) >= 10:
        return []
    remaining = [q for q in all_items if q not in current]
    rng.shuffle(remaining)
    need_n = max(0, 10 - len(current))
    return remaining[:need_n]


def build_quiz(video_id: str, seed: int) -> List[Dict]:
    rng = random.Random(seed)
    dataset = load_dataset(video_id)
    qa_pairs: List[Dict] = dataset.get("qa_pairs", [])
    video_path = dataset.get("video_path", f"output_video/{video_id}.mp4")

    # 分组并先按类别各取一题
    cat2items = group_by_category(qa_pairs)
    picked = pick_one_per_category(cat2items, rng)

    # 覆盖难度
    picked += ensure_difficulty_coverage(qa_pairs, picked, rng)
    # 补足到10题
    picked += top_up_to_ten(qa_pairs, picked, rng)

    # 截断（以防万一）
    picked = picked[:10]

    # 生成的json结构改为与 output_json/20250820-151238_quiz10.json 类似
    # 扁平化结构：直接返回题目列表（每题包含 video_id 与 video_path）
    flat_questions: List[Dict] = []
    for q in picked:
        flat_questions.append({
            "video_id": video_id,
            "video_path": video_path,
            "question": q.get("question", ""),
            "answer": q.get("answer", ""),
            "question_type": q.get("question_type", ""),
            "difficulty": q.get("difficulty", "")
        })
    return flat_questions


def save_quiz(quiz: List[Dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(quiz, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="从 output_json/{video_id}.json 抽样生成10题测验JSON")
    parser.add_argument("--video_id", required=True, help="数据文件夹名称，如 20250820-151238")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--output", help="输出文件路径，默认 output_json/{video_id}_quiz10.json")
    args = parser.parse_args()

    quiz = build_quiz(args.video_id, args.seed)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path("output_json") / f"{args.video_id}_quiz10.json"

    save_quiz(quiz, out_path)
    print(f"已生成测验文件：{out_path}")


if __name__ == "__main__":
    main()


