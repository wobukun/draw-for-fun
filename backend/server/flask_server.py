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
draw_character_2_path = os.path.join(backend_dir, "gacha", "draw_character_2.py")
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
draw_character_2 = import_module_from_path("draw_character_2", draw_character_2_path)
draw_weapon = import_module_from_path("draw_weapon", draw_weapon_path)
goal_probability = import_module_from_path("goal_probability", goal_probability_path)

CharacterGachaSimulator = draw_character.CharacterGachaSimulator
CharacterGachaSimulator2 = draw_character_2.CharacterGachaSimulator2
WeaponGachaSimulator = draw_weapon.WeaponGachaSimulator

app = Flask(__name__)
CORS(app)  # 启用 CORS，允许跨域请求

class GachaServer:
    """抽卡服务器类"""
    
    def __init__(self):
        """初始化抽卡服务器"""
        self.character_simulator = None
        self.character_simulator_2 = None
        self.weapon_simulator = None
    
    def handle_gacha(self):
        """处理抽卡请求"""
        try:
            data = request.json
            mode = data.get('mode')
            action = data.get('action')
            
            if mode == 'character':
                # 角色活动祈愿-1
                return self._handle_character_gacha(data, action, CharacterGachaSimulator)
            elif mode == 'character2':
                # 角色活动祈愿-2
                return self._handle_character_gacha(data, action, CharacterGachaSimulator2)
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

    def _handle_character_gacha(self, data, action, SimulatorClass):
        """处理角色抽卡的通用方法"""
        # 从请求中获取抽卡进度参数
        current_pity = data.get('current_pity', 0)
        up_pity = data.get('up_pity', 0)
        avg_count = data.get('avg_count', 0)
        up_count = data.get('up_count', 0)
        guarantee_up = data.get('guarantee_up', False)
        total_pulls = data.get('total_pulls', 0)
        migu_counter = data.get('migu_counter', 0)
        
        # 创建新的模拟器实例，使用请求中的抽卡进度参数
        sim = SimulatorClass()
        sim.pity = current_pity
        sim.four_star_pity = data.get('four_star_pity', 0)
        sim.up_pity = up_pity
        sim.avg_count = avg_count
        sim.up_count = up_count
        sim.four_star_up_count = data.get('four_star_up_count', 0)
        sim.four_star_avg_count = data.get('four_star_avg_count', 0)
        sim.four_star_up_1_count = data.get('four_star_up_1_count', 0)
        sim.four_star_up_2_count = data.get('four_star_up_2_count', 0)
        sim.four_star_up_3_count = data.get('four_star_up_3_count', 0)
        sim.guarantee_up = guarantee_up
        sim.guarantee_four_star_up = data.get('guarantee_four_star_up', False)
        sim.total_pulls = total_pulls
        sim.migu_counter = migu_counter
        
        # 获取5星UP角色名称（从模块中获取）
        if SimulatorClass == CharacterGachaSimulator2:
            five_star_up_name = draw_character_2.FIVE_STAR_UP_CHARACTER
        else:
            five_star_up_name = draw_character.FIVE_STAR_UP_CHARACTER
        
        if action == 'one':
            # 角色单抽
            result = sim.pull_one()
            return self.process_character_result(result, five_star_up_name)
        elif action == 'ten':
            # 角色十连
            result = sim.pull_ten()
            return self.process_character_ten_result(result, five_star_up_name)
        elif action == 'auto':
            # 角色自动模拟
            count = data.get('count', 1000)
            start_pity = data.get('start_pity', 0)
            sim = SimulatorClass(start_pity)
            result = sim.simulate_pulls(count)
            result['total_pulls'] = count
            return jsonify(result)
        else:
            return jsonify({'error': 'Unknown action'}), 400

    def handle_goal_probability(self):
        """根据资源与目标，估算达成目标概率（蒙特卡洛模拟）"""
        try:
            data = request.json or {}

            # 资源（纠缠之缘=抽数）
            resources = int(data.get('resources', data.get('intertwined_fate', data.get('pulls', 0))))
            if resources < 0:
                return jsonify({'error': 'resources must be >= 0'}), 400

            # 目标：允许用"层数"或直接 copies
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
            if trials < 100:
                return jsonify({'error': 'trials must be >= 100'}), 400

            # 执行蒙特卡洛模拟
            calculator = goal_probability.GoalProbabilityCalculator()
            
            # 根据请求中的 mode 参数选择模拟器类型
            mode = data.get('mode', 'character')
            if mode == 'character2':
                simulator_class = CharacterGachaSimulator2
            else:
                simulator_class = CharacterGachaSimulator
            
            result = calculator.calculate_goal_probability(
                resources=resources,
                character_target_copies=character_target_copies,
                weapon_target_copies=weapon_target_copies,
                trials=trials,
                character_simulator_class=simulator_class
            )
            
            return jsonify(result)
        except Exception as e:
            app.logger.error(f"Error calculating goal probability: {e}")
            return jsonify({'error': str(e)}), 500

    def handle_required_pulls_for_95_percent(self):
        """计算达成目标所需的抽数（95%置信度）"""
        try:
            data = request.json or {}

            # 目标：允许用"层数"或直接 copies
            if 'target_character_copies' in data:
                character_target_copies = int(data.get('target_character_copies', 0))
            elif 'target_character_constellation' in data:
                character_target_copies = goal_probability.GoalProbabilityCalculator.constellation_to_copies(
                    int(data.get('target_character_constellation', 0))
                )
            else:
                character_target_copies = 0

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
            trials = int(data.get('trials', 2000))
            if trials < 100:
                return jsonify({'error': 'trials must be >= 100'}), 400

            # 执行蒙特卡洛模拟
            calculator = goal_probability.GoalProbabilityCalculator()
            
            # 根据请求中的 mode 参数选择模拟器类型
            mode = data.get('mode', 'character')
            if mode == 'character2':
                simulator_class = CharacterGachaSimulator2
            else:
                simulator_class = CharacterGachaSimulator
            
            result = calculator.calculate_required_pulls_for_confidence(
                character_target_copies=character_target_copies,
                weapon_target_copies=weapon_target_copies,
                confidence=0.95,
                trials=trials,
                character_simulator_class=simulator_class
            )
            
            return jsonify(result)
        except Exception as e:
            app.logger.error(f"Error calculating required pulls for 95%: {e}")
            return jsonify({'error': str(e)}), 500

    def handle_required_pulls_for_50_percent(self):
        """计算达成目标所需的抽数（50%置信度，中位数）"""
        try:
            data = request.json or {}

            # 目标：允许用"层数"或直接 copies
            if 'target_character_copies' in data:
                character_target_copies = int(data.get('target_character_copies', 0))
            elif 'target_character_constellation' in data:
                character_target_copies = goal_probability.GoalProbabilityCalculator.constellation_to_copies(
                    int(data.get('target_character_constellation', 0))
                )
            else:
                character_target_copies = 0

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
            trials = int(data.get('trials', 2000))
            if trials < 100:
                return jsonify({'error': 'trials must be >= 100'}), 400

            # 执行蒙特卡洛模拟
            calculator = goal_probability.GoalProbabilityCalculator()
            
            # 根据请求中的 mode 参数选择模拟器类型
            mode = data.get('mode', 'character')
            if mode == 'character2':
                simulator_class = CharacterGachaSimulator2
            else:
                simulator_class = CharacterGachaSimulator
            
            result = calculator.calculate_required_pulls_for_confidence(
                character_target_copies=character_target_copies,
                weapon_target_copies=weapon_target_copies,
                confidence=0.50,
                trials=trials,
                character_simulator_class=simulator_class
            )
            
            return jsonify(result)
        except Exception as e:
            app.logger.error(f"Error calculating required pulls for 50%: {e}")
            return jsonify({'error': str(e)}), 500

    def process_character_result(self, result, five_star_up_name='5星UP角色-1'):
        """处理角色单抽结果，转换为前端需要的格式"""
        is_5star = result['results'][0]
        is_4star = result['four_star_results'][0]
        star = 5 if is_5star else (4 if is_4star else 3)
        
        # 确定物品名称
        name = '3星物品'
        if is_5star:
            # 5星物品
            if result['is_up'][0]:
                name = five_star_up_name
            else:
                name = '5星常驻角色'
        elif is_4star:
            # 4星物品
            if result['is_four_star_up'][0]:
                name = result['four_star_items'][0]
            else:
                name = '4星常驻物品'
        
        return jsonify({
            'star': star,
            'name': name,
            'is_up': result['is_up'][0],
            'is_four_star_up': result['is_four_star_up'][0],
            'four_star_item': result['four_star_items'][0],
            'new_pity': result['new_pity'],
            'current_pity': result['new_pity'],  # 添加 current_pity 字段以兼容前端
            'new_four_star_pity': result['new_four_star_pity'],
            'used_prob': result['used_probs'][0],
            'avg_count': result['avg_count'],
            'up_count': result['up_count'],
            'four_star_up_count': result.get('four_star_up_count', 0),
            'four_star_avg_count': result.get('four_star_avg_count', 0),
            'four_star_up_1_count': result.get('four_star_up_1_count', 0),
            'four_star_up_2_count': result.get('four_star_up_2_count', 0),
            'four_star_up_3_count': result.get('four_star_up_3_count', 0),
            'up_pity': result['up_pity'],
            'start_up_pity': result['start_up_pity'],
            'total_pulls': result['total_pulls'],
            'guarantee_up': result['guarantee_up'],
            'guarantee_four_star_up': result['guarantee_four_star_up'],
            'capture_minguang': result['capture_minguang'][0],
            'migu_counter': result['migu_counter'],
            'guarantee_capture_minguang': result['guarantee_capture_minguang'],
            'capture_minguang_count': result['capture_minguang_count']
        })

    def process_character_ten_result(self, result, five_star_up_name='5星UP角色-1'):
        """处理角色十连结果，转换为前端需要的格式"""
        # 构建结果数组，每个元素包含star、name等信息
        results = []
        for i in range(10):
            is_5star = result['results'][i]
            is_4star = result['four_star_results'][i]
            star = 5 if is_5star else (4 if is_4star else 3)
            
            # 确定物品名称
            name = '3星物品'
            if is_5star:
                # 5星物品
                if result['is_up'][i]:
                    name = five_star_up_name
                else:
                    name = '5星常驻角色'
            elif is_4star:
                # 4星物品
                if result['is_four_star_up'][i]:
                    name = result['four_star_items'][i]
                else:
                    name = '4星常驻物品'
            
            results.append({
                'star': star,
                'name': name,
                'is_up': result['is_up'][i],
                'is_four_star_up': result['is_four_star_up'][i],
                'capture_minguang': result['capture_minguang'][i]
            })
        
        return jsonify({
            'results': results,
            'new_pity': result['new_pity'],
            'current_pity': result['new_pity'],  # 添加 current_pity 字段以兼容前端
            'new_four_star_pity': result['new_four_star_pity'],
            'avg_count': result['avg_count'],
            'up_count': result['up_count'],
            'four_star_up_count': result.get('four_star_up_count', 0),
            'four_star_avg_count': result.get('four_star_avg_count', 0),
            'four_star_up_1_count': result.get('four_star_up_1_count', 0),
            'four_star_up_2_count': result.get('four_star_up_2_count', 0),
            'four_star_up_3_count': result.get('four_star_up_3_count', 0),
            'up_pity': result['up_pity'],
            'start_up_pity': result['start_up_pity'],
            'total_pulls': result['total_pulls'],
            'guarantee_up': result['guarantee_up'],
            'guarantee_four_star_up': result['guarantee_four_star_up'],
            'migu_counter': result['migu_counter'],
            'guarantee_capture_minguang': result['guarantee_capture_minguang'],
            'capture_minguang_count': result['capture_minguang_count']
        })

    def process_weapon_result(self, result):
        """处理武器单抽结果，转换为前端需要的格式"""
        return jsonify({
            'star': 5 if result['results'][0] else (4 if result['four_star_results'][0] else 3),
            'is_up': result['is_up'][0],
            'is_four_star_up': result['is_four_star_up'][0],
            'new_pity': result['new_pity'],
            'new_four_star_pity': result['new_four_star_pity'],
            'used_prob': result['used_probs'][0],
            'avg_count': result['avg_count'],
            'up_count': result['up_count'],
            'fate_count': result['fate_count'],
            'up_pity': result['up_pity'],
            'start_up_pity': result['start_up_pity'],
            'total_pulls': result['total_pulls'],
            'guarantee_up': result['guarantee_up'],
            'fate_point': result['fate_point'],
            'is_fate_guaranteed': result['is_fate_guaranteed']
        })

    def process_weapon_ten_result(self, result):
        """处理武器十连结果，转换为前端需要的格式"""
        return jsonify({
            'results': result['results'],
            'four_star_results': result['four_star_results'],
            'is_up': result['is_up'],
            'is_four_star_up': result['is_four_star_up'],
            'new_pity': result['new_pity'],
            'new_four_star_pity': result['new_four_star_pity'],
            'used_probs': result['used_probs'],
            'avg_count': result['avg_count'],
            'up_count': result['up_count'],
            'fate_count': result['fate_count'],
            'up_pity': result['up_pity'],
            'start_up_pity': result['start_up_pity'],
            'total_pulls': result['total_pulls'],
            'guarantee_up': result['guarantee_up'],
            'fate_point': result['fate_point'],
            'is_fate_guaranteed': result['is_fate_guaranteed']
        })


# 创建服务器实例
server = GachaServer()

@app.route('/api/gacha', methods=['POST'])
def handle_gacha():
    """处理抽卡请求"""
    return server.handle_gacha()

@app.route('/api/goal_probability', methods=['POST'])
def handle_goal_probability():
    """根据资源与目标，估算达成目标概率（蒙特卡洛模拟）"""
    return server.handle_goal_probability()

@app.route('/api/required_pulls_for_95_percent', methods=['POST'])
def handle_required_pulls_for_95_percent():
    """计算达成目标所需的抽数（95%置信度）"""
    return server.handle_required_pulls_for_95_percent()

@app.route('/api/required_pulls_for_50_percent', methods=['POST'])
def handle_required_pulls_for_50_percent():
    """计算达成目标所需的抽数（50%置信度，中位数）"""
    return server.handle_required_pulls_for_50_percent()

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """关闭服务器"""
    import os
    import signal
    import sys
    func = request.environ.get('werkzeug.server.shutdown')
    if func is not None:
        # 使用Werkzeug的内置关闭方法
        func()
        return jsonify({'message': 'Server shutting down...'})
    else:
        # 如果不是运行在Werkzeug服务器上，使用信号关闭
        response = jsonify({'message': 'Server shutting down...'})
        # 在后台线程中关闭服务器
        import threading
        def shutdown_server():
            import time
            time.sleep(0.1)  # 等待响应发送完成
            if os.name == 'nt':  # Windows系统
                os._exit(0)  # 强制退出进程
            else:  # Unix系统
                os.kill(os.getpid(), signal.SIGINT)  # 发送中断信号
        threading.Thread(target=shutdown_server).start()
        return response


@app.route('/api/')
def api_info():
    """API信息"""
    return jsonify({
        'message': 'Gacha Simulator API',
        'endpoints': [
            '/api/gacha',
            '/api/goal_probability',
            '/api/required_pulls_for_95_percent',
            '/api/required_pulls_for_50_percent',
            '/api/shutdown'
        ]
    })


if __name__ == '__main__':
    print("Starting Gacha Simulator Server...")
    print("API endpoints:")
    print("  - POST /api/gacha")
    print("  - POST /api/goal_probability")
    print("  - POST /api/required_pulls_for_95_percent")
    print("  - POST /api/required_pulls_for_50_percent")
    print("  - POST /api/shutdown")
    print("  - GET  /api/")
    app.run(host='0.0.0.0', port=8888, debug=True)
