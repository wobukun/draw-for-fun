#!/usr/bin/env python3
"""Flask 后端服务器 - 抽卡模拟器

简要说明：
- 使用 Flask 框架实现的抽卡模拟器后端服务
- 提供角色和武器的抽卡模拟 API
- 支持单抽、十连和自动模拟功能

主要API：
- POST /api/gacha - 处理抽卡请求
- POST /api/shutdown - 关闭服务器
"""

import sys
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

# 添加必要的路径到系统路径
sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)

# 直接指定抽卡模拟器模块的路径
draw_character_path = os.path.join(backend_dir, "gacha", "draw_character.py")
draw_weapon_path = os.path.join(backend_dir, "gacha", "draw_weapon.py")
goal_probability_path = os.path.join(backend_dir, "gacha", "goal_probability.py")

# 动态导入模块
import importlib.util

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 导入抽卡模拟器模块
draw_character = import_module_from_path("draw_character", draw_character_path)
draw_weapon = import_module_from_path("draw_weapon", draw_weapon_path)
goal_probability = import_module_from_path("goal_probability", goal_probability_path)

CharacterGachaSimulator = draw_character.CharacterGachaSimulator
WeaponGachaSimulator = draw_weapon.WeaponGachaSimulator

app = Flask(__name__)
CORS(app)  # 启用 CORS，允许跨域请求

class GachaServer:
    """抽卡服务器类"""
    
    def __init__(self):
        """初始化抽卡服务器"""
        self.character_simulator = None
        self.weapon_simulator = None
    
    def handle_gacha(self):
        """处理抽卡请求"""
        try:
            data = request.json
            mode = data.get('mode')
            action = data.get('action')
            
            if mode == 'character':
                # 角色抽卡
                # 从请求中获取抽卡进度参数
                current_pity = data.get('current_pity', 0)
                up_pity = data.get('up_pity', 0)
                avg_count = data.get('avg_count', 0)
                up_count = data.get('up_count', 0)
                guarantee_up = data.get('guarantee_up', False)
                total_pulls = data.get('total_pulls', 0)
                
                # 创建新的模拟器实例，使用请求中的抽卡进度参数
                sim = CharacterGachaSimulator()
                sim.pity = current_pity
                sim.up_pity = up_pity
                sim.avg_count = avg_count
                sim.up_count = up_count
                sim.guarantee_up = guarantee_up
                sim.total_pulls = total_pulls
                
                if action == 'one':
                    # 角色单抽
                    result = sim.pull_one()
                    return self.process_character_result(result)
                elif action == 'ten':
                    # 角色十连
                    result = sim.pull_ten()
                    return self.process_character_ten_result(result)
                elif action == 'auto':
                    # 角色自动模拟
                    count = data.get('count', 1000)
                    start_pity = data.get('start_pity', 0)
                    sim = CharacterGachaSimulator(start_pity)
                    result = sim.simulate_pulls(count)
                    result['total_pulls'] = count
                    return jsonify(result)
            elif mode == 'weapon':
                # 武器抽卡
                # 从请求中获取抽卡进度参数
                current_pity = data.get('current_pity', 0)
                up_pity = data.get('up_pity', 0)
                fate_pity = data.get('fate_pity', 0)
                avg_count = data.get('avg_count', 0)
                up_count = data.get('up_count', 0)
                fate_count = data.get('fate_count', 0)
                guarantee_up = data.get('guarantee_up', False)
                fate_point = data.get('fate_point', 0)
                is_fate_guaranteed = data.get('is_fate_guaranteed', False)
                total_pulls = data.get('total_pulls', 0)
                
                # 创建新的模拟器实例，使用请求中的抽卡进度参数
                sim = WeaponGachaSimulator()
                sim.pity = current_pity
                sim.up_pity = up_pity
                sim.fate_pity = fate_pity
                sim.avg_count = avg_count
                sim.up_count = up_count
                sim.fate_count = fate_count
                sim.guarantee_up = guarantee_up
                sim.fate_point = fate_point
                sim.is_fate_guaranteed = is_fate_guaranteed
                sim.total_pulls = total_pulls
                
                if action == 'one':
                    # 武器单抽
                    result = sim.pull_one()
                    return self.process_weapon_result(result)
                elif action == 'ten':
                    # 武器十连
                    result = sim.pull_ten()
                    return self.process_weapon_ten_result(result)
                elif action == 'auto':
                    # 武器自动模拟
                    count = data.get('count', 1000)
                    start_pity = data.get('start_pity', 0)
                    sim = WeaponGachaSimulator(start_pity)
                    result = sim.simulate_pulls(count)
                    result['total_pulls'] = count
                    return jsonify(result)
            else:
                return jsonify({'error': 'Unknown mode'}), 400
        except Exception as e:
            app.logger.error(f"Error handling gacha request: {e}")
            return jsonify({'error': str(e)}), 500

    def handle_goal_probability(self):
        """根据资源与目标，估算达成目标概率（蒙特卡洛模拟）"""
        try:
            data = request.json or {}

            # 资源（纠缠之缘=抽数）
            resources = int(data.get('resources', data.get('intertwined_fate', data.get('pulls', 0))))
            if resources < 0:
                return jsonify({'error': 'resources must be >= 0'}), 400

            # 目标：允许用“层数”或直接 copies
            # 角色：0命=1个UP角色，1命=2个UP角色... => copies = constellation + 1
            if 'target_character_copies' in data:
                character_target_copies = int(data.get('target_character_copies', 0))
            elif 'target_character_constellation' in data:
                character_target_copies = goal_probability.GoalProbabilityCalculator.constellation_to_copies(
                    int(data.get('target_character_constellation', 0))
                )
            else:
                character_target_copies = 0

            # 武器：1精=1把目标武器，2精=2把目标武器... => copies = refinement
            if 'target_weapon_copies' in data:
                weapon_target_copies = int(data.get('target_weapon_copies', 0))
            elif 'target_weapon_refinement' in data:
                weapon_target_copies = goal_probability.GoalProbabilityCalculator.refinement_to_copies(
                    int(data.get('target_weapon_refinement', 0))
                )
            else:
                weapon_target_copies = 0

            if character_target_copies < 0 or weapon_target_copies < 0:
                return jsonify({'error': 'targets must be >= 0'}), 400
            if character_target_copies == 0 and weapon_target_copies == 0:
                return jsonify({'error': 'at least one target must be > 0'}), 400

            # 模拟参数
            trials = int(data.get('trials', 5000))
            if trials <= 0:
                return jsonify({'error': 'trials must be > 0'}), 400
            seed = data.get('seed', None)

            # 起始抽卡状态（可选；默认都按 0 起算）
            start = goal_probability.StartState(
                character_pity=int(data.get('character_pity', 0)),
                character_guarantee_up=bool(data.get('character_guarantee_up', False)),
                weapon_pity=int(data.get('weapon_pity', 0)),
                weapon_guarantee_up=bool(data.get('weapon_guarantee_up', False)),
                weapon_fate_point=int(data.get('weapon_fate_point', 0)),
                weapon_is_fate_guaranteed=bool(data.get('weapon_is_fate_guaranteed', False)),
            )

            # 策略：auto / character_first / weapon_first
            strategy_req = str(data.get('strategy', 'auto')).lower()
            results = {}

            def run(strategy: str):
                calculator = goal_probability.GoalProbabilityCalculator()
                return calculator.estimate_goal_probability(
                    pulls=resources,
                    character_target_copies=character_target_copies,
                    weapon_target_copies=weapon_target_copies,
                    trials=trials,
                    strategy=strategy,
                    seed=seed,
                    start=start,
                    draw_character_module=draw_character,
                    draw_weapon_module=draw_weapon,
                )

            if strategy_req in ('character_first', 'character_then_weapon'):
                r = run('character_then_weapon')
                results[r['strategy']] = r
                best = r
            elif strategy_req in ('weapon_first', 'weapon_then_character'):
                r = run('weapon_then_character')
                results[r['strategy']] = r
                best = r
            elif strategy_req == 'auto':
                r1 = run('character_then_weapon')
                r2 = run('weapon_then_character')
                results[r1['strategy']] = r1
                results[r2['strategy']] = r2
                best = r1 if r1['probability'] >= r2['probability'] else r2
            else:
                return jsonify({'error': f'Unknown strategy: {strategy_req}'}), 400

            return jsonify({
                'resources': resources,
                'targets': {
                    'character_target_copies': character_target_copies,
                    'weapon_target_copies': weapon_target_copies
                },
                'interpretation': {
                    'character_copy_definition': '每个UP五星角色计为1个“角色拷贝”（用于命之座）',
                    'weapon_copy_definition': '每个“定轨武器”(is_fate=True)计为1把目标武器（用于精炼）'
                },
                'start_state': {
                    'character_pity': start.character_pity,
                    'character_guarantee_up': start.character_guarantee_up,
                    'weapon_pity': start.weapon_pity,
                    'weapon_guarantee_up': start.weapon_guarantee_up,
                    'weapon_fate_point': start.weapon_fate_point,
                    'weapon_is_fate_guaranteed': start.weapon_is_fate_guaranteed
                },
                'best': best,
                'all_strategies': results
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error handling goal probability request: {e}")
            return jsonify({'error': str(e)}), 500
    
    def shutdown(self):
        """关闭服务器"""
        try:
            # 关闭服务器的逻辑
            print("[DEBUG] 接收到关闭服务器的请求")
            import threading
            import time
            
            def exit_program():
                print("[DEBUG] 关闭服务器线程启动，等待 0.5 秒后退出")
                time.sleep(0.5)
                print("[DEBUG] 调用 os._exit(0) 退出程序")
                os._exit(0)
            
            thread = threading.Thread(target=exit_program)
            thread.daemon = True
            thread.start()
            print("[DEBUG] 关闭服务器线程已启动")
            
            return jsonify({'message': 'Server shutting down...'})
        except Exception as e:
            print(f"[ERROR] 关闭服务器时出错: {e}")
            import traceback
            traceback.print_exc()
            app.logger.error(f"Error shutting down server: {e}")
            return jsonify({'error': str(e)}), 500
    
    def handle_required_pulls_for_95_percent(self):
        """处理95%概率所需抽数的请求"""
        try:
            data = request.json
            
            # 获取参数
            character_target_constellation = int(data.get('character_target_constellation', 0))
            weapon_target_refinement = int(data.get('weapon_target_refinement', 0))
            strategy = str(data.get('strategy', 'character_then_weapon')).lower()
            
            # 验证策略
            if strategy not in ('character_then_weapon', 'weapon_then_character'):
                return jsonify({'error': f'Unknown strategy: {strategy}'}), 400
            
            # 计算所需抽数
            calculator = goal_probability.GoalProbabilityCalculator()
            result = calculator.calculate_required_pulls_for_95_percent_probability(
                character_target_constellation=character_target_constellation,
                weapon_target_refinement=weapon_target_refinement,
                strategy=strategy,
                draw_character_module=draw_character,
                draw_weapon_module=draw_weapon,
            )
            
            return jsonify(result)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error handling required pulls request: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    def handle_required_pulls_for_50_percent(self):
        """处理50%概率所需抽数（期望）的请求"""
        try:
            data = request.json
            
            # 获取参数
            character_target_constellation = int(data.get('character_target_constellation', 0))
            weapon_target_refinement = int(data.get('weapon_target_refinement', 0))
            strategy = str(data.get('strategy', 'character_then_weapon')).lower()
            
            # 验证策略
            if strategy not in ('character_then_weapon', 'weapon_then_character'):
                return jsonify({'error': f'Unknown strategy: {strategy}'}), 400
            
            # 计算所需抽数
            calculator = goal_probability.GoalProbabilityCalculator()
            result = calculator.calculate_required_pulls_for_50_percent_probability(
                character_target_constellation=character_target_constellation,
                weapon_target_refinement=weapon_target_refinement,
                strategy=strategy,
                draw_character_module=draw_character,
                draw_weapon_module=draw_weapon,
            )
            
            return jsonify(result)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error handling required pulls request: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    def index(self):
        """根路径"""
        return '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>抽卡模拟器</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    background-color: #f5f5f5;
                    color: #333;
                    line-height: 1.6;
                }
                
                .container {
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 40px;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                }
                
                h1 {
                    color: #4a4a4a;
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #e0e0e0;
                }
                
                p {
                    text-align: center;
                    margin-bottom: 30px;
                    font-size: 16px;
                }
                
                .footer {
                    margin-top: 40px;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 14px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>抽卡模拟器</h1>
                <p>后端API服务已启动，请使用Vue前端访问。</p>
                <p>请在项目根目录运行 <code>npm run dev</code> 启动前端开发服务器，然后在浏览器中访问前端地址（默认是 http://localhost:3000）。</p>
                <div class="footer">
                    <p>抽卡模拟器 v1.0</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def process_character_result(self, result):
        """处理角色单抽结果"""
        response_data = {}
        if len(result['results']) == len(result['is_up']) == len(result['used_probs']) and len(result['capture_minguang']) == len(result['results']):
            is_5star, is_up, prob, capture_minguang = result['results'][0], result['is_up'][0], result['used_probs'][0], result['capture_minguang'][0]
            if is_5star:
                star = 5
                if is_up:
                    name = 'UP角色'
                else:
                    name = '常驻角色'
            else:
                # 简化处理，不区分3星和4星，统一标注为3/4星
                star = 4
                name = '3/4星'
            response_data = {
                'star': star,
                'name': name,
                'probability': prob,
                'total_pulls': result['total_pulls'],
                'current_pity': result['new_pity'],
                'up_pity': result['up_pity'],
                'avg_count': result['avg_count'],
                'up_count': result['up_count'],
                'guarantee_up': result['guarantee_up'],
                'capture_minguang': capture_minguang
            }
        return jsonify(response_data)
    
    def process_character_ten_result(self, result):
        """处理角色十连结果"""
        response_data = {
            'results': [],
            'total_pulls': result['total_pulls'],
            'current_pity': result['new_pity'],
            'up_pity': result['up_pity'],
            'avg_count': result['avg_count'],
            'up_count': result['up_count'],
            'guarantee_up': result['guarantee_up']
        }
        if len(result['results']) == len(result['is_up']) == len(result['used_probs']) and len(result['capture_minguang']) == len(result['results']):
            for i, (is_5star, is_up, prob, capture_minguang) in enumerate(zip(result['results'], result['is_up'], result['used_probs'], result['capture_minguang'])):
                if is_5star:
                    star = 5
                    if is_up:
                        name = 'UP角色'
                    else:
                        name = '常驻角色'
                else:
                    # 简化处理，不区分3星和4星，统一标注为3/4星
                    star = 4
                    name = '3/4星'
                response_data['results'].append({
                    'star': star,
                    'name': name,
                    'probability': prob,
                    'capture_minguang': capture_minguang
                })
        return jsonify(response_data)
    
    def process_weapon_result(self, result):
        """处理武器单抽结果"""
        response_data = {}
        if len(result['results']) == len(result['is_up']) == len(result['used_probs']) == len(result['is_fate']):
            is_5star, is_up, prob, is_fate = result['results'][0], result['is_up'][0], result['used_probs'][0], result['is_fate'][0]
            if is_5star:
                star = 5
                if is_up:
                    name = 'UP武器'
                else:
                    name = '常驻武器'
            else:
                # 简化处理，不区分3星和4星，统一标注为3/4星
                star = 4
                name = '3/4星'
                is_fate = False
            response_data = {
                'star': star,
                'name': name,
                'is_fate': is_fate,
                'probability': prob,
                'total_pulls': result['total_pulls'],
                'current_pity': result['new_pity'],
                'up_pity': result['up_pity'],
                'fate_pity': result.get('fate_pity', 0),
                'avg_count': result['avg_count'],
                'up_count': result['up_count'],
                'fate_count': result.get('fate_count', 0),
                'guarantee_up': result['guarantee_up'],
                'fate_point': result['fate_point'],
                'is_fate_guaranteed': result['is_fate_guaranteed']
            }
        return jsonify(response_data)
    
    def process_weapon_ten_result(self, result):
        """处理武器十连结果"""
        response_data = {
            'results': [],
            'total_pulls': result['total_pulls'],
            'current_pity': result['new_pity'],
            'up_pity': result['up_pity'],
            'fate_pity': result.get('fate_pity', 0),
            'avg_count': result['avg_count'],
            'up_count': result['up_count'],
            'fate_count': result.get('fate_count', 0),
            'guarantee_up': result['guarantee_up'],
            'fate_point': result['fate_point'],
            'is_fate_guaranteed': result['is_fate_guaranteed']
        }
        if len(result['results']) == len(result['is_up']) == len(result['used_probs']) == len(result['is_fate']):
            for i, (is_5star, is_up, prob, is_fate) in enumerate(zip(result['results'], result['is_up'], result['used_probs'], result['is_fate'])):
                if is_5star:
                    star = 5
                    if is_up:
                        name = 'UP武器'
                    else:
                        name = '常驻武器'
                else:
                    # 简化处理，不区分3星和4星，统一标注为3/4星
                    star = 4
                    name = '3/4星'
                    is_fate = False
                response_data['results'].append({
                    'star': star,
                    'name': name,
                    'is_fate': is_fate,
                    'probability': prob
                })
        return jsonify(response_data)

# 创建服务器实例
server = GachaServer()

# 注册路由
@app.route('/api/gacha', methods=['POST'])
def handle_gacha():
    return server.handle_gacha()

@app.route('/api/goal_probability', methods=['POST'])
def handle_goal_probability():
    return server.handle_goal_probability()

@app.route('/api/required_pulls_for_95_percent', methods=['POST'])
def handle_required_pulls_for_95_percent():
    return server.handle_required_pulls_for_95_percent()

@app.route('/api/required_pulls_for_50_percent', methods=['POST'])
def handle_required_pulls_for_50_percent():
    return server.handle_required_pulls_for_50_percent()

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    return server.shutdown()

@app.route('/api/')
def index():
    return server.index()

if __name__ == '__main__':
    """启动服务器"""
    port = 8888
    print(f"[INFO] Flask服务器启动在 http://localhost:{port}")
    print("[INFO] 后端API服务已启动")
    print(f"[INFO] 进程ID: {os.getpid()}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)