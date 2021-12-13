import sentry_sdk
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.kafka import producer
from app.core.logging import logger

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

if settings.SENTRY_DSN_URL is not None:
    sentry_sdk.init(settings.SENTRY_DSN_URL)

    app.add_middleware(SentryAsgiMiddleware)


@app.on_event("startup")
async def startup_event():
    logger.info("starting kafka producer")
    await producer.start()


@app.on_event("shutdown")
async def shutdown_event():
    await producer.stop()


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
app.mount(
    settings.HAADF_IMAGE_URL_PREFIX,
    StaticFiles(directory=settings.HAADF_IMAGE_STATIC_DIR),
    name="haadf",
)
