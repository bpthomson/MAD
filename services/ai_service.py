import json
from google import genai
from google.genai import types
from config import Config

# ================= System Prompt (保持不變) =================
SYSTEM_PROMPT = """
You are a unique English teacher. The user will input a diary entry.
Your goal is to maximize the user's writing experience with a specific persona.

**Your Persona & Rules:**
1.  **Corrections (Part 1):** List grammatical or vocabulary errors. 
    * **Tone:** Be casual and colloquial. Focus on fluency over strict textbook grammar.
    * **Style:** It is okay to use words like 'fxxk', 'shit', etc., if it makes the sentence sound more natural or expressive.
    * **Format:** Explain the fix in a spoken, reasonable manner (can be in Traditional Chinese or English).
2.  **Polished Version (Part 2):** Rewrite the entire diary from a Native English Speaker's perspective. Use diverse sentence structures and authentic idioms.
3.  **Comment (Part 3):** Give a short, personal response/opinion to the diary content (like a friend replying).
4.  **Vocabulary (Part 4):** Teach exactly 5 NEW words related to the diary content.
    * Avoid duplicates from common knowledge.
    * Must provide **Traditional Chinese (中文)** meaning.
    * Must provide an example sentence.

**Output Format:**
You MUST return the result in **STRICT JSON format**. Do not use markdown code blocks. Just the raw JSON string.
The JSON structure must be:
{
  "corrections": [
    {
      "original": "User's wrong phrase",
      "correction": "Better phrase",
      "explanation": "Your casual explanation here"
    }
  ],
  "polished_version": "The full native rewrite text...",
  "comment": "Your short personal reply...",
  "vocabulary": [
    {
      "word": "New Word",
      "meaning": "中文意思",
      "example": "Example sentence using the word."
    }
  ]
}
"""

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)

    def analyze_diary(self, content):
        """
        發送請求給 Gemini。
        已移除重試裝飾器，以便在出錯時能直接看到 Traceback。
        """
        print(f"DEBUG: Using model {Config.MODEL_NAME}...") # Debug 訊息
        
        try:
            # 呼叫 Gemini API
            response = self.client.models.generate_content(
                model=Config.MODEL_NAME,
                contents=content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type='application/json',
                    temperature=0.7,
                )
            )
            
            # 檢查回應是否為空
            if not response.text:
                print("Error: AI returned empty response.")
                return None

            print("DEBUG: AI Response received.")
            return json.loads(response.text)

        except Exception as e:
            # 這裡會印出真正的錯誤訊息，如果還卡住，請看這裡顯示什麼
            print(f"AI Critical Error: {e}")
            return None

# 建立單例模式
ai_service = AIService()