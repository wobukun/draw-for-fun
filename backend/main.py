#!/usr/bin/env python3
"""祈愿模拟器服务器启动脚本

简要说明：
- 祈愿模拟器的启动入口
- 负责启动服务器管理器并运行

主要用法：
- 运行：`python backend/main.py`
- 系统会自动启动前端和后端服务器
"""

import sys
import os

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.server.server_manager import WishServerManager

def main():
    """主函数"""
    manager = WishServerManager()
    manager.run()

if __name__ == "__main__":
    main()