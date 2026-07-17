import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Sequence


_GUIDE_PATH = Path(__file__).resolve().parent / "knowledge" / "app_guide.md"
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a", "an", "and", "are", "can", "do", "does", "for", "from", "how", "i",
    "in", "is", "it", "me", "my", "of", "on", "or", "our", "please", "should",
    "the", "their", "this", "to", "use", "using", "we", "what", "when", "where",
    "which", "with", "you", "your",
}
_WEAK_QUERY_WORDS = {
    "add", "change", "check", "create", "edit", "find", "get", "help",
    "make", "manage", "need", "open", "see", "set", "show", "start", "update",
}
_MIN_SCORE = 4
_UNSUPPORTED_TITLE = "Unsupported Features"
_HELP_TITLE = "Getting Help"


@dataclass(frozen=True)
class HelpChunk:
    title: str
    route: str
    content: str
    aliases: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()
    outcome: str = ""
    limitations: str = ""
    unsupported: bool = False

    @property
    def searchable_text(self) -> str:
        parts = [
            self.title,
            " ".join(self.aliases),
            self.content,
            " ".join(self.prerequisites),
            " ".join(self.steps),
            self.outcome,
            self.limitations,
        ]
        return "\n".join(part for part in parts if part)


@dataclass(frozen=True)
class RetrievalResult:
    chunks: tuple[HelpChunk, ...]
    unsupported: bool
    confidence: int


def _normalize_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("ses"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _tokens(text: str) -> set[str]:
    raw = _TOKEN_PATTERN.findall(text.lower())
    normalized = {_normalize_token(token) for token in raw}
    return {
        token for token in normalized
        if token not in _STOP_WORDS and len(token) > 1
    }


def _parse_list_field(value: str) -> tuple[str, ...]:
    items = [item.strip() for item in value.split(",")]
    return tuple(item for item in items if item)


def _finalize_chunk(
    title: str,
    route: str,
    aliases: Sequence[str],
    prerequisites: Sequence[str],
    steps: Sequence[str],
    outcome: str,
    limitations: str,
    body: Sequence[str],
) -> HelpChunk:
    content_parts = [line for line in body if line]
    if prerequisites and not any(line.lower().startswith("prerequisite") for line in content_parts):
        content_parts.append("Prerequisites: " + " ".join(prerequisites))
    if steps:
        content_parts.append("Steps:")
        content_parts.extend(f"{index}. {step}" for index, step in enumerate(steps, start=1))
    if outcome:
        content_parts.append(f"Outcome: {outcome}")
    if limitations:
        content_parts.append(f"Limitations: {limitations}")
    return HelpChunk(
        title=title,
        route=route,
        content="\n".join(content_parts).strip(),
        aliases=tuple(aliases),
        prerequisites=tuple(prerequisites),
        steps=tuple(steps),
        outcome=outcome,
        limitations=limitations,
        unsupported=title == _UNSUPPORTED_TITLE,
    )


@lru_cache(maxsize=1)
def load_chunks() -> tuple[HelpChunk, ...]:
    chunks: List[HelpChunk] = []
    title = ""
    route = ""
    aliases: List[str] = []
    prerequisites: List[str] = []
    steps: List[str] = []
    outcome = ""
    limitations = ""
    body: List[str] = []
    collecting_steps = False

    def flush() -> None:
        nonlocal title, route, aliases, prerequisites, steps, outcome, limitations, body, collecting_steps
        if title and (body or steps or prerequisites or aliases):
            chunks.append(
                _finalize_chunk(
                    title,
                    route,
                    aliases,
                    prerequisites,
                    steps,
                    outcome,
                    limitations,
                    body,
                )
            )
        title = ""
        route = ""
        aliases = []
        prerequisites = []
        steps = []
        outcome = ""
        limitations = ""
        body = []
        collecting_steps = False

    for raw_line in _GUIDE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("## "):
            flush()
            title = stripped[3:].strip()
            continue
        if not title or not stripped:
            if not stripped:
                collecting_steps = False
            continue

        lower = stripped.lower()
        if lower.startswith("route:"):
            route = stripped.split(":", 1)[1].strip()
            collecting_steps = False
        elif lower.startswith("aliases:"):
            aliases = list(_parse_list_field(stripped.split(":", 1)[1]))
            collecting_steps = False
        elif lower.startswith("prerequisites:"):
            prerequisites = [stripped.split(":", 1)[1].strip()]
            collecting_steps = False
        elif lower == "steps:":
            collecting_steps = True
        elif collecting_steps and re.match(r"^\d+\.\s+", stripped):
            steps.append(re.sub(r"^\d+\.\s+", "", stripped))
        elif lower.startswith("outcome:"):
            outcome = stripped.split(":", 1)[1].strip()
            collecting_steps = False
        elif lower.startswith("limitations:"):
            limitations = stripped.split(":", 1)[1].strip()
            collecting_steps = False
        else:
            collecting_steps = False
            body.append(stripped)

    flush()
    return tuple(chunks)


def _alias_tokens(chunk: HelpChunk) -> set[str]:
    tokens: set[str] = set()
    for alias in chunk.aliases:
        tokens |= _tokens(alias)
    return tokens


def _score_chunk(query_tokens: set[str], chunk: HelpChunk) -> tuple[int, int, int]:
    title_tokens = _tokens(chunk.title)
    alias_tokens = _alias_tokens(chunk)
    body_tokens = _tokens(chunk.searchable_text)
    strong_query = {token for token in query_tokens if token not in _WEAK_QUERY_WORDS}
    weak_query = query_tokens & _WEAK_QUERY_WORDS

    title_hits = len(strong_query & title_tokens) + len(weak_query & title_tokens)
    alias_hits = len(strong_query & alias_tokens)
    body_hits = len(strong_query & body_tokens)
    weak_body_hits = len(weak_query & body_tokens)

    score = (
        8 * len(strong_query & title_tokens)
        + 7 * alias_hits
        + 3 * body_hits
        + 1 * len(weak_query & title_tokens)
        + 1 * weak_body_hits
    )
    # Prefer dedicated feature chunks over the unsupported catch-all when both match.
    if chunk.unsupported:
        score = max(score - 2, 0)
    return score, alias_hits + title_hits, alias_hits


def retrieve(question: str, limit: int = 3) -> list[HelpChunk]:
    return list(retrieve_with_meta(question, limit=limit).chunks)


def retrieve_with_meta(question: str, limit: int = 3) -> RetrievalResult:
    chunks = load_chunks()
    help_chunk = next((chunk for chunk in chunks if chunk.title == _HELP_TITLE), None)
    unsupported_chunk = next((chunk for chunk in chunks if chunk.unsupported), None)
    query_tokens = _tokens(question)

    if not query_tokens:
        fallback = tuple(chunk for chunk in (help_chunk,) if chunk) or chunks[:1]
        return RetrievalResult(fallback, False, 0)

    scored: list[tuple[int, int, int, HelpChunk]] = []
    for chunk in chunks:
        score, feature_hits, alias_hits = _score_chunk(query_tokens, chunk)
        if score:
            scored.append((score, feature_hits, alias_hits, chunk))

    scored.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3].title))
    if not scored or scored[0][0] < _MIN_SCORE:
        fallback = unsupported_chunk or help_chunk
        if fallback:
            return RetrievalResult((fallback,), True, scored[0][0] if scored else 0)
        return RetrievalResult(tuple(chunks[:1]), True, 0)

    top = [item for item in scored if item[0] >= _MIN_SCORE][:limit]
    selected = tuple(chunk for _, _, _, chunk in top)
    unsupported = bool(selected and selected[0].unsupported)
    return RetrievalResult(selected, unsupported, top[0][0])


def format_context(chunks: Iterable[HelpChunk]) -> str:
    blocks: List[str] = []
    for chunk in chunks:
        lines = [f"[{chunk.title}]", f"Route: {chunk.route}"]
        if chunk.aliases:
            lines.append("Aliases: " + ", ".join(chunk.aliases))
        if chunk.prerequisites:
            lines.append("Prerequisites: " + " ".join(chunk.prerequisites))
        if chunk.steps:
            lines.append("Steps:")
            lines.extend(f"{index}. {step}" for index, step in enumerate(chunk.steps, start=1))
        if chunk.outcome:
            lines.append(f"Outcome: {chunk.outcome}")
        if chunk.limitations:
            lines.append(f"Limitations: {chunk.limitations}")
        if chunk.content and not chunk.steps:
            lines.append(chunk.content)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
