from openai import OpenAI
from dotenv import load_dotenv
from db import qdrant_client
from qdrant_client.models import PointStruct
import json
import uuid

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

Use save_link to save links.
Use search_links to retrieve links.

Never invent links.
Always rely on tool results.

When search_links returns multiple results:
- Consider title, description, category, score, and user intent.
- Do not choose solely based on score.
- The highest score is not always the correct result.
- Prefer the result that best matches the user's request.
- Return a single link when one result is clearly the best match.
- Return multiple links only when there is genuine ambiguity.
- If no relevant result exists, clearly say so.
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