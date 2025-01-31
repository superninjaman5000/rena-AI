from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.chat import chat_with_ai
from app.database import setup_database
from pydantic import BaseModel

app = FastAPI()

# Initialize the database connection
setup_database()

class ChatRequest(BaseModel):
    message: str  # Validates user input

@app.get("/")
async def root():
    return {"message": "Rena AI Backend is Running!"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Handles AI chat messages via REST API."""
    response = chat_with_ai(request.message)
    return {"response": response}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time chat."""
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            response = chat_with_ai(message)  # Get AI response
            await websocket.send_text(response)  # Send response back
    except WebSocketDisconnect:
        print("WebSocket disconnected")
