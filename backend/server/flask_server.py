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
        if len(result['results']) == len(result['is_up']) == len(result['used_probs']):
            is_5star, is_up, prob = result['results'][0], result['is_up'][0], result['used_probs'][0]
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
                'guarantee_up': result['guarantee_up']
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
        if len(result['results']) == len(result['is_up']) == len(result['used_probs']):
            for i, (is_5star, is_up, prob) in enumerate(zip(result['results'], result['is_up'], result['used_probs'])):
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
                    'probability': prob
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