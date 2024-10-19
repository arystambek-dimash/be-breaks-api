import json
import uuid

from celery.result import AsyncResult
from fastapi import APIRouter, status, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from src.contollers.genai.genai_controller import generate_image_and_model_task
from src.contollers.genai.genai_helpers import regenerate_description
from src.services.redis.config import get_redis_client
from src.services.redis.helpers import generate_image_hash

router = APIRouter(prefix="/3d", tags=["routers"])


@router.post("/generator", status_code=status.HTTP_202_ACCEPTED)
async def router_describe_image(
        upload_image: UploadFile = File(...)
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
        task_ids = []
        for idx, _object in enumerate(item_components):
            component_status = {
                "name_of_component": _object.get("name_of_component", ""),
                "description_of_component": _object.get("description_of_component", ""),
                "object_model": None,
                "image_url": None,
                "status": "in progress",
                "error": None
            }
            status_data["components"].append(component_status)

            task = generate_image_and_model_task.delay(_object.get("name_to_prompt"), image_id, idx)
            task_ids.append(task.id)

        await redis_client.set(f"status:{image_id}", json.dumps(status_data))
        return JSONResponse(content={"image_id": image_id, "task_ids": task_ids}, status_code=status.HTTP_202_ACCEPTED)


@router.get('/status/{image_id}', status_code=status.HTTP_200_OK)
async def get_status(image_id: str):
    try:
        redis_client = await get_redis_client()
        cached_response = await redis_client.get(f"status:{image_id}")
        if cached_response:
            status_data = json.loads(cached_response)
            print(status_data)
            # if "in progress" in str(status_data.values()):
            #     return JSONResponse(content={"status": "In progress"}, status_code=status.HTTP_200_OK)
            all_completed = all(
                component["status"] == "completed" for component in status_data.get("components", [])
            )
            if not all_completed:
                return JSONResponse({"status": "In progress"}, status_code=status.HTTP_200_OK)
            modified_data = {
                "image_id": image_id,
                "data": []
            }

            for data in status_data.get("components", []):
                modified_data["data"].append(
                    {
                        "imgSrc": data["image_url"],
                        "title": data["name_of_component"],
                        "des": data["description_of_component"],
                        "topic": data["name_of_component"],
                        "object": data["object_model"],
                    }
                )
            return modified_data
        else:
            raise HTTPException(status_code=404, detail="Data not found.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to retrieve data.")


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": task_result.status,  # E.g., PENDING, STARTED, SUCCESS, FAILURE
        "result": task_result.result if task_result.status == "SUCCESS" else None
    }
