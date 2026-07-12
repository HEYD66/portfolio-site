from app import app, db, Project
import os

with app.app_context():
    print(f"app.root_path: {app.root_path}")
    print(f"app.config['PROJECTS_FOLDER']: {app.config['PROJECTS_FOLDER']}")
    
    # 获取项目1
    project = Project.query.get(1)
    if project:
        print(f"当前项目图片URL: {project.image_url}")
        
        # 提取文件名
        if project.image_url:
            filename = project.image_url.split('/')[-1]
            
            # 检查文件是否存在于项目文件夹
            project_file_path = os.path.join(app.config['PROJECTS_FOLDER'], str(project.id), 'images', filename)
            absolute_project_path = os.path.abspath(project_file_path)
            print(f"项目文件路径: {project_file_path}")
            print(f"项目文件绝对路径: {absolute_project_path}")
            print(f"文件存在于项目文件夹: {os.path.exists(project_file_path)}")
            
            # 检查URL对应的绝对路径
            url_file_path = os.path.join(app.root_path, project.image_url.lstrip('/'))
            absolute_url_path = os.path.abspath(url_file_path)
            print(f"URL文件路径: {url_file_path}")
            print(f"URL文件绝对路径: {absolute_url_path}")
            print(f"文件存在于URL路径: {os.path.exists(url_file_path)}")
            
            # 更新URL为项目图片专用路由
            new_image_url = f"/project-images/{project.id}/{filename}"
            project.image_url = new_image_url
            db.session.commit()
            print(f"已更新图片URL为: {new_image_url}")
            
            # 测试项目图片路由
            test_url = f"http://127.0.0.1:10008{new_image_url}"
            print(f"测试URL: {test_url}")
        else:
            print("项目没有图片URL")
    else:
        print("未找到项目1")