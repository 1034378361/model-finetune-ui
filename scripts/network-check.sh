#!/bin/bash

# 网络连接诊断脚本
# 帮助诊断WSL中Streamlit访问问题

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测环境
check_environment() {
    print_info "🔍 环境检测"
    echo "===================="
    
    # 检测操作系统
    if grep -qi microsoft /proc/version 2>/dev/null; then
        print_success "检测到WSL环境"
        echo "WSL版本: $(grep -i microsoft /proc/version)"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "检测到原生Linux环境"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "检测到macOS环境"
    else
        print_info "未知环境: $OSTYPE"
    fi
    
    echo
}

# 检查网络配置
check_network() {
    print_info "🌐 网络配置检查"
    echo "===================="
    
    # 获取IP地址
    print_info "IP地址信息:"
    echo "  - localhost: 127.0.0.1"
    
    if command -v hostname >/dev/null 2>&1; then
        local host_ip=$(hostname -I | awk '{print $1}' 2>/dev/null)
        if [[ -n "$host_ip" ]]; then
            echo "  - 主机IP: $host_ip"
        fi
    fi
    
    # 检查WSL特殊配置
    if grep -qi microsoft /proc/version 2>/dev/null; then
        if [[ -f /etc/resolv.conf ]]; then
            local windows_ip=$(grep nameserver /etc/resolv.conf | awk '{print $2}' | head -1)
            echo "  - Windows主机IP: $windows_ip"
        fi
    fi
    
    echo
}

# 检查端口
check_ports() {
    print_info "🔌 端口检查"
    echo "===================="
    
    local port=8501
    
    # 检查端口是否被占用
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln | grep -q ":$port "; then
            print_warning "端口 $port 已被占用"
            echo "占用端口的进程:"
            netstat -tulnp | grep ":$port "
        else
            print_success "端口 $port 可用"
        fi
    elif command -v ss >/dev/null 2>&1; then
        if ss -tuln | grep -q ":$port "; then
            print_warning "端口 $port 已被占用"
            echo "占用端口的进程:"
            ss -tulnp | grep ":$port "
        else
            print_success "端口 $port 可用"
        fi
    else
        print_warning "无法检查端口状态（缺少netstat或ss命令）"
    fi
    
    echo
}

# 检查Streamlit进程
check_streamlit() {
    print_info "📊 Streamlit进程检查"
    echo "===================="
    
    if pgrep -f streamlit >/dev/null 2>&1; then
        print_info "发现运行中的Streamlit进程:"
        ps aux | grep streamlit | grep -v grep
    else
        print_info "没有运行中的Streamlit进程"
    fi
    
    echo
}

# 提供解决方案
provide_solutions() {
    print_info "💡 解决方案建议"
    echo "===================="
    
    if grep -qi microsoft /proc/version 2>/dev/null; then
        print_info "WSL环境建议:"
        echo "  1. 使用WSL专用启动脚本:"
        echo "     make run-wsl"
        echo "     或"
        echo "     ./scripts/run-wsl.sh"
        echo
        echo "  2. 手动配置端口转发:"
        echo "     在Windows PowerShell（管理员权限）中运行:"
        echo "     netsh interface portproxy add v4tov4 listenport=8501 connectaddress=<WSL_IP> connectport=8501"
        echo
        echo "  3. 直接使用Streamlit命令:"
        echo "     uv run streamlit run app.py --server.address 0.0.0.0 --server.port 8501"
        echo
        echo "  4. 访问地址尝试顺序:"
        echo "     - http://localhost:8501"
        echo "     - http://127.0.0.1:8501" 
        echo "     - http://<WSL_IP>:8501"
    else
        print_info "标准环境建议:"
        echo "  1. 使用标准启动命令:"
        echo "     make run"
        echo "     或"
        echo "     uv run model-finetune-ui"
        echo
        echo "  2. 直接访问:"
        echo "     http://localhost:8501"
    fi
    
    echo
    print_info "通用排错步骤:"
    echo "  1. 检查防火墙设置"
    echo "  2. 尝试不同的浏览器"
    echo "  3. 清理可能的端口占用"
    echo "  4. 重启终端会话"
    
    echo
}

# 主函数
main() {
    echo "🔍 Model Finetune UI 网络诊断工具"
    echo "========================================"
    echo
    
    check_environment
    check_network
    check_ports
    check_streamlit
    provide_solutions
    
    print_success "诊断完成！"
    print_info "如果问题仍然存在，请尝试建议的解决方案"
}

# 运行诊断
main "$@"