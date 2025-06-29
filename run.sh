#!/bin/bash
# TeleFwdBot 服务管理脚本
# 支持启动、重启、停止操作

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PID_FILE="$SCRIPT_DIR/.bot.pid"
LOG_FILE="$SCRIPT_DIR/logs/bot.log"

# 确保日志目录存在
mkdir -p "$SCRIPT_DIR/logs"

# 加载环境变量
load_env() {
    if [ -f "$SCRIPT_DIR/.env" ]; then
        set -a
        source "$SCRIPT_DIR/.env"
        set +a
        echo "已加载 .env 文件"
    else
        echo "未找到 .env 文件，将使用当前环境变量"
    fi
}

# 检查进程是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 启动服务
start() {
    if is_running; then
        echo "TeleFwdBot 已在运行中 (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    echo "正在启动 TeleFwdBot..."
    load_env
    
    cd "$SCRIPT_DIR"
    nohup uv run python main.py > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    sleep 2
    if is_running; then
        echo "TeleFwdBot 启动成功 (PID: $pid)"
        echo "日志文件: $LOG_FILE"
        return 0
    else
        echo "TeleFwdBot 启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务
stop() {
    if ! is_running; then
        echo "TeleFwdBot 未在运行"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    echo "正在停止 TeleFwdBot (PID: $pid)..."
    
    # 发送SIGTERM信号
    kill "$pid" 2>/dev/null
    
    # 等待进程结束
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # 如果进程仍在运行，强制杀死
    if kill -0 "$pid" 2>/dev/null; then
        echo "强制停止进程..."
        kill -9 "$pid" 2>/dev/null
    fi
    
    rm -f "$PID_FILE"
    echo "TeleFwdBot 已停止"
    return 0
}

# 重启服务
restart() {
    echo "正在重启 TeleFwdBot..."
    stop
    sleep 2
    start
}

# 查看状态
status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "TeleFwdBot 正在运行 (PID: $pid)"
        
        # 显示进程信息
        if command -v ps >/dev/null 2>&1; then
            ps -p "$pid" -o pid,ppid,cmd,etime 2>/dev/null || true
        fi
        
        # 显示日志文件大小
        if [ -f "$LOG_FILE" ]; then
            local log_size=$(du -h "$LOG_FILE" | cut -f1)
            echo "日志文件: $LOG_FILE ($log_size)"
        fi
    else
        echo "TeleFwdBot 未在运行"
    fi
}

# 查看日志
logs() {
    if [ -f "$LOG_FILE" ]; then
        if command -v tail >/dev/null 2>&1; then
            echo "最近的日志 (按 Ctrl+C 退出):"
            tail -f "$LOG_FILE"
        else
            echo "日志内容:"
            cat "$LOG_FILE"
        fi
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
}

# 显示帮助信息
usage() {
    echo "用法: $0 {start|stop|restart|status|logs}"
    echo ""
    echo "命令:"
    echo "  start   - 启动 TeleFwdBot"
    echo "  stop    - 停止 TeleFwdBot"
    echo "  restart - 重启 TeleFwdBot"
    echo "  status  - 查看运行状态"
    echo "  logs    - 查看日志 (实时)"
    echo ""
    echo "文件位置:"
    echo "  PID文件: $PID_FILE"
    echo "  日志文件: $LOG_FILE"
    echo "  配置文件: $SCRIPT_DIR/.env"
}

# 主逻辑
case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "未知命令: $1"
        usage
        exit 1
        ;;
esac

exit $? 