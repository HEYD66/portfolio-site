FROM docker.1panel.live/library/python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UPLOAD_ROOT=/app/static/uploads \
    DATABASE_PATH=/app/static/uploads/portfolio_new.db \
    VIDEO_MAX_BYTES=1073741824 \
    MAX_UPLOAD_BYTES=1090519040

WORKDIR /app

COPY requirements.txt .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY . .
RUN chmod +x /app/docker-entrypoint.sh \
    && mkdir -p \
        /app/static/uploads/images \
        /app/static/uploads/videos \
        /app/static/uploads/music \
        /app/static/uploads/docs \
        /app/static/uploads/downloads \
        /app/static/uploads/projects

EXPOSE 10008

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:10008", "wsgi:app"]
