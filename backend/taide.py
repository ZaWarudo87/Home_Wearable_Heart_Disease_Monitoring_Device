import os
import json
import requests
from typing import Any, Optional

TAIDE_API_URL = os.environ.get("TAIDE_API_URL", "http://140.113.95.112:8000/v1/chat/completions")

def _fallback_health_summary(lang: str = "zh-TW") -> str:
    if lang.lower().startswith("zh"):
        return "（離線模式）目前無法連線到 TAIDE 模型，請稍候再嘗試。"
    else:
        return "(Offline mode) TAIDE model is unavailable, please try again later."


def generate_text(system_prompt: str, user_prompt: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    payload = {
        "model": "taide-12b",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 512
    }

    try:
        response = requests.post(TAIDE_API_URL, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Local TAIDE API request failed: {e}")


def health_summary(
    overview: dict,
    user_profile: Optional[dict] = None,
    lang: str = "zh-TW",
) -> str:
    payload: dict[str, Any] = {"overview": overview}
    if user_profile:
        payload["user_profile"] = user_profile

    if lang.lower().startswith("zh"):
        system = (
            "你是健康助理。根據使用者的心臟健康指標，提供簡短、具體、非診斷性的建議。"
            "避免宣稱確診；若有危急徵象請提醒就醫。使用繁體中文。"
            "輸出請以 2~3 點條列為主，最後加一句提醒此為一般建議非醫療診斷。"
            "輸出格式為純文字，不使用任何styling。"
        )
    else:
        system = (
            "You are a health assistant. Provide short, specific, and non-diagnostic recommendations based on the user's heart health indicators."
            "Avoid claiming a diagnosis; if there is a critical sign, please notify the doctor."
            "Use English. Output in a list format with at least 2 points, followed by a general recommendation for non-medical diagnosis."
            "Output should be pure text, without any styling."
        )

    user_content = "User data (JSON):\n" + json.dumps(payload, ensure_ascii=False)

    try:
        return generate_text(system_prompt=system, user_prompt=user_content)
    except Exception as e:
        print(f"TAIDE generation error: {e}")
        return _fallback_health_summary(lang)
