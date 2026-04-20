import json
import logging
import os
from dataclasses import dataclass
from typing import Annotated, Optional, TypedDict, cast

from dotenv import load_dotenv
from fastapi import Depends, Request
from minio import Minio
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

_db_client: Optional[AsyncMongoClient] = None
_minio_bucket: Optional[Minio] = None
FILE_BUCKET_NAME = "my-bucket"


def gen_mongodb_url():
    username = os.getenv("MONGO_USERNAME", "admin")
    password = os.getenv("MONGO_PASSWORD", "password")
    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    return f"mongodb://{username}:{password}@{host}:{port}"


def get_mongodb_url():
    load_dotenv()
    if "MONGODB_URL" in os.environ:
        return os.environ["MONGODB_URL"]
    return gen_mongodb_url()


def get_db_client() -> AsyncMongoClient:
    global _db_client
    if _db_client is None:
        url = get_mongodb_url()
        _db_client = AsyncMongoClient(url)
    return _db_client


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
        "endpoint": f"{host}:{port}",
        "access_key": access_key,
        "secret_key": secret_key,
    }


def create_minio_client(cred: MinioConfig) -> Minio:
    return Minio(**cred, secure=False)


def init_state():
    mongo = get_db_client()
    return AppContext(
        logger=logging.getLogger("main"),
        mongo=mongo,
        minio=get_minio_client(),
        db=mongo.trip_itinerary_planner,
        bookings_collection=mongo.trip_itinerary_planner.bookings,
    )


async def init_collections(state: "AppContext"):
    await state.bookings_collection.delete_many({})
    await state.bookings_collection.insert_many(
        [
            {
                "user_id": "user1",
                "reference_number": "REF123",
                "customer_service_number": "CSN123",
                "provider_name": "Provider A",
            },
            {
                "user_id": "user1",
                "reference_number": "REF456",
                "customer_service_number": "CSN456",
                "provider_name": "Provider B",
            },
            {
                "user_id": "user2",
                "reference_number": "REF789",
                "customer_service_number": "CSN789",
                "provider_name": "Provider C",
            },
        ]
    )


def get_minio_client(cred: MinioConfig = get_minio_credentials()) -> Minio:
    global _minio_bucket
    if _minio_bucket is None:
        _minio_bucket = create_minio_client(cred)
    return _minio_bucket


def ensure_file_bucket_exists(minio_client: Minio, bucket_name: str = FILE_BUCKET_NAME):
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    desired_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadOnly",
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
            }
        ],
    }
    if json.loads(minio_client.get_bucket_policy(bucket_name)) != desired_policy:
        minio_client.set_bucket_policy(bucket_name, json.dumps(desired_policy))


@dataclass
class AppContext:
    logger: logging.Logger
    mongo: AsyncMongoClient
    minio: Minio
    db: AsyncDatabase
    bookings_collection: AsyncCollection


def get_state(request: Request):
    return cast(AppContext, request.app.state.ctx)


AppContextDep = Annotated[AppContext, Depends(get_state)]
