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
1. Corrections: Rigorously identify ALL grammatical errors and unnatural Chinglish phrasing. Act as an uncompromising advanced English writing coach.
    * Absolute Grammar Strictness: You MUST correct fundamental grammar errors (e.g., wrong prepositions, misuse of conjunctions like "despite + clause", singular/plural noun errors, incorrect word forms). Do not let any structural mistake slip.
    * Ruthless Anti-Chinglish: Aggressively target awkward phrasing caused by direct translation from Mandarin. If a phrase is grammatically correct but a native speaker would never use it in that context (e.g., using "go hand in hand" to compare scenery, or "searched randomly" for discovering a place), you MUST correct it and explain the native logic.
    * Defined Tolerance (Native Casual ONLY): You may ONLY accept casual phrasing if it is a common native habit (e.g., dropping pronouns like "Got no time"). Do NOT use this rule to excuse unnatural phrasing or vocabulary misuse.
    * Actionable Explanations: Briefly explain the grammatical rule or why the Chinglish phrase fails in American English context.
    * Snippet Strictness: The `context_snippet` MUST contain EXACTLY 3 words before and 3 words after the `original` word. Count strictly.
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
      "original": "THE EXACT MINIMAL INCORRECT WORD(S) ONLY.", 
      "correction": "the right part", 
      "explanation": "Detailed reason...",
      "unique_anchor": "Extract a continuous substring of 4 to 7 words from the original text that contains the 'original' word. This acts as a search anchor and MUST be an exact copy from the text."
    }}
  ],
  "polished_version": "...",
  "comment": "...",
  "vocabulary": [
    {{ "word": "...", "meaning": "...", "example": "..." }}
  ],
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
            spans_to_mark = []
            
            # 第一階段：計算所有錯誤單字的絕對座標 (Three-Tier Strategy)
            for i, corr in enumerate(corrections):
                orig_word = corr.get("original", "")
                anchor = corr.get("unique_anchor", "")
                
                if not orig_word or orig_word not in content:
                    continue
                
                # 策略 1：如果這個錯誤字串在全文只出現一次，直接定位！(完美解決長句子)
                if content.count(orig_word) == 1:
                    absolute_start = content.find(orig_word)
                    absolute_end = absolute_start + len(orig_word)
                    spans_to_mark.append((absolute_start, absolute_end, i, orig_word))
                    continue
                    
                # 策略 2：如果出現多次 (例如單字 iem)，利用 anchor 來精準定位
                if anchor and anchor in content:
                    anchor_start = content.find(anchor)
                    word_offset = anchor.find(orig_word) 
                    # 確保 orig_word 真的包在 anchor 裡面，且長度合理
                    if word_offset != -1:
                        absolute_start = anchor_start + word_offset
                        absolute_end = absolute_start + len(orig_word)
                        spans_to_mark.append((absolute_start, absolute_end, i, orig_word))
                        continue
                        
                # 策略 3 (Failsafe)：如果字串出現多次，但 AI 給的 anchor 爛掉找不到
                # 退而求其次，直接標記我們找到的第一個匹配項
                absolute_start = content.find(orig_word)
                absolute_end = absolute_start + len(orig_word)
                spans_to_mark.append((absolute_start, absolute_end, i, orig_word))

            # 第二階段：依座標由後往前排序 (Reverse order)
            spans_to_mark.sort(key=lambda x: x[0], reverse=True)
            
            # 第三階段：過濾重疊座標 (防止 HTML 巢狀破壞)
            filtered_spans = []
            last_start = float('inf')
            for span in spans_to_mark:
                start_idx, end_idx, idx, orig = span
                # 確保當前標籤的結尾，不會超車上一個標籤的開頭
                if end_idx <= last_start:
                    filtered_spans.append(span)
                    last_start = start_idx
            
            # 第四階段：執行精準插入
            for start_idx, end_idx, idx, orig in filtered_spans:
                marked_text = (
                    marked_text[:start_idx] + 
                    f'<mark class="highlight" data-index="{idx}">{orig}</mark>' + 
                    marked_text[end_idx:]
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