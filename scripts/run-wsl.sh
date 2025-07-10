#!/bin/bash

# WSL环境专用启动脚本
# 解决WSL中Streamlit网络访问问题

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检测WSL环境
detect_wsl() {
    if grep -qi microsoft /proc/version 2>/dev/null; then
        return 0  # 是WSL
    else
        return 1  # 不是WSL
    fi
}

# 获取WSL IP地址
get_wsl_ip() {
    # 尝试获取WSL的IP地址
    local wsl_ip=$(hostname -I | awk '{print $1}')
    if [[ -n "$wsl_ip" ]]; then
        echo "$wsl_ip"
    else
        echo "localhost"
    fi
}

# 获取Windows主机IP
get_windows_ip() {
    # 从/etc/resolv.conf获取Windows主机IP
    local windows_ip=$(grep nameserver /etc/resolv.conf | awk '{print $2}' | head -1)
    if [[ -n "$windows_ip" ]]; then
        echo "$windows_ip"
    else
        echo "192.168.1.1"  # 默认值
    fi
}

main() {
    print_info "🚀 Model Finetune UI - WSL专用启动器"
    echo "=" * 50
    
    if detect_wsl; then
        print_success "检测到WSL环境"
        
        # 获取IP地址信息
        WSL_IP=$(get_wsl_ip)
        WINDOWS_IP=$(get_windows_ip)
        
        print_info "网络配置:"
        echo "  - WSL IP: $WSL_IP"
        echo "  - Windows主机IP: $WINDOWS_IP"
        echo "  - 端口: 8501"
        
        # 启动应用
        print_info "启动Streamlit应用..."
        
        # 设置环境变量
        export STREAMLIT_SERVER_ADDRESS="0.0.0.0"
        export STREAMLIT_SERVER_PORT="8501"
        export STREAMLIT_SERVER_HEADLESS="false"
        
        # 启动应用
        uv run streamlit run app.py \
            --server.address 0.0.0.0 \
            --server.port 8501 \
            --server.headless false &
        
        # 获取进程ID
        STREAMLIT_PID=$!
        
        # 等待应用启动
        sleep 3
        
        print_success "应用已启动！"
        echo
        print_info "访问地址选项:"
        echo "  1. 本地访问: http://localhost:8501"
        echo "  2. WSL访问: http://$WSL_IP:8501"
        echo "  3. Windows访问: http://$WSL_IP:8501"
        echo
        print_warning "如果无法访问，请尝试:"
        echo "  1. 在Windows PowerShell中运行: netsh interface portproxy add v4tov4 listenport=8501 connectaddress=$WSL_IP connectport=8501"
        echo "  2. 检查Windows防火墙设置"
        echo "  3. 使用浏览器直接访问: http://$WSL_IP:8501"
        echo
        print_info "按 Ctrl+C 停止应用"
        
        # 等待用户中断
        wait $STREAMLIT_PID
        
    else
        print_info "非WSL环境，使用标准启动方式"
        uv run model-finetune-ui
    fi
}

# 清理函数
cleanup() {
    print_info "正在停止应用..."
    # 杀死所有streamlit进程
    pkill -f "streamlit run" 2>/dev/null || true
    print_success "应用已停止"
}

# 设置清理陷阱
trap cleanup EXIT INT TERM

# 运行主函数
main "$@"