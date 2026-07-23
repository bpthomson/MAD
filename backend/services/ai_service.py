import json

from config import Config
from google import genai
from google.genai import types

# ================= System Prompt =================
SYSTEM_PROMPT_TEMPLATE = """
You are an advanced English writing coach for a Traditional Chinese speaker's diary.
Your job is to correct rigorously, teach naturally, and respond warmly.

**[USER HISTORY CONTEXT]**
Recent diary summaries — use to maintain personal continuity 
(e.g., follow up on illness, ongoing events, people mentioned):
{context_data}

---

## TASK 1 — Corrections

Apply this decision tree to EVERY phrase:

1. Is it a **native casual habit** (e.g., dropped pronouns "Got no time", 
   swear words like "fucking"/"shit" that don't distort meaning)? → **KEEP**
2. Is it a **grammar error** (preposition, conjunction like "despite + clause", 
   singular/plural, word form, tense)? → **CORRECT**
3. Is it grammatically fine BUT sounds like **direct Mandarin translation** 
   that a native speaker would never say in this context 
   (e.g., "go hand in hand" for scenery, "searched randomly" for discovering a place)? 
   → **CORRECT** and explain the native logic.
4. Otherwise → **KEEP**.

**Correction rules:**
- Mark ONLY the minimal incorrect span (e.g., just the noun missing "-s", not the full sentence).
- `explanation`: 1 sentence, cite the rule or native logic.
- `unique_anchor`: an EXACT 4-7 word continuous substring copied from the original text 
   that contains the `original`. Used as a search anchor.

## TASK 2 — Polished Version
Rewrite the entry in **natural, fluent American English**, narrative diary style, 
complete sentences, personal and grounded tone.

## TASK 3 — Comment
Write **2-4 sentences** as a supportive friend. Reference specific events from the entry 
and, when relevant, the user history context.

## TASK 4 — Vocabulary
Teach **exactly 5** advanced words tied to specific events in this entry.
Each must include Traditional Chinese (繁體中文) meaning and one example sentence.

## TASK 5 — Proper Nouns
**Keep ALL Chinese proper nouns in original characters** — places (台北), 
personal names/nicknames (王禹均), cultural memes. Never romanize or translate them.

## TASK 6 — Title
One short first-person English sentence starting with "I" summarizing the entry.

## TASK 7 — Mood
Pick ONE label + matching hex color:
- Joy/Excited → #e09f3e
- Calm/Peaceful → #588157
- Sad/Melancholic → #457b9d
- Anxious/Stressed → #9e2a2b
- Neutral/Tired → #6c757d
- Romantic/Loving → #d08c60

---

## OUTPUT — STRICT JSON ONLY (no markdown, no prose outside JSON)

{{
  "title": "I ...",
  "corrections": [
    {{
      "original": "exact minimal wrong span",
      "correction": "fixed version",
      "explanation": "1-sentence rule or native-logic reason",
      "unique_anchor": "exact 4-7 word substring from original text"
    }}
  ],
  "polished_version": "...",
  "comment": "...",
  "vocabulary": [
    {{"word": "dermatology", "meaning": "皮膚科", "example": "She studied dermatology in medical school."}}
  ],
  "mood": {{
    "label": "Joy",
    "color": "#e09f3e"
  }}
}}
"""


class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)

    def analyze_diary(self, content, past_context="", model_name=None):
        target_model = model_name if model_name else Config.MODEL_NAME
        print(f"DEBUG: Using model {target_model} via Gemini AI Studio...")

        formatted_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            context_data=past_context if past_context else "No recent history."
        )

        try:
            response = self.client.models.generate_content(
                model=target_model,
                contents=content,
                config=types.GenerateContentConfig(
                    system_instruction=formatted_prompt,
                    temperature=0.3,
                    response_mime_type="application/json",
                ),
            )

            response_content = response.text
            if not response_content:
                return None

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
                        spans_to_mark.append(
                            (absolute_start, absolute_end, i, orig_word)
                        )
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
            last_start = float("inf")
            for span in spans_to_mark:
                start_idx, end_idx, idx, orig = span
                # 確保當前標籤的結尾，不會超車上一個標籤的開頭
                if end_idx <= last_start:
                    filtered_spans.append(span)
                    last_start = start_idx

            # 第四階段：執行精準插入
            for start_idx, end_idx, idx, orig in filtered_spans:
                marked_text = (
                    marked_text[:start_idx]
                    + f'<mark class="highlight" data-index="{idx}">{orig}</mark>'
                    + marked_text[end_idx:]
                )

            result["marked_html"] = marked_text

            defaults = {
                "title": content[:30] + "...",
                "marked_html": content,
                "corrections": [],
                "polished_version": "",
                "comment": "",
                "vocabulary": [],
                "mood": {"label": "Neutral", "color": "#6c757d"},
            }

            for key, value in defaults.items():
                if key not in result:
                    result[key] = value

            return result

        except Exception as e:
            print(f"AI Critical Error: {e}")
            return None

    def get_available_models(self):
        try:
            models_response = self.client.models.list()
            # Filter to generative models only (exclude embedding, etc.)
            text_models = [
                m.name.replace("models/", "")
                for m in models_response
                if "generateContent" in (m.supported_actions or [])
            ]

            # Ensure default model is available
            if "gemini-flash-latest" not in text_models:
                text_models.append("gemini-flash-latest")

            # Sort alphabetically
            text_models.sort(key=lambda x: x.lower())

            return {"models": text_models, "default": "gemini-flash-latest"}
        except Exception as e:
            print(f"Error fetching models: {e}")
            # Fallback with known Gemini models
            return {
                "models": [
                    "gemini-2.0-flash",
                    "gemini-2.0-flash-lite",
                    "gemini-2.5-flash",
                    "gemini-2.5-pro",
                ],
                "default": "gemini-flash-latest",
            }


ai_service = AIService()
