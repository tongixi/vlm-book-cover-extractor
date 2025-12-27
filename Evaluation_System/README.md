# 书籍封面描述评估系统

基于Web的人工评估界面，用于评估AI生成的书籍封面描述质量。

## 评估指标

### 1. 事实准确性 (Factual Correctness, FC)
- **定义**: 评估模型是否存在"幻觉"，即生成的描述是否包含封面中不存在的物体、颜色或文字错误
- **评分方式**: 二元判定
  - 满意 (S): 无任何事实性错误
  - 不满意 (U): 存在与图像不符的描述
- **计算公式**: FC = N_S / N_total × 100%

### 2. 语义完整性 (Semantic Completeness, SC)
- **定义**: 评估模型是否充分捕捉封面的关键视觉要素
- **评分维度**:
  1. 色彩基调（冷暖色、主色调）
  2. 构图布局（居中、留白、图文位置）
  3. 图像元素（人物、物体、背景纹理）
  4. 风格氛围（复古、极简、恐怖等）
- **评分方式**: 3分制
  - 3分（优秀）: 涵盖全部4个维度，描述详尽
  - 2分（良好）: 涵盖全维度但描述较笼统
  - 1分（较差）: 仅提及1个维度或相关性低
- **计算公式**: SC = (1/N) × Σ SC_i

## 安装与运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 目录结构
确保项目结构如下：
```
project_root/
├── book_covers/
│   ├── normal/
│   │   ├── 0001.png
│   │   ├── 0001.json
│   │   ├── 0002.png
│   │   ├── 0002.json
│   │   └── ...
│   └── art/
│       └── ...
└── Evaluation_System/
    ├── app.py
    ├── templates/
    │   ├── index.html
    │   ├── evaluate.html
    │   └── statistics.html
    ├── requirements.txt
    └── README.md
```

### 3. 运行系统
```bash
cd templates
python app.py
```

### 4. 访问系统
打开浏览器访问: http://localhost:5000

## 功能特点

1. **随机抽取**: 系统随机抽取未评估的图片进行评估
2. **进度追踪**: 实时显示评估进度
3. **多评估员支持**: 支持多人同时评估，记录每位评估员的贡献
4. **数据持久化**: 
   - 评估结果保存到 `evaluation_data.json`
   - 同时更新原始JSON文件中的 `human_evaluations` 字段
5. **统计分析**: 提供FC和SC指标的实时统计

## 数据格式

### 评估结果格式 (保存到原JSON文件)
```json
{
    "human_evaluations": [
        {
            "evaluator": "张三",
            "timestamp": "2024-01-15T10:30:00",
            "factual_correctness": "S",
            "semantic_completeness": 3,
            "sc_details": {
                "color": true,
                "layout": true,
                "elements": true,
                "style": true
            },
            "comments": "描述准确完整"
        }
    ]
}
```

## 配置

如需修改书籍封面目录路径，请编辑 `app.py` 中的 `BOOK_COVERS_DIR` 变量。

## 注意事项

1. 确保每张图片都有对应的同名JSON文件
2. JSON文件需为UTF-8编码
3. 建议在评估前先熟悉评估标准
