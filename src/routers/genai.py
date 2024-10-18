import json
import uuid

from fastapi import APIRouter, status, File, UploadFile, HTTPException

from src.routers.helpers import regenerate_description
from src.services.genai.openai import get_image_details
from src.services.redis.config import get_redis_client
from src.services.redis.helpers import generate_image_hash

router = APIRouter(prefix="/openai", tags=["routers"])


@router.post('/describer',
             status_code=status.HTTP_201_CREATED,
             description="image to text describer")
async def router_describe_image(upload_image: UploadFile = File(...)):
    try:
        contents = await upload_image.read()

        image_id = str(uuid.uuid4())
        image_hash = generate_image_hash(contents)

        redis_client = await get_redis_client()

        cached_response = await redis_client.get(image_hash)
        if cached_response:
            cached_response = json.loads(cached_response)
            if cached_response.get("description") is None:
                response = await regenerate_description(redis_client, image_hash, image_id, contents)
            else:
                return cached_response
        else:
            response = await regenerate_description(redis_client, image_hash, image_id, contents)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )
