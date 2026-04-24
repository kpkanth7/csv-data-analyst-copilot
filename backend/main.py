import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
from rag import build_csv_context

load_dotenv()
app = FastAPI(title="CSV Analyst AI")

# Allowing the React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keeping the CSV context in memory for now
sessions = {}
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "your_api_key_here"))
MODEL = "gemini-2.5-flash"

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="I only take .csv files.")
    
    contents = await file.read()
    try:
        context = build_csv_context(contents)
        session_id = str(uuid.uuid4())
        sessions[session_id] = context
        return {"session_id": session_id, "message": "Ready to chat!"}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse: {e}")

@app.post("/chat")
async def chat(request: ChatRequest):
    context = sessions.get(request.session_id)
    if not context:
        raise HTTPException(status_code=404, detail="Upload a file first.")

    # Setting the expert analyst persona and injecting the data context
    full_prompt = f"You are an expert data analyst. Context:\n{context}\nUser: {request.message}"

    async def stream_response():
        try:
            # Using the async client so we don't hang the server
            stream = await client.aio.models.generate_content_stream(
                model=MODEL,
                contents=full_prompt
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"\n\n**Error during streaming:** {str(e)}"

    return StreamingResponse(stream_response(), media_type="text/plain")
