const modal = document.getElementById('projectModal');
const form = document.getElementById('projectForm');
const modalTitle = document.getElementById('modalTitle');
const projectId = document.getElementById('projectId');
const title = document.getElementById('title');
const description = document.getElementById('description');
const imageUrlInput = document.getElementById('image_url');
const localImage = document.getElementById('local_image');
const videoUrlInput = document.getElementById('video_url');
const localVideo = document.getElementById('local_video');
const localDownload = document.getElementById('local_download');
const textContent = document.getElementById('text_content');
const githubUrl = document.getElementById('github_url');
const liveUrl = document.getElementById('live_url');
const downloadUrl = document.getElementById('download_url');
const categorySelect = document.getElementById('category_id');
const projectsTable = document.getElementById('projectsTable');
const imagePreviewText = document.getElementById('image-preview-text');
const videoPreviewText = document.getElementById('video-preview-text');
const downloadPreviewText = document.getElementById('download-preview-text');
const VIDEO_MAX_BYTES = 1024 * 1024 * 1024;
const DOWNLOAD_HELP_TEXT = '上传后会自动生成下载地址，前台点击“下载”会直接下载文件';
const VIDEO_HELP_TEXT = '视频最大支持 1GB';

const categoryModal = document.getElementById('categoryModal');
const categoryForm = document.getElementById('categoryForm');
const categoryModalTitle = document.getElementById('categoryModalTitle');
const categoryId = document.getElementById('categoryId');
const categoryName = document.getElementById('categoryName');
const categoriesTable = document.getElementById('categoriesTable');

let editingId = null;
let editingCategoryId = null;
let modalPointerDownTarget = null;

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const isJson = response.headers.get('content-type')?.includes('application/json');
    const payload = isJson ? await response.json() : null;
    if (!response.ok) {
        throw new Error(payload?.error || payload?.message || '请求失败');
    }
    return payload;
}

function setEmptyRow(tbody, colspan, message) {
    tbody.replaceChildren();
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = colspan;
    cell.className = 'empty-state';
    cell.textContent = message;
    row.appendChild(cell);
    tbody.appendChild(row);
}

function makeButton(label, className, onClick) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.textContent = label;
    button.addEventListener('click', onClick);
    return button;
}

function openModal() {
    modalTitle.textContent = '添加项目';
    form.reset();
    projectId.value = '';
    editingId = null;
    imagePreviewText.textContent = '';
    videoPreviewText.textContent = VIDEO_HELP_TEXT;
    downloadPreviewText.textContent = DOWNLOAD_HELP_TEXT;
    modal.classList.add('show');
}

function closeModal() {
    modal.classList.remove('show');
}

async function fetchProjects() {
    try {
        const projects = await requestJson('/api/projects');
        renderProjects(projects);
    } catch (error) {
        setEmptyRow(projectsTable, 3, error.message);
    }
}

function renderProjects(projects) {
    projectsTable.replaceChildren();
    if (!projects.length) {
        setEmptyRow(projectsTable, 3, '暂无项目，点击右上角添加。');
        return;
    }

    projects.forEach(project => {
        const row = document.createElement('tr');
        const titleCell = document.createElement('td');
        const descriptionCell = document.createElement('td');
        const actionsCell = document.createElement('td');

        titleCell.textContent = project.title;
        descriptionCell.textContent = project.description.length > 100
            ? `${project.description.slice(0, 100)}...`
            : project.description;
        actionsCell.className = 'actions';
        actionsCell.append(
            makeButton('编辑', 'btn', () => editProject(project.id)),
            makeButton('删除', 'btn btn-danger', () => deleteProject(project.id))
        );

        row.append(titleCell, descriptionCell, actionsCell);
        projectsTable.appendChild(row);
    });
}

async function editProject(id) {
    try {
        const project = await requestJson(`/api/projects/${id}`);
        modalTitle.textContent = '编辑项目';
        projectId.value = project.id;
        title.value = project.title || '';
        description.value = project.description || '';
        imageUrlInput.value = project.image_url || '';
        videoUrlInput.value = project.video_url || '';
        textContent.value = project.text_content || '';
        githubUrl.value = project.github_url || '';
        liveUrl.value = project.live_url || '';
        downloadUrl.value = project.download_url || '';
        categorySelect.value = project.category_id || '';
        localImage.value = '';
        localVideo.value = '';
        localDownload.value = '';
        imagePreviewText.textContent = '';
        videoPreviewText.textContent = VIDEO_HELP_TEXT;
        downloadPreviewText.textContent = DOWNLOAD_HELP_TEXT;
        editingId = project.id;
        modal.classList.add('show');
    } catch (error) {
        alert(error.message);
    }
}

async function deleteProject(id) {
    if (!confirm('确定要删除这个项目吗？')) return;
    try {
        await requestJson(`/api/projects/${id}`, { method: 'DELETE' });
        fetchProjects();
    } catch (error) {
        alert(error.message);
    }
}

function openCategoryModal() {
    categoryModalTitle.textContent = '添加分类';
    categoryForm.reset();
    categoryId.value = '';
    editingCategoryId = null;
    categoryModal.classList.add('show');
}

function closeCategoryModal() {
    categoryModal.classList.remove('show');
}

async function fetchCategories() {
    try {
        const categories = await requestJson('/api/categories');
        renderCategories(categories);
        populateCategoryOptions(categories);
    } catch (error) {
        setEmptyRow(categoriesTable, 3, error.message);
    }
}

function renderCategories(categories) {
    categoriesTable.replaceChildren();
    if (!categories.length) {
        setEmptyRow(categoriesTable, 3, '暂无分类。');
        return;
    }

    categories.forEach(category => {
        const row = document.createElement('tr');
        const nameCell = document.createElement('td');
        const dateCell = document.createElement('td');
        const actionsCell = document.createElement('td');

        nameCell.textContent = category.name;
        dateCell.textContent = new Date(category.created_at).toLocaleString();
        actionsCell.className = 'actions';
        actionsCell.append(
            makeButton('编辑', 'btn', () => editCategory(category.id)),
            makeButton('删除', 'btn btn-danger', () => deleteCategory(category.id))
        );

        row.append(nameCell, dateCell, actionsCell);
        categoriesTable.appendChild(row);
    });
}

async function editCategory(id) {
    try {
        const category = await requestJson(`/api/categories/${id}`);
        categoryModalTitle.textContent = '编辑分类';
        categoryId.value = category.id;
        categoryName.value = category.name;
        editingCategoryId = category.id;
        categoryModal.classList.add('show');
    } catch (error) {
        alert(error.message);
    }
}

async function deleteCategory(id) {
    if (!confirm('确定要删除这个分类吗？')) return;
    try {
        await requestJson(`/api/categories/${id}`, { method: 'DELETE' });
        fetchCategories();
    } catch (error) {
        alert(error.message);
    }
}

function populateCategoryOptions(categories) {
    const selectedCategoryId = categorySelect.value;
    categorySelect.replaceChildren();

    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = '无分类';
    categorySelect.appendChild(emptyOption);

    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        categorySelect.appendChild(option);
    });

    categorySelect.value = selectedCategoryId;
}

categoryForm.addEventListener('submit', async event => {
    event.preventDefault();
    const name = categoryName.value.trim();
    if (!name) return;

    try {
        if (editingCategoryId) {
            await requestJson(`/api/categories/${editingCategoryId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
        } else {
            await requestJson('/api/categories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
        }
        closeCategoryModal();
        fetchCategories();
    } catch (error) {
        alert(error.message);
    }
});

form.addEventListener('submit', async event => {
    event.preventDefault();
    let imageUrl = imageUrlInput.value.trim();
    let videoUrl = videoUrlInput.value.trim();
    let downloadFileUrl = downloadUrl.value.trim();

    try {
        if (localImage.files.length > 0) {
            const formData = new FormData();
            formData.append('file', localImage.files[0]);
            if (projectId.value) {
                formData.append('project_id', projectId.value);
            }

            const uploadData = await requestJson('/api/upload', {
                method: 'POST',
                body: formData
            });
            imageUrl = uploadData.file_url;
        }

        if (localVideo.files.length > 0) {
            if (localVideo.files[0].size > VIDEO_MAX_BYTES) {
                throw new Error('视频文件过大，最大支持 1GB');
            }

            const formData = new FormData();
            formData.append('file', localVideo.files[0]);
            if (projectId.value) {
                formData.append('project_id', projectId.value);
            }

            const uploadData = await requestJson('/api/upload', {
                method: 'POST',
                body: formData
            });
            videoUrl = uploadData.file_url;
        }

        if (localDownload.files.length > 0) {
            const formData = new FormData();
            formData.append('file', localDownload.files[0]);
            formData.append('purpose', 'download');
            if (projectId.value) {
                formData.append('project_id', projectId.value);
            }

            const uploadData = await requestJson('/api/upload', {
                method: 'POST',
                body: formData
            });
            downloadFileUrl = uploadData.file_url;
        }

        const projectData = {
            title: title.value.trim(),
            description: description.value.trim(),
            image_url: imageUrl,
            video_url: videoUrl,
            text_content: textContent.value,
            github_url: githubUrl.value.trim(),
            live_url: liveUrl.value.trim(),
            download_url: downloadFileUrl,
            category_id: categorySelect.value || null
        };

        if (editingId) {
            await requestJson(`/api/projects/${editingId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(projectData)
            });
        } else {
            await requestJson('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(projectData)
            });
        }

        closeModal();
        fetchProjects();
    } catch (error) {
        alert(error.message);
    }
});

function switchTab(tabName) {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.classList.remove('active');
        btn.style.color = '#666';
        btn.style.borderBottom = 'none';
    });
    tabContents.forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none';
    });

    const activeBtn = document.querySelector(`[onclick="switchTab('${tabName}')"]`);
    const activeContent = document.getElementById(`${tabName}-tab`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.style.color = 'var(--primary-color)';
        activeBtn.style.borderBottom = '3px solid var(--primary-color)';
    }
    if (activeContent) {
        activeContent.classList.add('active');
        activeContent.style.display = 'block';
    }

    if (tabName === 'projects') fetchProjects();
    if (tabName === 'categories') fetchCategories();
    if (tabName === 'music' && typeof fetchMusic === 'function') fetchMusic();
    if (tabName === 'site-config' && typeof fetchSiteConfig === 'function') fetchSiteConfig();
}

window.addEventListener('pointerdown', event => {
    modalPointerDownTarget = event.target;
});

window.addEventListener('click', event => {
    if (event.target === modal && modalPointerDownTarget === modal) closeModal();
    if (event.target === categoryModal && modalPointerDownTarget === categoryModal) closeCategoryModal();
    modalPointerDownTarget = null;
});

document.addEventListener('DOMContentLoaded', () => {
    fetchProjects();
    fetchCategories();
});
