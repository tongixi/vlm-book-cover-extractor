"""
书籍封面描述评估系统
基于Web的人工评估界面，用于评估AI生成的书籍封面描述
评估指标：
1. 事实准确性 (Factual Correctness, FC) - 二元判定
2. 语义完整性 (Semantic Completeness, SC) - 3分制
"""

import os
import json
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'book_cover_evaluation_secret_key_2024'

# 配置路径 - 可根据实际项目路径修改
BASE_DIR = Path(__file__).parent.parent
BOOK_COVERS_DIR = BASE_DIR / 'book_covers'
EVALUATION_DATA_FILE = Path(__file__).parent / 'evaluation_data.json'

def get_all_samples():
    """获取所有待评估的样本（图片和对应的JSON描述）"""
    samples = []
    
    # 遍历book_covers下的所有子目录
    for category_dir in BOOK_COVERS_DIR.iterdir():
        if category_dir.is_dir():
            category = category_dir.name
            # 查找所有png文件
            for img_file in category_dir.glob('*.png'):
                json_file = img_file.with_suffix('.json')
                if json_file.exists():
                    # 读取JSON描述
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            description_data = json.load(f)
                        
                        sample = {
                            'id': f"{category}/{img_file.stem}",
                            'category': category,
                            'image_path': str(img_file.relative_to(BASE_DIR)),
                            'json_path': str(json_file.relative_to(BASE_DIR)),
                            'description_data': description_data,
                            'image_name': img_file.name
                        }
                        samples.append(sample)
                    except Exception as e:
                        print(f"读取 {json_file} 失败: {e}")
    
    return samples

def load_evaluation_data():
    """加载评估数据"""
    if EVALUATION_DATA_FILE.exists():
        with open(EVALUATION_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'evaluations': {}, 'evaluators': {}}

def save_evaluation_data(data):
    """保存评估数据"""
    with open(EVALUATION_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_json_with_evaluation(json_path, evaluation, evaluator_name):
    """将评分结果更新到原始JSON文件"""
    full_path = BASE_DIR / json_path
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 初始化评估字段
        if 'human_evaluations' not in data:
            data['human_evaluations'] = []
        
        # 添加新评估
        eval_record = {
            'evaluator': evaluator_name,
            'timestamp': datetime.now().isoformat(),
            'factual_correctness': evaluation['fc'],
            'semantic_completeness': evaluation['sc'],
            'sc_details': evaluation.get('sc_details', {}),
            'comments': evaluation.get('comments', '')
        }
        data['human_evaluations'].append(eval_record)
        
        # 保存回文件
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"更新JSON文件失败: {e}")
        return False

@app.route('/')
def index():
    """首页 - 登录/注册评估员"""
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """评估员登录"""
    evaluator_name = request.form.get('evaluator_name', '').strip()
    if not evaluator_name:
        return jsonify({'success': False, 'message': '请输入评估员姓名'})
    
    session['evaluator_name'] = evaluator_name
    
    # 记录评估员信息
    eval_data = load_evaluation_data()
    if evaluator_name not in eval_data['evaluators']:
        eval_data['evaluators'][evaluator_name] = {
            'first_login': datetime.now().isoformat(),
            'evaluation_count': 0
        }
    eval_data['evaluators'][evaluator_name]['last_login'] = datetime.now().isoformat()
    save_evaluation_data(eval_data)
    
    return jsonify({'success': True, 'redirect': url_for('evaluate')})

@app.route('/evaluate')
def evaluate():
    """评估页面"""
    if 'evaluator_name' not in session:
        return redirect(url_for('index'))
    
    evaluator_name = session['evaluator_name']
    samples = get_all_samples()
    eval_data = load_evaluation_data()
    
    # 获取当前评估员已评估的样本
    evaluated_ids = set()
    for sample_id, evals in eval_data['evaluations'].items():
        for e in evals:
            if e['evaluator'] == evaluator_name:
                evaluated_ids.add(sample_id)
    
    # 筛选未评估的样本
    unevaluated = [s for s in samples if s['id'] not in evaluated_ids]
    
    # 随机选择一个未评估的样本
    if unevaluated:
        random.shuffle(unevaluated)
        current_sample = unevaluated[0]
    else:
        current_sample = None
    
    progress = {
        'total': len(samples),
        'evaluated': len(evaluated_ids),
        'remaining': len(unevaluated)
    }
    
    return render_template('evaluate.html', 
                         sample=current_sample,
                         evaluator_name=evaluator_name,
                         progress=progress)

@app.route('/submit_evaluation', methods=['POST'])
def submit_evaluation():
    """提交评估结果"""
    if 'evaluator_name' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    evaluator_name = session['evaluator_name']
    data = request.json
    
    sample_id = data.get('sample_id')
    json_path = data.get('json_path')
    fc = data.get('fc')  # 'S' or 'U'
    sc = data.get('sc')  # 1, 2, or 3
    sc_details = data.get('sc_details', {})
    comments = data.get('comments', '')
    
    if not all([sample_id, fc, sc]):
        return jsonify({'success': False, 'message': '请完成所有评估项'})
    
    evaluation = {
        'evaluator': evaluator_name,
        'timestamp': datetime.now().isoformat(),
        'fc': fc,
        'sc': int(sc),
        'sc_details': sc_details,
        'comments': comments
    }
    
    # 保存到评估数据文件
    eval_data = load_evaluation_data()
    if sample_id not in eval_data['evaluations']:
        eval_data['evaluations'][sample_id] = []
    eval_data['evaluations'][sample_id].append(evaluation)
    
    # 更新评估员统计
    eval_data['evaluators'][evaluator_name]['evaluation_count'] = \
        eval_data['evaluators'][evaluator_name].get('evaluation_count', 0) + 1
    
    save_evaluation_data(eval_data)
    
    # 更新原始JSON文件
    if json_path:
        update_json_with_evaluation(json_path, evaluation, evaluator_name)
    
    return jsonify({'success': True, 'message': '评估已保存'})

@app.route('/statistics')
def statistics():
    """统计页面"""
    if 'evaluator_name' not in session:
        return redirect(url_for('index'))
    
    eval_data = load_evaluation_data()
    samples = get_all_samples()
    
    # 计算FC和SC指标
    all_evaluations = []
    for sample_id, evals in eval_data['evaluations'].items():
        all_evaluations.extend(evals)
    
    if all_evaluations:
        # FC: 满意样本占比
        fc_satisfied = sum(1 for e in all_evaluations if e['fc'] == 'S')
        fc_total = len(all_evaluations)
        fc_score = fc_satisfied / fc_total if fc_total > 0 else 0
        
        # SC: 平均得分
        sc_scores = [e['sc'] for e in all_evaluations]
        sc_avg = sum(sc_scores) / len(sc_scores) if sc_scores else 0
    else:
        fc_score = 0
        sc_avg = 0
        fc_satisfied = 0
        fc_total = 0
    
    stats = {
        'total_samples': len(samples),
        'total_evaluations': len(all_evaluations),
        'fc_score': round(fc_score * 100, 2),
        'fc_satisfied': fc_satisfied,
        'fc_total': fc_total,
        'sc_avg': round(sc_avg, 2),
        'evaluators': eval_data['evaluators']
    }
    
    return render_template('statistics.html', stats=stats)

@app.route('/api/image/<path:image_path>')
def serve_image(image_path):
    """提供图片服务"""
    from flask import send_file
    full_path = BASE_DIR / image_path
    if full_path.exists():
        return send_file(full_path)
    return "Image not found", 404

@app.route('/logout')
def logout():
    """登出"""
    session.pop('evaluator_name', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # 确保模板目录存在
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    print("="*50)
    print("书籍封面描述评估系统")
    print("="*50)
    print(f"书籍封面目录: {BOOK_COVERS_DIR}")
    print(f"评估数据文件: {EVALUATION_DATA_FILE}")
    print("="*50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
