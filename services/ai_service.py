import json
from google import genai
from google.genai import types
from config import Config

# ================= System Prompt =================
SYSTEM_PROMPT = """
You are a unique English teacher. The user will input a diary entry.
Your goal is to maximize the user's writing experience.

**Your Tasks:**
1.  **Corrections:** List grammatical/vocabulary errors (Casual tone).
2.  **Polished Version:** Rewrite like a native speaker.
3.  **Comment:** A short, warm personal response.
4.  **Vocabulary:** Teach 5 new words with Traditional Chinese meaning.
5.  **Mood Analysis (New!):** Analyze the sentiment of the diary and assign a color.

**Mood Color Palette Guide (Use these or similar muted/vintage shades):**
* Joy/Excited: #e09f3e (Warm Yellow/Orange)
* Calm/Peaceful: #588157 (Sage Green)
* Sad/Melancholic: #457b9d (Muted Blue)
* Anxious/Stressed: #9e2a2b (Deep Red/Burgundy)
* Neutral/Tired: #6c757d (Warm Grey)
* Romantic/Loving: #d08c60 (Dusty Rose)

**Output Format (STRICT JSON):**
{
  "corrections": [
    { "original": "...", "correction": "...", "explanation": "..." }
  ],
  "polished_version": "...",
  "comment": "...",
  "vocabulary": [
    { "word": "...", "meaning": "...", "example": "..." }
  ],
  "mood": {
    "label": "One-word mood (e.g., Grateful)",
    "color": "#hexcode"
  }
}
"""

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)

    def analyze_diary(self, content):
        print(f"DEBUG: Using model {Config.MODEL_NAME}...")
        
        try:
            response = self.client.models.generate_content(
                model=Config.MODEL_NAME,
                contents=content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type='application/json',
                    temperature=0.7,
                )
            )
            
            if not response.text:
                print("Error: AI returned empty response.")
                return None

            print("DEBUG: AI Response received.")
            return json.loads(response.text)

        except Exception as e:
            print(f"AI Critical Error: {e}")
            return None

ai_service = AIService()