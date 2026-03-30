#!/usr/bin/env bash
#
# MedrixFlow 一键启动脚本
# macOS 双击即可运行，自动启动所有服务并在浏览器中打开
#

# 切换到脚本所在目录（即项目根目录）
cd "$(dirname "$0")" || exit 1

echo ""
echo "🚀 MedrixFlow 一键启动中..."
echo ""

# ── 环境检查 ──────────────────────────────────────────────────────────────────

check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        echo "✗ 缺少必要工具: $1"
        echo "  请先安装后再试。"
        echo ""
        echo "  按回车键关闭此窗口..."
        read -r
        exit 1
    fi
}

check_cmd node
check_cmd pnpm
check_cmd uv
check_cmd nginx

# ── 启动服务 ──────────────────────────────────────────────────────────────────

# 后台启动 make dev，同时等待端口就绪后打开浏览器
./scripts/serve.sh --dev &
SERVE_PID=$!

# 等待主应用端口 (1000) 就绪
echo "⏳ 等待服务启动..."
MAX_WAIT=180
WAITED=0
while ! nc -z localhost 1000 2>/dev/null; do
    sleep 2
    WAITED=$((WAITED + 2))
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo ""
        echo "✗ 服务启动超时（${MAX_WAIT}s）"
        echo "  请检查日志: logs/ 目录"
        echo ""
        echo "  按回车键关闭此窗口..."
        read -r
        exit 1
    fi
done

# ── 打开浏览器 ────────────────────────────────────────────────────────────────

echo ""
echo "🌐 在浏览器中打开 MedrixFlow..."
open "http://localhost:1000"

# ── 保持前台运行 ──────────────────────────────────────────────────────────────

wait $SERVE_PID
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "⚠️  服务已退出 (code: $EXIT_CODE)"
    echo "   按回车键关闭此窗口..."
    read -r
fi
