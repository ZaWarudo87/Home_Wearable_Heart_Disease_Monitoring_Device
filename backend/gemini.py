from __future__ import annotations

import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Optional
from google import genai


def _fallback_health_summary(lang: str = "zh-TW") -> str:
    if lang.lower().startswith("zh"):
        return("（離線模式）目前無法連線到 Gemini，請稍候再嘗試。")
    else:
        return("(Offline mode) Gemini is unavailable, please try again later.")


def generate_text(prompt: str, model: str = "gemini-3-flash-preview") -> str:
    client = genai.Client()
    if client is None:
        raise RuntimeError("Gemini not configured: missing/invalid GEMINI_API_KEY or SDK not installed.")
    else:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
    return response.text


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

    prompt = system + "\n\n" + "User data (JSON):\n" + json.dumps(payload, ensure_ascii=False)

    try:
        return generate_text(prompt)
    except Exception as e:
        print(f"Gemini generation error: {e}")
        # Safety: never break the API response
        return _fallback_health_summary()
