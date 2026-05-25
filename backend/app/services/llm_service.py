import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing from environment")

client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
You are Chrona, an elite senior Site Reliability Engineering AI incident response agent.

Your role:
- analyze production telemetry
- review alerts, logs, metrics
- interpret deterministic infrastructure analysis
- synthesize root cause
- recommend remediation actions

STRICT RULES:
1. Use provided deterministic evidence as highest priority.
2. Do not invent infrastructure.
3. Return ONLY valid JSON.
4. Confidence must be between 0.0 and 1.0.

Return exactly:

{
  "root_cause": "string",
  "confidence": 0.0,
  "reasoning": [
    "string",
    "string"
  ],
  "recommended_actions": [
    "string",
    "string"
  ],
  "ai_summary": "string"
}
"""


def _fallback_response(error_message: str) -> Dict[str, Any]:
    return {
        "root_cause": "Analysis unavailable",
        "confidence": 0.0,
        "reasoning": [
            "AI analysis failed safely.",
            error_message,
        ],
        "recommended_actions": [
            "Review deterministic root cause analysis",
            "Inspect infrastructure telemetry manually",
        ],
        "ai_summary": "Chrona AI agent could not complete synthesis safely.",
    }


def _safe_json_parse(raw: str) -> Dict[str, Any]:
    try:
        return json.loads(raw)
    except Exception:
        return _fallback_response("Malformed JSON returned by LLM")


def analyze_with_llm(agent_context: str) -> Dict[str, Any]:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.2,
            max_tokens=1200,
            timeout=20,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": agent_context,
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            return _fallback_response("Empty LLM response")

        parsed = _safe_json_parse(content)

        parsed.setdefault("root_cause", "Unknown")
        parsed.setdefault("confidence", 0.0)
        parsed.setdefault("reasoning", [])
        parsed.setdefault("recommended_actions", [])
        parsed.setdefault("ai_summary", "No summary generated")

        return parsed

    except Exception as exc:
        return _fallback_response(str(exc))