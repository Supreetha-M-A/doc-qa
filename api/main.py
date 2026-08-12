from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llm import stream_chat

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


SYSTEM = "You are a helpful assistant. Be concise."


@app.post("/api/chat")
def chat(req: ChatRequest):
    def generate():
        try:
            for text in stream_chat([m.model_dump() for m in req.messages], SYSTEM):
                yield text
        except Exception:
            yield "\n\n[error: generation failed]"

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/health")
def health():
    return {"ok": True}
