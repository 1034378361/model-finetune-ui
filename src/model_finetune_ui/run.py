#!/usr/bin/env python
"""
启动脚本

运行Model Finetune UI应用
"""

import os
import subprocess
import sys
from pathlib import Path


def setup_environment():
    """设置环境"""
    # 添加项目根路径
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 设置环境变量
    os.environ.setdefault("UI_DEBUG", "false")
    os.environ.setdefault("UI_OUTPUT_DIR", "./ui_output")

    # 检查依赖
    try:
        import numpy
        import pandas
        import streamlit

        print("✅ 基本依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: uv sync")
        sys.exit(1)


def check_main_project():
    """检查主项目是否可用"""
    try:
        # 尝试导入关键模块
        from model_finetune_ui.utils.encryption import EncryptionManager
        from model_finetune_ui.utils.validator import DataValidator

        print("✅ 关键模块检查通过")
        return True
    except ImportError as e:
        print(f"⚠️ 关键模块导入失败: {e}")
        print("请确保项目依赖已正确安装")
        return False


def get_python_executable():
    """获取当前Python解释器路径"""
    # 优先使用当前Python解释器
    return sys.executable


def run_streamlit_app():
    """运行Streamlit应用"""
    try:
        # 设置Streamlit配置
        app_path = Path(__file__).parent / "app.py"
        python_exe = get_python_executable()

        cmd = [
            python_exe,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.port",
            "8501",
            "--server.address",
            "localhost",
        ]

        print("🚀 启动Streamlit应用")
        print(f"📍 Python解释器: {python_exe}")
        print(f"📄 应用文件: {app_path}")

        # 运行应用
        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动应用时发生错误: {e}")
        print("💡 建议使用: uv run streamlit run app.py")
        sys.exit(1)


def main():
    """主函数"""
    print("🚀 Model Finetune UI 启动器")
    print("=" * 50)

    # 设置环境
    print("🔧 设置环境...")
    setup_environment()

    # 检查关键模块
    print("🔍 检查关键模块...")
    if not check_main_project():
        print("⚠️ 关键模块检查失败，某些功能可能不可用")
        response = input("是否继续启动？(y/N): ")
        if response.lower() != 'y':
            sys.exit(1)

    # 运行应用
    print("🌐 启动Web应用...")
    run_streamlit_app()


if __name__ == "__main__":
    main()
