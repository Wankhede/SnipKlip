from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.throttles import AssistantRateThrottle

from .llm import generate_answer
from .retrieval import retrieve
from .safety import REFUSAL_MESSAGE, inspect_question, sanitize_answer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AssistantRateThrottle])
def ask_assistant(request):
    safety = inspect_question(
        request.data.get("question"),
        settings.ASSISTANT_MAX_QUESTION_LENGTH,
    )
    if not safety.question:
        return Response(
            {"message": "Question is required.", "status": status.HTTP_400_BAD_REQUEST},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if safety.refused:
        return Response({
            "data": {
                "answer": REFUSAL_MESSAGE,
                "refused": True,
                "redacted": False,
                "provider": "safety",
                "sources": [],
            },
            "message": "Sensitive request refused.",
            "status": status.HTTP_200_OK,
        })

    chunks = retrieve(safety.question)
    answer = generate_answer(safety.question, chunks)
    return Response({
        "data": {
            "answer": sanitize_answer(answer.text),
            "refused": False,
            "redacted": safety.redacted,
            "provider": answer.provider,
            "sources": [
                {"title": chunk.title, "route": chunk.route}
                for chunk in chunks
            ],
        },
        "message": "Answer generated.",
        "status": status.HTTP_200_OK,
    })
