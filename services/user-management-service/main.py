"""
MANDI EAR™ User Management Service
Authentication, profiles, and preferences
"""

from fastapi import FastAPI

app = FastAPI(
    title="MANDI EAR™ User Management Service",
    description="User authentication and profile management",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "service": "User Management Service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}