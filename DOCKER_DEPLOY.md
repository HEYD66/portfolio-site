# Docker 部署说明

## 目录要求

在服务器上进入项目目录后执行。`docker-compose.yml` 会把宿主机的 `./static/uploads` 挂载到容器内 `/app/static/uploads`，数据库、图片、音乐、视频、下载附件都会持久保存在这个目录。

## 首次启动

```bash
cp .env.docker.example .env
mkdir -p static/uploads
```

编辑 `.env`，至少修改 `SECRET_KEY`：

```bash
openssl rand -hex 32
```

然后启动：

```bash
docker compose up -d --build
```

默认访问地址：

```text
http://服务器IP:10008
```

## 常用命令

```bash
docker compose ps
docker compose logs -f
docker compose restart
docker compose down
```

## 配置项

`.env` 支持这些常用配置：

```env
APP_PORT=10008
SECRET_KEY=please-change-this-to-a-long-random-secret
UPLOADS_HOST_DIR=./static/uploads
VIDEO_MAX_BYTES=1073741824
MAX_UPLOAD_BYTES=1090519040
GUNICORN_CMD_ARGS=--workers 2 --timeout 180 --access-logfile - --error-logfile -
```

`VIDEO_MAX_BYTES` 是视频单文件上限，默认 1GB。`MAX_UPLOAD_BYTES` 是请求体上限，默认比 1GB 多 16MB，给表单字段留空间。

`UPLOADS_HOST_DIR` 是宿主机持久化目录。生产环境可以改成绝对路径，例如：

```env
UPLOADS_HOST_DIR=/data/portfolio/uploads
```

## 反向代理提示

如果前面加 Nginx，并且需要上传 1GB 视频，Nginx 也要放开大小限制：

```nginx
client_max_body_size 1100m;
```

否则 Docker 容器内允许 1GB，Nginx 也可能先拦掉上传。

## 数据备份

重点备份这个目录：

```text
static/uploads
```

里面包含 SQLite 数据库 `portfolio_new.db` 和所有上传文件。
