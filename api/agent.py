from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI()


def save_link(url, description, category):
    try:
        with open("links.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({
        "url": url,
        "description": description,
        "category": category
    })

    with open("links.json", "w") as f:
        json.dump(data, f, indent=2)

    return "Link saved successfully"


def search_links(query):
    try:
        with open("links.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "[]"

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
                    "description": {"type": "string"},
                    "category": {"type": "string"}
                },
                "required": [
                    "url",
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