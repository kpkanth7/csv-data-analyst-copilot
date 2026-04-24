# CSV Data Analyst Copilot

> [!NOTE]
> **Live Demo:** [Render deployment link will go here soon!](#)

Hey everyone, Pradhyumna here! I built this CSV Data Analyst Copilot to make exploring and analyzing tabular data super easy and intuitive. Instead of writing pandas code or SQL queries, you just upload your CSV file and chat with an AI that acts as your personal expert data analyst.

## What It Does
Basically, you drop a `.csv` file into the slick UI, and the app instantly parses the structure, grabs a statistical summary, and lets you ask plain English questions about your data. The AI streams the answer right back to you. It's lightning-fast and super helpful for quick insights, data cleaning ideas, or just understanding what's in a massive spreadsheet.

## Tech Stack
- **Backend:** FastAPI (blazing fast, async python)
- **Frontend:** React + Vite (premium Vanilla CSS, dark mode, smooth streaming UI)
- **AI Engine:** Google Gemini 2.5 Flash (via the new `google-genai` SDK)
- **Package Management:** `uv` (because pip is too slow, honestly)

## Why We Used RAG (And Why No Embeddings)
You might be wondering: "Why didn't you chunk the CSV and use vector embeddings?"
Honestly, **because this is the best approach.** Passing the raw data summary directly into the massive context window of Gemini 2.5 Flash works flawlessly. When you chunk a tabular dataset into vector embeddings, you completely destroy the mathematical relationships between columns and rows. Vector search is great for paragraphs of text, but for analyzing *tabular* data, injecting the schema, null counts, summary statistics, and a sample of rows directly into the context window yields vastly superior, highly accurate analytical responses.

## FAQ
**Q: What happens if my file is massive?**
A: The backend parses the data and only passes the structural summary and a 20-row sample to the LLM. So, it works efficiently no matter the file size without blowing up the token limits.

**Q: What if I hit the Gemini API quota?**
A: Since we're using Gemini 2.5 Flash, there's a daily limit (around 250 messages or 1500 requests on the free tier). I've added a neat handler that catches the quota error and gracefully tells you in the chat: *"The quota is done for the day, check back tomorrow."* No crashes, no mess.

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
