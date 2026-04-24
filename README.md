# CSV Data Analyst Copilot

> [!NOTE]
> **Live Demo:** [https://csv-data-analyst-frontend.onrender.com](https://csv-data-analyst-frontend.onrender.com)
> **Backend API:** [https://csv-data-analyst-backend.onrender.com](https://csv-data-analyst-backend.onrender.com)

Hey everyone, Pradhyumna here! I built this CSV Data Analyst Copilot to make exploring and analyzing tabular data super easy, highly accurate, and intuitive. Instead of manually writing pandas code or SQL queries, you just upload your CSV file and chat with an AI that acts as your personal expert data analyst.

## How It Works (The Engine Under the Hood)
Unlike basic AI wrappers that guess or hallucinate answers based on a tiny data sample, this Copilot is built for **100% mathematical accuracy**. 

1. **Context Parsing**: When you drop a `.csv` file into the slick UI, the backend stores the full dataset in memory and passes a statistical summary to the AI so it understands your columns and data types.
2. **Invisible Pandas Execution**: When you ask a complex question (e.g., *"Which director had the most films in 2017?"*), the backend asks the AI to write a robust, multi-line Pandas Python script. The server then executes this script securely in the background against the *entire* massive dataset to calculate the exact answer.
3. **Dataset Agnostic**: It is incredibly smart with data anomalies. For example, if a cell contains multiple items separated by commas (like co-directors), it automatically uses `.explode()` to split them apart so individuals are counted perfectly. It adapts its logic dynamically based on whatever dataset you upload.
4. **Contextual Memory**: The backend remembers the last 3 interactions you had, so you can easily ask conversational follow-up questions like *"What about 2018?"* without restating the entire prompt.

## Tech Stack
- **Backend:** FastAPI (blazing fast, async python)
- **Frontend:** React + Vite (premium Vanilla CSS, dark mode, smooth streaming UI)
- **AI Engine:** Google Gemini 2.5 Flash (via the new `google-genai` SDK)
- **Package Management:** `uv` (because pip is too slow, honestly)

## Why We Built a Code-Execution RAG (And Why No Embeddings)
You might be wondering: "Why didn't you chunk the CSV and use vector embeddings?"
Honestly, **because passing text into embeddings destroys mathematical relationships.** Vector search is great for paragraphs of text, but for analyzing *tabular* data, it's terrible. By injecting the schema directly into the prompt and forcing the AI to write and execute Pandas code against the raw data, we get vastly superior, mathematically perfect analytical responses without hallucinations.

## FAQ
**Q: What happens if my file is massive?**
A: The backend securely holds the full file in memory for computation, but only passes the structural summary and a 20-row sample to the LLM to read. So, it works flawlessly and calculates exact answers without blowing up the API token limits.

**Q: What if I hit the Gemini API quota or the server is overloaded?**
A: Since we're using Gemini 2.5 Flash, there's a daily limit (around 1500 requests on the free tier), and occasionally Google's servers get overloaded (503 errors). I've built a **seamless fallback handler**. If the primary model throws a quota or high-demand error, the backend instantly reroutes your question to the `gemini-2.5-flash-lite` model. It won't crash, and you won't even notice the switch!

## How to Run It Locally

1. **Clone the repo:**
```bash
git clone https://github.com/kpkanth7/csv-data-analyst-copilot.git
cd csv-data-analyst-copilot
```

2. **Set up your API Key:**
Open the `backend/.env` file and drop your Gemini API key there:
`GEMINI_API_KEY=your_key_here`

3. **Start the Backend:**
```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

4. **Start the Frontend:**
Open a new terminal tab.
```bash
cd frontend
npm install
npm run dev
```

Hit `http://localhost:5173` in your browser and start chatting with your data!
