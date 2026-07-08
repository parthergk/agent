from fastapi import FastAPI
from pydantic import BaseModel
from agent import process_message, IncomingMessage
from preprocessor import preprocess_message

app = FastAPI()


class ChatRequest(BaseModel):
    message: IncomingMessage


@app.post("/chat")
async def chat(request: ChatRequest):

    preprocess_response = preprocess_message(request.message)
    response = process_message(preprocess_response)

    return {
        "response": response
    }
