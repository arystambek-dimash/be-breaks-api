import asyncio
import json
import os
import logging

from src.config import MEDIA_DIR
from src.services.aws.s3 import generate_key, upload_file
from src.services.genai.openai import generate_image
from src.services.huggingface.generate_mesh import check_input_image, preprocess, generate
from src.services.redis.config import get_redis_client
from src.worker import celery_app

# Set up the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@celery_app.task
def generate_image_and_model_task(prompt: str, image_id: str, idx: int):
    loop = asyncio.get_event_loop()
    try:
        logger.info(f"Task started for image_id: {image_id}, component index: {idx}, prompt: {prompt}")
        image_url = loop.run_until_complete(generate_image(prompt, image_id, idx))
        logger.info(f"Image generated successfully: {image_url}")

        image_filename = f"{image_id}_{idx}.png"
        image_path = os.path.join(MEDIA_DIR, image_filename)

        if not os.path.exists(image_path):
            raise Exception(f"Image {image_filename} was not saved.")

        author_role = "user"
        file_type = "3dmodel"
        model_name = f"{image_id}_{idx}.obj"

        # model_url = loop.run_until_complete(
        #     process_image_to_3d_model(image_path, author_role, file_type, model_name)
        # )
        # logger.info(f"3D model generated successfully: {model_url}")

        loop.run_until_complete(update_response_in_redis(image_id, idx, image_url, ""))
        logger.info(f"Task completed for image_id: {image_id}, component index: {idx}")

    except Exception as e:
        logger.error(f"Error in task for image_id: {image_id}, component index: {idx} - {str(e)}")
        loop.run_until_complete(update_response_with_error(image_id, idx, str(e)))


#
# async def process_image_to_3d_model(image_path: str, author_role: str, file_type: str, name: str) -> str:
#     retries = 5
#     backoff_factor = 2
#     for attempt in range(1, retries + 1):
#         try:
#             logger.info(f"Processing image to 3D model (Attempt {attempt}) for file: {image_path}")
#
#             if not await check_input_image(image_path):
#                 raise Exception("Input image check failed.")
#
#             preprocessed_image = await preprocess(image_path, foreground_ratio=0.75)
#             if not preprocessed_image:
#                 raise Exception("Image preprocessing failed.")
#
#             model_path = await generate(preprocessed_image)
#             if not model_path:
#                 raise Exception("3D model generation failed.")
#
#             s3_key = generate_key(author_role, file_type, name)
#             model_url = upload_file(model_path, s3_key)
#             if not model_url:
#                 raise Exception("Failed to upload 3D model to AWS S3.")
#
#             return model_url
#
#         except Exception as e:
#             logger.error(f"Error in 3D model generation: {str(e)}")
#             if "No GPU is currently available" in str(e) and attempt < retries:
#                 wait_time = backoff_factor ** (attempt - 1)
#                 logger.warning(f"No GPU available, retrying in {wait_time} seconds (Attempt {attempt})")
#                 await asyncio.sleep(wait_time)
#                 continue
#             else:
#                 raise


async def update_response_in_redis(image_id: str, idx: int, image_url: str, model_url: str):
    redis_client = await get_redis_client()
    cached_response = await redis_client.get(f"status:{image_id}")

    if cached_response:
        status_data = json.loads(cached_response)
        if idx < len(status_data["components"]):
            status_data["components"][idx]["object_model"] = model_url
            status_data["components"][idx]["status"] = "completed"
            status_data["components"][idx]["image_url"] = image_url
            await redis_client.set(f"status:{image_id}", json.dumps(status_data))
        logger.info(f"Updated Redis for image_id: {image_id}, component index: {idx}")


async def update_response_with_error(image_id: str, idx: int, error: str):
    redis_client = await get_redis_client()
    cached_response = await redis_client.get(f"status:{image_id}")
    if cached_response:
        status_data = json.loads(cached_response)
        if idx < len(status_data["components"]):
            status_data["components"][idx]["status"] = "error"
            status_data["components"][idx]["error"] = error
            await redis_client.set(f"status:{image_id}", json.dumps(status_data))
        logger.info(f"Updated Redis with error for image_id: {image_id}, component index: {idx}, error: {error}")
