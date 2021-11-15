from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.kafka import producer

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)


@app.on_event("startup")
async def startup_event():
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
        expose_headers=["*"]
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
app.mount(
    settings.HAADF_IMAGE_URL_PREFIX,
    StaticFiles(directory=settings.HAADF_IMAGE_STATIC_DIR),
    name="haadf",
)
