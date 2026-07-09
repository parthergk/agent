import json
from openai import OpenAI
from .models import IncomingMessage, AgentResponse
from .prompts import SYSTEM_PROMPT
from .tools import TOOLS
from .memory_store import save_memory, search_memory

client = OpenAI()

def process_message(message: IncomingMessage) -> str:
    """
    Main entry point for handling incoming messages from the FastAPI app.
    """
    # Format incoming message context into a user prompt
    if message.type == "text":
        user_content = message.caption or ""
    else:
        parts = [f"Type: {message.type}"]
        if message.path:
            parts.append(f"File Path: {message.path}")
        if message.caption:
            parts.append(f"Caption: {message.caption}")
        user_content = "\n".join(parts)
        print("\n\nuser content", user_content)

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
        print("\n\nassistant msg", assistant_msg)
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

        final_response = client.chat.completions.parse(
            model="gpt-5-mini",
            messages=messages,
            # tools=TOOLS,
            response_format= AgentResponse
        )
        parsed_response = final_response.choices[0].message.parsed
        print("final response", parsed_response)
        return parsed_response or ""
        
    except Exception as e:
        print(f"Error processing message: {e}")
        return "Something went wrong while processing your request."
