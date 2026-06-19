from openai import OpenAI
from dotenv import load_dotenv
from db import qdrant_client
from qdrant_client.models import PointStruct
import json

load_dotenv()

client = OpenAI()


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
                    id=1,
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
            input= query,
            model="text-embedding-3-small"
        )

        query_vector = response.data[0].embedding

        data = qdrant_client.query_points(
            collection_name="links",
            query=query_vector,
            limit=3
        )
    except Exception as e:
        return str(e)

    matches = []

    for item in data:
        if query.lower() in json.dumps(item).lower():
            matches.append(item)

    return json.dumps(matches)


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
    }
]


SYSTEM_PROMPT = """
You are a Personal Link Memory Agent.

You help users save and retrieve links.

Rules:
- Use save_link whenever a link should be saved.
- Use search_links whenever links need to be searched.
- Never invent saved links.
- Always rely on tool outputs.
"""


def process_message(user_message: str) -> str:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_message
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