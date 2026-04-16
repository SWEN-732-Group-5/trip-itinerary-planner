import os
from datetime import date
from typing import TypedDict

from fastapi import APIRouter, Depends, File, UploadFile
from minio import Minio

from .auth import authenticated_user

file_router = APIRouter(prefix="/api/file", tags=["file"])
FILE_BUCKET_NAME = "my-bucket"


class MinioConfig(TypedDict):
    endpoint: str
    access_key: str
    secret_key: str


def get_minio_credentials() -> MinioConfig:
    host = os.getenv("MINIO_HOST", "localhost")
    port = os.getenv("MINIO_PORT", "9000")
    access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    return {
        "endpoint": f"http://{host}:{port}",
        "access_key": access_key,
        "secret_key": secret_key,
    }


def create_minio_client(cred: MinioConfig = get_minio_credentials()) -> Minio:
    return Minio(**cred, secure=False)


minio_client = create_minio_client()


def default_file_name():
    return "unnamed_file_" + date.today().isoformat().replace("-", "_")


@file_router.post("/upload")
def upload_file(file: UploadFile = File(...), user: dict = Depends(authenticated_user)):
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)

    file_name = f"{user['user_id']}/{file.filename or default_file_name()}"

    result = minio_client.put_object(
        FILE_BUCKET_NAME,
        file_name,
        file.file,
        length=size,
        content_type=file.content_type or "application/octet-stream",
    )
    return {"object_name": result.object_name, "bucket_name": result.bucket_name}
