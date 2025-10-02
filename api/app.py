# ==================== api/app.py ====================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import stream, download

app = FastAPI(
    title="TeleStore API",
    description="Stream and download files from Telegram",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(stream.router)
app.include_router(download.router)

@app.get("/")
async def root():
    """API info endpoint"""
    return {
        "name": "TeleStore API",
        "version": "1.0.0",
        "endpoints": {
            "stream": "/{fileId}",
            "watch": "/watch/{fileId}",
            "download": "/dl/{fileId}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}