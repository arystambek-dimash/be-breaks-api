import json

from fastapi import HTTPException

from src.services.genai.openai import get_image_details, detail_by_text


async def regenerate_description(redis_client, image_hash, image_id, contents):
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


async def regenerate_query_description(redis_client, query, query_id):
    response = await detail_by_text(query)

    if response is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate description."
        )

    await redis_client.setex(query, 3600, json.dumps({
        "query_id": query_id,
        "description": response
    }))
    await redis_client.setex(f"query:{query_id}", 3600, query)

    return {
        "query_id": query_id,
        "description": response
    }
