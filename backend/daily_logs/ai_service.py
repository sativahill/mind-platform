import hashlib
import json
import logging
import re
from typing import Any

from django.conf import settings
from django.db import transaction
from google import genai

from .models import (
    DailyLog,
    DailyLogSuggestion,
)


logger = logging.getLogger(__name__)


GEMINI_MODEL = "gemini-2.5-flash"
MAX_SUGGESTIONS = 3


class DailyLogAnalysisError(Exception):
    """
    Безопасная ошибка анализа Daily Log.

    Ошибка Gemini не должна ломать сохранение
    самой записи Daily Log.
    """


def build_daily_log_analysis_prompt(
    daily_log: DailyLog,
) -> str:
    return f"""
You analyze one personal Daily Log entry for PROJECT,
a personal growth platform.

Your only task right now is to find possible completed wins.

Important rules:

- Extract only achievements or completed meaningful actions.
- A win must describe something that already happened.
- Do not treat plans, intentions, wishes or future tasks as wins.
- Do not invent facts.
- Do not exaggerate ordinary events.
- Do not create a win from every sentence.
- Return no more than {MAX_SUGGESTIONS} suggestions.
- It is valid and often correct to return an empty list.
- Preserve the language used in the Daily Log.
- Keep titles concise and factual.
- Use stable wording for the same event when analyzing the same entry again.
- Description is optional.
- Do not congratulate the user.
- Do not explain your reasoning.
- Do not return Markdown.
- Return valid JSON only.

Win size guidance:

- small:
  a useful everyday action, minor completion or small personal step.

- medium:
  meaningful progress, completion of a substantial task,
  a notable training result or an important milestone.

- large:
  a major achievement, major life event, competition result,
  qualification, release, graduation or exceptional milestone.

Required JSON shape:

{{
  "suggestions": [
    {{
      "type": "win",
      "title": "Short factual title",
      "description": "Optional useful detail",
      "size": "small"
    }}
  ]
}}

Allowed size values:

- small
- medium
- large

If there is no clear completed win, return:

{{
  "suggestions": []
}}

Daily Log date:

{daily_log.date.isoformat()}

Daily Log content:

{daily_log.content}
""".strip()


def normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    return " ".join(
        value.strip().split()
    )


def normalize_size(value: Any) -> str:
    if not isinstance(value, str):
        return DailyLogSuggestion.SIZE_SMALL

    normalized_value = value.strip().lower()

    allowed_sizes = {
        DailyLogSuggestion.SIZE_SMALL,
        DailyLogSuggestion.SIZE_MEDIUM,
        DailyLogSuggestion.SIZE_LARGE,
    }

    if normalized_value not in allowed_sizes:
        return DailyLogSuggestion.SIZE_SMALL

    return normalized_value


def normalize_title_for_key(
    value: str,
) -> str:
    """
    Нормализует заголовок для дедупликации.

    Размер победы и описание намеренно не участвуют
    в ключе: Gemini может изменить их при повторном
    анализе, хотя событие останется тем же.
    """
    normalized_value = value.casefold().strip()

    normalized_value = re.sub(
        r"[^\w\s]",
        " ",
        normalized_value,
        flags=re.UNICODE,
    )

    normalized_value = re.sub(
        r"\s+",
        " ",
        normalized_value,
    )

    return normalized_value.strip()


def build_suggestion_key(
    suggestion_type: str,
    title: str,
) -> str:
    """
    Ключ определяет само событие, а не текущую
    интерпретацию его размера или описания.

    Поэтому одна победа не станет новой только
    из-за изменения medium → large.
    """
    normalized_payload = {
        "type": suggestion_type,
        "title": normalize_title_for_key(
            title
        ),
    }

    serialized_payload = json.dumps(
        normalized_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized_payload.encode("utf-8")
    ).hexdigest()


def parse_gemini_response(
    response_text: str,
) -> list[dict[str, str]]:
    if not response_text:
        return []

    cleaned_response = response_text.strip()

    if cleaned_response.startswith("```"):
        cleaned_response = (
            cleaned_response
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

    try:
        payload = json.loads(
            cleaned_response
        )
    except json.JSONDecodeError as error:
        raise DailyLogAnalysisError(
            "Gemini returned invalid JSON."
        ) from error

    if not isinstance(payload, dict):
        raise DailyLogAnalysisError(
            "Gemini returned an invalid response structure."
        )

    raw_suggestions = payload.get(
        "suggestions",
        [],
    )

    if not isinstance(
        raw_suggestions,
        list,
    ):
        raise DailyLogAnalysisError(
            "Gemini suggestions must be a list."
        )

    valid_suggestions: list[
        dict[str, str]
    ] = []

    seen_keys: set[str] = set()

    for raw_suggestion in (
        raw_suggestions[
            :MAX_SUGGESTIONS
        ]
    ):
        if not isinstance(
            raw_suggestion,
            dict,
        ):
            continue

        suggestion_type = (
            normalize_text(
                raw_suggestion.get(
                    "type"
                )
            )
            .lower()
        )

        if (
            suggestion_type
            != DailyLogSuggestion.TYPE_WIN
        ):
            continue

        title = normalize_text(
            raw_suggestion.get(
                "title"
            )
        )

        if not title:
            continue

        title = title[:255]

        description = normalize_text(
            raw_suggestion.get(
                "description"
            )
        )

        size = normalize_size(
            raw_suggestion.get(
                "size"
            )
        )

        suggestion_key = (
            build_suggestion_key(
                suggestion_type=(
                    suggestion_type
                ),
                title=title,
            )
        )

        if suggestion_key in seen_keys:
            continue

        seen_keys.add(
            suggestion_key
        )

        valid_suggestions.append(
            {
                "suggestion_type": (
                    suggestion_type
                ),
                "title": title,
                "description": (
                    description
                ),
                "size": size,
                "suggestion_key": (
                    suggestion_key
                ),
            }
        )

    return valid_suggestions


def request_gemini_analysis(
    daily_log: DailyLog,
) -> list[dict[str, str]]:
    if not settings.GEMINI_API_KEY:
        raise DailyLogAnalysisError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    prompt = (
        build_daily_log_analysis_prompt(
            daily_log
        )
    )

    try:
        response = (
            client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": (
                        "application/json"
                    ),
                    "temperature": 0.1,
                },
            )
        )
    except Exception as error:
        logger.exception(
            "Gemini Daily Log analysis failed "
            "for DailyLog id=%s",
            daily_log.id,
        )

        raise DailyLogAnalysisError(
            "Daily Log analysis is temporarily unavailable."
        ) from error

    return parse_gemini_response(
        response.text or ""
    )


@transaction.atomic
def save_daily_log_suggestions(
    daily_log: DailyLog,
    suggestions: list[
        dict[str, str]
    ],
) -> list[DailyLogSuggestion]:
    """
    Заменяет только ожидающие предложения.

    Accepted и dismissed сохраняются. Если Gemini снова
    вернула уже принятую победу с тем же ключом, новое
    pending-предложение не создаётся.
    """
    daily_log.suggestions.filter(
        status=(
            DailyLogSuggestion
            .STATUS_PENDING
        )
    ).delete()

    saved_suggestions: list[
        DailyLogSuggestion
    ] = []

    for suggestion in suggestions:
        suggestion_object, created = (
            DailyLogSuggestion
            .objects
            .get_or_create(
                daily_log=daily_log,
                suggestion_key=(
                    suggestion[
                        "suggestion_key"
                    ]
                ),
                defaults={
                    "suggestion_type": (
                        suggestion[
                            "suggestion_type"
                        ]
                    ),
                    "title": (
                        suggestion[
                            "title"
                        ]
                    ),
                    "description": (
                        suggestion[
                            "description"
                        ]
                    ),
                    "size": (
                        suggestion[
                            "size"
                        ]
                    ),
                    "status": (
                        DailyLogSuggestion
                        .STATUS_PENDING
                    ),
                },
            )
        )

        if not created:
            continue

        saved_suggestions.append(
            suggestion_object
        )

    return saved_suggestions


def analyze_daily_log(
    daily_log: DailyLog,
) -> list[DailyLogSuggestion]:
    """
    Полная операция:

    Daily Log
    → Gemini
    → проверенный JSON
    → DailyLogSuggestion в PostgreSQL
    """
    suggestions = (
        request_gemini_analysis(
            daily_log
        )
    )

    return save_daily_log_suggestions(
        daily_log=daily_log,
        suggestions=suggestions,
    )