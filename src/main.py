from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from src.config import settings, MEDIA_DIR
from src.middlewares import ImageSizeMiddleware
from src.routers import genai

app = FastAPI(docs_url=settings.FASTAPI_DOCS_URL)

app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

app.add_middleware(ImageSizeMiddleware)

app.include_router(genai.router, prefix="/api/genai")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)