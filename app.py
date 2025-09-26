#!/usr/bin/env python3
"""
Streamlit Cloud兼容性启动文件

这个文件作为Streamlit Cloud的入口点，将请求转发到新的项目结构中。
由于项目重构为标准Python包结构，真正的应用位于 src/model_finetune_ui/app.py
"""

import sys
from pathlib import Path

# 添加src目录到Python路径，支持包导入
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    # 导入并运行真正的应用
    from model_finetune_ui.app import main

    # 运行主应用
    if __name__ == "__main__":
        main()

except ImportError as e:
    import streamlit as st
    st.error(f"导入错误: {e}")
    st.error("请确保项目结构正确，并且所有依赖都已安装。")
    st.stop()
