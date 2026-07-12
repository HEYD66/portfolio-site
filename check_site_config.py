from app import app, db, SiteConfig
import os

with app.app_context():
    # 检查站点图标配置
    config = SiteConfig.query.first()
    if config:
        print(f"Site icon: {config.site_icon}")
    else:
        print("No site config found")
    
    # 检查根目录images和docs文件夹中的文件
    images_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
    docs_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'docs')
    
    print(f"\n根目录images文件夹内容:")
    if os.path.exists(images_dir):
        for file in os.listdir(images_dir):
            print(f"  {file}")
    else:
        print("  文件夹不存在")
    
    print(f"\n根目录docs文件夹内容:")
    if os.path.exists(docs_dir):
        for file in os.listdir(docs_dir):
            print(f"  {file}")
    else:
        print("  文件夹不存在")
    
    # 检查项目文件夹中的图片
    print(f"\n项目文件夹内容:")
    projects_dir = app.config['PROJECTS_FOLDER']
    if os.path.exists(projects_dir):
        for project_id in os.listdir(projects_dir):
            project_images_dir = os.path.join(projects_dir, project_id, 'images')
            if os.path.exists(project_images_dir):
                images = os.listdir(project_images_dir)
                print(f"  项目 {project_id} 图片数量: {len(images)}")
                if images:
                    print(f"    图片列表: {images}")
