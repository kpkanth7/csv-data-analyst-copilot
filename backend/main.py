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
        import pandas as pd
        import io
        df = pd.read_csv(io.BytesIO(contents))
        context = build_csv_context(contents)
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"context": context, "history": [], "df": df}
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
    df = session_data.get("df")

    # Keep only the last 3 conversations (6 messages: 3 user + 3 assistant)
    recent_history = history[-6:]
    history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in recent_history])
    if history_text:
        history_text = f"\n\nPrevious Conversation:\n{history_text}"

    # Pre-computation Step: Ask the LLM to write pandas code
    computed_data = ""
    if df is not None:
        code_prompt = f"""
You are a Pandas Python code generator. The user uploaded a CSV loaded as a DataFrame named `df`.
Context: {context}
Question: {request.message}
Write a single Python expression using `df` that answers the question exactly.
Examples: df['delay'].sum(), df.groupby('type')['delay'].mean().idxmax()
Return ONLY the raw python expression. Do NOT write markdown, backticks, or comments. If no code is needed, return 'NONE'.
"""
        try:
            code_res = await client.aio.models.generate_content(model="gemini-2.5-flash", contents=code_prompt)
            code = code_res.text.strip().strip('`').strip()
            if code.lower().startswith('python'):
                code = code[6:].strip()
            
            if code != 'NONE' and 'df' in code and 'import' not in code and 'eval' not in code and 'exec' not in code:
                import pandas as pd
                result = eval(code, {"__builtins__": {}}, {"df": df, "pd": pd})
                computed_data = f"\n\n[Backend Computed Data Result (100% mathematically accurate): {result}]\nUse this exact computed result in your final answer."
                print(f"Executed Pandas: {code} -> {result}")
        except Exception as e:
            print(f"Pandas execution failed: {e}")

    # Setting the expert analyst persona and injecting the data context + history + exact computed data
    full_prompt = (
        f"You are an expert data analyst. Provide clear, comprehensive, yet concise answers. "
        f"Avoid unnecessary rambling, but ALWAYS include relevant context, units, and brief explanations of the numbers you provide so the user doesn't have to ask follow-up questions. "
        f"Context:\n{context}{history_text}{computed_data}\n\nUser: {request.message}"
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
            if any(term in error_msg for term in ["429", "quota", "exhausted", "503", "unavailable", "high demand"]):
                # Quota reached or model overloaded! Fallback to flash-lite
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
