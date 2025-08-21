import os
import json
import random
import pandas as pd

"""
从 c_relative_direction_tool/output/relative_direction_all.csv 随机抽取若干条问答，
并生成符合指定格式的 JSON 文件。

可在下方修改配置：视频信息、抽样数量、随机种子、CSV 路径与输出路径。
"""

# ========= 可配置参数（便于修改） =========
VIDEO_ID = "video_001"
VIDEO_PATH = "videos/001.mp4"
NUM_QA_PAIRS = 10             # 生成多少条问答
RANDOM_SEED = 42              # 随机种子，方便复现/更改

# 输入 CSV（相对方向模块的输出）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(
    PROJECT_ROOT,
    "c_relative_direction_tool",
    "output",
    "relative_direction_all.csv",
)

# 输出 JSON 文件路径
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "0_infer_and_score", "output")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "relative_direction_qa.json")

# 题型字段（保持与示例一致，同时包含示例中的拼写字段）
QUESTION_TYPE = "c_relative_direction"


def build_question_text(row: pd.Series) -> str:
    """将第 L 列(QuestionHard) 与第 N 列(OptionsHard) 拼接为问题文本。"""
    q_raw = row.get("QuestionHard", None)
    opts_raw = row.get("OptionsHard", None)
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


def main():
    # 保证输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"找不到 CSV 文件：{CSV_FILE}")

    df = pd.read_csv(CSV_FILE)

    # 基础校验：需要 L/M/N 三列
    required_cols = ["QuestionHard", "AnswerHard", "OptionsHard"]
    for c in required_cols:
        if c not in df.columns:
            raise KeyError(f"CSV 缺少必要列：{c}")

    # 过滤无效行：题目/答案为空或选项为空列表
    df_valid = df[
        df["QuestionHard"].notna()
        & df["AnswerHard"].notna()
        & df["OptionsHard"].notna()
        & (df["OptionsHard"].astype(str).str.strip() != "[]")
        & (df["QuestionHard"].astype(str).str.strip() != "")
    ]

    # 抽样
    sampled = sample_rows(df_valid, NUM_QA_PAIRS, RANDOM_SEED)

    # 生成 qa_pairs
    qa_pairs = []
    # 生成 a, b, c ... 的尾标
    suffix_letters = [chr(ord('a') + i) for i in range(len(sampled))]

    for idx, (i, row) in enumerate(sampled.iterrows()):
        question_text = build_question_text(row)
        answer = str(row.get("AnswerHard", "")).strip()

        qa_pairs.append({
            "question_id": f"q_001{suffix_letters[idx]}",
            "question": question_text,
            "answer": answer,
            "question_type": QUESTION_TYPE,
        })

    result = {
        "video_id": VIDEO_ID,
        "video_path": VIDEO_PATH,
        "qa_pairs": qa_pairs,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"已生成 JSON：{OUTPUT_JSON}")


if __name__ == "__main__":
    main()


