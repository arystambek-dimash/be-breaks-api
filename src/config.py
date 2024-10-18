from pydantic_settings import BaseSettings

from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    FASTAPI_DOCS_URL: str

    # another server to save datas
    BACKEND_RESPONSE_URL: str

    HUGGING_FACE_TOKEN: str

    OPENAI_API_KEY: str


def get_settings():
    return Settings()


settings = get_settings()
