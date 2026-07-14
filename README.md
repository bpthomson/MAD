# AI Diary Assistant

An intelligent, decoupled web application that leverages advanced LLMs to polish diary entries, correct English grammar, and teach vocabulary in context. 

This document explains **how the repository works internally** and the architecture of the system.

## 🏗 System Architecture & How it Works

The project is split into two distinct tiers: a **Vue 3 SPA** (Single Page Application) frontend and a **Flask (Python)** backend REST API. 

### 1. The Brain: AI Integration (Groq API)
The core intelligence of the app is powered by the **Groq API**. 
- In `backend/services/ai_service.py`, the system constructs a rigorous system prompt instructing the model to act as a strict English coach.
- It dynamically queries Groq's `/models` endpoint to list available models, filtering out audio models like Whisper, and defaults to `llama-3.3-70b-versatile` for high-speed, high-quality reasoning.
- The AI returns structured JSON containing grammar corrections, a polished rewrite, 5 advanced vocabulary words, a sentiment analysis (mood), and exact string-matching anchors to map corrections back to the original text.

### 2. The Storage: Database (Google Sheets API)
Instead of a traditional SQL database, this project uses **Google Sheets** as a lightweight, accessible database (`backend/services/db_service.py`).
- It uses the `gspread` library and authenticates via a Service Account (`credentials.json` or environment variables).
- **Caching**: To minimize API calls to Google, the backend caches the spreadsheet records with a 15-minute TTL.
- When a diary is saved, all the AI-generated JSON data (corrections, vocabulary, mood) is serialized into strings and saved alongside the raw text and polished HTML in the sheet.

### 3. The Backend: Flask REST API (`backend/app.py`)
The backend is completely stateless and handles routing:
- **Authentication**: A simple global password is required. The backend issues a session cookie upon login. All endpoints use a `@login_required` decorator.
- **Data Flow**: When the frontend submits a diary entry (`POST /api/diary`), the backend grabs the user's 3 most recent entries from the DB to give the AI *context* (allowing the AI to follow up on past events). It then calls the `ai_service`, saves the result via `db_service`, and returns the newly generated timestamp back to the frontend.

### 4. The Frontend: Vue 3 + Vite (`frontend/`)
The frontend is responsible for the interactive user experience:
- **Proxying**: The `vite.config.js` proxies all `/api` requests to the local Flask server on port 5000, preventing CORS issues during development.
- **Views**: 
  - `index.vue`: The main writing interface. It fetches the available Groq models dynamically so the user can choose their preferred LLM.
  - `result.vue`: The Insight page. It implements a split-pane layout parsing the AI's JSON payload to create interactive text highlighting—clicking a highlighted word in the original text maps to the exact correction reason in the details panel.
  - `history.vue`: Fetches the timeline of entries, decoding the serialized mood data to display color-coded sentiment tags.

---

## 🛠 Local Setup & Development

### Backend (Python via `uv`)
We use **`uv`** for lightning-fast Python environment management instead of the standard built-in `venv`.

```bash
cd backend
# Create a virtual environment with uv
uv venv
# Activate the environment
source .venv/bin/activate
# Install dependencies instantly
uv pip install -r requirements.txt

# Start the Flask API
python app.py
```
*(Ensure you have your `.env` configured with `GROQ_API_KEY`, `SECRET_KEY`, and `DIARY_PASSWORD`, along with a valid `credentials.json` for Google Sheets).*

### Frontend (Node.js)
```bash
cd frontend
npm install
npm run dev
```
