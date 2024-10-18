import base64
import json

from openai import OpenAI
from src.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

PROMPT = """
Объясни что показано на изображении, и расскажи о его основных компонентах с объяснением что они делают и как работает.
Отправь мне ответ в таком формате:
```
    {
        "name_of_item": "str",
        "description_of_item": "str",
        "item_components": [
            {
                "name_of_component": "str",
                "description_of_component": "str"
            }
        ]
    }  
```

Note: json values должно быть на русском языке
"""


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
                        "text": PROMPT,
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
