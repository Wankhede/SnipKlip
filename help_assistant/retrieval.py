import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List


_GUIDE_PATH = Path(__file__).resolve().parent / "knowledge" / "app_guide.md"
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a", "an", "and", "are", "can", "do", "for", "how", "i", "in", "is",
    "it", "my", "of", "on", "the", "to", "use", "what", "where", "with",
}


@dataclass(frozen=True)
class HelpChunk:
    title: str
    route: str
    content: str


def _tokens(text: str) -> set[str]:
    return {
        token for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in _STOP_WORDS and len(token) > 1
    }


@lru_cache(maxsize=1)
def load_chunks() -> tuple[HelpChunk, ...]:
    chunks: List[HelpChunk] = []
    title = ""
    route = ""
    body: List[str] = []

    for line in _GUIDE_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if title and body:
                chunks.append(HelpChunk(title, route, "\n".join(body).strip()))
            title = line[3:].strip()
            route = ""
            body = []
        elif line.startswith("Route: "):
            route = line[7:].strip()
        elif title and line.strip():
            body.append(line.strip())

    if title and body:
        chunks.append(HelpChunk(title, route, "\n".join(body).strip()))
    return tuple(chunks)


def retrieve(question: str, limit: int = 3) -> list[HelpChunk]:
    query_tokens = _tokens(question)
    if not query_tokens:
        return list(load_chunks()[:limit])

    scored: list[tuple[int, HelpChunk]] = []
    for chunk in load_chunks():
        title_tokens = _tokens(chunk.title)
        body_tokens = _tokens(chunk.content)
        score = 4 * len(query_tokens & title_tokens) + len(query_tokens & body_tokens)
        if score:
            scored.append((score, chunk))

    scored.sort(key=lambda item: (-item[0], item[1].title))
    if not scored:
        return [chunk for chunk in load_chunks() if chunk.title == "Getting Help"][:1]
    return [chunk for _, chunk in scored[:limit]]


def format_context(chunks: Iterable[HelpChunk]) -> str:
    return "\n\n".join(
        f"[{chunk.title}]\nRoute: {chunk.route}\n{chunk.content}"
        for chunk in chunks
    )
