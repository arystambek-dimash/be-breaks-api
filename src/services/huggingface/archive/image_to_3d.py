import gradio_client
from gradio_client import Client

from src.config import settings

client = Client("ThomasSimonini/Roblox-3D-Assets-Generator-v1")

result = client.predict(
    input_image=gradio_client.handle_file(
        'https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png'),
    sample_steps=75,
    sample_seed=42,
    api_name="/generate_mvs"
)

print(result)

result = client.predict(
    api_name="/make3d"
)
print(result)
