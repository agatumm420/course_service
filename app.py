from fastapi import FastAPI

from Controllers.admin_api import router as admin_router


app = FastAPI(
    title="Courses Service",
    description="Course and lesson management API with a lightweight admin panel.",
    version="1.0.0",
)
app.include_router(admin_router)
