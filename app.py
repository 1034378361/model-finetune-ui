#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model Finetune UI项目 - 主应用

基于Streamlit构建的Web界面，允许用户：
1. 选择model_type（0或1）
2. 上传5个CSV文件（w, a, b, A, Range）
3. 生成加密的模型文件
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import tempfile
import logging

# 添加主项目路径，以便引用其模块
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.processor import ModelProcessor
from utils.encryption import EncryptionManager
from utils.file_handler import FileHandler
from utils.validator import DataValidator
from utils.template_generator import TemplateGenerator
from utils.utils import performance_monitor, EnhancedLogger

# 配置Streamlit页面
st.set_page_config(
    page_title="Model Finetune UI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelFinetuneApp:
    """主应用类"""
    
    def __init__(self):
        self.processor = ModelProcessor()
        self.encryptor = EncryptionManager()
        self.file_handler = FileHandler()
        self.validator = DataValidator()
        self.template_generator = TemplateGenerator()
        
        # 初始化session state
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
        if 'result_path' not in st.session_state:
            st.session_state.result_path = None
            
    def render_header(self):
        """渲染页面头部"""
        st.title("🚀 Model Finetune UI")
        st.markdown("---")
        st.markdown("""
        ### 📋 功能说明
        - **Model Type 0**: 模型微调模式（仅使用A系数）
        - **Model Type 1**: 完整建模模式（使用w、a、b、A系数）
        - **Range数据**: 用于计算指标范围的参考数据
        """)
        
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.header("⚙️ 配置选项")
            
            # Model Type选择
            model_type = st.selectbox(
                "选择模型类型",
                options=[0, 1],
                format_func=lambda x: f"Type {x} - {'微调模式' if x == 0 else '完整建模模式'}",
                help="Type 0: 仅使用A系数进行微调\nType 1: 使用完整的w、a、b、A系数建模"
            )
            
            # 输出目录设置
            output_dir = st.text_input(
                "输出目录",
                value="./ui_output",
                help="生成的模型文件保存位置"
            )
            
            return model_type, output_dir
    
    def render_file_upload_section(self, model_type: int):
        """渲染文件上传区域"""
        st.header("📁 数据文件上传")
        
        # 添加模板下载区域
        self.render_template_download_section(model_type)
        
        col1, col2 = st.columns(2)
        
        uploaded_files = {}
        
        with col1:
            st.subheader("系数矩阵文件")
            
            if model_type == 1:
                # Type 1需要上传w, a, b文件
                uploaded_files['w'] = st.file_uploader(
                    "📄 上传CSV文件 - w权重系数",
                    type=['csv'],
                    help="w权重系数矩阵，行为水质参数，列为特征"
                )
                
                uploaded_files['a'] = st.file_uploader(
                    "📄 上传CSV文件 - a权重系数",
                    type=['csv'],
                    help="a权重系数矩阵，行为水质参数，列为特征"
                )
                
                uploaded_files['b'] = st.file_uploader(
                    "📄 上传CSV文件 - b幂系数",
                    type=['csv'],
                    help="b幂系数矩阵，行为水质参数，列为特征"
                )
                
                # Type 1模式说明：A系数自动生成
                st.info("💡 **微调系数说明**: Type 1模式将根据Range数据自动生成微调系数（全部设为1.0），无需手动上传")
            else:
                # Type 0需要A系数文件
                uploaded_files['A'] = st.file_uploader(
                    "📄 上传CSV文件 - A微调系数",
                    type=['csv'],
                    help="微调系数矩阵，行为水质参数，列为A"
                )
        
        with col2:
            st.subheader("范围数据文件")
            
            uploaded_files['Range'] = st.file_uploader(
                "📄 上传CSV文件 - Range数据",
                type=['csv'],
                help="用于计算指标范围的参考数据，包含各水质参数的观测值"
            )
            
            # 显示文件格式说明
            with st.expander("📖 文件格式说明"):
                if model_type == 1:
                    st.markdown("""
                    **Type 1 - 完整建模模式文件要求**：
                    
                    **w权重系数矩阵格式**：
                    - 行索引：特征编号（STZ1, STZ2, ..., STZ25）
                    - 列索引：水质参数（turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n）
                    - 数据类型：浮点数
                    
                    **a权重系数矩阵格式**：
                    - 行索引：特征编号（STZ1, STZ2, ..., STZ25）
                    - 列索引：水质参数（turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n）
                    - 数据类型：浮点数
                    
                    **b幂系数矩阵格式**：
                    - 行索引：水质参数（turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n）
                    - 列索引：特征编号（STZ1, STZ2, ..., STZ25）
                    - 数据类型：浮点数
                    
                    **Range数据格式**：
                    - **行索引**：水质参数名称（turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n）
                    - **列索引**：min和max（最小值和最大值）
                    - **数据内容**：每个水质参数的取值范围
                    - **注意**：A微调系数将根据此数据的行索引自动生成（全部设为1.0）
                    
                    **💡 提示**：
                    - 可以先下载对应的模板文件，填入数据后上传
                    - 模板文件已包含正确的行列名称格式
                    """)
                else:
                    st.markdown("""
                    **Type 0 - 微调模式文件要求**：
                    
                    **A微调系数矩阵格式**：
                    - 行索引：水质参数（turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n）
                    - 列索引：A列
                    - 数据类型：浮点数
                    
                    **Range数据格式**：
                    - **行索引**：水质参数名称（turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n）
                    - **列索引**：min和max（最小值和最大值）
                    - **数据内容**：每个水质参数的取值范围
                    
                    **💡 提示**：
                    - 可以先下载对应的模板文件，填入数据后上传
                    - 模板文件已包含正确的行列名称格式
                    """)
        
        return uploaded_files
    
    def render_template_download_section(self, model_type: int):
        """渲染模板下载区域"""
        st.subheader("📥 下载模板文件")
        
        # 获取当前模型类型需要的模板
        required_templates = self.template_generator.get_required_templates(model_type)
        template_info = self.template_generator.get_template_info()
        
        # 创建下载按钮列
        cols = st.columns(len(required_templates))
        
        for i, template_type in enumerate(required_templates):
            with cols[i]:
                info = template_info[template_type]
                
                # 生成模板内容
                if template_type == 'Range':
                    template_content = self.template_generator.generate_range_template()
                else:
                    template_content = self.template_generator.generate_coefficient_template(template_type)
                
                # 下载按钮
                st.download_button(
                    label=f"📥 {info['name']}",
                    data=template_content,
                    file_name=info['filename'],
                    mime='text/csv',
                    help=info['description']
                )
        
        st.markdown("---")
    
    def validate_uploaded_files(self, uploaded_files: Dict, model_type: int):
        """验证上传的文件"""
        errors = []
        
        # 检查必需文件
        if model_type == 1:
            required_files = ['w', 'a', 'b', 'Range']  # Type 1不需要A文件，自动生成
        else:
            required_files = ['A', 'Range']  # Type 0需要A文件
        
        for file_type in required_files:
            if not uploaded_files.get(file_type):
                errors.append(f"缺少{file_type}文件")
        
        if errors:
            st.error("文件验证失败：" + "、".join(errors))
            return False
        
        return True
    
    @performance_monitor("process_uploaded_files")
    def process_uploaded_files(self, uploaded_files: Dict, model_type: int, output_dir: str):
        """处理上传的文件"""
        try:
            with st.spinner("正在处理文件..."):
                # 记录操作上下文
                EnhancedLogger.log_operation_context(
                    "process_uploaded_files",
                    model_type=model_type,
                    files_count=len(uploaded_files),
                    output_dir=output_dir
                )
                
                # 读取上传的文件
                processed_data = {}
                
                for file_type, uploaded_file in uploaded_files.items():
                    if uploaded_file is not None:
                        df = self.file_handler.read_uploaded_file(uploaded_file, file_type)
                        if df is not None:
                            processed_data[file_type] = df
                            st.success(f"✅ {file_type}文件读取成功：{df.shape}")
                            EnhancedLogger.log_data_summary(df, f"{file_type}文件")
                        else:
                            st.error(f"❌ {file_type}文件读取失败")
                            return None
                
                # 验证数据格式
                if not self.validator.validate_data_format(processed_data, model_type):
                    st.error("数据格式验证失败")
                    return None
                
                # 处理数据
                result = self.processor.process_user_data(processed_data, model_type)
                
                if result:
                    # 加密保存
                    encrypted_path = self.encryptor.encrypt_and_save(result, output_dir)
                    
                    if encrypted_path:
                        st.success(f"🎉 处理完成！模型文件已保存到：{encrypted_path}")
                        return encrypted_path
                    else:
                        st.error("加密保存失败")
                        return None
                else:
                    st.error("数据处理失败")
                    return None
                    
        except Exception as e:
            st.error(f"处理过程中发生错误：{str(e)}")
            logger.error(f"处理错误：{traceback.format_exc()}")
            return None
    
    def render_result_section(self, result_path: str):
        """渲染结果显示区域"""
        if result_path:
            st.header("🎯 处理结果")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"📄 模型文件：{result_path}")
                
                # 显示文件信息
                if os.path.exists(result_path):
                    file_size = os.path.getsize(result_path)
                    st.metric("文件大小", f"{file_size} bytes")
                    
                    # 提供下载按钮
                    with open(result_path, 'rb') as f:
                        file_data = f.read()
                    
                    st.download_button(
                        label="📥 下载模型文件",
                        data=file_data,
                        file_name=os.path.basename(result_path),
                        mime='application/octet-stream'
                    )
            
            with col2:
                st.success("✅ 处理完成")
                st.markdown(f"""
                **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                
                **说明**：
                - 模型文件已加密保存
                - 可以直接用于后续的水质预测
                - 请妥善保管加密文件
                """)
    
    def run(self):
        """运行主应用"""
        # 渲染页面
        self.render_header()
        
        # 获取配置
        model_type, output_dir = self.render_sidebar()
        
        # 文件上传区域
        uploaded_files = self.render_file_upload_section(model_type)
        
        # 处理按钮
        if st.button("🚀 开始处理", type="primary", use_container_width=True):
            if self.validate_uploaded_files(uploaded_files, model_type):
                result_path = self.process_uploaded_files(uploaded_files, model_type, output_dir)
                if result_path:
                    st.session_state.processing_complete = True
                    st.session_state.result_path = result_path
                    st.rerun()
        
        # 显示结果
        if st.session_state.processing_complete and st.session_state.result_path:
            self.render_result_section(st.session_state.result_path)
        
        # 页脚
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
        🚀 Model Finetune UI - 基于原项目的数据处理界面
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    app = ModelFinetuneApp()
    app.run()