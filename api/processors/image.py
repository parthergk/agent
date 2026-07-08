import os
import base64
from typing import Optional
from openai import OpenAI
from agent import IncomingMessage

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def process_image(path, caption: Optional[str], mime_type: Optional[str]) -> IncomingMessage:
    if caption:
        return IncomingMessage(
            type="image",
            path=path,
            caption=caption,
            mime_type=mime_type
        )
    else:
        user_content = [{
            "type": "text", 
            "text": """Analyze the image and create a short description (5-10 words). 
                        Do not describe the image in detail."""
            }]

        if path and os.path.exists(path):
            try:
                base64_image = encode_image(path)
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
                
                client = OpenAI()
                response = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": user_content
                        }
                    ]
                )
                description = response.choices[0].message.content.strip()
                return IncomingMessage(
                    type="image",
                    path=path,
                    caption=description,
                    mime_type=mime_type
                )
            except Exception as e:
                print(f"Error encoding/analyzing image: {e}")
                return IncomingMessage(
                    type="image",
                    path=path,
                    caption=f"[Image Analysis Error]: {str(e)}",
                    mime_type=mime_type,
                )
        
        return IncomingMessage(
            type="image",
            path=path,
            caption="unnamed image",
            mime_type=mime_type
        )
