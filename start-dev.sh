#!/usr/bin/env bash

# 开发环境同样使用唯一入口；start-ui.sh 已开启自动重载。
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT_DIR/start-ui.sh" "$@"
