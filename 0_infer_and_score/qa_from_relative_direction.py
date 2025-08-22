import os
import json
import random
import pandas as pd

"""
从 output_csv/数据文件夹名称/relative_direction_all.csv 随机抽取若干条问答，
并生成符合指定格式的 JSON 文件。

支持三个难度层次：Hard、Medium、Easy
可在下方修改配置：视频信息、抽样数量、随机种子、CSV 路径与输出路径。
"""

# ========= 可配置参数（便于修改） =========
VIDEO_ID = "video_001"
VIDEO_PATH = "videos/001.mp4"
NUM_QA_PAIRS_PER_LEVEL = 10  # 每个难度层次生成多少条问答
RANDOM_SEED = 42              # 随机种子，方便复现/更改

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

# 输入 CSV（相对方向模块的输出）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_folder_name = get_data_folder_name()
CSV_FILE = os.path.join(
    PROJECT_ROOT,
    "output_csv",
    data_folder_name,
    "relative_direction_all.csv",
)

# 输出 JSON 文件路径
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output_json", data_folder_name)
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "relative_direction_qa.json")

# 题型字段（保持与示例一致，同时包含示例中的拼写字段）
QUESTION_TYPE = "c_relative_direction"

# 定义三个难度层次的列名
DIFFICULTY_LEVELS = {
    "hard": {
        "question": "QuestionHard",
        "answer": "AnswerHard", 
        "options": "OptionsHard"
    },
    "medium": {
        "question": "QuestionMedium",
        "answer": "AnswerMedium",
        "options": "OptionsMedium"
    },
    "easy": {
        "question": "QuestionEasy",
        "answer": "AnswerEasy", 
        "options": "OptionsEasy"
    }
}


def build_question_text(row: pd.Series, difficulty: str) -> str:
    """将问题与选项拼接为问题文本。"""
    level_cols = DIFFICULTY_LEVELS[difficulty]
    q_raw = row.get(level_cols["question"], None)
    opts_raw = row.get(level_cols["options"], None)
    q = "" if pd.isna(q_raw) else str(q_raw).strip()
    opts = "" if pd.isna(opts_raw) else str(opts_raw).strip()
    # 与示例格式一致：问题 + 选项列表字符串
    return f"{q}{opts}" if opts else q


def sample_rows(df: pd.DataFrame, k: int, seed: int) -> pd.DataFrame:
    """随机抽样 k 条（不放回）。若样本不足则取全部。"""
    if df.empty:
        return df
    k = min(k, len(df))
    return df.sample(n=k, random_state=seed)


def process_difficulty_level(df: pd.DataFrame, difficulty: str, num_pairs: int, seed: int) -> list:
    """处理指定难度层次的问题。"""
    level_cols = DIFFICULTY_LEVELS[difficulty]
    
    # 过滤该难度层次的有效行
    df_valid = df[
        df[level_cols["question"]].notna()
        & df[level_cols["answer"]].notna()
        & df[level_cols["options"]].notna()
        & (df[level_cols["options"]].astype(str).str.strip() != "[]")
        & (df[level_cols["question"]].astype(str).str.strip() != "")
    ]
    
    if df_valid.empty:
        print(f"警告：{difficulty} 难度层次没有有效数据")
        return []
    
    # 抽样
    sampled = sample_rows(df_valid, num_pairs, seed)
    
    # 生成 qa_pairs
    qa_pairs = []
    suffix_letters = [chr(ord('a') + i) for i in range(len(sampled))]
    
    for idx, (i, row) in enumerate(sampled.iterrows()):
        question_text = build_question_text(row, difficulty)
        answer = str(row.get(level_cols["answer"], "")).strip()
        
        qa_pairs.append({
            "question_id": f"q_001{difficulty[0].upper()}{suffix_letters[idx]}",  # 例如：q_001Ha, q_001Mb, q_001Ec
            "question": question_text,
            "answer": answer,
            "question_type": QUESTION_TYPE,
            "difficulty": difficulty  # 添加难度标识
        })
    
    return qa_pairs


def main():
    # 保证输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"找不到 CSV 文件：{CSV_FILE}")

    df = pd.read_csv(CSV_FILE)

    # 基础校验：检查所有难度层次的必要列
    all_required_cols = []
    for level_cols in DIFFICULTY_LEVELS.values():
        all_required_cols.extend([level_cols["question"], level_cols["answer"], level_cols["options"]])
    
    for c in all_required_cols:
        if c not in df.columns:
            raise KeyError(f"CSV 缺少必要列：{c}")

    # 处理所有难度层次
    all_qa_pairs = []
    
    for difficulty in DIFFICULTY_LEVELS.keys():
        print(f"处理 {difficulty} 难度层次...")
        qa_pairs = process_difficulty_level(df, difficulty, NUM_QA_PAIRS_PER_LEVEL, RANDOM_SEED)
        all_qa_pairs.extend(qa_pairs)
        print(f"  - 生成了 {len(qa_pairs)} 条问答对")

    result = {
        "video_id": VIDEO_ID,
        "video_path": VIDEO_PATH,
        "qa_pairs": all_qa_pairs,
        "statistics": {
            "total_qa_pairs": len(all_qa_pairs),
            "by_difficulty": {
                difficulty: len([q for q in all_qa_pairs if q.get("difficulty") == difficulty])
                for difficulty in DIFFICULTY_LEVELS.keys()
            }
        }
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"已生成 JSON：{OUTPUT_JSON}")
    print(f"总计生成 {len(all_qa_pairs)} 条问答对")
    for difficulty, count in result["statistics"]["by_difficulty"].items():
        print(f"  - {difficulty}: {count} 条")


if __name__ == "__main__":
    main()


