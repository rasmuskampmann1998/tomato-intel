from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Route Imports
from routes import (
    auth_routes,
    admin_routes,
    editor_routes,
    researcher_routes,
    breeding_routes,
    competitor_routes,
    alert_detail_routes,
    alert_routes,
    patent_routes,
    regulation_routes,
    genetic_routes,
    social_media_routes,
    weekly_data_routes,
    monthly_data_routes
)
from schedulers.scheduler import start_schedulers

# Initialize the FastAPI application
app = FastAPI(title="Agriculture Assistant API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route for Tomato AI Assistant
@app.get("/", tags=["Root"])
async def root():
    return JSONResponse(
        content={"message": "Welcome to Tomato AI Assistant API"},
        status_code=200
    )

# Event handler for starting all scheduled jobs during application startup
@app.on_event("startup")
async def startup_event():
    start_schedulers()

# Registering Routes
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(editor_routes.router)
app.include_router(researcher_routes.router)
app.include_router(breeding_routes.router)
app.include_router(competitor_routes.router)
app.include_router(alert_detail_routes.router)
app.include_router(alert_routes.router)
app.include_router(patent_routes.router)
app.include_router(regulation_routes.router)
app.include_router(genetic_routes.router)
app.include_router(social_media_routes.router)
app.include_router(weekly_data_routes.router)
app.include_router(monthly_data_routes.router)
# Entry point to run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=False)
