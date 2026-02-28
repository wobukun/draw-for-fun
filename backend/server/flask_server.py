#!/usr/bin/env python3
"""Flask 后端服务器 - 祈愿模拟器

简要说明：
- 使用 Flask 框架实现的祈愿模拟器后端服务
- 提供角色和武器的祈愿模拟 API
- 支持单抽、十连和自动模拟功能

主要API：
- POST /api/wish - 处理祈愿请求
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
CharacterWish_path = os.path.join(backend_dir, "wish", "CharacterWish.py")
CharacterWish2_path = os.path.join(backend_dir, "wish", "CharacterWish2.py")
WeaponWish_path = os.path.join(backend_dir, "wish", "WeaponWish.py")
GoalProbability_path = os.path.join(backend_dir, "wish", "GoalProbability.py")

# 动态导入模块
import importlib.util

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 导入抽卡模拟器模块
CharacterWish = import_module_from_path("CharacterWish", CharacterWish_path)
CharacterWish2 = import_module_from_path("CharacterWish2", CharacterWish2_path)
WeaponWish = import_module_from_path("WeaponWish", WeaponWish_path)
GoalProbability = import_module_from_path("GoalProbability", GoalProbability_path)

CharacterWishSimulator = CharacterWish.CharacterWishSimulator
CharacterWishSimulator2 = CharacterWish2.CharacterWishSimulator2
WeaponWishSimulator = WeaponWish.WeaponWishSimulator

app = Flask(__name__)
CORS(app)  # 启用 CORS，允许跨域请求

class WishServer:
    """祈愿服务器类"""
    
    def __init__(self):
        """初始化祈愿服务器"""
        self.character_simulator = None
        self.character_simulator_2 = None
        self.weapon_simulator = None
    
    def handle_wish(self):
        """处理祈愿请求"""
        try:
            data = request.json
            mode = data.get('mode')
            action = data.get('action')
            
            if mode == 'character':
                # 角色活动祈愿-1
                return self._handle_character_wish(data, action, CharacterWishSimulator)
            elif mode == 'character2':
                # 角色活动祈愿-2
                return self._handle_character_wish(data, action, CharacterWishSimulator2)
            elif mode == 'weapon':
                # 武器祈愿
                return self._handle_weapon_wish(data, action)
            else:
                return jsonify({'error': 'Unknown mode'}), 400
        except Exception as e:
            app.logger.error(f"Error handling wish request: {e}")
            return jsonify({'error': str(e)}), 500

    def _handle_character_wish(self, data, action, SimulatorClass):
        """处理角色祈愿的通用方法"""
        # 从请求中获取抽卡进度参数
        current_pity = data.get('current_pity', 0)
        up_pity = data.get('up_pity', 0)
        avg_count = data.get('avg_count', 0)
        up_count = data.get('up_count', 0)
        guarantee_up = data.get('guarantee_up', False)
        total_pulls = data.get('total_pulls', 0)
        migu_counter = data.get('migu_counter', 0)
        last_five_star_cost = data.get('last_five_star_cost', 0)
        
        # 创建新的模拟器实例，使用请求中的祈愿进度参数
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
        sim.last_five_star_cost = last_five_star_cost
        
        # 获取5星UP角色名称（从模块中获取）
        if SimulatorClass == CharacterWishSimulator2:
            five_star_up_name = CharacterWish2.FIVE_STAR_UP_CHARACTER
        else:
            five_star_up_name = CharacterWish.FIVE_STAR_UP_CHARACTER
        
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

    def _handle_weapon_wish(self, data, action):
        """处理武器祈愿的通用方法"""
        # 从请求中获取祈愿进度参数
        current_pity = data.get('current_pity', 0)
        four_star_pity = data.get('four_star_pity', 0)
        avg_count = data.get('avg_count', 0)
        five_star_up_counts = data.get('five_star_up_counts', {'5星UP武器-1': 0, '5星UP武器-2': 0})
        four_star_up_count = data.get('four_star_up_count', 0)
        four_star_avg_count = data.get('four_star_avg_count', 0)
        guarantee_up = data.get('guarantee_up', False)
        four_star_guarantee_up = data.get('four_star_guarantee_up', False)
        fate_point = data.get('fate_point', 0)
        total_pulls = data.get('total_pulls', 0)
        last_five_star_cost = data.get('last_five_star_cost', 0)
        selected_fate_weapon = data.get('selected_fate_weapon', None)
        
        # 创建新的模拟器实例，使用请求中的祈愿进度参数
        sim = WeaponWishSimulator()
        sim.pity = current_pity
        sim.four_star_pity = four_star_pity
        sim.avg_count = avg_count
        sim.five_star_up_counts = five_star_up_counts
        sim.four_star_up_count = four_star_up_count
        sim.four_star_avg_count = four_star_avg_count
        sim.guarantee_up = guarantee_up
        sim.four_star_guarantee_up = four_star_guarantee_up
        sim.fate_point = fate_point
        sim.total_pulls = total_pulls
        sim.last_five_star_cost = last_five_star_cost
        sim.selected_fate_weapon = selected_fate_weapon
        
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
            sim = WeaponWishSimulator(start_pity)
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
                character_target_copies = GoalProbability.GoalProbabilityCalculator.constellation_to_copies(
                    int(data.get('target_character_constellation', 0))
                )
            else:
                character_target_copies = 0

            # 武器：1精=1把目标武器，2精=2把目标武器... => copies = refinement
            if 'target_weapon_copies' in data:
                weapon_target_copies = int(data.get('target_weapon_copies', 0))
            elif 'target_weapon_refinement' in data:
                weapon_target_copies = GoalProbability.GoalProbabilityCalculator.refinement_to_copies(
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
            calculator = GoalProbability.GoalProbabilityCalculator()
            
            # 根据请求中的 mode 参数选择模拟器类型
            mode = data.get('mode', 'character')
            if mode == 'character2':
                simulator_class = CharacterWishSimulator2
            else:
                simulator_class = CharacterWishSimulator
            
            result = calculator.estimate_goal_probability(
                pulls=resources,
                character_target_copies=character_target_copies,
                weapon_target_copies=weapon_target_copies,
                trials=trials,
                strategy="character_then_weapon",
                seed=None,
                start=GoalProbability.StartState(),
                draw_character_module=CharacterWish,
                draw_weapon_module=WeaponWish
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
                character_target_copies = GoalProbability.GoalProbabilityCalculator.constellation_to_copies(
                    int(data.get('target_character_constellation', 0))
                )
            else:
                character_target_copies = 0

            if 'target_weapon_copies' in data:
                weapon_target_copies = int(data.get('target_weapon_copies', 0))
            elif 'target_weapon_refinement' in data:
                weapon_target_copies = GoalProbability.GoalProbabilityCalculator.refinement_to_copies(
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
            calculator = GoalProbability.GoalProbabilityCalculator()
            
            # 根据请求中的 mode 参数选择模拟器类型
            mode = data.get('mode', 'character')
            if mode == 'character2':
                simulator_class = CharacterWishSimulator2
            else:
                simulator_class = CharacterWishSimulator
            
            result = calculator.calculate_required_pulls_for_95_percent_probability(
                character_target_constellation=data.get('target_character_constellation', 0),
                weapon_target_refinement=data.get('target_weapon_refinement', 0),
                strategy="character_then_weapon",
                draw_character_module=CharacterWish,
                draw_weapon_module=WeaponWish
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
                character_target_copies = GoalProbability.GoalProbabilityCalculator.constellation_to_copies(
                    int(data.get('target_character_constellation', 0))
                )
            else:
                character_target_copies = 0

            if 'target_weapon_copies' in data:
                weapon_target_copies = int(data.get('target_weapon_copies', 0))
            elif 'target_weapon_refinement' in data:
                weapon_target_copies = GoalProbability.GoalProbabilityCalculator.refinement_to_copies(
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
            calculator = GoalProbability.GoalProbabilityCalculator()
            
            # 根据请求中的 mode 参数选择模拟器类型
            mode = data.get('mode', 'character')
            if mode == 'character2':
                simulator_class = CharacterWishSimulator2
            else:
                simulator_class = CharacterWishSimulator
            
            result = calculator.calculate_required_pulls_for_50_percent_probability(
                character_target_constellation=data.get('target_character_constellation', 0),
                weapon_target_refinement=data.get('target_weapon_refinement', 0),
                strategy="character_then_weapon",
                draw_character_module=CharacterWish,
                draw_weapon_module=WeaponWish
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
            'current_pity': result['new_pity'],
            'four_star_pity': result['new_four_star_pity'],
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
            'capture_minguang_count': result['capture_minguang_count'],
            'last_five_star_cost': result.get('last_five_star_cost', 0)
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
            'current_pity': result['new_pity'],
            'four_star_pity': result['new_four_star_pity'],
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
            'capture_minguang_count': result['capture_minguang_count'],
            'last_five_star_cost': result.get('last_five_star_cost', 0)
        })

    def process_weapon_result(self, result):
        """处理武器单抽结果，转换为前端需要的格式"""
        return jsonify({
            'star': 5 if result['results'][0] else (4 if result['four_star_results'][0] else 3),
            'name': result['weapon_names'][0],
            'is_up': result['is_up'][0],
            'is_four_star_up': result['is_four_star_up'][0],
            'is_fate': result['is_fate'][0],
            'current_pity': result['new_pity'],
            'four_star_pity': result['new_four_star_pity'],
            'used_prob': result.get('used_probs', [0])[0],
            'avg_count': result['avg_count'],
            'five_star_up_counts': result.get('five_star_up_counts', {'5星UP武器-1': 0, '5星UP武器-2': 0}),
            'total_pulls': result['total_pulls'],
            'guarantee_up': result['guarantee_up'],
            'four_star_guarantee_up': result.get('four_star_guarantee_up', False),
            'fate_point': result['fate_point'],
            'selected_fate_weapon': result.get('selected_fate_weapon', None),
            'four_star_up_count': result.get('four_star_up_count', 0),
            'four_star_avg_count': result.get('four_star_avg_count', 0),
            'last_five_star_cost': result.get('last_five_star_cost', 0)
        })

    def process_weapon_ten_result(self, result):
        """处理武器十连结果，转换为前端需要的格式"""
        return jsonify({
            'results': result['results'],
            'weapon_names': result['weapon_names'],
            'four_star_results': result['four_star_results'],
            'is_up': result['is_up'],
            'is_four_star_up': result['is_four_star_up'],
            'is_fate': result['is_fate'],
            'current_pity': result['new_pity'],
            'four_star_pity': result['new_four_star_pity'],
            'used_probs': result.get('used_probs', [0] * 10),
            'avg_count': result['avg_count'],
            'five_star_up_counts': result.get('five_star_up_counts', {'5星UP武器-1': 0, '5星UP武器-2': 0}),
            'total_pulls': result['total_pulls'],
            'guarantee_up': result['guarantee_up'],
            'four_star_guarantee_up': result.get('four_star_guarantee_up', False),
            'fate_point': result['fate_point'],
            'selected_fate_weapon': result.get('selected_fate_weapon', None),
            'four_star_up_count': result.get('four_star_up_count', 0),
            'four_star_avg_count': result.get('four_star_avg_count', 0),
            'last_five_star_cost': result.get('last_five_star_cost', 0)
        })


# 创建服务器实例
server = WishServer()

@app.route('/api/wish', methods=['POST'])
def handle_wish():
    """处理祈愿请求"""
    return server.handle_wish()

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
        'message': 'Wish Simulator API',
        'endpoints': [
            '/api/wish',
            '/api/goal_probability',
            '/api/required_pulls_for_95_percent',
            '/api/required_pulls_for_50_percent',
            '/api/shutdown'
        ]
    })


if __name__ == '__main__':
    print("Starting Wish Simulator Server...")
    print("API endpoints:")
    print("  - POST /api/wish")
    print("  - POST /api/goal_probability")
    print("  - POST /api/required_pulls_for_95_percent")
    print("  - POST /api/required_pulls_for_50_percent")
    print("  - POST /api/shutdown")
    print("  - GET  /api/")
    app.run(host='0.0.0.0', port=8888, debug=True)
