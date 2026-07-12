from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
import argparse

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_ROOT = os.environ.get('UPLOAD_ROOT', os.path.join(BASE_DIR, 'static', 'uploads'))
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(UPLOAD_ROOT, 'portfolio_new.db'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DATABASE_PATH.replace('\\', '/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 创建数据库实例
db = SQLAlchemy(app)

# 文件上传配置
app.config['UPLOAD_FOLDER'] = UPLOAD_ROOT
DOWNLOAD_EXTENSIONS = {'zip', 'rar', '7z', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md', 'csv', 'json'}
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'md', 'mp3', 'wav', 'ogg', 'aac', 'flac', 'mp4', 'webm', 'mov', 'ogv'} | DOWNLOAD_EXTENSIONS
app.config['VIDEO_MAX_BYTES'] = int(os.environ.get('VIDEO_MAX_BYTES', 1024 * 1024 * 1024))
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_BYTES', app.config['VIDEO_MAX_BYTES'] + 16 * 1024 * 1024))

os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# 分类目录配置
app.config['UPLOAD_CATEGORIES'] = {
    'images': ['png', 'jpg', 'jpeg', 'gif'],
    'videos': ['mp4', 'webm', 'mov', 'ogv'],
    'music': ['mp3', 'wav', 'ogg', 'aac', 'flac'],
    'docs': ['txt', 'md'],
    'downloads': sorted(DOWNLOAD_EXTENSIONS)
}

# 项目文件夹配置
app.config['PROJECTS_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'projects')

# 确保上传目录和项目主目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROJECTS_FOLDER'], exist_ok=True)

# 确保分类目录存在（兼容旧逻辑）
for category in app.config['UPLOAD_CATEGORIES']:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], category), exist_ok=True)

# 检查文件扩展名是否允许
@app.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(error):
    return jsonify({'error': '上传文件过大，视频最大支持 1GB'}), 413

def allowed_file(filename):
    return filename and '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_upload_size(file_storage):
    stream = file_storage.stream
    current_position = stream.tell()
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(current_position)
    return size

def resolve_uploaded_file_path(file_url):
    if not file_url:
        return ''
    path_parts = file_url.strip('/').split('/')
    if len(path_parts) >= 3 and path_parts[0] in {'project-images', 'project-videos', 'project-downloads'}:
        folder_map = {
            'project-images': 'images',
            'project-videos': 'videos',
            'project-downloads': 'downloads'
        }
        return os.path.join(app.config['PROJECTS_FOLDER'], path_parts[1], folder_map[path_parts[0]], path_parts[2])
    return os.path.join(app.root_path, file_url.lstrip('/'))

# 根据文件扩展名获取分类
def get_file_category(filename):
    if not allowed_file(filename):
        return ''
    ext = filename.rsplit('.', 1)[1].lower()
    for category, extensions in app.config['UPLOAD_CATEGORIES'].items():
        if ext in extensions:
            return category
    return ''

# 用户模型，用于存储密码
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, default='admin')
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 音乐模型，用于存储背景音乐信息
class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_path': self.file_path,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat()
        }

# 网站配置模型
class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100), nullable=False, default='我的作品展示')
    site_subtitle = db.Column(db.String(200), nullable=False, default='欢迎访问我的个人作品展示页面')
    footer_text = db.Column(db.String(200), nullable=False, default='© 2024 我的个人作品展示')
    site_icon = db.Column(db.String(200), nullable=True)  # 站点图标
    music_enabled = db.Column(db.Boolean, default=True)  # 全局音乐开关
    control_panel_visible = db.Column(db.Boolean, default=False)  # 控制首页是否显示控制台按钮
    theme = db.Column(db.String(50), nullable=False, default='fresh')  # 全局主题设置
    
    def to_dict(self):
        return {
            'id': self.id,
            'site_title': self.site_title,
            'site_subtitle': self.site_subtitle,
            'footer_text': self.footer_text,
            'site_icon': self.site_icon,
            'music_enabled': self.music_enabled,
            'control_panel_visible': self.control_panel_visible,
            'theme': self.theme
        }

# 分类模型
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # 分类名称，唯一
    created_at = db.Column(db.DateTime, server_default=db.func.now())  # 创建时间
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }

# 定义Project模型
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    video_url = db.Column(db.String(300), nullable=True, server_default='')
    github_url = db.Column(db.String(200), nullable=True)
    live_url = db.Column(db.String(200), nullable=True)
    download_url = db.Column(db.String(200), nullable=True)  # 添加下载地址字段
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)  # 关联分类
    category = db.relationship('Category', backref=db.backref('projects', lazy=True))  # 关系
    # 使用server_default确保字段存在
    text_content = db.Column(db.Text, nullable=True, server_default='')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'video_url': self.video_url or '',
            'github_url': self.github_url,
            'live_url': self.live_url,
            'download_url': self.download_url,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'text_content': self.text_content or ''
        }

@app.route('/')
def index():
    # 获取搜索关键词
    search_query = request.args.get('search', '')
    # 获取分类ID
    category_id = request.args.get('category')
    
    # 构建查询
    query = Project.query
    
    # 根据分类筛选
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # 根据搜索关键词查询项目
    if search_query:
        query = query.filter(
            (Project.title.like(f'%{search_query}%')) | 
            (Project.description.like(f'%{search_query}%')) |
            (Project.text_content.like(f'%{search_query}%'))
        )
    
    # 执行查询
    projects = query.all()
    
    # 获取网站配置，如果不存在则创建默认配置
    site_config = SiteConfig.query.first()
    if not site_config:
        site_config = SiteConfig()
        db.session.add(site_config)
        db.session.commit()
    
    # 获取所有分类，用于前端显示
    carousel_projects = [project for project in projects if not project.video_url]
    categories = Category.query.all()
    
    return render_template(
        'index.html',
        projects=projects,
        carousel_projects=carousel_projects,
        site_config=site_config,
        categories=categories,
        search_query=search_query
    )

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        # 获取第一个用户（管理员）
        user = User.query.first()
        
        # 如果没有用户，创建默认管理员用户，默认密码为 'admin'
        if not user:
            user = User(username='admin')
            user.set_password('admin')
            db.session.add(user)
            db.session.commit()
        
        # 验证密码
        if user.check_password(password):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='密码错误')
    return render_template('login.html')

# 检查登录状态的装饰器
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 控制台路由，需要登录
@app.route('/admin')
@login_required
def admin():
    site_config = SiteConfig.query.first()
    return render_template('admin.html', site_config=site_config)

# 登出路由
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# 修改密码路由
@app.route('/api/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    new_password = data.get('new_password')
    
    if not new_password:
        return jsonify({'error': '密码不能为空'}), 400
    
    # 获取当前用户
    user = User.query.first()
    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': '密码修改成功'})

# 音乐管理API
# 获取所有音乐
@app.route('/api/music', methods=['GET'])
def get_music():
    music_list = Music.query.all()
    # 更新音乐文件路径，添加分类目录
    for music in music_list:
        if not music.file_path.startswith('/static/uploads/music/'):
            # 提取文件名
            filename = music.file_path.split('/')[-1]
            # 更新为包含分类目录的路径
            music.file_path = f"/static/uploads/music/{filename}"
    db.session.commit()
    return jsonify([music.to_dict() for music in music_list])

# 获取默认音乐
@app.route('/api/music/default', methods=['GET'])
def get_default_music():
    default_music = Music.query.filter_by(is_default=True).first()
    return jsonify(default_music.to_dict() if default_music else {})

# 上传音乐
@app.route('/api/music', methods=['POST'])
@login_required
def upload_music():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        # 音乐文件始终保存在根目录的music文件夹
        category = 'music'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
        file.save(file_path)
        
        # 创建音乐记录
        music = Music(
            filename=file.filename,
            file_path=f"/static/uploads/{category}/{filename}"
        )
        
        # 如果是第一个音乐，设为默认
        if not Music.query.first():
            music.is_default = True
        
        db.session.add(music)
        db.session.commit()
        return jsonify(music.to_dict()), 201
    
    return jsonify({'error': 'File type not allowed'}), 400

# 设置默认音乐
@app.route('/api/music/<int:id>/default', methods=['PUT'])
@login_required
def set_default_music(id):
    # 取消所有默认音乐
    Music.query.update({'is_default': False})
    
    # 设置当前音乐为默认
    music = Music.query.get_or_404(id)
    music.is_default = True
    db.session.commit()
    return jsonify({'message': '默认音乐设置成功'})

# 删除音乐
@app.route('/api/music/<int:id>', methods=['DELETE'])
@login_required
def delete_music(id):
    music = Music.query.get_or_404(id)
    
    # 删除文件
    file_path = os.path.join(app.root_path, music.file_path.lstrip('/'))
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 如果删除的是默认音乐，设置下一个音乐为默认
    if music.is_default:
        next_music = Music.query.filter(Music.id != id).first()
        if next_music:
            next_music.is_default = True
    
    db.session.delete(music)
    db.session.commit()
    return jsonify({'message': '音乐删除成功'})

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    # 检查项目图片路径，确保使用正确的格式
    for project in projects:
        if project.image_url:
            if '/static/uploads/images/' in project.image_url and '/project-images/' not in project.image_url:
                # 提取文件名
                filename = project.image_url.split('/')[-1]
                # 更新为项目图片专用路由
                project.image_url = f"/project-images/{project.id}/{filename}"
            # 验证文件是否存在，如果不存在，尝试从项目文件夹中获取
            file_path = os.path.join(app.root_path, project.image_url.lstrip('/'))
            if not os.path.exists(file_path) and '/project-images/' in project.image_url:
                # 检查项目文件夹中的图片
                filename = project.image_url.split('/')[-1]
                project_file_path = os.path.join(app.config['PROJECTS_FOLDER'], str(project.id), 'images', filename)
                if os.path.exists(project_file_path):
                    # 文件存在于项目文件夹，URL格式正确，无需修改
                    pass
    db.session.commit()
    return jsonify([project.to_dict() for project in projects])

# 修复所有现有项目的图片URL和文件位置
@app.route('/fix-project-images')
@login_required
def fix_project_images():
    projects = Project.query.all()
    fixed_count = 0
    
    for project in projects:
        if project.image_url:
            # 提取文件名
            filename = project.image_url.split('/')[-1]
            
            # 检查文件是否存在于旧位置
            old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename)
            
            # 检查文件是否存在于项目文件夹
            project_file_path = os.path.join(app.config['PROJECTS_FOLDER'], str(project.id), 'images', filename)
            
            if os.path.exists(old_file_path):
                # 文件存在于旧位置，移动到项目文件夹
                import shutil
                shutil.move(old_file_path, project_file_path)
                # 更新URL
                project.image_url = f"/project-images/{project.id}/{filename}"
                fixed_count += 1
            elif not os.path.exists(project_file_path) and '/project-images/' in project.image_url:
                # 文件不存在于项目文件夹，但URL指向项目图片路由，检查实际文件名
                import glob
                image_files = glob.glob(os.path.join(app.config['PROJECTS_FOLDER'], str(project.id), 'images', '*'))
                if image_files:
                    # 找到图片文件，更新URL
                    actual_filename = os.path.basename(image_files[0])
                    project.image_url = f"/project-images/{project.id}/{actual_filename}"
                    fixed_count += 1
    
    db.session.commit()
    return f"Fixed {fixed_count} projects. <a href='/debug-projects'>Check debug info</a>"

# 分类API

# 获取所有分类
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories])

# 添加分类
@app.route('/api/categories', methods=['POST'])
@login_required
def add_category():
    data = request.json
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': '分类名称不能为空'}), 400
    
    # 检查分类是否已存在
    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({'error': '分类已存在'}), 400
    
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201

# 获取单个分类
@app.route('/api/categories/<int:id>', methods=['GET'])
def get_category(id):
    category = Category.query.get_or_404(id)
    return jsonify(category.to_dict())

# 更新分类
@app.route('/api/categories/<int:id>', methods=['PUT'])
@login_required
def update_category(id):
    category = Category.query.get_or_404(id)
    data = request.json
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': '分类名称不能为空'}), 400
    
    # 检查分类是否已存在（排除当前分类）
    existing_category = Category.query.filter(Category.name == name, Category.id != id).first()
    if existing_category:
        return jsonify({'error': '分类已存在'}), 400
    
    category.name = name
    db.session.commit()
    return jsonify(category.to_dict())

# 删除分类
@app.route('/api/categories/<int:id>', methods=['DELETE'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    # 检查是否有项目使用该分类
    if category.projects:
        return jsonify({'error': '该分类下还有项目，无法删除'}), 400
    
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': '分类删除成功'})

# 项目API更新



@app.route('/api/projects/<int:id>', methods=['GET'])
def get_project(id):
    project = Project.query.get_or_404(id)
    return jsonify(project.to_dict())

@app.route('/api/projects/<int:id>', methods=['PUT'])
@login_required
def update_project(id):
    project = Project.query.get_or_404(id)
    data = request.json
    
    # 获取旧图片URL，用于清理旧文件
    old_image_url = project.image_url
    old_video_url = project.video_url
    old_download_url = project.download_url
    
    # 更新项目信息
    project.title = (data.get('title') or '').strip()
    project.description = (data.get('description') or '').strip()
    project.image_url = (data.get('image_url') or '').strip()
    project.video_url = (data.get('video_url') or '').strip()
    project.github_url = (data.get('github_url') or '').strip()
    project.live_url = (data.get('live_url') or '').strip()
    project.download_url = (data.get('download_url') or '').strip()  # 添加下载地址更新
    project.category_id = data.get('category_id')  # 添加分类更新
    project.text_content = data.get('text_content', '')
    if not project.title or not project.description:
        return jsonify({'error': '标题和描述不能为空'}), 400
    
    db.session.commit()
    
    # 如果更新了图片，且新图片在根目录images文件夹中，移动到项目文件夹
    if project.image_url and '/static/uploads/images/' in project.image_url:
        # 提取文件名
        old_filename = project.image_url.split('/')[-1]
        # 构建旧文件路径和新文件路径
        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', old_filename)
        project_folder = os.path.join(app.config['PROJECTS_FOLDER'], str(project.id))
        new_file_path = os.path.join(project_folder, 'images', old_filename)
        
        # 移动文件
        if os.path.exists(old_file_path):
            import shutil
            shutil.move(old_file_path, new_file_path)
            # 更新图片URL为项目图片专用路由
            project.image_url = f"/project-images/{project.id}/{old_filename}"
            db.session.commit()

    if project.video_url and '/static/uploads/videos/' in project.video_url:
        old_filename = project.video_url.split('/')[-1]
        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', old_filename)
        project_folder = os.path.join(app.config['PROJECTS_FOLDER'], str(project.id))
        new_file_path = os.path.join(project_folder, 'videos', old_filename)
        if os.path.exists(old_file_path):
            import shutil
            shutil.move(old_file_path, new_file_path)
            project.video_url = f"/project-videos/{project.id}/{old_filename}"
            db.session.commit()

    if project.download_url and '/static/uploads/downloads/' in project.download_url:
        old_filename = project.download_url.split('/')[-1]
        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'downloads', old_filename)
        project_folder = os.path.join(app.config['PROJECTS_FOLDER'], str(project.id))
        new_file_path = os.path.join(project_folder, 'downloads', old_filename)
        if os.path.exists(old_file_path):
            import shutil
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            shutil.move(old_file_path, new_file_path)
            project.download_url = f"/project-downloads/{project.id}/{old_filename}"
            db.session.commit()
    
    # 清理旧图片文件（如果旧图片在项目文件夹中）
    if old_image_url and ('/static/uploads/projects/' in old_image_url or '/project-images/' in old_image_url) and old_image_url != project.image_url:
        old_file_path = os.path.join(app.root_path, old_image_url.lstrip('/'))
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    if old_video_url and ('/static/uploads/projects/' in old_video_url or '/project-videos/' in old_video_url) and old_video_url != project.video_url:
        old_file_path = os.path.join(app.root_path, old_video_url.lstrip('/'))
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    if old_download_url and ('/static/uploads/projects/' in old_download_url or '/project-downloads/' in old_download_url) and old_download_url != project.download_url:
        old_file_path = resolve_uploaded_file_path(old_download_url)
        if os.path.exists(old_file_path):
            os.remove(old_file_path)
    
    return jsonify(project.to_dict())

@app.route('/api/projects/<int:id>', methods=['DELETE'])
@login_required
def delete_project(id):
    project = Project.query.get_or_404(id)
    
    # 删除项目文件夹
    project_folder = os.path.join(app.config['PROJECTS_FOLDER'], str(id))
    if os.path.exists(project_folder):
        import shutil
        shutil.rmtree(project_folder)
    
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted'})

# 网站配置API
# 获取网站配置
@app.route('/api/site-config', methods=['GET'])
def get_site_config():
    site_config = SiteConfig.query.first()
    if not site_config:
        site_config = SiteConfig()
        db.session.add(site_config)
        db.session.commit()
    return jsonify(site_config.to_dict())

# 更新网站配置
@app.route('/api/site-config', methods=['PUT'])
@login_required
def update_site_config():
    data = request.json
    site_config = SiteConfig.query.first()
    if not site_config:
        site_config = SiteConfig()
        db.session.add(site_config)
    
    site_config.site_title = data.get('site_title', site_config.site_title)
    site_config.site_subtitle = data.get('site_subtitle', site_config.site_subtitle)
    site_config.footer_text = data.get('footer_text', site_config.footer_text)
    site_config.site_icon = data.get('site_icon', site_config.site_icon)
    site_config.music_enabled = data.get('music_enabled', site_config.music_enabled)
    site_config.control_panel_visible = data.get('control_panel_visible', site_config.control_panel_visible)
    site_config.theme = data.get('theme', site_config.theme)
    
    db.session.commit()
    return jsonify({'message': '网站配置更新成功', 'config': site_config.to_dict()})

# 文件上传路由
@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    project_id = request.form.get('project_id')
    purpose = request.form.get('purpose', '')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        # 获取文件分类
        category = get_file_category(file.filename)
        if purpose == 'download':
            category = 'downloads'
        if category == 'videos' and get_upload_size(file) > app.config['VIDEO_MAX_BYTES']:
            return jsonify({'error': '视频文件过大，最大支持 1GB'}), 413
        
        # 构建文件保存路径
        if project_id:
            if not project_id.isdigit():
                return jsonify({'error': 'Invalid project id'}), 400
            # 保存到项目文件夹
            project_folder = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
            # 确保项目文件夹和分类子目录存在
            for cat in app.config['UPLOAD_CATEGORIES']:
                os.makedirs(os.path.join(project_folder, cat), exist_ok=True)
            file_path = os.path.join(project_folder, category, filename)
            # 使用专门的项目图片路由
            if category == 'images':
                file_url = f"/project-images/{project_id}/{filename}"
            elif category == 'videos':
                file_url = f"/project-videos/{project_id}/{filename}"
            elif category == 'downloads':
                file_url = f"/project-downloads/{project_id}/{filename}"
            else:
                file_url = f"/static/uploads/projects/{project_id}/{category}/{filename}"
        else:
            # 保存到根分类目录（兼容旧逻辑）
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], category, filename)
            file_url = f"/static/uploads/{category}/{filename}"
        
        file.save(file_path)
        return jsonify({'file_url': file_url}), 201
    
    return jsonify({'error': 'File type not allowed'}), 400

# 静态文件测试路由
@app.route('/test-image/<path:filename>')
def test_image(filename):
    # 测试图片文件是否能被正确访问
    file_path = os.path.join(app.root_path, 'static', filename)
    if os.path.exists(file_path):
        return send_from_directory(os.path.join(app.root_path, 'static'), filename)
    else:
        # 返回详细的错误信息，包括文件路径和可用文件列表
        import glob
        files_in_dir = glob.glob(os.path.join(app.root_path, 'static', 'uploads', 'projects', '*', 'images', '*'))
        files_str = '\n'.join(files_in_dir)
        return f"File not found: {file_path}\n\nAvailable files:\n{files_str}", 404

# 调试路由，用于检查所有项目的图片URL
@app.route('/debug-projects')
@login_required
def debug_projects():
    with app.app_context():
        projects = Project.query.all()
        debug_info = []
        
        for p in projects:
            file_exists = False
            actual_file_path = ""
            
            if p.image_url:
                if '/project-images/' in p.image_url:
                    # 处理项目图片路由
                    parts = p.image_url.split('/')
                    if len(parts) >= 3:
                        project_id = parts[2]
                        filename = '/'.join(parts[3:])
                        actual_file_path = os.path.join(app.config['PROJECTS_FOLDER'], project_id, 'images', filename)
                        file_exists = os.path.exists(actual_file_path)
                else:
                    # 处理普通静态文件路径
                    actual_file_path = os.path.join(app.root_path, p.image_url.lstrip('/'))
                    file_exists = os.path.exists(actual_file_path)
            
            debug_info.append(f"Project {p.id}: {p.title}\n  Image URL: {p.image_url}\n  Actual file path: {actual_file_path}\n  File exists: {file_exists}\n  URL accessible: {'Yes' if p.image_url else 'No image'}\n")
        
        return f"<pre>{''.join(debug_info)}</pre>"

# 项目图片专用路由，确保图片能被正确访问
@app.route('/project-images/<int:project_id>/<path:filename>')
def project_images(project_id, filename):
    # 构建图片文件路径
    file_path = os.path.join(app.config['PROJECTS_FOLDER'], str(project_id), 'images', filename)
    if os.path.exists(file_path):
        # 获取文件所在目录
        dir_path = os.path.dirname(file_path)
        # 从目录发送文件
        return send_from_directory(dir_path, filename)
    else:
        # 返回404
        return f"File not found: {file_path}", 404

@app.route('/project-videos/<int:project_id>/<path:filename>')
def project_videos(project_id, filename):
    file_path = os.path.join(app.config['PROJECTS_FOLDER'], str(project_id), 'videos', filename)
    if os.path.exists(file_path):
        dir_path = os.path.dirname(file_path)
        return send_from_directory(dir_path, filename)
    return f"File not found: {file_path}", 404

# 更新项目创建和更新逻辑，使用项目图片专用路由
@app.route('/project-downloads/<int:project_id>/<path:filename>')
def project_downloads(project_id, filename):
    file_path = os.path.join(app.config['PROJECTS_FOLDER'], str(project_id), 'downloads', filename)
    if os.path.exists(file_path):
        dir_path = os.path.dirname(file_path)
        return send_from_directory(dir_path, filename, as_attachment=True)
    return f"File not found: {file_path}", 404

@app.route('/api/projects', methods=['POST'])
@login_required
def add_project():
    data = request.json
    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()
    if not title or not description:
        return jsonify({'error': '标题和描述不能为空'}), 400

    project = Project(
        title=title,
        description=description,
        image_url=(data.get('image_url') or '').strip(),
        video_url=(data.get('video_url') or '').strip(),
        github_url=(data.get('github_url') or '').strip(),
        live_url=(data.get('live_url') or '').strip(),
        download_url=(data.get('download_url') or '').strip(),  # 添加下载地址
        category_id=data.get('category_id'),  # 添加分类
        text_content=data.get('text_content', '')
    )
    db.session.add(project)
    db.session.commit()
    
    # 为项目创建文件夹和分类子目录
    project_folder = os.path.join(app.config['PROJECTS_FOLDER'], str(project.id))
    os.makedirs(project_folder, exist_ok=True)
    for category in app.config['UPLOAD_CATEGORIES']:
        os.makedirs(os.path.join(project_folder, category), exist_ok=True)
    
    # 将图片从根目录images文件夹移动到项目文件夹
    if project.image_url and '/static/uploads/images/' in project.image_url:
        # 提取文件名
        old_filename = project.image_url.split('/')[-1]
        # 构建旧文件路径和新文件路径
        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', old_filename)
        new_file_path = os.path.join(project_folder, 'images', old_filename)
        
        # 移动文件
        if os.path.exists(old_file_path):
            import shutil
            shutil.move(old_file_path, new_file_path)
            # 更新图片URL为项目图片专用路由
            project.image_url = f"/project-images/{project.id}/{old_filename}"
            db.session.commit()

    if project.video_url and '/static/uploads/videos/' in project.video_url:
        old_filename = project.video_url.split('/')[-1]
        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', old_filename)
        new_file_path = os.path.join(project_folder, 'videos', old_filename)
        if os.path.exists(old_file_path):
            import shutil
            shutil.move(old_file_path, new_file_path)
            project.video_url = f"/project-videos/{project.id}/{old_filename}"
            db.session.commit()

    if project.download_url and '/static/uploads/downloads/' in project.download_url:
        old_filename = project.download_url.split('/')[-1]
        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'downloads', old_filename)
        new_file_path = os.path.join(project_folder, 'downloads', old_filename)
        if os.path.exists(old_file_path):
            import shutil
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            shutil.move(old_file_path, new_file_path)
            project.download_url = f"/project-downloads/{project.id}/{old_filename}"
            db.session.commit()
    
    return jsonify(project.to_dict()), 201

# 为现有项目创建文件夹
def create_project_folders():
    with app.app_context():
        projects = Project.query.all()
        for project in projects:
            # 为项目创建文件夹和分类子目录
            project_folder = os.path.join(app.config['PROJECTS_FOLDER'], str(project.id))
            os.makedirs(project_folder, exist_ok=True)
            for category in app.config['UPLOAD_CATEGORIES']:
                os.makedirs(os.path.join(project_folder, category), exist_ok=True)

def migrate_project_video_column():
    inspector = db.inspect(db.engine)
    columns = [column['name'] for column in inspector.get_columns('project')]
    migrations = {
        'video_url': "ALTER TABLE project ADD COLUMN video_url VARCHAR(300) DEFAULT ''",
        'download_url': "ALTER TABLE project ADD COLUMN download_url VARCHAR(200)",
        'category_id': "ALTER TABLE project ADD COLUMN category_id INTEGER",
        'text_content': "ALTER TABLE project ADD COLUMN text_content TEXT DEFAULT ''",
    }
    with db.engine.begin() as connection:
        for column, statement in migrations.items():
            if column not in columns:
                connection.execute(db.text(statement))
                columns.append(column)

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='启动Flask应用')
    parser.add_argument('--port', type=int, default=10008, help='应用运行端口')
    args = parser.parse_args()
    
    with app.app_context():
        db.create_all()
        migrate_project_video_column()
    
    # 为现有项目创建文件夹
    create_project_folders()
    
    # 使用指定端口或默认端口10008，监听所有地址以便公网访问
    app.run(debug=True, host='0.0.0.0', port=args.port)
