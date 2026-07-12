# 个人作品展示网站

一个基于Flask框架开发的个人作品展示网站，包含前端展示、后端管理和控制台功能，支持多种主题切换、背景音乐播放、作品管理等功能。

## 功能特点

### 🎨 主题系统
- 支持4种默认主题：磁带未来主义、清新、赛博朋克、漫画风格
- 主题实时切换，无需刷新页面
- 主题偏好自动保存

### 🎵 背景音乐
- 支持多种音频格式：MP3、WAV、OGG、AAC、FLAC
- 动态波形可视化，随音乐律动
- 音量控制，支持0-100%调节
- 上一曲/下一曲切换
- 音乐目录下拉菜单
- 全局音乐开关

### 📁 作品管理
- 支持图片、文字、GitHub链接等多种展示形式
- 作品添加、编辑、删除功能
- 支持本地图片上传
- 响应式设计，适配不同设备

### 🔧 管理控制台
- 作品管理
- 音乐管理
- 网站配置
- 密码修改
- 安全登录机制

## 技术栈

### 后端
- **框架**：Flask
- **ORM**：Flask-SQLAlchemy
- **数据库**：SQLite
- **认证**：Werkzeug Security

### 前端
- **HTML5**：语义化标签
- **CSS3**：Flexbox、Grid、CSS变量
- **JavaScript**：ES6+、Web Audio API
- **模板引擎**：Jinja2

## 安装与运行

### 快速启动（推荐）

我们提供了自动化启动脚本，解压后即可直接使用：

#### Windows系统
1. 双击运行 `start.bat` 文件
2. 等待自动完成环境检查、依赖安装和应用启动
3. 访问 http://127.0.0.1:10008

#### Linux/Ubuntu系统
1. 在终端中运行：
   ```bash
   chmod +x start.sh  # 赋予执行权限
   ./start.sh install # 一键安装依赖、初始化数据库、创建并启动systemd服务
   ```
2. 等待自动完成环境检查、依赖安装和应用启动
3. 访问 http://127.0.0.1:10008

如果只是本地开发运行：
```bash
./start.sh dev
```

### 手动安装步骤

如果您希望手动安装和配置，可以按照以下步骤操作：

#### 环境要求
- Python 3.7+
- pip

#### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd portfolio
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```

3. **激活虚拟环境**
   - Windows：
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux：
     ```bash
     source venv/bin/activate
     ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

5. **启动应用**
   ```bash
   python app.py
   ```

6. **访问应用**
   - 前端展示：http://127.0.0.1:10008
   - 控制台登录：http://127.0.0.1:10008/login

### 默认账号
- **密码**：admin
- 登录后可在控制台修改密码

## 项目结构

```
portfolio/
├── app.py                 # Flask应用主入口
├── wsgi.py                # WSGI入口文件（生产部署）
├── requirements.txt       # 项目依赖
├── .gitignore            # Git忽略文件
├── instance/              # 数据库文件目录
│   └── portfolio_new.db   # SQLite数据库文件
├── static/                # 静态资源目录
│   ├── css/               # CSS样式文件
│   │   ├── style.css      # 主样式文件
│   │   └── themes/        # 主题样式目录
│   ├── js/                # JavaScript文件
│   └── uploads/           # 上传文件存储目录
└── templates/             # HTML模板目录
    ├── index.html         # 首页模板
    ├── admin.html         # 控制台模板
    └── login.html         # 登录页模板
```

## 使用指南

### 1. 访问前端展示页
- 打开浏览器，访问 http://127.0.0.1:5000
- 可以看到作品展示和音乐控制栏

### 2. 登录控制台
- 访问 http://127.0.0.1:5000/login
- 使用默认密码 `admin` 登录

### 3. 管理作品
- 登录后点击「项目管理」标签
- 点击「添加项目」按钮添加新作品
- 填写作品信息，可上传本地图片
- 保存后在前端展示页查看效果

### 4. 管理音乐
- 点击「音乐管理」标签
- 上传背景音乐，支持多种格式
- 设置默认音乐
- 管理音乐列表

### 5. 配置网站
- 点击「网站配置」标签
- 修改网站标题、副标题、页脚文本
- 控制背景音乐开关

### 6. 修改密码
- 在任意标签页点击「修改密码」按钮
- 输入新密码，确认后保存

## 部署指南

### 本地开发
```bash
python app.py
```

### 生产部署

#### 一键部署脚本（Ubuntu推荐）
```bash
chmod +x start.sh
./start.sh install
```

脚本会自动完成：
- 安装 `python3`、`python3-pip`、`python3-venv`（如果系统缺失）
- 创建 Linux 可用的虚拟环境
- 安装 `requirements.txt`
- 生成 `.env` 和 `SECRET_KEY`
- 初始化 SQLite 数据库和上传目录
- 使用 `gunicorn + systemd` 创建生产服务

常用命令：
```bash
./start.sh status    # 查看服务状态
./start.sh restart   # 重启服务
./start.sh stop      # 停止服务
./start.sh logs      # 查看实时日志
./start.sh uninstall # 移除systemd服务，不删除数据
```

默认 Gunicorn 只监听 `127.0.0.1:10008`，适合配合 Nginx 反向代理。若需要直接公网访问：
```bash
APP_HOST=0.0.0.0 ./start.sh install
```

WSL 如果没有启用 systemd，`install` 会提示 `systemd 当前状态为 offline`。这种情况下可先用 `./start.sh dev` 做本地测试，或启用 WSL systemd 后再执行 `install`。

#### 手动使用Gunicorn
```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 3 -b 0.0.0.0:8000 wsgi:app
```

#### 使用Docker Compose（推荐）
```bash
# 复制并修改环境变量
cp .env.docker.example .env

# 构建并启动
docker compose up -d --build

# 查看状态和日志
docker compose ps
docker compose logs -f

# 停止服务
docker compose down
```

默认端口是 `10008`，可在 `.env` 中修改：

```env
APP_PORT=10008
SECRET_KEY=please-change-this-to-a-long-random-secret
```

Compose 会把 `./static/uploads` 挂载到容器内 `/app/static/uploads`，SQLite 数据库和上传文件都会持久保存在宿主机目录里。

#### 手动使用Docker
```bash
docker build -t portfolio .
docker run --rm -p 10008:10008 \
  -e SECRET_KEY='please-change-this' \
  -v "$(pwd)/static/uploads:/app/static/uploads" \
  portfolio
```

#### 使用Nginx + Gunicorn
1. 配置Nginx反向代理
2. 使用Systemd管理Gunicorn服务
3. 配置SSL证书

## 配置说明

### 环境变量
- `SECRET_KEY`：应用密钥，用于会话加密
- `SQLALCHEMY_DATABASE_URI`：数据库连接字符串
- `DEBUG`：调试模式开关

### 配置文件
- `app.py`：主配置文件
- `.env`：环境变量配置（可选）

## 安全注意事项

1. 部署到生产环境时，务必：
   - 设置强密码
   - 关闭DEBUG模式
   - 使用HTTPS
   - 设置合适的SECRET_KEY

2. 定期备份数据库文件
3. 限制控制台访问IP
4. 定期更新依赖包

## 开发说明

### 添加新主题
1. 在 `static/css/themes/` 目录下创建新主题CSS文件
2. 主题CSS文件应包含所有必要的CSS变量
3. 在 `templates/index.html` 和 `templates/admin.html` 中添加主题选项

### 添加新功能
1. 创建新的路由和视图函数
2. 添加相应的模板或API端点
3. 更新数据库模型（如果需要）
4. 添加必要的JavaScript和CSS

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request，共同改进项目！

## 联系方式

如有问题或建议，欢迎通过以下方式联系：
- Email：your-email@example.com
- GitHub：your-github-username

---

**祝使用愉快！** 🎉
