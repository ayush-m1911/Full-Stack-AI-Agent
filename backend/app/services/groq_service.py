"""
Groq streaming service — handles all LLM calls.

Supports:
- Intent-routed text analysis (summarize / sentiment / qa / explain)
- PDF document grounding
- Image OCR grounding (text or code)
  * Code path: identifies language, explains logic, flags bugs, estimates complexity
  * Text path: treats OCR text like a document
"""

from typing import AsyncGenerator, Optional

from groq import AsyncGroq

from app.core.config import settings
from app.models.schemas import IntentType





_INTENT_PROMPTS: dict[str, str] = {
    "summarize": (
        "You are an expert summarizer. Produce a clear, concise summary with bullet-point "
        "key takeaways. Format: 1-2 sentence overview, then 3-6 bullet points."
    ),
    "sentiment": (
        "You are a sentiment analysis expert. Analyse emotional tone, polarity "
        "(positive / negative / neutral / mixed), and intensity. "
        "Format:\n**Overall Sentiment**: <label>\n**Confidence**: <High/Medium/Low>\n"
        "**Key phrases**: ...\n**Analysis**: <detailed explanation>"
    ),
    "qa": (
        "You are a precise Q&A assistant. Answer based on the provided text. "
        "If the answer is not in the text, say so clearly. Cite relevant parts."
    ),
    "explain": (
        "You are an expert explainer. Break down the concept clearly for a general audience. "
        "Use simple language, concrete examples, and analogies. Add headings for clarity."
    ),
    "unknown": (
        "You are a helpful AI assistant. Do your best to help with the text-related request."
    ),
}



_PDF_PREFIX = (
    "You are analyzing a PDF document. The full extracted text is inside [DOCUMENT] tags. "
    "Base your response on that content. Cite specific sections to support your answers.\n\n"
)

_IMAGE_TEXT_PREFIX = (
    "You are analyzing text extracted from an image via OCR. "
    "The OCR text is inside [IMAGE_TEXT] tags. "
    "Treat it as the primary source material for the user's query. "
    "Note: OCR may contain minor errors; reason about the most likely intended meaning.\n\n"
)

_IMAGE_CODE_PREFIX = (
    "You are an expert code analyst. The following code was extracted from an image via OCR. "
    "The code is inside [CODE] tags. "
    "Your job is to:\n"
    "1. **Explain the logic** — what does this code do, step by step?\n"
    "2. **Identify the programming language** (confirm or correct if already known).\n"
    "3. **Spot potential bugs** — logic errors, edge cases, off-by-one, null issues, etc.\n"
    "4. **Estimate time and space complexity** where relevant (Big-O notation).\n"
    "5. **Answer the user's specific question** about the code, if any.\n"
    "Be thorough, precise, and use code formatting in your response.\n\n"
)

_AUDIO_PREFIX = (
    "You are analyzing an audio transcript produced by OpenAI Whisper. "
    "The full transcript is inside [TRANSCRIPT] tags. "
    "Use it as the primary source material for the user's query. "
    "Note: Whisper may occasionally mishear words; use context to interpret ambiguous phrases.\n\n"
)


def _build_system_prompt(
    intent: IntentType,
    has_pdf: bool = False,
    image_content_type: Optional[str] = None,
    has_audio: bool = False,
) -> str:
    if image_content_type in ("code", "mixed"):
        return _IMAGE_CODE_PREFIX + _INTENT_PROMPTS.get(intent, _INTENT_PROMPTS["unknown"])
    if image_content_type == "text":
        return _IMAGE_TEXT_PREFIX + _INTENT_PROMPTS.get(intent, _INTENT_PROMPTS["unknown"])
    if has_audio:
        return _AUDIO_PREFIX + _INTENT_PROMPTS.get(intent, _INTENT_PROMPTS["unknown"])
    base = _INTENT_PROMPTS.get(intent, _INTENT_PROMPTS["unknown"])
    return (_PDF_PREFIX + base) if has_pdf else base


def _build_messages(
    user_message: str,
    conversation_history: list[dict],
    pdf_context: Optional[str] = None,
    image_context: Optional[str] = None,
    image_content_type: Optional[str] = None,
    detected_language: Optional[str] = None,
    audio_context: Optional[str] = None,
) -> list[dict]:
    """Build Groq message list with optional grounding context."""
    messages: list[dict] = []
    for msg in conversation_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})


    if image_context:
        tag = "CODE" if image_content_type in ("code", "mixed") else "IMAGE_TEXT"
        lang_hint = f" ({detected_language})" if detected_language else ""
        augmented = (
            f"[{tag}{lang_hint}]\n{image_context}\n[/{tag}]\n\n"
            f"[USER QUERY]\n{user_message}"
        )
        messages.append({"role": "user", "content": augmented})
    elif audio_context:
        augmented = (
            f"[TRANSCRIPT]\n{audio_context}\n[/TRANSCRIPT]\n\n"
            f"[USER QUERY]\n{user_message}"
        )
        messages.append({"role": "user", "content": augmented})
    elif pdf_context:
        augmented = (
            f"[DOCUMENT]\n{pdf_context}\n[/DOCUMENT]\n\n"
            f"[USER QUERY]\n{user_message}"
        )
        messages.append({"role": "user", "content": augmented})
    else:
        messages.append({"role": "user", "content": user_message})

    return messages


async def stream_response(
    user_message: str,
    intent: IntentType,
    conversation_history: list[dict],
    pdf_context: Optional[str] = None,
    image_context: Optional[str] = None,
    image_content_type: Optional[str] = None,
    detected_language: Optional[str] = None,
    audio_context: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Streams response tokens from Groq.
    Priority: image_context > audio_context > pdf_context > plain text.
    """
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    system_prompt = _build_system_prompt(
        intent,
        has_pdf=bool(pdf_context) and not image_context and not audio_context,
        image_content_type=image_content_type if image_context else None,
        has_audio=bool(audio_context) and not image_context,
    )
    messages = _build_messages(
        user_message, conversation_history,
        pdf_context=pdf_context if not image_context and not audio_context else None,
        image_context=image_context,
        image_content_type=image_content_type,
        detected_language=detected_language,
        audio_context=audio_context if not image_context else None,
    )

    stream = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        temperature=settings.GROQ_TEMPERATURE,
        max_tokens=settings.GROQ_MAX_TOKENS,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


async def get_full_response(
    user_message: str,
    intent: IntentType,
    conversation_history: list[dict],
    pdf_context: Optional[str] = None,
    image_context: Optional[str] = None,
    image_content_type: Optional[str] = None,
    detected_language: Optional[str] = None,
    audio_context: Optional[str] = None,
) -> str:
    """Non-streaming variant — collects the full response."""
    tokens: list[str] = []
    async for token in stream_response(
        user_message, intent, conversation_history,
        pdf_context, image_context, image_content_type, detected_language, audio_context
    ):
        tokens.append(token)
    return "".join(tokens)
