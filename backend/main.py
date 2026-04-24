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
    allow_origins=["*"],
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
        sessions[session_id] = {"context": context, "history": []}
        return {"session_id": session_id, "message": "Ready to chat!"}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse: {e}")

@app.post("/chat")
async def chat(request: ChatRequest):
    session_data = sessions.get(request.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Upload a file first.")

    context = session_data["context"]
    history = session_data["history"]

    # Keep only the last 3 conversations (6 messages: 3 user + 3 assistant)
    recent_history = history[-6:]
    history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_history])
    if history_text:
        history_text = f"\n\nPrevious Conversation:\n{history_text}"

    # Setting the expert analyst persona and injecting the data context + history
    full_prompt = (
        f"You are an expert data analyst. Be highly concise, direct, and relevant. "
        f"Prioritize quality and exact answers over quantity. Do NOT over-explain, avoid fluff, and only provide exactly what is asked. "
        f"Context:\n{context}{history_text}\n\nUser: {request.message}"
    )

    async def stream_response():
        full_response = []
        try:
            # Try with the primary model first
            stream = await client.aio.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=full_prompt
            )
            async for chunk in stream:
                if chunk.text:
                    full_response.append(chunk.text)
                    yield chunk.text
            
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
                # Quota reached! Fallback to flash-lite
                try:
                    fallback_stream = await client.aio.models.generate_content_stream(
                        model="gemini-2.5-flash-lite",
                        contents=full_prompt
                    )
                    # Only stream the fallback if we haven't already output text from the first model
                    if not full_response:
                        async for chunk in fallback_stream:
                            if chunk.text:
                                full_response.append(chunk.text)
                                yield chunk.text
                    else:
                        yield "\n\n*[Switched to backup model due to limits. Please ask your question again.]*"
                        return
                except Exception as fallback_e:
                    yield f"\n\n**Both AI models reached their daily limit.** Please check back tomorrow."
            else:
                import traceback
                traceback.print_exc()
                yield f"\n\n**Error during streaming:** {str(e)}"

        if full_response:
            # Save conversation to history only if we got a response
            session_data["history"].append({"role": "user", "content": request.message})
            session_data["history"].append({"role": "assistant", "content": "".join(full_response)})

    return StreamingResponse(stream_response(), media_type="text/plain")
