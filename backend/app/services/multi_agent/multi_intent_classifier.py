"""
Multi-Input Intent Classifier.

Extended version of the single-input intent classifier supporting:
  summarize | sentiment | question_answering | code_explanation
  | comparison | general_chat | followup | unknown

Uses keyword fast-path (no LLM cost) for obvious cases, then falls back
to a Groq JSON-mode call for ambiguous messages.

Mandatory clarification rule: if confidence < 0.50, return "followup"
with a clarifying question. The agent must NOT guess at low confidence.
"""

from __future__ import annotations

import json
import logging
from typing import Tuple

from groq import AsyncGroq

from app.core.config import settings
from app.models.schemas import MultiIntentType

log = logging.getLogger(__name__)





_SYSTEM_PROMPT = """You are an intent classification engine for a multi-modal AI agent.
The user may supply any combination of: text query, PDF documents, images, or audio recordings.
Classify what the user wants to do into ONE of these intents:

  summarize          — condense source material into key points
  sentiment          — analyse emotional tone / polarity
  question_answering — answer a specific question about the provided content
  code_explanation   — explain / analyse / debug code found in image or text
  comparison         — compare or contrast multiple provided sources
  general_chat       — open-ended conversation, no specific source to analyse
  followup           — request is too ambiguous; ask a clarifying question

Rules:
1. Reply ONLY with valid JSON matching the schema below — no prose.
2. If intent is "followup", provide a short, helpful "followup_question".
3. confidence: 0.0–1.0. Use < 0.50 for genuinely ambiguous requests.
4. If multiple source types are present and the query asks to compare them,
   prefer "comparison".
5. If the image appears to contain code, prefer "code_explanation" over "question_answering".

Schema:
{
  "intent": "<one of the 7 intents above>",
  "confidence": <float 0-1>,
  "followup_question": "<string or null>"
}"""





_KW: dict[str, list[str]] = {
    "summarize":         ["summarize", "summary", "tldr", "brief", "condense", "key points", "shorten", "gist"],
    "sentiment":         ["sentiment", "tone", "feeling", "emotion", "positive", "negative", "mood", "polarity"],
    "question_answering":["what is", "who is", "when did", "how does", "why did", "answer", "tell me about",
                          "what are", "how many", "where is"],
    "code_explanation":  ["explain this code", "debug", "bug", "time complexity", "space complexity",
                          "what does this function", "explain the logic", "code review"],
    "comparison":        ["compare", "contrast", "difference", "similar", "same topic", "both discuss",
                          "versus", " vs ", "how do they differ"],
    "general_chat":      ["hello", "hi ", "hey ", "thanks", "thank you", "help me", "what can you"],
}


def _fast_classify(query: str) -> MultiIntentType | None:
    lower = query.lower()
    for intent, kws in _KW.items():
        if any(kw in lower for kw in kws):
            return intent
    return None






async def classify_multi_intent(
    query: str,
    source_types: list[str],
    context_snippet: str = "",
) -> Tuple[MultiIntentType, float, str | None]:
    """
    Returns (intent, confidence, followup_question).

    source_types: list of source_type strings present (e.g. ["pdf", "audio"])
    """



    non_text = [t for t in source_types if t != "text"]
    if len(non_text) >= 2:
        lower = query.lower()
        if any(kw in lower for kw in _KW["comparison"]):
            return "comparison", 0.92, None

    quick = _fast_classify(query)
    if quick and len(query.split()) >= 3:
        return quick, 0.87, None


    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    user_content = f"User query: {query}"
    if source_types:
        user_content += f"\nSource types present: {', '.join(source_types)}"
    if context_snippet:
        user_content += f"\nContext preview:\n{context_snippet[:400]}"

    try:
        resp = await client.chat.completions.create(
            model=settings.GROQ_INTENT_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        parsed = json.loads(raw)

        intent: MultiIntentType = parsed.get("intent", "general_chat")
        confidence: float = float(parsed.get("confidence", 0.5))
        followup: str | None = parsed.get("followup_question")


        if confidence < 0.50:
            return "followup", confidence, followup or "What would you like me to do with this content?"

        return intent, confidence, followup

    except Exception as exc:
        log.warning("Multi-intent classification failed: %s", exc)
        return "general_chat", 0.5, None
