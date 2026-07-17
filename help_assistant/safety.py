import re
from dataclasses import dataclass


REFUSAL_MESSAGE = (
    "I can explain how to use SnipKlip, but I cannot access or disclose customer, "
    "salon, staff, payment, credential, or administrator data. Please ask a general "
    "how-to question without including personal or confidential information."
)

_SENSITIVE_REQUEST_PATTERNS = (
    r"\b(show|list|give|export|reveal|find)\b.{0,40}\b(customer|client|staff|employee|admin|owner)\b.{0,30}\b(data|details|email|phone|password|record|token)",
    r"\b(show|give|reveal|find|export)\b.{0,30}\b(password|secret|api[ _-]?key|access[ _-]?token|credit card|cvv|otp)\b",
    r"\b(ignore|override|forget)\b.{0,30}\b(previous|system|developer|instructions|rules)\b",
    r"\b(system prompt|hidden prompt|jailbreak|database dump|sql query)\b",
)

_PII_PATTERNS = (
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "[email redacted]"),
    (re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)"), "[phone/number redacted]"),
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[payment number redacted]"),
)

_OUTPUT_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[ _-]?key|secret|password|access[ _-]?token)\b\s*[:=]\s*\S+"
)


@dataclass(frozen=True)
class SafetyResult:
    question: str
    refused: bool
    redacted: bool


def inspect_question(raw_question: object, max_length: int) -> SafetyResult:
    question = str(raw_question or "").strip()
    if not question:
        return SafetyResult("", False, False)

    question = question[:max_length]
    if any(re.search(pattern, question, re.IGNORECASE) for pattern in _SENSITIVE_REQUEST_PATTERNS):
        return SafetyResult(question, True, False)

    sanitized = question
    for pattern, replacement in _PII_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return SafetyResult(sanitized, False, sanitized != question)


def sanitize_answer(answer: str) -> str:
    sanitized = _OUTPUT_SECRET_PATTERN.sub(r"\1: [redacted]", answer)
    for pattern, replacement in _PII_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized.strip()
