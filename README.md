
# 用于VQA数据生成的合成数据后处理工具包

## 项目概览

本项目，SynVSI标注工具包，旨在将从虚幻引擎（Unreal Engine）收集的原始3D空间数据，转换为结构化的视频问答（VQA）数据集。其主要目标是生成高质量的问答（Q&A）对，适用于训练和评估多模态大语言模型（MLLM）。

这些问答对的生成遵循一个源自VSI-Bench基准测试的分类体系，该体系专注于空间和时空理解能力。此分类体系将视觉空间问题分为以下几个关键领域：

*   **空间配置 (Configuration)**：理解对象的空间布局，包括：
    *   相对方向 (Relative Direction)
    *   相对距离 (Relative Distance)
    *   对象计数 (Object Count)
    *   路径规划 (Route Plan)
*   **测量 (Measurement)**：量化对象和空间的属性，例如：
    *   对象尺寸 (Object Size)
    *   房间大小 (Room Size)
    *   绝对距离 (Absolute Distance)
*   **时空 (Spatiotemporal)**：分析随时间变化的事件和对象状态，例如：
    *   出现顺序 (Appearance Order)

该工具包提供了一套脚本，用于处理原始数据、提取相关的空间和时间信息，并根据VSI-Bench分类体系生成相应的问答对，同时还提供了可选的场景可视化功能。

## 目录结构

-   `.gitignore`: 指定Git应忽略的、有意不进行跟踪的文件。
-   `0_data_cleanup_tool/`: 初始数据处理、丰富化和可视化。
-   `0_original_ue_anno/`: 存储原始的虚幻引擎标注数据及相关处理脚本（如帧提取）。
-   `m_absolute_distance_tool/`: 绝对距离计算与可视化。
-   `m_object_size_tool/`: 对象尺寸计算与可视化。
-   `m_room_size_tool/`: 房间大小计算与问答生成。
-   `c_object_count_tool/`: 对象计数与问答生成。
-   `c_relative_direction_tool/`: 相对方向分析与可视化。
-   `c_relative_distance_tool/`: 相对距离比较与可视化。
-   `c_route_plan_tool/`: 路径规划与问答生成。
-   `s_appearance_order_tool/`: 出现顺序分析与可视化。
-   `0_infer_and_score/`: 用于问答整合、模型推理和评分的占位目录。
-   `run_all.py`: 用于运行整个流程的脚本。

每个工具目录通常包含一个 `output/` 文件夹，用于存放生成的CSV文件和图像。

## 工具套件

该工具包由多个模块组成，每个模块针对VSI-Bench分类体系的特定方面，以生成多样化的问答对。这些工具按顺序处理数据，前一阶段的输出通常作为后一阶段的输入。

### 1. 数据清理与提取 (`0_data_cleanup_tool/`)

-   **功能**: 处理原始帧数据，清理名称，筛选对象，转换单位，并对对象进行排序。
-   **核心脚本**:
    -   `anno_extraction.py`: 清理、筛选、转换单位并对唯一的Actor（对象）进行排序。
    -   `2d_anno_visualization.py`: 生成Actor分布的2D俯视可视化图。
    -   `3d_anno_visualization.py`: 生成Actor分布的3D可视化图。
    -   *(可选)* `0_original_ue_anno/frame_extraction.py`: 从UE输出中提取并处理原始帧元数据（如果数据存在于 `0_original_ue_anno/` 中）。
-   **输入**:
    -   `anno_extraction.py` 需要UE的原始输出（例如 `Screenshot_summary.csv`）。
    -   可视化脚本需要 `0_data_cleanup_tool/output/ranked_unique_actor_anno.csv`。
-   **输出** (位于 `0_data_cleanup_tool/output/`):
    -   `ranked_unique_actor_anno.csv`: 清理并排序后的Actor元数据。
    -   `2d_anno_visualization.png`: 2D Actor分布图。
    -   `3d_anno_visualization.png`: 3D Actor分布图。

### 2. 绝对距离分析 (`m_absolute_distance_tool/`)

-   **功能**: 计算所有唯一对象对之间的最小距离，并生成相关的问答。
-   **核心脚本**:
    -   `absolute_distance_all.py`: 计算距离并生成问答。
    -   `absolute_distance_visual.py`: 可视化选定对象对的3D边界框和距离（需在脚本中设置 `POSSIBILITY_ID`）。
-   **输入**:
    -   `0_data_cleanup_tool/output/ranked_unique_actor_anno.csv`
-   **输出** (位于 `m_absolute_distance_tool/output/`):
    -   `absolute_distances_all.csv`: 所有计算出的距离、对象对和问答。
    -   `absolute_distance_visual.png` (如果运行了可视化脚本)。

### 3. 对象尺寸分析 (`m_object_size_tool/`)

-   **功能**: 计算对象的尺寸（如最长维度、体积），并生成相关的问答。
-   **核心脚本**:
    -   `object_size_all.py`: 计算对象尺寸并生成问答。
    -   `object_size_visual.py`: 可视化选定对象及其尺寸（需在脚本中设置 `POSSIBILITY_ID`）。
-   **输入**:
    -   `0_data_cleanup_tool/output/ranked_unique_actor_anno.csv`
-   **输出** (位于 `m_object_size_tool/output/`):
    -   `object_size_all.csv`: 计算出的对象尺寸和问答。
    -   `object_size_visual.png` (如果运行了可视化脚本)。

### 4. 房间大小分析 (`m_room_size_tool/`)

-   **功能**: 从JSON数据中提取房间尺寸，计算房间面积，并生成关于房间大小的问答。
-   **核心脚本**:
    -   `room_size_all.py`: 提取房间尺寸，计算面积，并生成问答。
-   **输入**:
    -   包含房间边界数据的JSON文件（例如，来自 `0_original_ue_anno/` 的 `result_Actor_BP_HDAGenenrator_C_UAID_*.json`）。
-   **输出** (位于 `m_room_size_tool/output/`):
    -   `room_size_all.csv`: 房间尺寸、面积和问答。

### 5. 对象计数分析 (`c_object_count_tool/`)

-   **功能**: 根据指定标准（如类型、位置）对对象进行计数，并生成相关的问答。
-   **核心脚本**:
    -   `object_count_all.py`: 执行计数并生成问答。
-   **输入**:
    -   `0_data_cleanup_tool/output/ranked_unique_actor_anno.csv`
-   **输出** (位于 `c_object_count_tool/output/`):
    -   `object_count_all.csv`: 对象计数结果和问答。
    -   *(如果开发了可视化脚本，可能会在此处添加)*

### 6. 相对方向分析 (`c_relative_direction_tool/`)

-   **功能**: 从观察者视角（站在一个对象处，面向另一个对象）确定目标对象的相对方向，并生成问答。
-   **核心脚本**:
    -   `relative_direction_all.py`: 计算Actor三元组的相对方向并生成问答。
    -   `relative_direction_visual.py`: 可视化选定的三元组（需在脚本中设置 `POSSIBILITY_ID`）。
-   **输入**:
    -   `0_data_cleanup_tool/output/ranked_unique_actor_anno.csv`
-   **输出** (位于 `c_relative_direction_tool/output/`):
    -   `relative_direction_all.csv`: 相对方向数据、Actors和问答。
    -   `relative_direction_visual.png` (如果运行了可视化脚本)。

### 7. 相对距离分析 (`c_relative_distance_tool/`)

-   **功能**: 对于一个主对象和几个选项对象，识别出最近的选项对象，并生成问答。
-   **核心脚本**:
    -   `relative_distance_all.py`: 使用预先计算的绝对距离，识别最近的对象并生成问答。
    -   `relative_distance_visual.py`: 在3D空间中可视化主对象和选项对象，并高亮显示最近的一个（需在脚本中设置 `POSSIBILITY_ID`）。
-   **输入**:
    -   `0_data_cleanup_tool/output/ranked_unique_actor_anno.csv`
    -   `m_absolute_distance_tool/output/absolute_distances_all.csv`
-   **输出** (位于 `c_relative_distance_tool/output/`):
    -   `relative_distance_all.csv`: 相对距离比较数据和问答。
    -   `relative_distance_visual.png` (如果运行了可视化脚本)。

### 8. 路径规划分析 (`c_route_plan_tool/`)

-   **功能**: 在起点、终点和可选的中间点之间生成复杂的路径导航场景，并创建关于所需转向方向的多项选择题。
-   **核心脚本**:
    -   `route_plan_all.py`: 识别有效路径，计算转向指令，生成多项选择问答。
    -   `route_plan_visual.py`: 可视化选定路径，包括Actor位置、路径、朝向和转向（需在脚本中设置 `POSSIBILITY_ID`）。
-   **输入**:
    -   `0_data_cleanup_tool/output/ranked_unique_actor_anno.csv`
    -   `m_absolute_distance_tool/output/absolute_distances_all.csv` (由 `route_plan_all.py` 内部用于距离检查)
-   **输出** (位于 `c_route_plan_tool/output/`):
    -   `route_plan_all.csv`: 路径规划数据、生成的问题、多项选择选项及答案。
    -   `route_plan_visual.png` (如果运行了可视化脚本)。

### 9. 出现顺序分析 (`s_appearance_order_tool/`)

-   **功能**: 根据对象首次出现的帧来确定其出现顺序，并生成关于该序列的问答。
-   **核心脚本**:
    -   `appearance_order_all.py`: 确定出现顺序并生成问答。
    -   `appearance_order_visual.py`: 可视化对象出现的时间线或序列（如适用，需设置 `POSSIBILITY_ID`）。
-   **输入**:
    -   `0_data_cleanup_tool/output/ranked_unique_actor_anno.csv`
-   **输出** (位于 `s_appearance_order_tool/output/`):
    -   `appearance_order_all.csv`: 对象出现顺序数据和问答。
    -   `appearance_order_visual.png` (如果运行了可视化脚本)。

### 10. 推理与评分 (`0_infer_and_score/`)

-   **功能**: (规划中) 整合所有生成工具产出的问答对，通过推理模型运行它们，并对结果进行评分。
-   **核心脚本**: (规划中)
    -   `qa_all.py`: 从各个 `_all.csv` 文件中收集并整合问答，形成统一格式。
    -   `infer_all.py`: 获取整合后的问答数据，运行推理（例如，使用预训练模型），并将结果与分数一同保存。
-   **输入**:
    -   来自其他工具目录的各种 `*_all.csv` 文件（例如 `absolute_distances_all.csv`, `relative_direction_all.csv`）。
    -   `infer_all.py` 需要整合后的问答文件（例如 `all_qa.csv`）。
-   **输出** (位于 `0_infer_and_score/output/`):
    -   `all_qa.csv` (或类似文件): 整合后的问答数据。
    -   `inference_results.csv` (或类似文件): 推理输出和分数。

## 快速入门
### 环境要求

-   Python 3.x
-   必需的 Python 包: `pandas`, `numpy`, `matplotlib`。
-   `0_infer_and_score/` 目录下的脚本（如果实现）可能需要额外的包（例如 `transformers`, `torch`）。请检查具体脚本的要求。

### 安装

1.  克隆本仓库。
2.  安装核心依赖包：
    ```bash
    pip install pandas numpy matplotlib
    ```
3.  如果需要运行推理，请安装额外的依赖包（实现后请参考 `0_infer_and_score/` 脚本中的导入）。

### 运行工具

1.  **输入数据**:
    -   对于初始处理脚本 `0_data_cleanup_tool/anno_extraction.py`，请确保您的原始数据（例如来自UE的 `Screenshot_summary.csv`）已正确放置，通常放在 `0_original_ue_anno/` 内的一个子目录中，并在运行时通过命令行参数指定该子目录。
    -   如果使用可选的 `0_original_ue_anno/frame_extraction.py`，请确保原始的UE帧元数据位于 `0_original_ue_anno/` 中。
    -   后续脚本通常使用前一阶段的输出，主要是 `0_data_cleanup_tool/output/ranked_unique_actor_anno.csv`。

2.  **文件路径**: 脚本使用相对路径，以确保在项目结构内的可移植性。

3.  **执行顺序 (`run_all.py`)**:
    -   `run_all.py` 脚本提供了一种自动执行整个流程的方法。它通常按以下顺序运行：
        1.  数据清理与丰富化 (`0_data_cleanup_tool/`)
        2.  测量类工具 (`m_*/`)
        3.  比较类工具 (`c_*/`)
        4.  序列类工具 (`s_*/`)
        5.  可视化脚本 (可选，由 `run_all.py` 中的 `ENABLE_VISUALIZATIONS` 控制)
        6.  推理脚本 (可选，由 `run_all.py` 中的 `ENABLE_INFERENCE_SCRIPTS` 控制)
    -   要运行整个流程：
        ```bash
        python3 run_all.py
        ```
    -   修改 `run_all.py` 文件顶部的布尔标志（如 `ENABLE_VISUALIZATIONS`, `ENABLE_INFERENCE_SCRIPTS`, `ENABLE_FRAME_EXTRACTION`）来控制可选步骤。

4.  **单独运行脚本**:
    -   进入脚本所在目录，并使用 Python 3 运行它。
        ```bash
        cd <tool_directory>
        python3 script_name.py
        ```
    -   示例：
        ```bash
        cd 0_data_cleanup_tool
        python3 anno_extraction.py --data_subdir <your_data_subdirectory_name>
        ```
    -   某些脚本可能接受命令行参数（例如 `--data_subdir`, `--min_frames`）。如果脚本使用了 `argparse`，可以查看脚本内容或使用 `-h` 或 `--help` 运行以获取帮助。

5.  **可视化脚本 (`*_visual.py`)**:
    -   这些脚本通常用于可视化由相应数据处理脚本生成的 `*_all.csv` 文件中的特定场景或数据点。
    -   您可能需要修改可视化脚本顶部的 `POSSIBILITY_ID`（或类似变量）来选择要可视化的CSV条目。
    -   输出通常是图像文件（如 `.png`），保存在工具的 `output/` 目录中，并且常常会直接显示在屏幕上。

6.  **输出**:
    -   在每个工具的文件夹内，检查 `output/` 子目录以获取生成的CSV文件（数据和问答）和图像文件（可视化结果）。