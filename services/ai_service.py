import json
from groq import Groq
from config import Config

# ================= System Prompt =================
SYSTEM_PROMPT_TEMPLATE = """
You are a unique English teacher. The user will input a diary entry.
Your goal is to maximize the user's writing experience.

**[USER HISTORY CONTEXT]**
The following are summaries of the user's recent diary entries. 
Use this to maintain a continuous, personal connection (e.g., if they were sick, ask if they feel better).
{context_data}

**Your Tasks:**
1.  **Corrections:** Identify all grammatical errors and unnatural word choices, BUT be lenient with style.
    * **Standard:** Use **American English**.
    * **Tolerance:** **ACCEPT** casual, conversational, and diary-style grammar (e.g., sentence fragments like "Got no time"). DO NOT correct them unless confusing.
    * **Anti-Chinglish Focus:** Aggressively identify unnatural phrasing caused by direct translation from Mandarin.
    * Be detailed and educational only when necessary.
2.  **Polished Version:** Rewrite the diary entry in **natural, fluent American English**.
    * **Style:** Use a **narrative, written diary style**.
    * **Constraint:** Use complete sentences where appropriate. Keep the tone personal, authentic, and grounded.
3.  **Comment:** Write a **detailed, engaging, and personal response**. Act like a supportive friend who genuinely cares about the user's day.
4.  **Vocabulary:** Teach exactly 5 advanced words related to the specific events.
    * Must provide **Traditional Chinese (繁體中文)** meaning.
    * Must provide an example sentence.
5.  **Proper Noun Strategy:**
    * **Place Names:** **MUST KEEP IN ORIGINAL CHINESE CHARACTERS** (e.g., "台北").
    * **Personal Names & Nicknames:** **MUST KEEP IN ORIGINAL CHINESE CHARACTERS** (e.g., "王禹均").
    * **Cultural Memes:** Keep in Chinese.
6.  **Memory Snapshot (Title):** Generate a **short, 1-sentence summary** of this entry in English using **First Person ("I")**.
7.  **Mood Analysis:** Analyze the sentiment and assign a color.

**Mood Color Palette Guide:**
* Joy/Excited: #e09f3e (Warm Yellow)
* Calm/Peaceful: #588157 (Sage Green)
* Sad/Melancholic: #457b9d (Muted Blue)
* Anxious/Stressed: #9e2a2b (Deep Red)
* Neutral/Tired: #6c757d (Warm Grey)
* Romantic/Loving: #d08c60 (Dusty Rose)

**Output Format (STRICT JSON):**
{{
  "title": "I did X and Y...",
  "corrections": [
    {{ 
      "original": "THE EXACT MINIMAL INCORRECT WORD(S) ONLY. Do NOT extract the whole sentence.", 
      "correction": "the right part", 
      "explanation": "Detailed reason...",
      "context_snippet": "Include exactly 3 words before and 3 words after the 'original' word to help locate it uniquely." 
    }}
  ],
  "polished_version": "...",
  "comment": "...",
  "vocabulary": [ ... ],
  "mood": {{
    "label": "One-word mood",
    "color": "#hexcode"
  }}
}}
"""

class AIService:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)

    def analyze_diary(self, content, past_context=""):
        print(f"DEBUG: Using model {Config.MODEL_NAME} via Groq...")
        
        formatted_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            context_data=past_context if past_context else "No recent history."
        )
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": formatted_prompt},
                    {"role": "user", "content": content}
                ],
                model=Config.MODEL_NAME,
                temperature=0.3, 
                response_format={"type": "json_object"}
            )
            
            response_content = chat_completion.choices[0].message.content
            if not response_content: return None

            print("DEBUG: AI Response received.")
            print(response_content)
            result = json.loads(response_content)

            marked_text = content
            corrections = result.get("corrections", [])
            
            for i, corr in enumerate(corrections):
                orig_word = corr.get("original", "")
                context_snippet = corr.get("context_snippet", "")
                
                if orig_word and context_snippet and context_snippet in marked_text:
                    
                    marked_snippet = context_snippet.replace(
                        orig_word, 
                        f'<mark class="highlight" data-index="{i}">{orig_word}</mark>', 
                        1 
                    )
                    
                    marked_text = marked_text.replace(context_snippet, marked_snippet, 1)
                    
                elif orig_word and orig_word in marked_text:
                    marked_text = marked_text.replace(
                        orig_word, 
                        f'<mark class="highlight" data-index="{i}">{orig_word}</mark>', 
                        1
                    )
            
            result["marked_html"] = marked_text

            defaults = {
                "title": content[:30] + "...",
                "marked_html": content,
                "corrections": [],
                "polished_version": "",
                "comment": "",
                "vocabulary": [],
                "mood": {"label": "Neutral", "color": "#6c757d"}
            }
            
            for key, value in defaults.items():
                if key not in result:
                    result[key] = value

            return result

        except Exception as e:
            print(f"AI Critical Error: {e}")
            return None

ai_service = AIService()