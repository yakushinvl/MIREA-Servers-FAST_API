from fastapi import FastAPI
import os
from app.routers import tasks, users, admin, websocket

app = FastAPI(title="MIREA Servers FAST API")

app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(websocket.router)

@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "env": os.getenv("APP_ENV", "local")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
