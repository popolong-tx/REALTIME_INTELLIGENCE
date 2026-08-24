#!/usr/bin/env bash

# 兼容旧命令：统一转到 UI + API 服务，避免启动过时的双服务架构。
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT_DIR/start-ui.sh" "$@"
