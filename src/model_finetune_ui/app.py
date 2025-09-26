#!/usr/bin/env python
"""
Model Finetune UI项目 - 主应用

基于Streamlit构建的Web界面，允许用户：
1. 选择model_type（0或1）
2. 上传5个CSV文件（w, a, b, A, Range）
3. 生成加密的模型文件
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import streamlit as st

# 添加项目根路径以支持绝对导入
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入核心模块
try:
    from .core.processor import ModelProcessor
except ImportError:
    # 如果相对导入失败，使用绝对导入
    from src.model_finetune_ui.core.processor import ModelProcessor

# 尝试导入工具模块，如果失败则使用简化版本
try:
    from .utils.encryption import EncryptionManager
    from .utils.decryption import DecryptionManager
    from .utils.file_handler import FileHandler
    from .utils.template_generator import TemplateGenerator
    from .utils.utils import EnhancedLogger, performance_monitor
    from .utils.validator import DataValidator
    UTILS_AVAILABLE = True
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from src.model_finetune_ui.utils.encryption import EncryptionManager
        from src.model_finetune_ui.utils.decryption import DecryptionManager
        from src.model_finetune_ui.utils.file_handler import FileHandler
        from src.model_finetune_ui.utils.template_generator import TemplateGenerator
        from src.model_finetune_ui.utils.utils import EnhancedLogger, performance_monitor
        from src.model_finetune_ui.utils.validator import DataValidator
        UTILS_AVAILABLE = True
    except ImportError as e:
        st.error(f"工具模块导入失败: {e}")
        st.info("应用将以简化模式运行")
        UTILS_AVAILABLE = False

    # 简化版装饰器
    def performance_monitor(name):
        def decorator(func):
            return func

        return decorator

    class EnhancedLogger:
        @staticmethod
        def log_operation_context(*args, **kwargs):
            pass

        @staticmethod
        def log_data_summary(*args, **kwargs):
            pass


# 配置Streamlit页面
st.set_page_config(
    page_title="Model Finetune UI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelFinetuneApp:
    """主应用类"""

    def __init__(self):
        self.processor = ModelProcessor()

        if UTILS_AVAILABLE:
            self.encryptor = EncryptionManager()
            self.decryptor = DecryptionManager()
            self.file_handler = FileHandler()
            self.validator = DataValidator()
            self.template_generator = TemplateGenerator()
        else:
            # 简化模式，使用基本功能
            self.encryptor = None
            self.decryptor = None
            self.file_handler = None
            self.validator = None
            self.template_generator = None

        # 初始化session state
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
        if 'result_path' not in st.session_state:
            st.session_state.result_path = None

    def render_header(self):
        """渲染页面头部"""
        st.title("🚀 Model Finetune UI")
        st.markdown("---")
        st.markdown(
            """
        ### 📋 功能说明
        - **Model Type 0**: 模型微调模式（仅使用A系数）
        - **Model Type 1**: 完整建模模式（使用w、a、b、A系数）
        - **Range数据**: 用于计算指标范围的参考数据
        """
        )

    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.header("⚙️ 配置选项")

            # 应用模式选择
            app_mode = st.selectbox(
                "选择应用模式",
                options=["encrypt", "decrypt"],
                format_func=lambda x: "📦 加密模式 (CSV→BIN)" if x == "encrypt" else "🔓 解密模式 (BIN→CSV)",
                help="加密模式: 上传CSV文件生成加密BIN文件\n解密模式: 上传BIN文件解析并下载CSV文件",
            )

            if app_mode == "encrypt":
                # Model Type选择
                model_type = st.selectbox(
                    "选择模型类型",
                    options=[0, 1],
                    format_func=lambda x: f"Type {x} - {'微调模式' if x == 0 else '完整建模模式'}",
                    help="Type 0: 仅使用A系数进行微调\nType 1: 使用完整的w、a、b、A系数建模",
                )

                # 输出目录设置
                output_dir = st.text_input(
                    "输出目录", value="./ui_output", help="生成的模型文件保存位置"
                )
            else:
                model_type = None
                output_dir = None

            return app_mode, model_type, output_dir

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
                # Type 1需要上传w, a, b, A文件
                uploaded_files['w'] = st.file_uploader(
                    "📄 上传CSV文件 - w权重系数",
                    type=['csv'],
                    help="w权重系数矩阵，行为特征编号，列为水质参数",
                )

                uploaded_files['a'] = st.file_uploader(
                    "📄 上传CSV文件 - a权重系数",
                    type=['csv'],
                    help="a权重系数矩阵，行为特征编号，列为水质参数",
                )

                uploaded_files['b'] = st.file_uploader(
                    "📄 上传CSV文件 - b幂系数",
                    type=['csv'],
                    help="b幂系数矩阵，行为水质参数，列为特征编号",
                )

                uploaded_files['A'] = st.file_uploader(
                    "📄 上传CSV文件 - A微调系数",
                    type=['csv'],
                    help="A微调系数矩阵，行为水质参数，列为A",
                )

                # Type 1模式说明：现在需要A系数
                st.info(
                    "💡 **系数文件说明**: Type 1模式需要上传w、a、b、A四个系数文件和Range数据文件"
                )
            else:
                # Type 0需要A系数文件
                uploaded_files['A'] = st.file_uploader(
                    "📄 上传CSV文件 - A微调系数",
                    type=['csv'],
                    help="微调系数矩阵，行为水质参数，列为A",
                )

        with col2:
            st.subheader("范围数据文件")

            uploaded_files['Range'] = st.file_uploader(
                "📄 上传CSV文件 - Range数据",
                type=['csv'],
                help="用于计算指标范围的参考数据，包含各水质参数的观测值",
            )

            # 显示文件格式说明
            with st.expander("📖 文件格式说明"):
                if model_type == 1:
                    st.markdown(
                        """
                    **Type 1 - 完整建模模式文件要求**：
                    
                    **w权重系数矩阵格式**：
                    - 行索引：特征编号（STZ1, STZ2, ..., STZ26）
                    - 列索引：水质参数（turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n）
                    - 数据类型：浮点数
                    
                    **a权重系数矩阵格式**：
                    - 行索引：特征编号（STZ1, STZ2, ..., STZ26）
                    - 列索引：水质参数（turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n）
                    - 数据类型：浮点数
                    
                    **b幂系数矩阵格式**：
                    - 行索引：水质参数（turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n）
                    - 列索引：特征编号（STZ1, STZ2, ..., STZ26）
                    - 数据类型：浮点数
                    
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
                    """
                    )
                else:
                    st.markdown(
                        """
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
                    """
                    )

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
                    template_content = (
                        self.template_generator.generate_coefficient_template(
                            template_type
                        )
                    )

                # 下载按钮
                st.download_button(
                    label=f"📥 {info['name']}",
                    data=template_content,
                    file_name=info['filename'],
                    mime='text/csv',
                    help=info['description'],
                )

        st.markdown("---")

    def validate_uploaded_files(self, uploaded_files: dict, model_type: int):
        """验证上传的文件"""
        errors = []

        # 检查必需文件
        if model_type == 1:
            required_files = ['w', 'a', 'b', 'A', 'Range']  # Type 1现在也需要A文件
        else:
            required_files = ['A', 'Range']  # Type 0需要A文件

        for file_type in required_files:
            if not uploaded_files.get(file_type):
                errors.append(f"缺少{file_type}文件")

        if errors:
            st.error("文件验证失败：" + "、".join(errors))
            return False

        return True

    def render_decrypt_section(self):
        """渲染解密模式界面"""
        st.header("🔓 模型文件解密")

        st.markdown("""
        ### 📋 功能说明
        - 上传加密的模型BIN文件
        - 自动解密并解析出参数
        - 下载对应的CSV文件
        """)

        # BIN文件上传
        uploaded_bin = st.file_uploader(
            "📄 上传BIN文件",
            type=['bin'],
            help="上传需要解密的模型文件（.bin格式）",
        )

        if uploaded_bin is not None:
            st.success(f"✅ 文件已上传：{uploaded_bin.name} ({uploaded_bin.size} bytes)")

            # 处理按钮
            if st.button("🔓 解密文件", type="primary", use_container_width=True):
                result = self.process_decrypt_file(uploaded_bin)
                if result:
                    st.session_state.decrypt_result = result
                    st.session_state.decrypt_complete = True
                    st.rerun()

        # 显示解密结果
        if getattr(st.session_state, 'decrypt_complete', False) and getattr(st.session_state, 'decrypt_result', None):
            self.render_decrypt_result(st.session_state.decrypt_result)

    def process_decrypt_file(self, uploaded_bin_file):
        """处理BIN文件解密"""
        try:
            # 创建进度条和状态容器
            progress_bar = st.progress(0)
            status_text = st.empty()
            info_container = st.container()

            # 步骤1: 准备文件
            status_text.info("🔍 步骤1/4: 验证和准备文件...")
            progress_bar.progress(25)

            with info_container:
                file_size = len(uploaded_bin_file.read())
                uploaded_bin_file.seek(0)  # 重置文件指针
                st.info(f"📁 文件信息: {uploaded_bin_file.name} ({file_size:,} bytes)")

            # 保存上传的文件到临时位置
            temp_path = Path(f"temp_{uploaded_bin_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_bin_file.read())

            # 步骤2: 解密文件
            status_text.info("🔓 步骤2/4: 解密BIN文件...")
            progress_bar.progress(50)

            decrypted_data = self.decryptor.decrypt_bin_file(str(temp_path))

            if not decrypted_data:
                status_text.error("❌ BIN文件解密失败")
                st.error("解密失败，可能的原因：文件损坏、格式不正确或加密密钥问题")
                temp_path.unlink(missing_ok=True)
                return None

            # 显示解密成功信息
            model_type = decrypted_data.get('type', '未知')
            feature_count = len(self.decryptor.feature_stations) if self.decryptor.feature_stations else 0

            with info_container:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("模型类型", f"Type {model_type}")
                with col2:
                    st.metric("特征数量", f"{feature_count}个")
                with col3:
                    st.metric("参数数量", f"{len(self.decryptor.water_params)}个")

            # 步骤3: 解析参数
            status_text.info("📋 步骤3/4: 解析模型参数...")
            progress_bar.progress(75)

            csv_data = self.decryptor.parse_to_csv_format(decrypted_data)

            if not csv_data:
                status_text.error("❌ 参数解析失败")
                st.error("数据解析失败，模型结构可能不符合标准格式")
                temp_path.unlink(missing_ok=True)
                return None

            # 显示解析统计
            total_cells = sum(df.size for df in csv_data.values())
            total_non_zero = sum((df != 0).sum().sum() for df in csv_data.values()
                               if df.select_dtypes(include=[float, int]).size > 0)

            with info_container:
                st.success(f"✅ 解析成功: {len(csv_data)}个参数文件, {total_cells:,}个数据点, {total_non_zero:,}个非零值")

            # 步骤4: 生成CSV文件
            status_text.info("💾 步骤4/4: 生成CSV文件...")
            progress_bar.progress(90)

            csv_files = self.decryptor.generate_csv_files(csv_data)

            if not csv_files:
                status_text.error("❌ CSV文件生成失败")
                st.error("CSV文件生成失败，请重试")
                temp_path.unlink(missing_ok=True)
                return None

            # 显示文件统计
            total_size = sum(len(content) for content in csv_files.values())

            # 完成
            progress_bar.progress(100)
            status_text.success("🎉 解密处理完成！")

            with info_container:
                st.success(f"✅ 生成{len(csv_files)}个CSV文件，总大小: {total_size:,} bytes ({total_size/1024:.1f} KB)")

            # 清理临时文件
            temp_path.unlink(missing_ok=True)

            return {
                'model_type': model_type,
                'feature_count': feature_count,
                'csv_files': csv_files,
                'original_filename': uploaded_bin_file.name,
                'file_size': file_size,
                'total_cells': total_cells,
                'total_non_zero': total_non_zero,
                'total_csv_size': total_size
            }

        except Exception as e:
            if 'status_text' in locals():
                status_text.error(f"❌ 处理失败: {str(e)}")
            st.error(f"解密过程中发生错误：{str(e)}")
            logger.error(f"解密错误：{str(e)}")
            # 清理临时文件
            if 'temp_path' in locals():
                temp_path.unlink(missing_ok=True)
            return None

    def render_decrypt_result(self, result):
        """渲染解密结果区域"""
        st.header("🎯 解密结果")

        # 概览信息
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("模型类型", f"Type {result.get('model_type', 'N/A')}")
        with col2:
            st.metric("特征数量", f"{result.get('feature_count', 'N/A')}个")
        with col3:
            st.metric("CSV文件", f"{len(result['csv_files'])}个")
        with col4:
            total_size_kb = result.get('total_csv_size', 0) / 1024
            st.metric("总大小", f"{total_size_kb:.1f} KB")

        # 详细信息展开框
        with st.expander("📊 详细统计信息", expanded=False):
            info_col1, info_col2 = st.columns(2)

            with info_col1:
                st.markdown("**📁 原文件信息:**")
                st.info(f"""
                • 文件名: {result['original_filename']}
                • 原始大小: {result.get('file_size', 0):,} bytes
                • 解密时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """)

            with info_col2:
                st.markdown("**📈 数据统计:**")
                st.info(f"""
                • 数据点总数: {result.get('total_cells', 0):,}个
                • 非零值数量: {result.get('total_non_zero', 0):,}个
                """)

        # CSV文件预览和下载
        st.subheader("📄 CSV文件详情")

        # 文件列表表格
        file_data = []
        for filename, content in result['csv_files'].items():
            file_size = len(content)
            file_type = filename.replace('_coefficients.csv', '').replace('_data.csv', '').replace('.csv', '')

            # 尝试解析CSV以获取维度信息
            try:
                import pandas as pd
                import io
                df = pd.read_csv(io.BytesIO(content), index_col=0)
                dimensions = f"{df.shape[0]}×{df.shape[1]}"
            except:
                dimensions = "N/A"

            file_data.append({
                '文件类型': file_type,
                '文件名': filename,
                '维度': dimensions,
                '大小': f"{file_size:,} bytes"
            })

        # 显示文件信息表格
        if file_data:
            import pandas as pd
            df_files = pd.DataFrame(file_data)
            st.dataframe(df_files, use_container_width=True)

        # 下载区域
        st.subheader("📥 下载CSV文件")

        # 批量下载按钮
        if len(result['csv_files']) > 1:
            # 创建ZIP包
            import zipfile
            import io

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, content in result['csv_files'].items():
                    zip_file.writestr(filename, content)

            zip_buffer.seek(0)

            col_zip, col_space = st.columns([1, 3])
            with col_zip:
                st.download_button(
                    label="📦 批量下载 (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"decrypted_csvs_{result['original_filename'].replace('.bin', '')}.zip",
                    mime='application/zip',
                    use_container_width=True
                )

        # 单个文件下载
        if len(result['csv_files']) > 1:
            cols = st.columns(min(3, len(result['csv_files'])))
            for i, (filename, content) in enumerate(result['csv_files'].items()):
                with cols[i % 3]:
                    st.download_button(
                        label=f"📄 {filename.replace('_coefficients', '').replace('.csv', '')}",
                        data=content,
                        file_name=filename,
                        mime='text/csv',
                        help=f"下载 {filename}",
                        use_container_width=True
                    )
        else:
            # 单个文件时居中显示
            for filename, content in result['csv_files'].items():
                st.download_button(
                    label=f"📥 下载 {filename}",
                    data=content,
                    file_name=filename,
                    mime='text/csv',
                    help=f"下载解析后的 {filename} 文件",
                    use_container_width=True
                )

    @performance_monitor("process_uploaded_files")
    def process_uploaded_files(
        self, uploaded_files: dict, model_type: int, output_dir: str
    ):
        """处理上传的文件"""
        try:
            with st.spinner("正在处理文件..."):
                # 记录操作上下文
                EnhancedLogger.log_operation_context(
                    "process_uploaded_files",
                    model_type=model_type,
                    files_count=len(uploaded_files),
                    output_dir=output_dir,
                )

                # 读取上传的文件
                processed_data = {}

                for file_type, uploaded_file in uploaded_files.items():
                    if uploaded_file is not None:
                        df = self.file_handler.read_uploaded_file(
                            uploaded_file, file_type
                        )
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
                        mime='application/octet-stream',
                    )

            with col2:
                st.success("✅ 处理完成")
                st.markdown(
                    f"""
                **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                
                **说明**：
                - 模型文件已加密保存
                - 可以直接用于后续的水质预测
                - 请妥善保管加密文件
                """
                )

    def run(self):
        """运行主应用"""
        # 渲染页面
        self.render_header()

        # 获取配置
        app_mode, model_type, output_dir = self.render_sidebar()

        if app_mode == "encrypt":
            # 加密模式：CSV → BIN
            self.render_encrypt_mode(model_type, output_dir)
        else:
            # 解密模式：BIN → CSV
            self.render_decrypt_mode()

        # 渲染页脚
        self.render_footer()

    def render_encrypt_mode(self, model_type, output_dir):
        """渲染加密模式界面"""
        # 文件上传区域
        uploaded_files = self.render_file_upload_section(model_type)

        # 处理按钮
        if st.button("🚀 开始处理", type="primary", use_container_width=True):
            if self.validate_uploaded_files(uploaded_files, model_type):
                result_path = self.process_uploaded_files(
                    uploaded_files, model_type, output_dir
                )
                if result_path:
                    st.session_state.processing_complete = True
                    st.session_state.result_path = result_path
                    st.rerun()

        # 显示结果
        if st.session_state.processing_complete and st.session_state.result_path:
            self.render_result_section(st.session_state.result_path)

    def render_decrypt_mode(self):
        """渲染解密模式界面"""
        # 检查解密功能是否可用
        if not UTILS_AVAILABLE or not self.decryptor:
            st.error("❌ 解密功能不可用")
            st.info("请确保所有依赖模块已正确安装")
            return

        # 渲染解密界面
        self.render_decrypt_section()

    def render_footer(self):
        """渲染页脚"""
        st.markdown("---")
        st.markdown(
            """
        <div style='text-align: center; color: #666;'>
        🚀 Model Finetune UI - 基于原项目的数据处理界面<br>
        支持加密模式(CSV→BIN)和解密模式(BIN→CSV)
        </div>
        """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    app = ModelFinetuneApp()
    app.run()
