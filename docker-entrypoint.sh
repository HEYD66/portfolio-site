#!/usr/bin/env sh
set -eu

mkdir -p \
  "${UPLOAD_ROOT:-/app/static/uploads}/images" \
  "${UPLOAD_ROOT:-/app/static/uploads}/videos" \
  "${UPLOAD_ROOT:-/app/static/uploads}/music" \
  "${UPLOAD_ROOT:-/app/static/uploads}/docs" \
  "${UPLOAD_ROOT:-/app/static/uploads}/downloads" \
  "${UPLOAD_ROOT:-/app/static/uploads}/projects"

python - <<'PY'
from app import app, db, create_project_folders, migrate_project_video_column

with app.app_context():
    db.create_all()
    migrate_project_video_column()

create_project_folders()
print("database ready")
PY

exec "$@"
