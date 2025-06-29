#!/bin/bash
# 自动加载 .env 并运行主程序

if [ -f .env ]; then
  set -a
  source .env
  set +a
else
  echo "未找到 .env 文件，将使用当前环境变量。"
fi

exec uv run python main.py "$@" 