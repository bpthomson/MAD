# AI Diary Assistant

An intelligent, decoupled web application that helps you polish your diary entries, correct your English grammar, and learn new vocabulary using advanced LLMs.

## Architecture

This project is separated into a frontend and backend architecture:

- **Frontend**: Vue 3 + Vite. Provides a responsive, glassmorphic UI for composing entries, viewing history, and interacting with AI corrections.
- **Backend**: Flask (Python). Serves as a stateless RESTful API.
- **Database**: Google Sheets API. Used as a lightweight, accessible database for storing diary entries.
- **AI Engine**: Groq API. Powers the grammar correction, style polishing, vocabulary extraction, and mood analysis.

## Features

- **Interactive Corrections**: Click on highlighted words in your original entry to see detailed grammar explanations.
- **Dynamic Model Selection**: Connects to the Groq API to fetch the latest available LLMs (defaulting to `llama-3.3-70b-versatile`).
- **Vocabulary Bank**: Automatically extracts and defines 5 advanced vocabulary words based on your entry's context.
- **Mood Tracking**: Analyzes the emotional tone of your entry and assigns a color-coded mood label.

## Setup Instructions

### 1. Backend Setup

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend/` directory with the following variables:
   ```env
   GROQ_API_KEY=your_groq_api_key
   SECRET_KEY=your_flask_secret_key
   DIARY_PASSWORD=your_app_login_password
   ```
5. Add your Google Sheets Service Account credentials as `credentials.json` in the `backend/` directory.

### 2. Frontend Setup

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

## Running the Application

1. **Start the Backend Server**:
   ```bash
   cd backend
   source .venv/bin/activate
   python app.py
   ```
   The backend will run on `http://127.0.0.1:5000`.

2. **Start the Frontend Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```
   The frontend will run on `http://localhost:5173`. Vite is configured to proxy `/api` requests to the Flask backend automatically.
