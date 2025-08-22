import os
import json
import pandas as pd
from pathlib import Path
from ast import literal_eval

class SimplifiedVQADatasetGenerator:
    def __init__(self, output_csv_root: str = "output_csv", output_json_root: str = "output_json"):
        self.output_csv_root = Path(output_csv_root)
        self.output_json_root = Path(output_json_root)
        self.output_json_root.mkdir(parents=True, exist_ok=True)
        
        # 定义CSV文件到JSON类别的映射
        self.csv_to_category = {
            "ranked_unique_actor_anno.csv": None,  # 这个文件不生成QA，只是基础数据
            "absolute_distances_all.csv": "m_absolute_distance",
            "object_size_all.csv": "m_object_size", 
            "room_size_all.csv": "m_room_size",
            "object_count_all.csv": "c_object_count",
            "relative_direction_all.csv": "c_relative_direction",
            "relative_distance_all.csv": "c_relative_distance",
            "route_plan_all.csv": "c_route_plan",
            "appearance_order_all.csv": "s_appearance_order"
        }
        
        # 仅对需要的题型保留难度
        self.difficulty_mapping = {
            "c_relative_direction": "hard",  # 该类会由专门方法细分三档
            "c_route_plan": "hard"
        }
        self.categories_with_difficulty = {"c_relative_direction", "c_route_plan"}

    def _parse_options(self, raw_val):
        """将CSV中的Options字段解析为列表。支持list对象或字符串形式。"""
        if raw_val is None or (isinstance(raw_val, float) and pd.isna(raw_val)):
            return None
        if isinstance(raw_val, list):
            return raw_val if len(raw_val) > 0 else None
        s = str(raw_val).strip()
        if not s:
            return None
        # 常见情况："['A. xxx', 'B. yyy']" -> 使用literal_eval安全解析
        try:
            parsed = literal_eval(s)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except Exception:
            pass
        # 若是以分隔符拼接的字符串，尝试用 ' ; ' 或 ',' 拆分
        if ";" in s:
            parts = [p.strip() for p in s.split(";") if p.strip()]
            return parts if parts else None
        if "," in s and s.count(".") >= 2:
            parts = [p.strip() for p in s.split(",") if p.strip()]
            return parts if parts else None
        return None

    def _merge_options_into_question(self, question: str, options_list) -> str:
        """将选项合并到问题末尾，格式：Question + 空格 + 'A. xxx B. yyy ...'"""
        if not options_list:
            return question
        opts = [str(o).strip() for o in options_list if str(o).strip()]
        if not opts:
            return question
        return f"{question} {' '.join(opts)}"

    def get_data_folders(self) -> list:
        """获取所有数据文件夹"""
        if not self.output_csv_root.exists():
            return []
        
        folders = []
        for item in self.output_csv_root.iterdir():
            if item.is_dir():
                folders.append(item.name)
        return folders

    def process_csv_to_qa_pairs(self, csv_path: Path, folder_name: str, category: str) -> list:
        """处理CSV文件并生成简化的QA对"""
        if not csv_path.exists():
            print(f"Warning: CSV file not found: {csv_path}")
            return []
        
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"Error reading CSV {csv_path}: {e}")
            return []
        
        qa_pairs = []
        
        if category == "c_relative_direction":
            # 特殊处理相对方向，因为它有三个难度层次
            qa_pairs.extend(self._process_relative_direction(df, folder_name))
        elif category == "s_appearance_order":
            # 特殊处理appearance_order，因为它有特殊的列结构
            qa_pairs.extend(self._process_appearance_order(df, folder_name))
        else:
            # 处理其他类别
            for index, row in df.iterrows():
                qa_pair = {
                    "video_id": folder_name,
                    "video_path": f"output_video/{folder_name}.mp4",
                    "question": row.get('Question', ''),
                    "answer": row.get('Answer', ''),
                    "question_type": category
                }
                # 仅指定题型保留难度
                if category in self.categories_with_difficulty:
                    default_diff = self.difficulty_mapping.get(category)
                    if default_diff:
                        qa_pair["difficulty"] = default_diff
                # 若存在通用 Options 列则合并到 question
                if 'Options' in row and pd.notna(row.get('Options')):
                    options = self._parse_options(row.get('Options'))
                    if options:
                        qa_pair['question'] = self._merge_options_into_question(qa_pair['question'], options)
                qa_pairs.append(qa_pair)
        
        return qa_pairs

    def _process_relative_direction(self, df: pd.DataFrame, folder_name: str) -> list:
        """特殊处理相对方向数据，因为它有三个难度层次"""
        qa_pairs = []
        
        for index, row in df.iterrows():
            # 处理Hard难度
            if pd.notna(row.get('QuestionHard')) and pd.notna(row.get('AnswerHard')):
                qa_pair = {
                    "video_id": folder_name,
                    "video_path": f"output_video/{folder_name}.mp4",
                    "question": row.get('QuestionHard', ''),
                    "answer": row.get('AnswerHard', ''),
                    "question_type": "c_relative_direction",
                    "difficulty": "hard"
                }
                if pd.notna(row.get('OptionsHard')):
                    options = self._parse_options(row.get('OptionsHard'))
                    if options:
                        qa_pair['question'] = self._merge_options_into_question(qa_pair['question'], options)
                qa_pairs.append(qa_pair)
            
            # 处理Medium难度
            if pd.notna(row.get('QuestionMedium')) and pd.notna(row.get('AnswerMedium')):
                qa_pair = {
                    "video_id": folder_name,
                    "video_path": f"output_video/{folder_name}.mp4",
                    "question": row.get('QuestionMedium', ''),
                    "answer": row.get('AnswerMedium', ''),
                    "question_type": "c_relative_direction",
                    "difficulty": "medium"
                }
                if pd.notna(row.get('OptionsMedium')):
                    options = self._parse_options(row.get('OptionsMedium'))
                    if options:
                        qa_pair['question'] = self._merge_options_into_question(qa_pair['question'], options)
                qa_pairs.append(qa_pair)
            
            # 处理Easy难度
            if pd.notna(row.get('QuestionEasy')) and pd.notna(row.get('AnswerEasy')):
                qa_pair = {
                    "video_id": folder_name,
                    "video_path": f"output_video/{folder_name}.mp4",
                    "question": row.get('QuestionEasy', ''),
                    "answer": row.get('AnswerEasy', ''),
                    "question_type": "c_relative_direction",
                    "difficulty": "easy"
                }
                if pd.notna(row.get('OptionsEasy')):
                    options = self._parse_options(row.get('OptionsEasy'))
                    if options:
                        qa_pair['question'] = self._merge_options_into_question(qa_pair['question'], options)
                qa_pairs.append(qa_pair)
        
        return qa_pairs

    def _process_appearance_order(self, df: pd.DataFrame, folder_name: str) -> list:
        """特殊处理appearance_order数据，从J列提取Question，K列提取Answer，L列提取Options"""
        qa_pairs = []
        
        for index, row in df.iterrows():
            # 从J列提取Question，K列提取Answer
            question = row.get('Question', '')
            answer = row.get('Answer', '')
            
            if pd.notna(question) and pd.notna(answer):
                qa_pair = {
                    "video_id": folder_name,
                    "video_path": f"output_video/{folder_name}.mp4",
                    "question": question,
                    "answer": answer,
                    "question_type": "s_appearance_order"
                }
                if 'Options' in row and pd.notna(row.get('Options')):
                    options = self._parse_options(row.get('Options'))
                    if options:
                        qa_pair['question'] = self._merge_options_into_question(qa_pair['question'], options)
                qa_pairs.append(qa_pair)
        
        return qa_pairs

    def generate_vqa_dataset(self, folder_name: str) -> dict:
        """为单个数据文件夹生成VQA数据集"""
        folder_path = self.output_csv_root / folder_name
        
        if not folder_path.exists():
            print(f"Warning: Data folder not found: {folder_path}")
            return {}
        
        all_qa_pairs = []
        
        # 处理每个CSV文件
        for csv_file, category in self.csv_to_category.items():
            if category is None:
                continue  # 跳过基础数据文件
                
            csv_path = folder_path / csv_file
            qa_pairs = self.process_csv_to_qa_pairs(csv_path, folder_name, category)
            all_qa_pairs.extend(qa_pairs)
        
        # 生成统计信息
        statistics = {
            "total_qa_pairs": len(all_qa_pairs),
            "by_difficulty": {},
            "by_category": {}
        }
        
        # 按难度统计（仅统计带有难度键的题目）
        for qa_pair in all_qa_pairs:
            if "difficulty" in qa_pair:
                difficulty = qa_pair["difficulty"]
                statistics["by_difficulty"][difficulty] = statistics["by_difficulty"].get(difficulty, 0) + 1
        
        # 按类别统计
        for qa_pair in all_qa_pairs:
            category = qa_pair.get("question_type", "unknown")
            statistics["by_category"][category] = statistics["by_category"].get(category, 0) + 1
        
        dataset = {
            "video_id": folder_name,
            "video_path": f"output_video/{folder_name}.mp4",
            "qa_pairs": all_qa_pairs,
            "statistics": statistics
        }
        
        return dataset

    def save_dataset(self, dataset: dict, folder_name: str):
        """保存数据集到JSON文件"""
        output_file = self.output_json_root / f"{folder_name}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"Saved dataset to: {output_file}")
        print(f"Total QA pairs: {dataset['statistics']['total_qa_pairs']}")

    def generate_all_datasets(self):
        """生成所有数据文件夹的VQA数据集"""
        data_folders = self.get_data_folders()
        
        if not data_folders:
            print("No data folders found in output_csv directory")
            return
        
        print(f"Found {len(data_folders)} data folders: {data_folders}")
        
        for folder_name in data_folders:
            print(f"\nProcessing folder: {folder_name}")
            dataset = self.generate_vqa_dataset(folder_name)
            
            if dataset:
                self.save_dataset(dataset, folder_name)
            else:
                print(f"No dataset generated for {folder_name}")

    def generate_summary(self):
        """生成总体统计摘要"""
        data_folders = self.get_data_folders()
        
        if not data_folders:
            return
        
        summary = {
            "total_folders": len(data_folders),
            "folders": [],
            "overall_statistics": {
                "total_qa_pairs": 0,
                "by_difficulty": {},
                "by_category": {}
            }
        }
        
        for folder_name in data_folders:
            json_file = self.output_json_root / f"{folder_name}.json"
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    dataset = json.load(f)
                
                folder_summary = {
                    "folder_name": folder_name,
                    "qa_pairs_count": dataset["statistics"]["total_qa_pairs"],
                    "by_difficulty": dataset["statistics"]["by_difficulty"],
                    "by_category": dataset["statistics"]["by_category"]
                }
                
                summary["folders"].append(folder_summary)
                
                # 累加总体统计
                summary["overall_statistics"]["total_qa_pairs"] += dataset["statistics"]["total_qa_pairs"]
                
                for difficulty, count in dataset["statistics"]["by_difficulty"].items():
                    summary["overall_statistics"]["by_difficulty"][difficulty] = \
                        summary["overall_statistics"]["by_difficulty"].get(difficulty, 0) + count
                
                for category, count in dataset["statistics"]["by_category"].items():
                    summary["overall_statistics"]["by_category"][category] = \
                        summary["overall_statistics"]["by_category"].get(category, 0) + count
        
        # 保存摘要
        summary_file = self.output_json_root / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummary saved to: {summary_file}")
        print(f"Total QA pairs across all folders: {summary['overall_statistics']['total_qa_pairs']}")

def main():
    generator = SimplifiedVQADatasetGenerator()
    generator.generate_all_datasets()
    generator.generate_summary()

if __name__ == "__main__":
    main()
