import json
import os
import time

from src.config import MEDIA_DIR
from src.services.aws.s3 import generate_key, upload_file
from src.services.huggingface.generate_image import image_generator
from src.services.huggingface.generate_mesh import check_input_image, preprocess, generate
from src.services.redis.config import get_redis_client


def generate_image_and_model(prompt: str, image_id: str, idx: int):
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(image_generator(prompt, image_id, idx))

        image_filename = f"{image_id}_{idx}.png"
        image_path = os.path.join(MEDIA_DIR, image_filename)

        if not os.path.exists(image_path):
            raise Exception(f"Image {image_filename} was not saved.")

        author_role = "user"
        file_type = "3dmodel"
        model_name = f"{image_id}_{idx}.obj"

        model_url = process_image_to_3d_model(
            image_path, author_role, file_type, model_name
        )

        async def update_response_in_redis():
            redis_client = await get_redis_client()
            cached_response = await redis_client.get(image_id)
            if cached_response:
                status_data = json.loads(cached_response)
                if idx < len(status_data["components"]):
                    status_data["components"][idx]["object_model"] = model_url
                    status_data["components"][idx]["status"] = "completed"
                    await redis_client.set(image_id, json.dumps(status_data))

        loop.run_until_complete(update_response_in_redis())

    except Exception as e:
        # Update the stored status with error information
        async def update_response_with_error():
            redis_client = await get_redis_client()
            cached_response = await redis_client.get(image_id)
            if cached_response:
                status_data = json.loads(cached_response)
                if idx < len(status_data["components"]):
                    status_data["components"][idx]["status"] = "error"
                    status_data["components"][idx]["error"] = str(e)
                    await redis_client.set(image_id, json.dumps(status_data))

        loop.run_until_complete(update_response_with_error())
    finally:
        loop.close()


def process_image_to_3d_model(image_path: str, author_role: str, file_type: str, name: str) -> str:
    retries = 5
    backoff_factor = 2
    for attempt in range(1, retries + 1):
        try:
            if not check_input_image(image_path):
                raise Exception("Input image check failed.")

            preprocessed_image = preprocess(image_path, foreground_ratio=0.75)
            if not preprocessed_image:
                raise Exception("Image preprocessing failed.")

            model_path = generate(preprocessed_image)
            if not model_path:
                raise Exception("3D model generation failed.")

            s3_key = generate_key(author_role, file_type, name)
            model_url = upload_file(model_path, s3_key)
            if not model_url:
                raise Exception("Failed to upload 3D model to AWS S3.")

            return model_url

        except Exception as e:
            error_message = str(e)
            if "No GPU is currently available" in error_message and attempt < retries:
                wait_time = backoff_factor ** (attempt - 1)
                print(f"Attempt {attempt} failed due to GPU unavailability. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"Attempt {attempt} failed with error: {e}")
                raise
