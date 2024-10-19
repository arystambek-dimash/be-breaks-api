import os
import io
from typing import Any, Dict
from PIL import Image
import httpx
from rembg import remove

from src.config import settings, MEDIA_DIR

API_URL = "https://api-inference.huggingface.co/models/renderartist/toyboxflux"
headers = {"Authorization": f"Bearer {settings.HUGGING_FACE_TOKEN}"}

timeout = httpx.Timeout(600, connect=120)


async def query(payload: Dict[str, Any]) -> bytes:
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.content
        except httpx.ReadTimeout:
            raise
        except httpx.HTTPError as http_err:
            print(http_err)
            raise
        except Exception as err:
            print(err)
            raise


async def generate_image(inputs: str, image_id: str, index: int) -> str:
    prompt = (
        f"{inputs}. Generate a high-quality photo of the object against a plain white background, "
        "focusing solely on the object without any additional elements."
        "Generate the component exactly"
    )
    image_bytes = await query({"inputs": prompt})

    image = Image.open(io.BytesIO(image_bytes))
    image = remove(image)

    filename = f"{image_id}_{index}.png"

    image_path = os.path.join(MEDIA_DIR, filename)

    image.save(image_path)

    image_url = f"/media/{filename}"

    return image_url
