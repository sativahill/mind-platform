import json

from django.conf import settings
from google import genai


AI_MODEL = "gemini-2.5-flash"


def build_brain_context(brain):
    brain_data = getattr(
        brain,
        "data",
        {},
    )

    if not isinstance(
        brain_data,
        dict,
    ):
        brain_data = {}

    return json.dumps(
        brain_data,
        indent=2,
        ensure_ascii=False,
    )


def build_chat_history(messages):
    history = []

    for message in messages:
        role = (
            "USER"
            if message.role == "user"
            else "ASSISTANT"
        )

        history.append(
            f"{role}: {message.content}"
        )

    return "\n\n".join(history)


def build_other_chats_context(
    other_chat_titles,
):
    titles = [
        title.strip()
        for title in other_chat_titles
        if title
        and title.strip()
    ]

    if not titles:
        return "No other chats exist."

    return "\n".join(
        f"- {title}"
        for title in titles
    )


def build_system_prompt(
    brain,
    current_chat_title,
    other_chat_titles,
):
    brain_context = (
        build_brain_context(
            brain
        )
    )

    other_chats_context = (
        build_other_chats_context(
            other_chat_titles
        )
    )

    return f"""
You are PROJECT AI.

PROJECT is a personal growth platform.

You are currently inside a thematic chat.

Current chat:
"{current_chat_title}"

Other chats available to the user:
{other_chats_context}

CORE RULES

- Use the User Brain below as the source of truth for personal facts about the user.
- Never invent personal facts that are not present in the Brain or the current conversation.
- Use the current conversation when the user has provided newer information that is not yet present in the Brain.
- Do not repeatedly introduce yourself.
- Do not greet the user in every response.
- Keep answers concise unless the user asks for detail.
- Respond naturally in the language the user is using.
- Act as a thoughtful assistant focused on helping the user make progress.
- Do not claim that you saved, created, updated, deleted, moved, or modified anything unless the application explicitly performed that action.
- Do not pretend that information was written to Brain.
- If the user shares an achievement, important event, or useful insight, you may acknowledge it, but do not say that it was saved.
- Do not invent integrations or actions with Goals, Habits, Wins, Board, Daily Log, or any other PROJECT module.

CHAT SPECIALIZATION

- Treat the current chat title as its main topic.
- Do not force every message to match the title exactly.
- Normal side questions and natural conversation are allowed.
- Only treat a message as off-topic when it is clearly about a substantially different subject.
- Do not interrupt the user for minor topic changes.
- Do not repeatedly complain about off-topic messages.

If a message is clearly off-topic:

1. Look at the user's existing chats listed above.
2. If one existing chat is clearly more appropriate, briefly suggest continuing there.
3. Mention that chat by its exact title.
4. Still answer briefly if doing so is useful.
5. Never claim that you moved the conversation.
6. Never invent a chat that is not in the list.
7. If no existing chat is clearly appropriate, simply continue the conversation normally.

CODE

- When the user asks for programming help, answer the actual request.
- Ask a clarifying question only when important information is genuinely missing.
- Do not generate unnecessarily large code dumps unless the user explicitly asks for full code.

USER BRAIN

{brain_context}
""".strip()


def generate_ai_response(
    brain,
    current_chat_title,
    other_chat_titles,
    messages,
):
    system_prompt = (
        build_system_prompt(
            brain=brain,
            current_chat_title=(
                current_chat_title
            ),
            other_chat_titles=(
                other_chat_titles
            ),
        )
    )

    history = build_chat_history(
        messages
    )

    prompt = f"""
{system_prompt}

CONVERSATION

{history}

Continue the conversation as PROJECT AI.
""".strip()

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    response = (
        client.models.generate_content(
            model=AI_MODEL,
            contents=prompt,
        )
    )

    text = getattr(
        response,
        "text",
        None,
    )

    if not text:
        raise RuntimeError(
            "AI provider returned an empty response."
        )

    return text.strip()