import json
import uuid
from typing import Optional, Literal
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from db import qdrant_client
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, VectorParams, Distance, PayloadSchemaType

load_dotenv()

client = OpenAI()

class IncomingMessage(BaseModel):
    type: Literal["text", "image", "audio", "video", "document"]
    path: Optional[str] = None
    caption: Optional[str] = None
    mime_type: Optional[str] = None

# Ensure the 'memories' collection exists in Qdrant and has index
try:
    collections = qdrant_client.get_collections().collections
    existing_collections = [c.name for c in collections]
    if "memories" not in existing_collections:
        qdrant_client.create_collection(
            collection_name="memories",
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE
            )
        )
        qdrant_client.create_payload_index(
            collection_name="memories",
            field_name="memory_type",
            field_schema=PayloadSchemaType.KEYWORD
        )
except Exception as e:
    print(f"Failed to check/create 'memories' collection and index: {e}")


def save_memory(memory_type: str, content: str, metadata: dict) -> str:
    """
    Saves a memory point to the 'memories' Qdrant collection.
    """
    try:
        # Create text embedding representation using memory_type, title, category, and description
        title = metadata.get("title", "")
        category = metadata.get("category", "")
        description = metadata.get("description", "")
        text_to_embed = f"Type: {memory_type}\nTitle: {title}\nCategory: {category}\nDescription: {description}"
        
        response = client.embeddings.create(
            input=text_to_embed,
            model="text-embedding-3-small"
        )
        vector = response.data[0].embedding
        
        point_id = str(uuid.uuid4())
        qdrant_client.upsert(
            collection_name="memories",
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "memory_type": memory_type,
                        "content": content,
                        "metadata": metadata
                    }
                )
            ]
        )
        return f"Successfully saved memory of type '{memory_type}'."
    except Exception as e:
        return f"Error saving memory: {str(e)}"


def search_memory(query: str, memory_type: Optional[str] = None) -> str:
    """
    Searches the 'memories' collection using vector similarity.
    """
    try:
        response = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_vector = response.data[0].embedding
        
        # Build keyword filter
        query_filter = None
        if memory_type:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(value=memory_type)
                    )
                ]
            )
            
        try:
            search_results = qdrant_client.query_points(
                collection_name="memories",
                query=query_vector,
                query_filter=query_filter,
                limit=5
            )
            points = search_results.points
        except Exception as filter_err:
            # Fallback to post-filtering if index filter fails
            print(f"Filter query failed: {filter_err}. Retrying with post-filtering...")
            search_results = qdrant_client.query_points(
                collection_name="memories",
                query=query_vector,
                limit=20
            )
            points = search_results.points
            if memory_type:
                points = [p for p in points if p.payload.get("memory_type") == memory_type][:5]
        
        matches = []
        for point in points:
            matches.append({
                "score": point.score,
                "memory_type": point.payload.get("memory_type"),
                "content": point.payload.get("content"),
                "metadata": point.payload.get("metadata", {})
            })
            
        return json.dumps(matches)
    except Exception as e:
        return f"Error searching memory: {str(e)}"


# Define tool signatures for the LLM completion
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Store a user memory (link, image, audio, video, or document) in the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_type": {
                        "type": "string",
                        "enum": ["link", "image", "audio", "video", "document"],
                        "description": "The classification of the memory."
                    },
                    "content": {
                        "type": "string",
                        "description": "For file types (image, audio, video, document), use the file path. For link type, use the URL."
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Information parsed/generated from the caption, e.g. title, category, and description.",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "A generated title for the memory based on the caption/description."
                            },
                            "category": {
                                "type": "string",
                                "description": "A generated category name for categorization."
                            },
                            "description": {
                                "type": "string",
                                "description": "A description of the memory."
                            }
                        },
                        "required": ["title", "category", "description"]
                    }
                },
                "required": ["memory_type", "content", "metadata"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Query stored memories semantically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The text to search for within memories."
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["link", "image", "audio", "video", "document"],
                        "description": "Optional type parameter to restrict the search filter."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a Personal Memory Agent.
You have two tools: `save_memory` and `search_memory` to persist and retrieve user memories.
Supported memory types are: link, image, audio, video, document.

Instructions:
1. When user provides content to save (a file upload or link or description to save):
   - Call `save_memory`.
   - Set `memory_type` to one of: 'link', 'image', 'audio', 'video', 'document'.
   - Set `content` to the URL (for links) or the file path (for image, audio, video, document).
   - Generate metadata containing 'title', 'category', and 'description' based on the caption, transcript, or content.
   - Once saved successfully, reply with a clean confirmation, e.g., 'Image saved: <title>' or 'Link saved: <title>'.

2. When user wants to search or find something:
   - Call `search_memory` with a relevant search query.
   - If search returns an image result, you MUST respond ONLY with the exact format `[SEND_IMAGE: <exact_image_path>]` in your final text response so that the system's image sender can deliver it. Do not include extra text, descriptions, or choices for the image file if you are sending it.
   - For other memory types, summarize the results naturally.

3. If the user request is unrelated to saving or searching memories (links, images, audio, video, documents), respond exactly:
Sorry i can't help you for this.
"""

def process_message(message: IncomingMessage) -> str:
    """
    Main entry point for handling incoming messages from the FastAPI app.
    """
    # Format incoming message context into a user prompt
    if message.type == "text":
        user_content = message.caption or ""
    else:
        parts = [f"User uploaded a {message.type}."]
        if message.path:
            parts.append(f"File Path: {message.path}")
        if message.caption:
            parts.append(f"Caption/Description: {message.caption}")
        user_content = "\n".join(parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
            tools=TOOLS
        )

        assistant_msg = response.choices[0].message
        messages.append(assistant_msg)

        if not assistant_msg.tool_calls:
            return assistant_msg.content or ""

        for tool_call in assistant_msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if name == "save_memory":
                result = save_memory(
                    memory_type=args.get("memory_type"),
                    content=args.get("content"),
                    metadata=args.get("metadata")
                )
            elif name == "search_memory":
                result = search_memory(
                    query=args.get("query"),
                    memory_type=args.get("memory_type")
                )
            else:
                result = f"Unknown tool: {name}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        final_response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
            tools=TOOLS
        )
        return final_response.choices[0].message.content or ""
        
    except Exception as e:
        print(f"Error processing message: {e}")
        return "Something went wrong while processing your request."