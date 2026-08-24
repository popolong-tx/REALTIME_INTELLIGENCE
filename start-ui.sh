#!/usr/bin/env bash

# 量化交易建议系统 - 唯一启动入口（UI + API）

set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
PYTHON_BIN="$BACKEND_DIR/venv/bin/python"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Nexus Quant 量化交易建议系统${NC}"
echo -e "${GREEN}========================================${NC}"

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo -e "${YELLOW}首次运行：创建 Python 环境...${NC}"
    python3 -m venv "$BACKEND_DIR/venv"
fi

if ! "$PYTHON_BIN" -c "import fastapi, uvicorn, pydantic, pydantic_settings, sqlalchemy, yfinance, pandas, numpy, sklearn, joblib, httpx, requests, dotenv, jose, passlib" >/dev/null 2>&1; then
    echo -e "${YELLOW}检测到依赖不完整，正在补齐...${NC}"
    "$PYTHON_BIN" -m pip install -r "$BACKEND_DIR/requirements-ui.txt"
fi

mkdir -p "$BACKEND_DIR/data"

# Only replace a listener that is demonstrably this project's old UI process.
# An unrelated process on the requested port is never terminated automatically.
LISTENER_PID="$(lsof -nP -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [[ -n "$LISTENER_PID" ]]; then
    LISTENER_CWD="$(lsof -a -p "$LISTENER_PID" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1 || true)"
    LISTENER_COMMAND="$(ps -p "$LISTENER_PID" -o command= 2>/dev/null || true)"
    SERVER_PID="$LISTENER_PID"
    SERVER_CWD="$LISTENER_CWD"
    SERVER_COMMAND="$LISTENER_COMMAND"

    # With --reload, lsof may return the multiprocessing worker first. Trust it
    # only when its direct parent is this project's Uvicorn reload process.
    if [[ "$LISTENER_CWD" == "$BACKEND_DIR" && "$LISTENER_COMMAND" == *"multiprocessing.spawn"* ]]; then
        PARENT_PID="$(ps -p "$LISTENER_PID" -o ppid= 2>/dev/null | tr -d ' ' || true)"
        if [[ -n "$PARENT_PID" ]]; then
            PARENT_CWD="$(lsof -a -p "$PARENT_PID" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1 || true)"
            PARENT_COMMAND="$(ps -p "$PARENT_PID" -o command= 2>/dev/null || true)"
            if [[ "$PARENT_CWD" == "$BACKEND_DIR" && "$PARENT_COMMAND" == *"uvicorn app.main_ui:app"* ]]; then
                SERVER_PID="$PARENT_PID"
                SERVER_CWD="$PARENT_CWD"
                SERVER_COMMAND="$PARENT_COMMAND"
            fi
        fi
    fi

    if [[ "$SERVER_CWD" == "$BACKEND_DIR" && "$SERVER_COMMAND" == *"uvicorn app.main_ui:app"* ]]; then
        echo -e "${YELLOW}发现本工程旧服务（PID ${SERVER_PID}），正在平滑重启...${NC}"
        kill -TERM "$SERVER_PID"
        for _ in {1..50}; do
            if ! kill -0 "$SERVER_PID" 2>/dev/null; then
                break
            fi
            sleep 0.1
        done
        if kill -0 "$SERVER_PID" 2>/dev/null; then
            echo -e "${RED}旧服务未能在 5 秒内退出，请先手动停止 PID $SERVER_PID。${NC}" >&2
            exit 1
        fi
    else
        echo -e "${RED}端口 $PORT 已被其他程序占用，未自动终止该程序。${NC}" >&2
        echo "PID: $LISTENER_PID" >&2
        echo "目录: ${LISTENER_CWD:-未知}" >&2
        echo "命令: ${LISTENER_COMMAND:-未知}" >&2
        exit 1
    fi
fi

echo -e "${GREEN}界面地址: http://localhost:${PORT}${NC}"
echo "API 文档: http://localhost:${PORT}/docs"
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"

cd "$BACKEND_DIR"
exec "$PYTHON_BIN" -m uvicorn app.main_ui:app --host "$HOST" --port "$PORT" --reload
