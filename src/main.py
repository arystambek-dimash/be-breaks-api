from fastapi import FastAPI

from src.config import settings
from src.middlewares import ImageSizeMiddleware
from src.routers import genai

app = FastAPI(docs_url=settings.FASTAPI_DOCS_URL)

app.add_middleware(ImageSizeMiddleware)

app.include_router(genai.router, prefix="/api/genai")
