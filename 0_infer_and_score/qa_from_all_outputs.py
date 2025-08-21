import os
import json
import random
import pandas as pd

"""
统一从各模块 output CSV 抽样问答并分别生成 JSON：
 - m_absolute_distance_tool/output/absolute_distances_all.csv => m_absolute_distance.json
 - m_object_size_tool/output/object_size_all.csv => m_object_size.json
 - m_room_size_tool/output/room_size_all.csv => m_room_size.json （若不存在则跳过）
 - c_object_count_tool/output/object_counts_all.csv => c_object_count.json （若不存在则跳过，注意文件名可能为 object_count_all.csv）
 - c_relative_direction_tool/output/relative_direction_all.csv => c_relative_direction.json
 - c_relative_distance_tool/output/relative_distance_all.csv => c_relative_distance.json
 - c_route_plan_tool/output/route_plan_all.csv => c_route_plan.json
 - s_appearance_order_tool/output/appearance_order_all.csv => s_appearance_order.json

可配置项见脚本顶部：视频信息、每模块抽样数量、随机种子。
"""

# ===== 可配置参数 =====
VIDEO_ID = "video_001"
VIDEO_PATH = "videos/001.mp4"
NUM_QA_PER_MODULE = 10
RANDOM_SEED = 123

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "0_infer_and_score", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def sample_rows(df: pd.DataFrame, k: int, seed: int) -> pd.DataFrame:
    if df.empty:
        return df
    k = min(k, len(df))
    return df.sample(n=k, random_state=seed)


def to_json(video_id: str, video_path: str, qa_pairs: list) -> dict:
    return {
        "video_id": video_id,
        "video_path": video_path,
        "qa_pairs": qa_pairs,
    }


def make_ids(prefix: str, n: int):
    return [f"q_{prefix}{chr(ord('a') + i)}" for i in range(n)]


def process_absolute_distance():
    path = os.path.join(PROJECT_ROOT, "m_absolute_distance_tool", "output", "absolute_distances_all.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = ["Question", "Answer"]
    if not all(c in df.columns for c in required):
        return None
    df = df[df["Question"].notna() & df["Answer"].notna()]
    df_s = sample_rows(df, NUM_QA_PER_MODULE, RANDOM_SEED)
    ids = make_ids("abs_", len(df_s))
    qa = []
    for (i, row), qid in zip(df_s.iterrows(), ids):
        qa.append({
            "question_id": qid,
            "question": str(row["Question"]).strip(),
            "answer": str(row["Answer"]).strip(),
            "question_type": "m_absolute_distance",
        })
    return to_json(VIDEO_ID, VIDEO_PATH, qa)


def process_object_size():
    path = os.path.join(PROJECT_ROOT, "m_object_size_tool", "output", "object_size_all.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = ["Question", "Answer"]
    if not all(c in df.columns for c in required):
        return None
    df = df[df["Question"].notna() & df["Answer"].notna()]
    df_s = sample_rows(df, NUM_QA_PER_MODULE, RANDOM_SEED)
    ids = make_ids("size_", len(df_s))
    qa = []
    for (i, row), qid in zip(df_s.iterrows(), ids):
        qa.append({
            "question_id": qid,
            "question": str(row["Question"]).strip(),
            "answer": str(row["Answer"]).strip(),
            "question_type": "m_object_size",
        })
    return to_json(VIDEO_ID, VIDEO_PATH, qa)


def process_room_size():
    path = os.path.join(PROJECT_ROOT, "m_room_size_tool", "output", "room_size_all.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = ["Question", "Answer"]
    if not all(c in df.columns for c in required):
        return None
    df = df[df["Question"].notna() & df["Answer"].notna()]
    df_s = sample_rows(df, NUM_QA_PER_MODULE, RANDOM_SEED)
    ids = make_ids("room_", len(df_s))
    qa = []
    for (i, row), qid in zip(df_s.iterrows(), ids):
        qa.append({
            "question_id": qid,
            "question": str(row["Question"]).strip(),
            "answer": str(row["Answer"]).strip(),
            "question_type": "m_room_size",
        })
    return to_json(VIDEO_ID, VIDEO_PATH, qa)


def process_object_count():
    # 文件名可能为 object_counts_all.csv 或 object_count_all.csv（脚本写入为 object_counts_all.csv）
    p1 = os.path.join(PROJECT_ROOT, "c_object_count_tool", "output", "object_counts_all.csv")
    p2 = os.path.join(PROJECT_ROOT, "c_object_count_tool", "output", "object_count_all.csv")
    path = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
    if not path:
        return None
    df = pd.read_csv(path)
    required = ["Question", "Answer"]
    if not all(c in df.columns for c in required):
        return None
    df = df[df["Question"].notna() & df["Answer"].notna()]
    df_s = sample_rows(df, NUM_QA_PER_MODULE, RANDOM_SEED)
    ids = make_ids("count_", len(df_s))
    qa = []
    for (i, row), qid in zip(df_s.iterrows(), ids):
        qa.append({
            "question_id": qid,
            "question": str(row["Question"]).strip(),
            "answer": str(row["Answer"]).strip(),
            "question_type": "c_object_count",
        })
    return to_json(VIDEO_ID, VIDEO_PATH, qa)


def process_relative_direction():
    path = os.path.join(PROJECT_ROOT, "c_relative_direction_tool", "output", "relative_direction_all.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = ["QuestionHard", "AnswerHard", "OptionsHard"]
    if not all(c in df.columns for c in required):
        return None
    df = df[df["QuestionHard"].notna() & df["AnswerHard"].notna() & df["OptionsHard"].notna() & (df["OptionsHard"].astype(str).str.strip() != "[]")]
    df_s = sample_rows(df, NUM_QA_PER_MODULE, RANDOM_SEED)
    ids = make_ids("reldir_", len(df_s))
    qa = []
    for (i, row), qid in zip(df_s.iterrows(), ids):
        q = str(row["QuestionHard"]).strip() + str(row["OptionsHard"]).strip()
        qa.append({
            "question_id": qid,
            "question": q,
            "answer": str(row["AnswerHard"]).strip(),
            "question_type": "c_relative_direction",
        })
    return to_json(VIDEO_ID, VIDEO_PATH, qa)


def process_relative_distance():
    path = os.path.join(PROJECT_ROOT, "c_relative_distance_tool", "output", "relative_distance_all.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = ["Question", "Answer", "Options"]
    if not all(c in df.columns for c in required):
        return None
    df = df[df["Question"].notna() & df["Answer"].notna() & df["Options"].notna() & (df["Options"].astype(str).str.strip() != "[]")]
    df_s = sample_rows(df, NUM_QA_PER_MODULE, RANDOM_SEED)
    ids = make_ids("reldist_", len(df_s))
    qa = []
    for (i, row), qid in zip(df_s.iterrows(), ids):
        q = str(row["Question"]).strip() + str(row["Options"]).strip()
        qa.append({
            "question_id": qid,
            "question": q,
            "answer": str(row["Answer"]).strip(),
            "question_type": "c_relative_distance",
        })
    return to_json(VIDEO_ID, VIDEO_PATH, qa)


def process_route_plan():
    path = os.path.join(PROJECT_ROOT, "c_route_plan_tool", "output", "route_plan_all.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = ["Question", "Answer", "Options"]
    if not all(c in df.columns for c in required):
        return None
    df = df[df["Question"].notna() & df["Answer"].notna() & df["Options"].notna() & (df["Options"].astype(str).str.strip() != "[]")]
    df_s = sample_rows(df, NUM_QA_PER_MODULE, RANDOM_SEED)
    ids = make_ids("route_", len(df_s))
    qa = []
    for (i, row), qid in zip(df_s.iterrows(), ids):
        q = str(row["Question"]).strip() + str(row["Options"]).strip()
        qa.append({
            "question_id": qid,
            "question": q,
            "answer": str(row["Answer"]).strip(),
            "question_type": "c_route_plan",
        })
    return to_json(VIDEO_ID, VIDEO_PATH, qa)


def process_appearance_order():
    path = os.path.join(PROJECT_ROOT, "s_appearance_order_tool", "output", "appearance_order_all.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    required = ["Question", "Answer", "Options"]
    if not all(c in df.columns for c in required):
        return None
    df = df[df["Question"].notna() & df["Answer"].notna() & df["Options"].notna() & (df["Options"].astype(str).str.strip() != "[]")]
    df_s = sample_rows(df, NUM_QA_PER_MODULE, RANDOM_SEED)
    ids = make_ids("appear_", len(df_s))
    qa = []
    for (i, row), qid in zip(df_s.iterrows(), ids):
        q = str(row["Question"]).strip() + str(row["Options"]).strip()
        qa.append({
            "question_id": qid,
            "question": q,
            "answer": str(row["Answer"]).strip(),
            "question_type": "s_appearance_order",
        })
    return to_json(VIDEO_ID, VIDEO_PATH, qa)


def save_json(obj: dict, filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"已生成：{path}")


def main():
    makers = [
        (process_absolute_distance, "m_absolute_distance.json"),
        (process_object_size, "m_object_size.json"),
        (process_room_size, "m_room_size.json"),
        (process_object_count, "c_object_count.json"),
        (process_relative_direction, "c_relative_direction.json"),
        (process_relative_distance, "c_relative_distance.json"),
        (process_route_plan, "c_route_plan.json"),
        (process_appearance_order, "s_appearance_order.json"),
    ]
    for maker, filename in makers:
        try:
            data = maker()
            if data and data.get("qa_pairs"):
                save_json(data, filename)
            else:
                print(f"跳过：{filename}（无数据或文件不存在）")
        except Exception as e:
            print(f"生成 {filename} 失败：{e}")


if __name__ == "__main__":
    main()


