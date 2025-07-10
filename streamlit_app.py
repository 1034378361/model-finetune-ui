#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model Finetune UI - Streamlit Cloud专用版本
简化版本，避免复杂依赖导致的部署问题
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import json
import tempfile
import base64
import io

# 配置Streamlit页面
st.set_page_config(
    page_title="Model Finetune UI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 水质参数定义
WATER_QUALITY_PARAMS = [
    'turbidity', 'ss', 'sd', 'do', 'codmn', 
    'codcr', 'chla', 'tn', 'tp', 'chroma', 'nh3n'
]

# 特征列表
FEATURES = [f'STZ{i}' for i in range(1, 26)]

def generate_template(template_type: str) -> str:
    """生成模板CSV内容"""
    if template_type == 'Range':
        # Range模板：行为水质参数，列为min和max
        df = pd.DataFrame(
            index=WATER_QUALITY_PARAMS,
            columns=['min', 'max']
        )
        # 填充示例数据
        example_ranges = {
            'turbidity': (0.1, 50.0),
            'ss': (1.0, 100.0),
            'sd': (0.1, 5.0),
            'do': (2.0, 15.0),
            'codmn': (0.5, 10.0),
            'codcr': (5.0, 50.0),
            'chla': (0.1, 20.0),
            'tn': (0.1, 5.0),
            'tp': (0.01, 0.5),
            'chroma': (5.0, 100.0),
            'nh3n': (0.01, 2.0)
        }
        for param in WATER_QUALITY_PARAMS:
            if param in example_ranges:
                df.loc[param, 'min'] = example_ranges[param][0]
                df.loc[param, 'max'] = example_ranges[param][1]
        
        return df.to_csv()
    
    elif template_type == 'A':
        # A系数模板：行为水质参数，列为A
        df = pd.DataFrame(
            index=WATER_QUALITY_PARAMS,
            columns=['A'],
            data=1.0  # 默认填充1.0
        )
        return df.to_csv()
    
    elif template_type in ['w', 'a']:
        # w/a系数模板：行为特征，列为水质参数
        df = pd.DataFrame(
            index=FEATURES,
            columns=WATER_QUALITY_PARAMS,
            data=np.random.uniform(0.1, 2.0, (len(FEATURES), len(WATER_QUALITY_PARAMS)))
        )
        return df.to_csv()
    
    elif template_type == 'b':
        # b系数模板：行为水质参数，列为特征
        df = pd.DataFrame(
            index=WATER_QUALITY_PARAMS,
            columns=FEATURES,
            data=np.random.uniform(0.5, 2.0, (len(WATER_QUALITY_PARAMS), len(FEATURES)))
        )
        return df.to_csv()
    
    return ""

def process_range_data(range_df: pd.DataFrame) -> dict:
    """处理Range数据，计算min/max"""
    result = {}
    for param in range_df.index:
        if param in WATER_QUALITY_PARAMS:
            result[param] = {
                'min': float(range_df.loc[param, 'min']),
                'max': float(range_df.loc[param, 'max'])
            }
    return result

def format_model_result(processed_data: dict, model_type: int) -> dict:
    """格式化模型结果"""
    result = {
        'model_type': model_type,
        'timestamp': datetime.now().isoformat(),
        'Range': {}
    }
    
    # 处理Range数据
    if 'Range' in processed_data:
        result['Range'] = process_range_data(processed_data['Range'])
    
    if model_type == 1:
        # Type 1: 需要w, a, b系数，A自动生成
        if 'w' in processed_data:
            result['w'] = processed_data['w'].values.flatten().tolist()
        if 'a' in processed_data:
            result['a'] = processed_data['a'].values.flatten().tolist()  
        if 'b' in processed_data:
            result['b'] = processed_data['b'].values.flatten().tolist()
        
        # 自动生成A系数
        if 'Range' in processed_data:
            A_coefficients = pd.DataFrame(1.0, index=WATER_QUALITY_PARAMS, columns=['A'])
            result['A'] = A_coefficients.values.flatten().tolist()
    else:
        # Type 0: 使用用户上传的A系数
        if 'A' in processed_data:
            result['A'] = processed_data['A'].values.flatten().tolist()
    
    return result

def main():
    """主函数"""
    st.title("🚀 Model Finetune UI")
    st.markdown("---")
    
    # 显示欢迎信息
    st.markdown("""
    ### 📋 功能说明
    - **Model Type 0**: 模型微调模式（仅使用A系数）
    - **Model Type 1**: 完整建模模式（使用w、a、b、A系数）
    - **Range数据**: 用于计算指标范围的参考数据
    """)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置选项")
        
        # Model Type选择
        model_type = st.selectbox(
            "选择模型类型",
            options=[0, 1],
            format_func=lambda x: f"Type {x} - {'微调模式' if x == 0 else '完整建模模式'}",
            help="Type 0: 仅使用A系数进行微调\nType 1: 使用完整的w、a、b、A系数建模"
        )
        
        # 显示环境信息
        st.markdown("---")
        st.subheader("📊 环境信息")
        st.metric("Python版本", f"{os.sys.version_info.major}.{os.sys.version_info.minor}")
        st.metric("Pandas版本", pd.__version__)
        st.metric("NumPy版本", np.__version__)
    
    # 模板下载区域
    st.header("📥 下载模板文件")
    
    if model_type == 1:
        required_templates = ['w', 'a', 'b', 'Range']
        template_descriptions = {
            'w': 'w权重系数模板',
            'a': 'a权重系数模板', 
            'b': 'b幂系数模板',
            'Range': 'Range数据模板'
        }
    else:
        required_templates = ['A', 'Range']
        template_descriptions = {
            'A': 'A微调系数模板',
            'Range': 'Range数据模板'
        }
    
    # 创建下载按钮
    cols = st.columns(len(required_templates))
    for i, template_type in enumerate(required_templates):
        with cols[i]:
            template_content = generate_template(template_type)
            st.download_button(
                label=f"📥 {template_descriptions[template_type]}",
                data=template_content,
                file_name=f"{template_type}_template.csv",
                mime='text/csv',
                help=f"下载{template_descriptions[template_type]}的CSV模板文件"
            )
    
    st.markdown("---")
    
    # 文件上传区域
    st.header("📁 数据文件上传")
    
    col1, col2 = st.columns(2)
    
    uploaded_files = {}
    
    with col1:
        st.subheader("系数矩阵文件")
        
        if model_type == 1:
            # Type 1需要上传w, a, b文件
            uploaded_files['w'] = st.file_uploader(
                "📄 上传CSV文件 - w权重系数",
                type=['csv'],
                help="w权重系数矩阵，行为特征，列为水质参数"
            )
            
            uploaded_files['a'] = st.file_uploader(
                "📄 上传CSV文件 - a权重系数",
                type=['csv'],
                help="a权重系数矩阵，行为特征，列为水质参数"
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
    
    # 处理按钮
    if st.button("🚀 开始处理", type="primary", use_container_width=True):
        # 验证文件
        if model_type == 1:
            required_files = ['w', 'a', 'b', 'Range']
        else:
            required_files = ['A', 'Range']
        
        missing_files = [f for f in required_files if not uploaded_files.get(f)]
        
        if missing_files:
            st.error(f"缺少文件：{', '.join(missing_files)}")
        else:
            with st.spinner("正在处理文件..."):
                try:
                    # 读取上传的文件
                    processed_data = {}
                    
                    for file_type, uploaded_file in uploaded_files.items():
                        if uploaded_file is not None:
                            df = pd.read_csv(uploaded_file, index_col=0)
                            processed_data[file_type] = df
                            st.success(f"✅ {file_type}文件读取成功：{df.shape}")
                    
                    # 处理数据
                    result = format_model_result(processed_data, model_type)
                    
                    if result:
                        # 生成结果文件
                        result_json = json.dumps(result, indent=2, ensure_ascii=False)
                        
                        # 显示结果
                        st.header("🎯 处理结果")
                        
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            st.success("✅ 处理完成")
                            st.metric("文件大小", f"{len(result_json)} bytes")
                            
                            # 下载按钮
                            st.download_button(
                                label="📥 下载模型文件",
                                data=result_json,
                                file_name=f"model_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime='application/json'
                            )
                        
                        with col4:
                            st.markdown(f"""
                            **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            
                            **说明**：
                            - 模型文件已生成
                            - 包含所有必要的系数数据
                            - 可以直接用于后续的水质预测
                            """)
                        
                        # 显示处理的数据概览
                        with st.expander("📊 数据概览"):
                            st.json(result)
                    
                except Exception as e:
                    st.error(f"处理过程中发生错误：{str(e)}")
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    🚀 Model Finetune UI v1.0.0 - 水质模型微调Web应用
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()