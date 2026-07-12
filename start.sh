#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="${APP_NAME:-portfolio}"
SERVICE_NAME="${SERVICE_NAME:-portfolio.service}"
APP_PORT="${APP_PORT:-10008}"
APP_HOST="${APP_HOST:-127.0.0.1}"
WORKERS="${WORKERS:-2}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
ENV_FILE="$PROJECT_DIR/.env"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
GUNICORN_BIN="$VENV_DIR/bin/gunicorn"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

info() { echo -e "${GREEN}==>${NC} $*"; }
warn() { echo -e "${YELLOW}WARN:${NC} $*"; }
fail() { echo -e "${RED}ERROR:${NC} $*" >&2; exit 1; }

usage() {
    cat <<EOF
个人作品展示网站一键部署脚本

用法:
  ./start.sh install      安装依赖、初始化数据库、创建并启动 systemd 服务
  ./start.sh dev          本地开发启动，使用 Flask 开发服务器
  ./start.sh start        启动 systemd 服务
  ./start.sh stop         停止 systemd 服务
  ./start.sh restart      重启 systemd 服务
  ./start.sh status       查看服务状态
  ./start.sh logs         查看实时日志
  ./start.sh uninstall    停止并移除 systemd 服务，不删除代码和数据

常用环境变量:
  APP_PORT=10008          应用端口
  APP_HOST=127.0.0.1      Gunicorn 监听地址；直接公网访问可设为 0.0.0.0
  WORKERS=2               Gunicorn worker 数
  SERVICE_NAME=portfolio.service

示例:
  chmod +x start.sh
  ./start.sh install
  APP_HOST=0.0.0.0 ./start.sh install
EOF
}

require_project_files() {
    cd "$PROJECT_DIR"
    [ -f "$PROJECT_DIR/app.py" ] || fail "未找到 app.py，请在项目根目录运行脚本。"
    [ -f "$PROJECT_DIR/wsgi.py" ] || fail "未找到 wsgi.py。"
    [ -f "$PROJECT_DIR/requirements.txt" ] || fail "未找到 requirements.txt。"
}

install_system_packages() {
    if command -v python3 >/dev/null 2>&1 && python3 -m venv --help >/dev/null 2>&1; then
        return
    fi

    if command -v apt-get >/dev/null 2>&1; then
        info "安装 Python 运行环境"
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    else
        fail "未找到可用的 python3/python3-venv，也不是 apt 系统。请先安装 Python 3 和 venv。"
    fi
}

ensure_venv() {
    if [ -d "$VENV_DIR" ] && [ ! -x "$PYTHON_BIN" ]; then
        backup="$PROJECT_DIR/venv.backup.$(date +%Y%m%d%H%M%S)"
        warn "检测到已有 venv 但不是当前 Linux 可用的虚拟环境，备份到 $backup"
        mv "$VENV_DIR" "$backup"
    fi

    if [ ! -d "$VENV_DIR" ]; then
        info "创建虚拟环境: $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi

    info "安装 Python 依赖"
    "$PIP_BIN" install --upgrade pip
    "$PIP_BIN" install -r "$PROJECT_DIR/requirements.txt"
}

ensure_env_file() {
    if [ -f "$ENV_FILE" ]; then
        return
    fi

    info "生成生产环境配置: .env"
    secret_key="$("$PYTHON_BIN" - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)"

    cat > "$ENV_FILE" <<EOF
SECRET_KEY=$secret_key
EOF
    chmod 600 "$ENV_FILE"
}

ensure_data_dirs() {
    info "准备上传和数据目录"
    mkdir -p \
        "$PROJECT_DIR/static/uploads/images" \
        "$PROJECT_DIR/static/uploads/music" \
        "$PROJECT_DIR/static/uploads/docs" \
        "$PROJECT_DIR/static/uploads/projects"
}

init_database() {
    info "初始化数据库"
    "$PYTHON_BIN" - <<'PY'
from app import app, db, create_project_folders
with app.app_context():
    db.create_all()
create_project_folders()
print("database ready")
PY
}

write_systemd_service() {
    command -v systemctl >/dev/null 2>&1 || fail "当前系统不支持 systemd，无法安装服务。"
    system_state="$(systemctl is-system-running 2>/dev/null || true)"
    if [ "$system_state" != "running" ] && [ "$system_state" != "degraded" ]; then
        fail "systemd 当前状态为 '$system_state'，无法安装服务。WSL 可先启用 systemd，或使用 './start.sh dev' 做本地测试。"
    fi

    info "写入 systemd 服务: $SERVICE_PATH"
    sudo tee "$SERVICE_PATH" >/dev/null <<EOF
[Unit]
Description=Personal Portfolio Website
After=network.target

[Service]
Type=simple
User=$(id -un)
Group=$(id -gn)
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$GUNICORN_BIN --workers $WORKERS --bind $APP_HOST:$APP_PORT wsgi:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
}

install_app() {
    require_project_files
    install_system_packages
    ensure_venv
    ensure_env_file
    ensure_data_dirs
    init_database
    write_systemd_service

    info "启动服务"
    sudo systemctl restart "$SERVICE_NAME"
    sudo systemctl --no-pager --full status "$SERVICE_NAME" || true

    echo
    info "部署完成"
    echo "本机访问: http://127.0.0.1:$APP_PORT"
    echo "服务管理: sudo systemctl status|restart|stop $SERVICE_NAME"
    echo "查看日志: ./start.sh logs"
    if [ "$APP_HOST" = "127.0.0.1" ]; then
        warn "当前只监听 127.0.0.1，适合配合 Nginx 反向代理。若要直接公网访问，使用 APP_HOST=0.0.0.0 ./start.sh install"
    fi
}

dev() {
    require_project_files
    install_system_packages
    ensure_venv
    ensure_env_file
    ensure_data_dirs
    init_database

    info "开发模式启动: http://127.0.0.1:$APP_PORT"
    "$PYTHON_BIN" "$PROJECT_DIR/app.py" --port "$APP_PORT"
}

service_action() {
    command -v systemctl >/dev/null 2>&1 || fail "当前系统不支持 systemd。"
    sudo systemctl "$1" "$SERVICE_NAME"
}

show_status() {
    command -v systemctl >/dev/null 2>&1 || fail "当前系统不支持 systemd。"
    sudo systemctl --no-pager --full status "$SERVICE_NAME"
}

show_logs() {
    command -v journalctl >/dev/null 2>&1 || fail "当前系统不支持 journalctl。"
    sudo journalctl -u "$SERVICE_NAME" -f
}

uninstall_service() {
    command -v systemctl >/dev/null 2>&1 || fail "当前系统不支持 systemd。"
    warn "将停止并移除 $SERVICE_NAME；不会删除项目文件、虚拟环境、上传文件或数据库。"
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    sudo rm -f "$SERVICE_PATH"
    sudo systemctl daemon-reload
    info "服务已移除"
}

main() {
    action="${1:-install}"
    case "$action" in
        install) install_app ;;
        dev) dev ;;
        start) service_action start ;;
        stop) service_action stop ;;
        restart) service_action restart ;;
        status) show_status ;;
        logs) show_logs ;;
        uninstall) uninstall_service ;;
        -h|--help|help) usage ;;
        *) usage; fail "未知操作: $action" ;;
    esac
}

main "$@"
