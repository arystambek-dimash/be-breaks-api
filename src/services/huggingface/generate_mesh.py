from os import path
from random import randint

from gradio_client import Client
import gradio_client

from src.config import settings

MESH_SPACE = settings.HUGGINGFACE_SPACE_NAME
SD3M_SPACE = settings.SD3M_SPACE_NAME


def init_client(is_hard=False):
    if not is_hard:
        return Client("TencentARC/InstantMesh")
    space_name = MESH_SPACE + str(randint(0, 4))
    print("Space name: ", space_name)
    client = Client(space_name, hf_token=settings.HUGGING_FACE_TOKEN)
    return client


def check_input_image(file_url):
    client = init_client()
    try:
        result = client.predict(
            gradio_client.handle_file(file_url),
            api_name="/check_input_image"
        )
    except Exception as err:
        print("Check: ", err)
        return False

    if len(result) != 0:
        print(result)
        return False
    return True


def preprocess(file_url, foreground_ratio):
    client = init_client()
    result = client.predict(
        gradio_client.handle_file(file_url),
        True,  # bool  in 'Remove Background' Checkbox component
        foreground_ratio,  # float (numeric value between 0.5 and 1.0) in 'Foreground Ratio' Slider component
        api_name="/preprocess"
    )
    print("Preprocess: ", result)
    return result


def generate(file_url: str):
    print("Making 3D model:")

    try:
        client = init_client(is_hard=True)
        result = client.predict(
            gradio_client.handle_file(file_url),
            sample_steps=75,
            sample_seed=42,
            api_name="/generate_mvs"
        )
        print("MVS: ", result)

        result = client.predict(
            api_name="/make3d"
        )
        print("3D: ", path.normpath(result[0]), '\n', path.normpath(result[1]))
    except Exception as err:
        print("\n\n!!!!Exception 3D: ", err, "\n\n")
        raise err
    return path.normpath(path.normpath(result[0]))
