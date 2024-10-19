from pathlib import Path

from pydantic_settings import BaseSettings

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / 'media'

Path.mkdir(MEDIA_DIR, exist_ok=True)


class Settings(BaseSettings):
    FASTAPI_DOCS_URL: str

    # another server to save datas
    BACKEND_RESPONSE_URL: str

    HUGGING_FACE_TOKEN: str

    OPENAI_API_KEY: str

    GOOGLE_API_KEY: str
    CSE_ID: str

    HUGGINGFACE_SPACE_NAME: str

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_BUCKET_NAME: str


def get_settings():
    return Settings()


settings = get_settings()
