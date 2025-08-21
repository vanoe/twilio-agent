import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import api
from config.settings import settings

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(api.router, tags=["API"])
PORT = int(os.getenv('PORT', 5050))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)