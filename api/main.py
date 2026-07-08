from fastapi import FastAPI
from pydantic import BaseModel
from agent import process_message, IncomingMessage

app = FastAPI()


class ChatRequest(BaseModel):
    message: IncomingMessage


@app.post("/chat")
async def chat(request: ChatRequest):
    print("Payload", request.message)

    response = process_message(
        request.message
    )

    return {
        "response": response
    }