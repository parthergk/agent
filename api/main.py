from fastapi import FastAPI
from pydantic import BaseModel
from agent import process_message

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):

    response = process_message(
        request.message
    )

    return {
        "response": response
    }