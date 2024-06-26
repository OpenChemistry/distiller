from fastapi import APIRouter

from app.api.api_v1.endpoints import (auth, files, jobs, machines, microscopes,
                                      notebooks, notifications, scans)

api_router = APIRouter()

api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(auth.router, prefix="", tags=["auth"])
api_router.include_router(notifications.router, prefix="", tags=["notfications"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(machines.router, prefix="/machines", tags=["machines"])
api_router.include_router(
    microscopes.router, prefix="/microscopes", tags=["microscopes"]
)
api_router.include_router(notebooks.router, prefix="/notebooks", tags=["notebooks"])
