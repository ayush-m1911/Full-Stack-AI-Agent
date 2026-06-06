"""
Intent Classifier — uses Groq to detect what the user wants to do with their text.

Supported intents:
  • summarize  — condense long text into key points
  • sentiment  — analyse emotional tone / polarity
  • qa         — answer a specific question about the text
  • explain    — break down a complex concept in the text
  • followup   — agent needs more information (ambiguous input)
  • unknown    — cannot determine intent

If the message is ambiguous the classifier returns `followup` along with a
clarifying question for the user.
"""

import json
import time
from typing import Tuple

from groq import AsyncGroq

from app.core.config import settings
from app.models.schemas import IntentType





_SYSTEM_PROMPT = """You are an intent classification engine for an AI text-analysis agent.
Your ONLY job is to classify what the user wants to do with their text into one of these intents:

  summarize  — user wants a concise summary / key points of a text
  sentiment  — user wants emotional tone, polarity, or mood analysis
  qa         — user wants answers to specific questions about a text
  explain    — user wants a concept or passage explained more clearly
  followup   — the request is too ambiguous to classify; you need to ask a clarifying question
  unknown    — intent genuinely cannot be determined even with a follow-up

Rules:
1. Respond ONLY with valid JSON matching the schema below — no extra text.
2. If you choose "followup", provide a short, friendly clarifying question in "followup_question".
3. Confidence must be 0.0–1.0.

Schema:
{
  "intent": "<one of: summarize | sentiment | qa | explain | followup | unknown>",
  "confidence": <float 0-1>,
  "followup_question": "<string or null>"
}
"""

_AMBIGUOUS_EXAMPLES = [
    "What should I do with this text?",
    "Help me with this.",
    "Can you look at this?",
    "Process this for me.",
    "What do you think?",
]


_INTENT_KEYWORDS: dict[str, list[str]] = {
    "summarize": ["summarize", "summary", "tldr", "shorten", "brief", "condense", "key points", "gist"],
    "sentiment": ["sentiment", "tone", "feeling", "emotion", "positive", "negative", "mood", "opinion"],
    "qa": ["what is", "who is", "when did", "how does", "why did", "answer", "question", "tell me about"],
    "explain": ["explain", "clarify", "what does", "meaning of", "define", "elaborate", "break down"],
}


def _fast_keyword_classify(message: str) -> IntentType | None:
    """Quick keyword match before calling the LLM (saves latency on obvious cases)."""
    lower = message.lower()
    for intent, kws in _INTENT_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            return intent
    return None


async def classify_intent(
    message: str,
    conversation_context: str = "",
) -> Tuple[IntentType, float, str | None]:
    """
    Returns (intent, confidence, followup_question).
    Uses a fast keyword pre-check to avoid LLM calls on obvious messages.
    """


    quick = _fast_keyword_classify(message)
    if quick and len(message.split()) > 3:
        return quick, 0.85, None


    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    user_content = f"User message: {message}"
    if conversation_context:
        user_content = f"Recent context:\n{conversation_context}\n\n{user_content}"

    try:
        t0 = time.perf_counter()
        response = await client.chat.completions.create(
            model=settings.GROQ_INTENT_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        elapsed = int((time.perf_counter() - t0) * 1000)

        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)

        intent: IntentType = parsed.get("intent", "unknown")
        confidence: float = float(parsed.get("confidence", 0.5))
        followup: str | None = parsed.get("followup_question")

        return intent, confidence, followup

    except Exception as exc:

        return "unknown", 0.0, None
