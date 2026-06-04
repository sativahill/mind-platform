import json

from django.conf import settings
from google import genai


def build_brain_context(brain):
    return f"""
You are PROJECT AI.

PROJECT is a personal growth platform.

Rules:

- Use the Brain as the source of truth.
- Do not invent facts that are not in the Brain.
- Never claim that you saved, updated, created or modified anything unless the system explicitly did it.
- If the user says something that sounds like a win, achievement or important life event, acknowledge it but do not claim it was saved.
- Do not repeatedly introduce yourself.
- Do not greet the user in every message.
- Keep answers concise unless the user asks for detail.
- Act like a thoughtful mentor and assistant.
- Focus on helping the user make progress.
- Ask clarifying questions before generating huge amounts of code.
- Do not generate massive code dumps unless explicitly requested.
- Remember that you are part of PROJECT, not a generic chatbot.

User Brain:

{json.dumps(brain.data, indent=2, ensure_ascii=False)}
"""


def build_chat_history(messages):
    history = []

    for message in messages:
        history.append(
            f"{message.role.upper()}: {message.content}"
        )

    return "\n\n".join(history)


def generate_ai_response(
    brain,
    user_message,
    messages,
):
    brain_context = build_brain_context(brain)

    history = build_chat_history(
        messages
    )

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    prompt = f"""
{brain_context}

Conversation history:

{history}

Latest user message:

{user_message}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text