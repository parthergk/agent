from openai import OpenAI
from dotenv import load_dotenv
from db import qdrant_client
from qdrant_client.models import PointStruct
import json
import uuid
import os
import base64

from pydantic import BaseModel
from typing import Optional, Literal

load_dotenv()

client = OpenAI()


class IncomingMessage(BaseModel):
    type: Literal["text", "image", "audio", "video", "document"]
    path: Optional[str] = None
    caption: Optional[str] = None
    mime_type: Optional[str] = None
    content: Optional[str] = None

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def save_link(url, title, description, category):
    text_to_embed = f"""
    Title: {title}
    Description: {description}
    Category: {category}
    URL: {url}
    """
    try:
        response = client.embeddings.create(
            input=text_to_embed,
            model="text-embedding-3-small"
        )

        vector = response.data[0].embedding

        qdrant_client.upsert(
            collection_name="links",
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "url": url,
                        "title": title,
                        "description": description,
                        "category": category
                    }
                )
            ]
        )
        return "Link saved successfully"
    except Exception as e:
        return str(e)


def search_links(query):
    try:
        response = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )

        query_vector = response.data[0].embedding

        results = qdrant_client.query_points(
            collection_name="links",
            query=query_vector,
            limit=2
        )
        matches = []
        for point in results.points:
            matches.append({
                "score": point.score,
                "url": point.payload["url"],
                "title": point.payload["title"],
                "description": point.payload["description"],
                "category": point.payload["category"]
                })

        return json.dumps(matches)

    except Exception as e:
        return str(e)


def save_image(image_path, description, category):
    text_to_embed = f"""
    Description: {description}
    Category: {category}
    """
    try:
        response = client.embeddings.create(
            input=text_to_embed,
            model="text-embedding-3-small"
        )

        vector = response.data[0].embedding

        qdrant_client.upsert(
            collection_name="images",
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "image_path": image_path,
                        "description": description,
                        "category": category
                    }
                )
            ]
        )
        return "Image saved successfully"
    except Exception as e:
        return str(e)


def search_images(query):
    try:
        response = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )

        query_vector = response.data[0].embedding

        results = qdrant_client.query_points(
            collection_name="images",
            query=query_vector,
            limit=2
        )
        matches = []
        for point in results.points:
            matches.append({
                "score": point.score,
                "image_path": point.payload["image_path"],
                "description": point.payload["description"],
                "category": point.payload["category"]
            })

        return json.dumps(matches)

    except Exception as e:
        return str(e)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_link",
            "description": "Save a website link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type":"string"},
                    "description": {"type": "string"},
                    "category": {"type": "string"}
                },
                "required": [
                    "url",
                    "title",
                    "description",
                    "category"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_links",
            "description": "Search saved links.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_image",
            "description": "Save an image. If user sends an image, analyze it (if no caption) or use caption to save it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "description": {"type": "string"},
                    "category": {"type": "string"}
                },
                "required": [
                    "image_path",
                    "description",
                    "category"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_images",
            "description": "Search saved images.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]


SYSTEM_PROMPT = """You are a Personal Memory Agent for links and images.

Available tools:
- save_link
- search_links
- save_image
- search_images

Rules:

1. Never invent links, images, titles, descriptions, or paths.
2. Always use tool results.
3. If the request is unrelated to saving or searching links/images, respond exactly:
Sorry right now i can only help you for links and images

Saving:

- When an image is successfully saved, respond with:
Image saved: <title>

Example:
Image saved: evening view

- Never include [SEND_IMAGE] when saving.
- Never return image paths when saving.

Searching Images:

- If a matching image is found, respond ONLY with:
[SEND_IMAGE: <exact_image_path>]

Example:
[SEND_IMAGE: E:\\agent\\whatsapp\\uploads\\1720106789.jpg]

- Do not add any description.
- Do not add any extra text.
- Do not explain the image.

Searching Links:

- Return only the most relevant link unless multiple results are genuinely ambiguous.
- If no result exists, clearly say so.

Multiple Results:

- Consider title, description, category, score, and user intent.
- Do not choose solely based on score.
- Prefer the result that best matches the request.

If no relevant image or link exists, clearly say so."""


def process_message(message: IncomingMessage) -> str:
    image_path = None
    caption = ""
    
    if message.type == "image":
        image_path = message.path
        caption = message.caption or ""
        
        if caption:
            user_prompt = f"""
            Image path: {image_path}
            User caption: {caption} 
            Use the exact image path provided above."""
        else:
            user_prompt = f"""
            Image_path: {image_path}
            Save this image. It has no caption, 
            so Analyze the image and create a short description (5-10 words).
            Do not describe the image in detail.
            Use the exact image path provided above."""
    else:
        user_prompt = message.caption or message.content or ""

    user_content = [{"type": "text", "text": user_prompt}]
    
    if image_path and os.path.exists(image_path):
        try:
            base64_image = encode_image(image_path)
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
        except Exception as e:
            print(f"Error encoding image: {e}")

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_content
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
            tools=TOOLS
        )

        assistant_message = response.choices[0].message

        messages.append(assistant_message)

        # No tool call
        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        for tool_call in assistant_message.tool_calls:

            name = tool_call.function.name
            args = json.loads(
                tool_call.function.arguments
            )

            if name == "save_link":
                result = save_link(
                    args["url"],
                    args["title"],
                    args["description"],
                    args["category"]
                )

            elif name == "search_links":
                result = search_links(
                    args["query"]
                )

            elif name == "save_image":
                result = save_image(
                    args["image_path"],
                    args["description"],
                    args["category"]
                )

            elif name == "search_images":
                result = search_images(
                    args["query"]
                )

            else:
                result = "Unknown tool"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        final_response = (
            client.chat.completions.create(
                model="gpt-5-mini",
                messages=messages,
                tools=TOOLS
            )
        )
        print("final response", final_response)
        return (
            final_response
            .choices[0]
            .message
            .content
        )

    except Exception as e:
        print(e)
        return (
            "Something went wrong while "
            "processing your request."
        )