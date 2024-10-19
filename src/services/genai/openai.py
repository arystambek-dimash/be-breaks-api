import base64
import io
import json
import os

import requests
from PIL import Image
from openai import OpenAI
from rembg import remove

from src.config import settings, MEDIA_DIR

client = OpenAI(api_key=settings.OPENAI_API_KEY)

IMAGE_PROMPT = """
Объясни что показано на изображении, и расскажи о его основных компонентах с объяснением что они делают и как работает.
Отправь мне ответ в таком формате:
```
    {
        "name_of_item": "str",
        "item_components": [
            {
                "name_of_component": "str",
                "name_to_prompt": "str"
                "description_of_component": "str"
            }
        ]
    }  
```

Note: все должно быть на английском
Note: Please generate AI representations of various components. Provide the name_to_prompt in English and include a brief description for each one so the AI understands what object to generate. For example, you might describe a component as "screen of monitor, cooler of processor, side bar of processor  (u should describe more detailing)" to indicate that it refers to a display device.
"""

TEXT_PRMPT = '''
Объясни важных 5 делати этого компонетно {component}  с объяснением что они делают и как работает.
Отправь мне ответ в таком формате:
```
    {
        "item_components": [
            {
                "name_of_component": "str",
                "name_to_prompt": "str"
                "description_of_component": "str"
            }
        ]
    }  
```

Note: все должно быть на английском
Note: Please generate AI representations of various components. Provide the name_to_prompt in English and include a brief description for each one so the AI understands what object to generate. For example, you might describe a component as "screen of monitor, cooler of processor, side bar of processor  (u should describe more detailing)" to indicate that it refers to a display device.
'''


async def get_image_details(base64_image: bytes):
    base64_image = base64.b64encode(base64_image).decode('utf-8')

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": IMAGE_PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        temperature=0.3
    )

    response_content = response.choices[0].message.content
    response_content = response_content.replace("```json", "").replace("```", "")
    response_dict = json.loads(response_content)

    return response_dict


async def detail_by_text(text: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": TEXT_PRMPT.format(component=text),
                    },
                ],
            }
        ],
        temperature=0.3
    )

    response_content = response.choices[0].message.content
    response_content = response_content.replace("```json", "").replace("```", "")
    response_dict = json.loads(response_content)

    return response_dict


async def generate_image(inputs: str, image_id: str, index: int) -> str:
    prompt = (
        f"{inputs}. Generate a high-quality photo of the object against a plain white background, "
        "focusing solely on the object without any additional elements."
    )

    response = client.images.generate(
        model="dall-e-2",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url

    image_response = requests.get(image_url)
    image = Image.open(io.BytesIO(image_response.content))

    image_no_bg = remove(image)

    filename = f"{image_id}_{index}.png"
    image_path = os.path.join(MEDIA_DIR, filename)
    image_no_bg.save(image_path)

    return f"/media/{filename}"
