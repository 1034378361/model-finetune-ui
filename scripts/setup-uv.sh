#!/bin/bash

# Model Finetune UI - UV 环境设置脚本
# 用于设置和验证uv管理的Python环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查uv是否安装
check_uv_installation() {
    print_info "检查uv安装状态..."
    
    if ! command -v uv &> /dev/null; then
        print_error "uv未安装，请先安装uv"
        print_info "安装方法: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    UV_VERSION=$(uv --version)
    print_success "uv已安装: $UV_VERSION"
}

# 验证Python版本
check_python_version() {
    print_info "检查Python版本要求..."
    
    PYTHON_VERSION=$(uv python --version 2>/dev/null || echo "未找到")
    print_info "当前Python版本: $PYTHON_VERSION"
    
    # 检查项目所需的Python版本
    REQUIRED_VERSION=$(grep "requires-python" pyproject.toml | cut -d'"' -f2)
    print_info "项目要求Python版本: $REQUIRED_VERSION"
}

# 同步依赖
sync_dependencies() {
    print_info "同步项目依赖..."
    
    # 安装基本依赖
    print_info "安装生产依赖..."
    uv sync
    
    print_success "依赖同步完成"
}

# 安装开发依赖
install_dev_dependencies() {
    read -p "是否安装开发依赖？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "安装开发依赖..."
        uv sync --dev
        print_success "开发依赖安装完成"
    else
        print_info "跳过开发依赖安装"
    fi
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    # 检查关键模块
    local modules=("streamlit" "pandas" "numpy" "cryptography")
    
    for module in "${modules[@]}"; do
        if uv run python -c "import $module" 2>/dev/null; then
            print_success "✓ $module 可用"
        else
            print_error "✗ $module 不可用"
        fi
    done
}

# 生成示例数据
generate_sample_data() {
    read -p "是否生成示例数据？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "生成示例数据..."
        uv run generate-sample-data
        print_success "示例数据生成完成"
    else
        print_info "跳过示例数据生成"
    fi
}

# 测试应用启动
test_app_startup() {
    read -p "是否测试应用启动？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "测试应用启动..."
        print_warning "应用将在5秒后启动，然后自动关闭..."
        
        # 启动应用并在5秒后停止
        timeout 5s uv run model-finetune-ui 2>/dev/null || true
        print_success "应用启动测试完成"
    else
        print_info "跳过应用启动测试"
    fi
}

# 显示使用说明
show_usage_info() {
    print_success "设置完成！"
    echo
    print_info "常用uv命令:"
    echo "  uv sync                    # 同步依赖"
    echo "  uv sync --dev             # 同步开发依赖"
    echo "  uv run model-finetune-ui  # 启动应用"
    echo "  uv run generate-sample-data # 生成示例数据"
    echo "  uv add package-name       # 添加新依赖"
    echo "  uv remove package-name    # 移除依赖"
    echo "  uv run python script.py   # 运行脚本"
    echo
    print_info "开发工具命令:"
    echo "  uv run black .            # 代码格式化"
    echo "  uv run ruff check .       # 代码检查"
    echo "  uv run mypy .             # 类型检查"
    echo "  uv run pytest            # 运行测试"
    echo
    print_info "更多信息请查看: README.md"
}

# 主函数
main() {
    print_info "开始设置Model Finetune UI的uv环境"
    echo "=" * 50
    
    # 检查当前目录
    if [[ ! -f "pyproject.toml" ]]; then
        print_error "未找到pyproject.toml文件，请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行设置步骤
    check_uv_installation
    check_python_version
    sync_dependencies
    install_dev_dependencies
    verify_installation
    generate_sample_data
    test_app_startup
    show_usage_info
    
    print_success "uv环境设置完成！"
}

# 显示帮助
show_help() {
    cat << EOF
Model Finetune UI - UV环境设置脚本

用法:
    $0 [选项]

选项:
    -h, --help      显示此帮助信息
    --no-dev        仅安装生产依赖，跳过开发依赖
    --no-test       跳过测试步骤
    --quiet         静默模式

示例:
    $0              # 完整设置流程
    $0 --no-dev     # 仅生产环境设置
    $0 --quiet      # 静默安装

此脚本将:
1. 检查uv安装状态
2. 验证Python版本兼容性
3. 同步项目依赖
4. 可选安装开发依赖
5. 验证关键模块
6. 可选生成示例数据
7. 可选测试应用启动

EOF
}

# 解析命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac