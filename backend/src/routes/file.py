import os
from datetime import date

from fastapi import APIRouter, Depends, File, UploadFile
from src.db import FILE_BUCKET_NAME, AppContextDep, ensure_file_bucket_exists

from .auth import authenticated_user

file_router = APIRouter(prefix="/api/file", tags=["file"])


def default_file_name():
    return "unnamed_file_" + date.today().isoformat().replace("-", "_")


@file_router.post("/upload")
def upload_file(
    state: AppContextDep,
    file: UploadFile = File(...),
    user: dict = Depends(authenticated_user),
):
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)

    file_name = f"{user['user_id']}/{file.filename or default_file_name()}"

    ensure_file_bucket_exists(state.minio)
    result = state.minio.put_object(
        FILE_BUCKET_NAME,
        file_name,
        file.file,
        length=size,
        content_type=file.content_type or "application/octet-stream",
    )
    return {"object_name": result.object_name, "bucket_name": result.bucket_name}
