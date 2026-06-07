"""稳定启动服务器脚本"""
import os
import sys

# 设置环境变量
os.environ.setdefault('FLASK_APP', 'app')
os.environ.setdefault('FLASK_ENV', 'development')

from app import app, init_db

if __name__ == "__main__":
    print("=== 启动 AI 小说转剧本工具 ===")
    init_db()
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        print(f"服务器启动失败: {e}")
        sys.exit(1)