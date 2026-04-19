from typing import Optional
import os
from dotenv import load_dotenv
from pymongo import AsyncMongoClient

_db_client: Optional[AsyncMongoClient] = None


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
        _db_client = AsyncMongoClient(url, tz_aware=True)
    return _db_client
