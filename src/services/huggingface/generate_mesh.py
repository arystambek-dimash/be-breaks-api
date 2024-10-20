from os import path

from gradio_client import Client, handle_file
import gradio_client

from src.config import settings

MESH_SPACE = settings.HUGGINGFACE_SPACE_NAME


def init_client():
    try:
        return Client(MESH_SPACE)
    except Exception as e:
        print(e)


client = init_client()


async def check_input_image(file_url):
    try:
        result = client.predict(
            handle_file(file_url),
            api_name="/check_input_image"
        )
    except Exception as err:
        print("Check Input Image Error:", err)
        return False

    if len(result) != 0:
        print("Input image check failed:", result)
        return False
    return True


async def preprocess(file_url, foreground_ratio):
    result = client.predict(
        gradio_client.handle_file(file_url),
        True,  # bool  in 'Remove Background' Checkbox component
        foreground_ratio,  # float (numeric value between 0.5 and 1.0) in 'Foreground Ratio' Slider component
        api_name="/preprocess"
    )
    print("Preprocess: ", result)
    return result


async def generate(file_url):
    print("Making 3D model:")

    try:
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
