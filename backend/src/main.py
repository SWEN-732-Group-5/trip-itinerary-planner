import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from src.db import init_collections, init_state
from src.routes.auth import auth_router
from src.routes.file import file_router
from src.routes.trip_routes import trip_router
from src.routes.user_routes import user_router


def config_logger(name) -> logging.Logger:
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger = logging.getLogger(name)
    return logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ctx = init_state()
    await init_collections(app.state.ctx)
    yield
    # Cleanup: close MongoDB connection
    await app.state.client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(trip_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(file_router)


def main(reload: bool = False):
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=reload)


def dev():
    main(reload=True)


if __name__ == "__main__":
    main()
