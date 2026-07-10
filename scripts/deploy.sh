#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOST="${1:-thinkpad}"
PORT="${2:-22}"
REMOTE_USER="${3:-w1ndys}"
REMOTE_DIR="${4:-/opt/$(basename "$ROOT_DIR")}"
PROJECT_NAME="$(basename "$ROOT_DIR")"
BACKEND_IMAGE="${PROJECT_NAME}-backend:latest"
FRONTEND_IMAGE="${PROJECT_NAME}-frontend:latest"
BASE_IMAGES=(
  "ghcr.io/astral-sh/uv:python3.11-bookworm-slim"
  "node:22-alpine"
  "nginx:1.27-alpine"
)
BUILD_DIR="$(mktemp -d)"
ARCHIVE_NAME="${PROJECT_NAME}-deploy.tar.gz"
REMOTE_ARCHIVE="/tmp/${ARCHIVE_NAME}"
REMOTE_PART="${REMOTE_ARCHIVE}.part"

cleanup() {
  rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

pull_image() {
  local image="$1"
  local attempt
  for attempt in 1 2 3; do
    if docker pull "$image"; then
      return 0
    fi
    echo "拉取 ${image} 失败（第 ${attempt}/3 次），准备重试..."
    sleep 2
  done
  echo "错误：拉取镜像 ${image} 失败。"
  return 1
}

for command_name in docker ssh scp tar gzip sha256sum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "错误：缺少命令 ${command_name}。"
    exit 1
  fi
done

if ! docker compose version >/dev/null 2>&1; then
  echo "错误：未安装 Docker Compose 插件。"
  exit 1
fi

echo "检查远端部署目录权限"
ssh -p "$PORT" "${REMOTE_USER}@${HOST}" bash -s -- "$REMOTE_DIR" <<'PREFLIGHT_SCRIPT'
set -Eeuo pipefail
REMOTE_DIR="$1"
PARENT_DIR="$(dirname "$REMOTE_DIR")"
if [[ (-d "$REMOTE_DIR" && -w "$REMOTE_DIR") || (! -e "$REMOTE_DIR" && -w "$PARENT_DIR") ]]; then
  exit 0
fi
if sudo -n true >/dev/null 2>&1; then
  exit 0
fi
echo "错误：当前用户无法写入 ${REMOTE_DIR}，且没有免密码 sudo 权限。"
echo "请先在目标服务器执行：sudo mkdir -p '${REMOTE_DIR}' && sudo chown -R \"\$(id -un):\$(id -gn)\" '${REMOTE_DIR}'"
exit 1
PREFLIGHT_SCRIPT

if [[ -f .env.production ]]; then
  ENV_FILE=.env.production
elif [[ -f .env ]]; then
  ENV_FILE=.env
else
  ENV_FILE=.env.example
  echo "警告：未找到 .env.production 或 .env，将使用 .env.example。"
fi

echo "[1/6] 拉取构建所需镜像"
for image in "${BASE_IMAGES[@]}"; do
  pull_image "$image"
done

echo "[2/6] 本地构建前后端镜像"
docker compose build backend frontend

echo "[3/6] 导出镜像并打包运维配置"
docker save "$BACKEND_IMAGE" "$FRONTEND_IMAGE" | gzip -1 >"$BUILD_DIR/image.tar.gz"
cp compose.yaml "$BUILD_DIR/compose.yaml"
cp "$ENV_FILE" "$BUILD_DIR/.env"
tar -C "$BUILD_DIR" -czf "$BUILD_DIR/$ARCHIVE_NAME" image.tar.gz compose.yaml .env
ARCHIVE_SIZE="$(du -h "$BUILD_DIR/$ARCHIVE_NAME" | cut -f1)"
ARCHIVE_SHA256="$(sha256sum "$BUILD_DIR/$ARCHIVE_NAME" | cut -d' ' -f1)"
echo "部署包大小：${ARCHIVE_SIZE}，SHA-256：${ARCHIVE_SHA256}"

echo "[4/6] 上传部署包到 ${REMOTE_USER}@${HOST}:${REMOTE_PART}"
ssh -o ServerAliveInterval=15 -o ServerAliveCountMax=6 -p "$PORT" \
  "${REMOTE_USER}@${HOST}" rm -f "$REMOTE_PART" "$REMOTE_ARCHIVE"
scp -o ServerAliveInterval=15 -o ServerAliveCountMax=6 -P "$PORT" \
  "$BUILD_DIR/$ARCHIVE_NAME" "${REMOTE_USER}@${HOST}:${REMOTE_PART}"

echo "校验远端部署包完整性"
ssh -o ServerAliveInterval=15 -o ServerAliveCountMax=6 -p "$PORT" \
  "${REMOTE_USER}@${HOST}" bash -s -- "$REMOTE_PART" "$REMOTE_ARCHIVE" "$ARCHIVE_SHA256" <<'VERIFY_SCRIPT'
set -Eeuo pipefail
REMOTE_PART="$1"
REMOTE_ARCHIVE="$2"
EXPECTED_SHA256="$3"
ACTUAL_SHA256="$(sha256sum "$REMOTE_PART" | cut -d' ' -f1)"
if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
  echo "错误：远端部署包校验失败，期望 ${EXPECTED_SHA256}，实际 ${ACTUAL_SHA256}。"
  exit 1
fi
mv -f "$REMOTE_PART" "$REMOTE_ARCHIVE"
echo "部署包校验通过。"
VERIFY_SCRIPT

echo "[5/6] 远端加载镜像并启动服务"
ssh -o ServerAliveInterval=15 -o ServerAliveCountMax=6 -p "$PORT" \
  "${REMOTE_USER}@${HOST}" bash -s -- "$REMOTE_DIR" "$REMOTE_ARCHIVE" <<'REMOTE_SCRIPT'
set -Eeuo pipefail

REMOTE_DIR="$1"
REMOTE_ARCHIVE="$2"

if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
elif command -v sudo >/dev/null 2>&1 && sudo -n docker info >/dev/null 2>&1; then
  DOCKER=(sudo docker)
else
  echo "错误：当前远端用户无法访问 Docker。"
  exit 1
fi

if [[ -w "$(dirname "$REMOTE_DIR")" ]] || [[ -d "$REMOTE_DIR" && -w "$REMOTE_DIR" ]]; then
  mkdir -p "$REMOTE_DIR/data"
  tar -xzf "$REMOTE_ARCHIVE" -C "$REMOTE_DIR"
  rm -f "$REMOTE_ARCHIVE"
else
  sudo -n mkdir -p "$REMOTE_DIR/data"
  sudo -n tar -xzf "$REMOTE_ARCHIVE" -C "$REMOTE_DIR"
  sudo -n chown -R "$(id -u):$(id -g)" "$REMOTE_DIR"
  rm -f "$REMOTE_ARCHIVE"
fi

cd "$REMOTE_DIR"
gzip -dc image.tar.gz | "${DOCKER[@]}" load
"${DOCKER[@]}" compose up -d --remove-orphans --no-build
rm -f image.tar.gz
"${DOCKER[@]}" image prune -f
REMOTE_SCRIPT

echo "[6/6] 部署完成：http://${HOST}"
