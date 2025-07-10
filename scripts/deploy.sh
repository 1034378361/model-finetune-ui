#!/bin/bash

# Model Finetune UI 部署脚本
# 用法: ./scripts/deploy.sh [platform]
# 平台选项: streamlit, docker, heroku

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

# 检查必要文件
check_requirements() {
    print_info "检查部署要求..."
    
    local required_files=("app.py" "requirements.txt" ".streamlit/config.toml")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "缺少必要文件: $file"
            exit 1
        fi
    done
    
    # 检查环境变量
    if [[ ! -f ".env" ]]; then
        print_warning "未找到 .env 文件，请确保在部署平台配置环境变量"
    fi
    
    print_success "要求检查通过"
}

# 生成requirements.txt
generate_requirements() {
    print_info "生成 requirements.txt..."
    
    if command -v uv &> /dev/null; then
        uv export --no-hashes > requirements.txt
        print_success "已使用 uv 生成 requirements.txt"
    else
        print_warning "未找到 uv，使用现有的 requirements.txt"
    fi
}

# Streamlit Cloud 部署
deploy_streamlit() {
    print_info "准备 Streamlit Cloud 部署..."
    
    # 检查Git状态
    if [[ -n $(git status --porcelain) ]]; then
        print_warning "有未提交的更改，正在提交..."
        git add .
        git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    # 推送到GitHub
    git push origin main 2>/dev/null || git push origin master
    
    print_success "代码已推送到GitHub"
    print_info "请访问 https://share.streamlit.io/ 完成部署配置"
    print_info "部署配置:"
    echo "  - Repository: $(git config --get remote.origin.url)"
    echo "  - Branch: main (或 master)"
    echo "  - Main file path: app.py"
    echo "  - Python version: 3.11"
}

# Docker 部署
deploy_docker() {
    print_info "开始 Docker 部署..."
    
    # 构建镜像
    docker build -t model-finetune-ui . || {
        print_error "Docker 构建失败"
        exit 1
    }
    
    print_success "Docker 镜像构建完成"
    
    # 运行容器
    print_info "启动容器..."
    docker run -d \
        --name model-finetune-ui \
        -p 8501:8501 \
        -e ENCRYPTION_KEY="${ENCRYPTION_KEY:-default-key-change-me}" \
        -e UI_OUTPUT_DIR="/app/output" \
        -v "$(pwd)/ui_output:/app/output" \
        model-finetune-ui
    
    print_success "容器已启动，访问 http://localhost:8501"
}

# Heroku 部署
deploy_heroku() {
    print_info "开始 Heroku 部署..."
    
    # 检查Heroku CLI
    if ! command -v heroku &> /dev/null; then
        print_error "请先安装 Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    # 检查是否已登录
    if ! heroku auth:whoami &> /dev/null; then
        print_info "请先登录 Heroku..."
        heroku login
    fi
    
    # 创建应用(如果不存在)
    APP_NAME="${HEROKU_APP_NAME:-model-finetune-ui-$(date +%s)}"
    heroku create "$APP_NAME" 2>/dev/null || print_info "应用已存在: $APP_NAME"
    
    # 设置环境变量
    heroku config:set ENCRYPTION_KEY="${ENCRYPTION_KEY:-default-key-change-me}" -a "$APP_NAME"
    heroku config:set UI_OUTPUT_DIR="/tmp/ui_output" -a "$APP_NAME"
    
    # 部署
    git push heroku main 2>/dev/null || git push heroku master
    
    print_success "Heroku 部署完成"
    heroku open -a "$APP_NAME"
}

# 清理函数
cleanup() {
    print_info "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 主函数
main() {
    local platform=${1:-streamlit}
    
    print_info "开始部署 Model Finetune UI 到 $platform"
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    # 执行检查
    check_requirements
    generate_requirements
    
    # 根据平台执行部署
    case $platform in
        streamlit)
            deploy_streamlit
            ;;
        docker)
            deploy_docker
            ;;
        heroku)
            deploy_heroku
            ;;
        *)
            print_error "不支持的平台: $platform"
            print_info "支持的平台: streamlit, docker, heroku"
            exit 1
            ;;
    esac
    
    print_success "部署脚本执行完成!"
}

# 显示帮助信息
show_help() {
    cat << EOF
Model Finetune UI 部署脚本

用法:
    $0 [platform] [options]

平台选项:
    streamlit    部署到 Streamlit Community Cloud (默认)
    docker       本地 Docker 容器部署
    heroku       部署到 Heroku

环境变量:
    ENCRYPTION_KEY      加密密钥 (必须设置)
    HEROKU_APP_NAME     Heroku 应用名称 (可选)

示例:
    $0 streamlit                    # 部署到 Streamlit Cloud
    $0 docker                       # 本地 Docker 部署
    ENCRYPTION_KEY=xxx $0 heroku    # 部署到 Heroku

更多信息请查看 DEPLOYMENT.md
EOF
}

# 检查参数
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# 执行主函数
main "$@"