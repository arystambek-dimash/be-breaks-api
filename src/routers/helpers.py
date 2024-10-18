import json

from fastapi import HTTPException

from src.services.genai.openai import get_image_details


async def regenerate_description(redis_client, image_hash, image_id, contents):
    """Helper function to regenerate description"""
    response = await get_image_details(contents)

    if response is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate description."
        )

    await redis_client.setex(image_hash, 3600, json.dumps({
        "image_id": image_id,
        "description": response
    }))
    await redis_client.setex(f"image:{image_id}", 3600, contents)

    return {
        "image_id": image_id,
        "description": response
    }
