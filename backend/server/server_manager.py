#!/usr/bin/env python3
"""抽卡模拟器服务器管理器

简要说明：
- 抽卡模拟器的服务器管理模块
- 负责管理前端和后端服务器的启动、监控和停止
- 提供服务器状态检查和进程管理功能

主要功能：
- 检查Node.js安装状态
- 启动后端API服务器
- 启动前端开发服务器
- 监控服务器进程状态
- 停止服务器进程
"""

import sys
import os
import subprocess

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
import time
import webbrowser
import re
import threading
import socket

# 添加当前目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class GachaServerManager:
    """抽卡模拟器服务器管理器"""
    
    def __init__(self):
        """初始化服务器管理器"""
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # 初始化属性
        self.backend_port = None
        self.backend_process = None
        self.frontend_process = None
        self.node_installed = False
        self.npm_path = None
    
    def _check_npm_path(self, npm_path):
        """检查指定的npm路径是否有效"""
        try:
            # 在Windows中，使用shell=True来确保命令正确执行
            if sys.platform == 'win32':
                result = subprocess.run(
                    npm_path + " --version",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=1.5,  # 减少超时时间
                    text=True
                )
            else:
                result = subprocess.run(
                    [npm_path, "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=1.5,  # 减少超时时间
                    text=True
                )
            
            if result.returncode == 0:
                print(f"✓ Node.js版本: {result.stdout.strip()}")
                return True, npm_path
        except FileNotFoundError:
            pass  # 快速跳过不存在的路径
        except Exception:
            pass  # 快速跳过执行失败的路径
        return False, None
    
    def _check_standard_npm_paths(self):
        """检查标准的npm路径"""
        # 尝试直接使用npm的路径
        npm_paths = ["npm", "npm.cmd"]
        
        for npm_path in npm_paths:
            found, valid_path = self._check_npm_path(npm_path)
            if found:
                return True, valid_path
        return False, None
    
    def _check_common_npm_paths(self):
        """检查常见的npm安装路径"""
        # 如果标准路径失败，尝试常见的安装路径
        common_paths = [
            "C:\\Program Files\\nodejs\\npm.cmd",
            "C:\\Program Files (x86)\\nodejs\\npm.cmd"
        ]
        
        for npm_path in common_paths:
            if os.path.exists(npm_path):
                found, valid_path = self._check_npm_path(npm_path)
                if found:
                    return True, valid_path
        return False, None
    
    def check_node_installed(self):
        """检查Node.js是否安装"""
        print("=== 检查Node.js安装状态 ===")
        
        # 尝试标准路径
        found, npm_path = self._check_standard_npm_paths()
        if found:
            return True, npm_path
        
        # 尝试常见安装路径
        found, npm_path = self._check_common_npm_paths()
        if found:
            return True, npm_path
        
        print("✗ 未找到Node.js")
        return False, None
    
    def is_port_in_use(self, port):
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.05)  # 减少超时时间
                return s.connect_ex(('localhost', port)) == 0
        except Exception:
            return True
    
    def is_backend_server(self, port):
        """验证指定端口是否运行着后端服务器"""
        try:
            # 延迟导入http.client模块
            import http.client
            conn = http.client.HTTPConnection('localhost', port, timeout=0.2)  # 进一步减少超时时间
            conn.request('GET', '/')
            response = conn.getresponse()
            conn.close()
            # 只要能建立连接并获得响应，就认为服务器已启动
            return True
        except Exception:
            return False
    
    def find_backend_port(self):
        """查找后端服务器实际使用的端口"""
        print("正在查找后端服务器端口...")
        # 从8888开始查找，最多尝试5个端口
        for port in range(8888, 8893):
            if self.is_port_in_use(port) and self.is_backend_server(port):
                print(f"✓ 发现后端服务器在端口: {port}")
                return str(port)
        print("✗ 未找到后端服务器端口，使用默认端口")
        return "8888"  # 默认端口，与flask_server.py保持一致
    
    def start_backend_server(self):
        """启动后端服务器"""
        print("=== 启动后端服务器 ===")
        backend_dir = os.path.join(self.project_root, "backend", "server")
        flask_server_path = os.path.join(backend_dir, "flask_server.py")
        
        print(f"后端目录: {backend_dir}")
        print(f"后端服务器文件: {flask_server_path}")
        
        if not os.path.exists(flask_server_path):
            print(f"✗ 错误：找不到后端服务器文件 {flask_server_path}")
            return False
        
        print(f"✓ 后端服务器文件存在")
        
        try:
            # 检查端口是否已经被占用
            print(f"检查端口 {8888} 是否被占用")
            if self.is_port_in_use(8888):
                print(f"✗ 错误：端口 {8888} 已被占用，请先关闭占用该端口的进程")
                return False
            
            # 启动后端服务器
            print("正在启动后端服务器...")
            print(f"启动命令: {sys.executable} flask_server.py")
            print(f"工作目录: {backend_dir}")
            
            # 启动后端服务器
            print("使用标准的进程创建方式启动后端服务器")
            # 不重定向输出，让后端服务器的输出直接显示在终端中
            self.backend_process = subprocess.Popen(
                [sys.executable, "flask_server.py"],
                cwd=backend_dir,
                shell=False
            )
            
            # 打印进程信息
            print(f"后端进程ID: {self.backend_process.pid}")
            print(f"后端进程状态: {self.backend_process.poll()}")
            
            # 等待服务器启动（减少等待时间）
            print("等待后端服务器启动...")
            for i in range(2):  # 减少等待次数
                time.sleep(0.5)  # 减少每次等待时间
                if self.backend_process.poll() is not None:
                    print(f"✗ 后端服务器进程已退出，退出码: {self.backend_process.poll()}")
                    return False
                print(f"... {i+1}秒")
            
            # 检查进程是否还在运行
            if self.backend_process.poll() is not None:
                print(f"✗ 后端服务器进程已退出，退出码: {self.backend_process.poll()}")
                return False
            
            # 直接设置后端服务器端口为默认值 8888
            # 因为我们已经确认 Flask 后端服务器会使用这个端口
            self.backend_port = "8888"
            print(f"✓ 后端服务器启动成功，使用端口: {self.backend_port}")
            return True
        except Exception as e:
            print(f"✗ 启动后端服务器失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_vite_config(self):
        """更新前端的vite.config.js文件，设置正确的代理端口"""
        print("=== 更新前端配置文件 ===")
        vite_config_path = os.path.join(self.project_root, "vite.config.js")
        
        if not os.path.exists(vite_config_path):
            print(f"✗ 错误：找不到vite.config.js文件 {vite_config_path}")
            return False
        
        try:
            # 读取当前配置
            print(f"正在读取vite.config.js文件: {vite_config_path}")
            with open(vite_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新代理配置的端口
            print(f"正在检查代理端口是否需要更新为: {self.backend_port}")
            updated_content = re.sub(
                r'target: \'http://localhost:\d+\'',
                f'target: \'http://localhost:{self.backend_port}\'',
                content
            )
            
            # 只有当内容确实发生变化时才写入文件
            if updated_content != content:
                print(f"正在写入更新后的vite.config.js文件")
                with open(vite_config_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"✓ 已更新vite.config.js，代理端口设置为: {self.backend_port}")
            else:
                print(f"✓ vite.config.js文件已存在且代理端口正确，无需更新")
            
            return True
        except Exception as e:
            print(f"✗ 更新vite.config.js失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def start_frontend_server(self, npm_path):
        """启动前端开发服务器"""
        print("=== 启动前端开发服务器 ===")
        
        # 检查package.json是否存在
        package_json_path = os.path.join(self.project_root, "package.json")
        if not os.path.exists(package_json_path):
            print(f"✗ 错误：找不到package.json文件 {package_json_path}")
            print("请确保您在正确的项目目录中")
            return False
        
        print(f"✓ 前端项目路径: {self.project_root}")
        try:
            # 启动前端开发服务器
            print(f"正在使用npm路径: {npm_path}")
            print("正在启动前端开发服务器...")
            if sys.platform == 'win32':
                # 在Windows上，使用shell=True来确保命令正确执行
                self.frontend_process = subprocess.Popen(
                    f"{npm_path} run dev",
                    shell=True,
                    cwd=self.project_root
                )
            else:
                # 在非Windows系统上
                self.frontend_process = subprocess.Popen(
                    [npm_path, "run", "dev"],
                    cwd=self.project_root
                )
            
            # 简化前端服务器启动检查，只检查进程是否启动
            print("等待前端开发服务器启动...")
            for i in range(3):  # 减少等待次数
                time.sleep(0.8)  # 减少每次等待时间
                if self.frontend_process.poll() is not None:
                    print(f"✗ 前端开发服务器进程已退出，退出码: {self.frontend_process.poll()}")
                    return False
                print(f"... {i+1}秒")
            
            # 检查进程是否还在运行
            if self.frontend_process.poll() is not None:
                print(f"✗ 前端开发服务器进程已退出，退出码: {self.frontend_process.poll()}")
                return False
            
            print("✓ 前端开发服务器启动成功")
            return True
        except Exception as e:
            print(f"✗ 启动前端开发服务器失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _try_terminate_process(self, process, name):
        """尝试使用terminate()停止进程"""
        print(f"1. 尝试使用terminate()停止{name}进程...")
        process.terminate()
        
        # 等待进程结束
        try:
            process.wait(timeout=2)
            if process.poll() is not None:
                print(f"✓ {name}进程已停止，退出码: {process.poll()}")
                return True
        except subprocess.TimeoutExpired:
            print(f"{name}进程未在2秒内停止，继续尝试...")
        return False
    
    def _try_taskkill_process(self, process, name):
        """在Windows上尝试使用taskkill停止进程及其子进程"""
        print(f"2. 尝试使用taskkill停止{name}进程及其子进程...")
        # 尝试使用taskkill /F /T 强制终止进程及其子进程
        result = subprocess.run(
            ['taskkill', '/F', '/T', '/PID', str(process.pid)],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"taskkill命令输出: {result.stdout}")
        if result.stderr:
            print(f"taskkill命令错误: {result.stderr}")
        
        # 等待进程结束
        try:
            process.wait(timeout=3)
            if process.poll() is not None:
                print(f"✓ {name}进程已停止，退出码: {process.poll()}")
                return True
        except subprocess.TimeoutExpired:
            print(f"{name}进程未在3秒内停止，继续尝试...")
        return False
    
    def _try_kill_process(self, process, name):
        """在非Windows系统上尝试使用kill()强制停止进程"""
        print(f"2. 尝试使用kill()强制停止{name}进程...")
        process.kill()
        # 等待进程结束
        try:
            process.wait(timeout=3)
            if process.poll() is not None:
                print(f"✓ {name}进程已停止，退出码: {process.poll()}")
                return True
        except subprocess.TimeoutExpired:
            print(f"{name}进程未在3秒内停止，继续尝试...")
        return False
    
    def _stop_port_process(self, port):
        """尝试停止占用指定端口的进程"""
        print(f"3. 检查后端服务器端口 {port} 是否仍然被占用...")
        if self.is_port_in_use(int(port)):
            print(f"端口 {port} 仍然被占用，尝试查找并终止占用该端口的进程...")
            if sys.platform == 'win32':
                # 在Windows上，使用netstat查找占用端口的进程
                result = subprocess.run(
                    ['netstat', '-ano'],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                # 查找占用指定端口的进程
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = parts[4]
                            print(f"发现占用端口 {port} 的进程 PID: {pid}")
                            # 尝试终止该进程
                            try:
                                subprocess.run(
                                    ['taskkill', '/F', '/PID', pid],
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                )
                                print(f"尝试终止PID为 {pid} 的进程")
                            except Exception as e:
                                print(f"终止进程时出错: {e}")
    
    def stop_process(self, process, name):
        """停止进程及其子进程"""
        if process is None:
            return
        
        try:
            if process.poll() is not None:
                print(f"{name}进程已经停止，退出码: {process.poll()}")
                return
            
            print(f"正在停止{name}进程 (PID: {process.pid})...")
            
            # 第一次尝试：使用terminate()
            if self._try_terminate_process(process, name):
                return
            
            # 第二次尝试：根据系统类型选择不同的方法
            if sys.platform == 'win32':
                if self._try_taskkill_process(process, name):
                    return
            else:
                if self._try_kill_process(process, name):
                    return
            
            # 第三次尝试：检查端口是否仍然被占用（针对服务器进程）
            if name == "后端服务器" and self.backend_port:
                self._stop_port_process(self.backend_port)
            
            # 最后检查进程状态
            if process.poll() is None:
                print(f"✗ 无法终止{name}进程，可能需要手动停止")
            else:
                print(f"✓ {name}进程已停止，退出码: {process.poll()}")
                
        except Exception as e:
            print(f"✗ 停止{name}进程时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def monitor_process(self, process, name):
        """监控进程状态"""
        if process is None:
            return
        
        print(f"开始监控{name}进程...")
        try:
            # 简单监控进程状态
            while process.poll() is None:
                time.sleep(1)
        except Exception as e:
            print(f"监控{name}进程时出错: {e}")
        
        print(f"{name}进程已停止，退出码: {process.poll()}")
    
    def _stop_frontend_server(self):
        """停止前端服务器"""
        if self.frontend_process:
            self.stop_process(self.frontend_process, "前端开发服务器")
    
    def _stop_backend_server(self):
        """停止后端服务器"""
        if self.backend_process:
            self.stop_process(self.backend_process, "后端服务器")
    
    def _check_backend_port_release(self):
        """检查后端端口是否已释放"""
        if not self.backend_port:
            return
        
        print(f"\n检查后端服务器端口 {self.backend_port} 是否仍然被占用...")
        if self.is_port_in_use(int(self.backend_port)):
            print(f"警告：端口 {self.backend_port} 仍然被占用！")
            if sys.platform == 'win32':
                self._try_stop_port_process(int(self.backend_port))
        else:
            print(f"✓ 后端服务器端口 {self.backend_port} 已释放")
    
    def _try_stop_port_process(self, port):
        """尝试停止占用指定端口的进程"""
        print("尝试查找并终止占用该端口的进程...")
        try:
            # 使用netstat查找占用端口的进程
            result = subprocess.run(
                ['netstat', '-ano'],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # 查找占用指定端口的进程
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[4]
                        print(f"发现占用端口 {port} 的进程 PID: {pid}")
                        # 尝试终止该进程
                        self._kill_process_by_pid(pid)
        except Exception as e:
            print(f"查找并终止占用端口的进程时出错: {e}")
    
    def _kill_process_by_pid(self, pid):
        """通过PID终止进程"""
        try:
            taskkill_result = subprocess.run(
                ['taskkill', '/F', '/PID', pid],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"终止进程结果: {taskkill_result.stdout}")
            if taskkill_result.stderr:
                print(f"终止进程错误: {taskkill_result.stderr}")
        except Exception as e:
            print(f"终止进程时出错: {e}")
    
    def stop_servers(self):
        """停止所有服务器"""
        print("\n=== 停止服务器 ===")
        print("正在停止所有服务器进程...")
        
        # 停止前端服务器
        self._stop_frontend_server()
        
        # 停止后端服务器
        self._stop_backend_server()
        
        # 额外检查：如果后端端口仍然被占用，尝试查找并终止占用该端口的进程
        self._check_backend_port_release()
        
        print("\n✓ 所有服务器已停止")
    
    def start_backend_thread(self):
        """在线程中启动后端服务器"""
        print("=== 启动后端服务器线程 ===")
        try:
            print("调用 start_backend_server 方法...")
            backend_started = self.start_backend_server()
            print(f"start_backend_server 方法返回: {backend_started}")
            if backend_started:
                print("后端服务器启动成功，调用 update_vite_config 方法...")
                self.update_vite_config()
                print("update_vite_config 方法执行完成")
            else:
                print("后端服务器启动失败")
        except Exception as e:
            print(f"后端服务器线程执行出错: {e}")
            import traceback
            traceback.print_exc()
    
    def start_frontend_thread(self):
        """在线程中启动前端服务器"""
        if self.node_installed:
            self.start_frontend_server(self.npm_path)
    
    def _print_startup_header(self):
        """打印启动流程的头部信息"""
        print("=" * 80)
        print("🎮 抽卡模拟器启动流程")
        print("=" * 80)
        print(f"[DEBUG] 项目根目录: {self.project_root}")
        print(f"[DEBUG] 当前目录: {os.getcwd()}")
        print(f"[DEBUG] Python解释器: {sys.executable}")
        print(f"[DEBUG] Python版本: {sys.version}")
        print(f"[DEBUG] 系统平台: {sys.platform}")
        print()
    
    def _check_nodejs_installation(self):
        """检查Node.js是否安装"""
        print("🔍 步骤 1: 检查Node.js安装状态")
        print("-" * 60)
        self.node_installed, self.npm_path = self.check_node_installed()
        print(f"[DEBUG] Node.js安装状态: {'已安装' if self.node_installed else '未安装'}")
        if self.node_installed:
            print(f"[DEBUG] npm路径: {self.npm_path}")
        print()
    
    def _start_servers(self):
        """启动后端和前端服务器"""
        print("🚀 步骤 2: 启动服务器")
        print("-" * 60)
        
        # 直接设置后端服务器端口为默认值 8888
        self.backend_port = "8888"
        print(f"[INFO] 已设置后端服务器端口: {self.backend_port}")
        
        # 启动后端服务器线程
        print("[INFO] 启动后端服务器线程...")
        backend_thread = threading.Thread(target=self.start_backend_thread)
        backend_thread.daemon = True
        backend_thread.start()
        print(f"[DEBUG] 后端服务器线程ID: {backend_thread.ident}")
        
        # 启动前端服务器线程
        print("[INFO] 启动前端服务器线程...")
        frontend_thread = threading.Thread(target=self.start_frontend_thread)
        frontend_thread.daemon = True
        frontend_thread.start()
        print(f"[DEBUG] 前端服务器线程ID: {frontend_thread.ident}")
        
        # 等待前端服务器线程完成启动
        if self.node_installed:
            print("[INFO] 等待前端服务器启动完成...")
            # 给前端服务器一些启动时间
            time.sleep(3)
            print("[INFO] 前端服务器线程启动完成")
        
        return frontend_thread
    
    def _open_browser_and_show_completion(self):
        """打开浏览器并显示启动完成信息"""
        # 打开浏览器
        print()
        print("🌐 步骤 3: 打开浏览器")
        print("-" * 60)
        frontend_url = "http://localhost:3000"
        print(f"[INFO] 正在打开浏览器: {frontend_url}")
        webbrowser.open(frontend_url)
        print(f"[SUCCESS] ✓ 浏览器已打开，请访问: {frontend_url}")
        print()
        
        # 启动完成提示
        print("✅ 步骤 4: 启动完成")
        print("-" * 60)
        print("[INFO] 现在您可以开始使用抽卡模拟器了！")
        print("[INFO] 功能说明:")
        print("  - 单抽：点击'单抽'按钮")
        print("  - 十连：点击'十连'按钮")
        print("  - 自动模拟：点击'自动模拟'按钮")
        print()
        print("[INFO] 服务器状态:")
        print(f"  - 后端服务器: http://localhost:{self.backend_port}")
        print(f"  - 前端服务器: {frontend_url}")
    
    def _show_nodejs_not_installed_message(self):
        """显示Node.js未安装的提示信息"""
        print()
        print("⚠️  步骤 3: Node.js未安装")
        print("-" * 60)
        print("[ERROR] ✗ 错误：未找到Node.js，请先安装Node.js")
        print("[INFO] 下载地址: https://nodejs.org/zh-cn/download/")
        print(f"[SUCCESS] ✓ 后端服务器已启动，使用端口: {self.backend_port}")
        print("[INFO] 您可以在安装Node.js后手动启动前端服务器")
    
    def _monitor_backend_process(self):
        """监控后端服务器进程"""
        print()
        print("👀 步骤 5: 监控服务器状态")
        print("-" * 60)
        print(f"[INFO] 后端服务器正在运行，使用端口: {self.backend_port}")
        print("[INFO] 按 Ctrl+C 停止服务器")
        print("[INFO] 开始监控后端服务器进程...")
        if self.backend_process:
            print(f"[DEBUG] 后端进程ID: {self.backend_process.pid}")
            
            # 简化的进程监控，减少检查频率
            print("[DEBUG] 开始简化的后端进程监控...")
            try:
                # 循环监控进程状态
                while True:
                    # 检查进程是否还在运行
                    poll_result = self.backend_process.poll()
                    if poll_result is not None:
                        print(f"[INFO] 后端服务器进程已停止，退出码: {poll_result}")
                        # 当后端进程被关闭时，关闭所有服务器
                        print("[INFO] 后端服务器进程已关闭，正在停止所有服务器...")
                        self.stop_servers()
                        break
                    
                    # 每 3 秒检查一次，减少输出频率
                    time.sleep(3)
            except Exception as e:
                print(f"[ERROR] 监控后端进程时出错: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[WARNING] 后端进程未初始化，无法监控")
    
    def _handle_keyboard_interrupt(self):
        """处理用户按下Ctrl+C的情况"""
        print()
        print("🛑 中断处理")
        print("-" * 60)
        print("[INFO] 用户按下 Ctrl+C，正在停止服务器...")
    
    def _handle_error(self, e):
        """处理启动过程中的错误"""
        print()
        print("❌ 错误处理")
        print("-" * 60)
        print(f"[ERROR] 错误信息: {e}")
        print("[DEBUG] 错误详情:")
        import traceback
        traceback.print_exc()
    
    def _cleanup_processes(self):
        """清理所有服务器进程"""
        print()
        print("🧹 清理进程")
        print("-" * 60)
        print("[INFO] 正在停止所有服务器进程...")
        self.stop_servers()
        print("[SUCCESS] ✓ 所有服务器进程已停止")
        print("=" * 80)
        print("🎮 抽卡模拟器已退出")
        print("=" * 80)
    
    def run(self):
        """运行服务器管理器"""
        self._print_startup_header()
        
        try:
            # 检查Node.js是否安装
            self._check_nodejs_installation()
            
            # 并行启动后端和前端服务器
            frontend_thread = self._start_servers()
            
            # 等待前端服务器启动
            if self.node_installed:
                self._open_browser_and_show_completion()
            else:
                self._show_nodejs_not_installed_message()
            
            # 监控后端进程
            self._monitor_backend_process()
            
        except KeyboardInterrupt:
            self._handle_keyboard_interrupt()
        except Exception as e:
            self._handle_error(e)
        finally:
            # 清理进程
            self._cleanup_processes()