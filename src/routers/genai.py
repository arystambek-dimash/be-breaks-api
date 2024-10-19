import json
import uuid

from fastapi import APIRouter, status, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from src.contollers.genai.genai_controller import generate_image_and_model
from src.contollers.genai.genai_helpers import regenerate_description
from src.services.redis.config import get_redis_client
from src.services.redis.helpers import generate_image_hash

router = APIRouter(prefix="/3d", tags=["routers"])


@router.post(
    '/generator',
    status_code=status.HTTP_202_ACCEPTED,
    description="Image to text describer",
)
async def router_describe_image(
        upload_image: UploadFile = File(...),
        background_tasks: BackgroundTasks = None,
):
    if upload_image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid image type. Only JPEG and PNG are supported."
        )

    try:
        contents = await upload_image.read()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to read uploaded image."
        )

    image_hash = generate_image_hash(contents)

    try:
        redis_client = await get_redis_client()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to connect to the cache."
        )

    existing_image_id = await redis_client.get(f"hash:{image_hash}")
    if existing_image_id:
        existing_image_id = existing_image_id.decode('utf-8')
        return JSONResponse(content={"image_id": existing_image_id}, status_code=status.HTTP_200_OK)
    else:
        image_id = str(uuid.uuid4())

        await redis_client.set(f"hash:{image_hash}", image_id)

        try:
            cached_description = await redis_client.get(f"description:{image_hash}")
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Cache access error."
            )

        if cached_description:
            response = json.loads(cached_description)
        else:
            response = await regenerate_description(
                redis_client, image_hash, image_id, contents
            )
            await redis_client.set(f"description:{image_hash}", json.dumps(response))

        status_data = {
            "image_id": image_id,
            "object_name": response.get("description", {}).get("name_of_item", ""),
            "description_of_item": response.get("description", {}).get("description_of_item", ""),
            "components": []
        }

        item_components = response.get("description", {}).get("item_components", [])
        for idx, _object in enumerate(item_components):
            component_status = {
                "name_of_component": _object.get("name_of_component", ""),
                "description_of_component": _object.get("description_of_component", ""),
                "object_model": None,
                "status": "in progress",
                "error": None
            }
            status_data["components"].append(component_status)

            background_tasks.add_task(
                generate_image_and_model,
                _object.get("name_to_prompt"),
                image_id,
                idx,
            )

        try:
            await redis_client.set(f"status:{image_id}", json.dumps(status_data))
        except Exception:
            pass

        return JSONResponse(content={"image_id": image_id}, status_code=status.HTTP_202_ACCEPTED)


@router.get('/status/{image_id}', status_code=status.HTTP_200_OK)
async def get_status(image_id: str):
    try:
        redis_client = await get_redis_client()
        cached_response = await redis_client.get(f"status:{image_id}")
        if cached_response:
            status_data = json.loads(cached_response)
            return status_data
        else:
            raise HTTPException(status_code=404, detail="Data not found.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to retrieve data.")
