import asyncio
import json
import os
from pathlib import Path
from urllib import error, request

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db import SessionLocal
from app.logic.transcript_manager import transcript_manager

router = APIRouter(prefix="/websocket", tags=["websocket"])

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.1")
OPENAI_SYSTEM_PROMPT = (
    "You are a helpful, concise phone agent for patient appointment reminder "
    "calls. Keep responses brief, natural, and easy to understand over the phone."
)


def extract_transcript_message(payload: dict) -> tuple[str, str] | None:
    content = (
        payload.get("transcript")
        or payload.get("content")
        or payload.get("text")
        or payload.get("message")
    )
    if not isinstance(content, str):
        return None

    raw_role = payload.get("role") or payload.get("speaker") or payload.get("source")
    role = str(raw_role or "agent").lower()
    if role in {"user", "patient", "caller"}:
        role = "user"
    else:
        role = "agent"

    return role, content


def should_persist_transcript(payload: dict) -> bool:
    return bool(
        payload.get("end_call")
        or payload.get("call_ended")
        or payload.get("event") in {"call_ended", "call_finished"}
    )


def is_response_required(payload: dict) -> bool:
    return payload.get("interaction_type") == "response_required"


def load_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() == "OPENAI_API_KEY":
                api_key = value.strip().strip("\"'")
                if api_key:
                    os.environ["OPENAI_API_KEY"] = api_key
                    return api_key

    raise RuntimeError("OPENAI_API_KEY is not configured")


def normalize_transcript_role(raw_role: str | None) -> str:
    role = str(raw_role or "agent").lower()
    if role in {"user", "patient", "caller"}:
        return "user"
    return "assistant"


def extract_transcript_messages(payload: dict) -> list[dict[str, str]]:
    transcript = payload.get("transcript")
    if not isinstance(transcript, list):
        transcript_message = extract_transcript_message(payload)
        if transcript_message is None:
            return []

        role, content = transcript_message
        return [{"role": "user" if role == "user" else "assistant", "content": content}]

    messages: list[dict[str, str]] = []
    for item in transcript:
        if not isinstance(item, dict):
            continue

        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            continue

        messages.append(
            {
                "role": normalize_transcript_role(item.get("role")),
                "content": content.strip(),
            }
        )

    return messages


async def generate_openai_response(messages: list[dict[str, str]]) -> str:
    return await asyncio.to_thread(generate_openai_response_sync, messages)


def generate_openai_response_sync(messages: list[dict[str, str]]) -> str:
    api_key = load_openai_api_key()
    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = json.dumps(
        {
            "model": OPENAI_MODEL,
            "instructions": OPENAI_SYSTEM_PROMPT,
            "input": messages,
            "max_output_tokens": 120,
        }
    ).encode("utf-8")

    openai_request = request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(openai_request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8")
        raise RuntimeError(f"OpenAI API error: {error_body}") from exc

    response = extract_openai_text(data)
    return response or "I am sorry, I did not catch that. Could you repeat it?"


def extract_openai_text(payload: dict) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return output_text.strip()

    chunks: list[str] = []
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue

            content = item.get("content")
            if not isinstance(content, list):
                continue

            for content_item in content:
                if not isinstance(content_item, dict):
                    continue

                text = content_item.get("text")
                if isinstance(text, str):
                    chunks.append(text)

    return "".join(chunks).strip()


async def retell_agent_websocket(websocket: WebSocket, call_id: str):
    await websocket.accept()

    first_event = {
        "response_id": 0,
        "content": "How may I help you?",
        "content_complete": True,
        "end_call": False,
    }
    await websocket.send_text(json.dumps(first_event))
    await transcript_manager.publish(call_id, "agent", first_event["content"])

    try:
        while True:
            message = await websocket.receive_text()
            request = json.loads(message)
            print(request)
            transcript = request.get("transcript")
            if isinstance(transcript, list):
                await transcript_manager.replace_transcript(call_id, transcript)
            else:
                transcript_message = extract_transcript_message(request)
                if transcript_message is not None:
                    role, content = transcript_message
                    await transcript_manager.publish(call_id, role, content)

            if should_persist_transcript(request):
                break

            if is_response_required(request):
                messages = extract_transcript_messages(request)
                response_content = await generate_openai_response(messages)
                response_event = {
                    "response_id": request.get("response_id"),
                    "content": response_content,
                    "content_complete": True,
                    "end_call": False,
                }
                await websocket.send_text(json.dumps(response_event))
                await transcript_manager.publish(call_id, "agent", response_content)
    except WebSocketDisconnect:
        pass
    finally:
        db = SessionLocal()
        try:
            transcript_manager.persist(call_id, db)
        finally:
            db.close()


@router.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    await retell_agent_websocket(websocket, call_id)


@router.websocket("/live-transcript/{call_id}")
async def live_transcript(websocket: WebSocket, call_id: str):
    await transcript_manager.connect(call_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        transcript_manager.disconnect(call_id, websocket)


@router.websocket("/agent-websocket/{call_id}")
async def agent_websocket(websocket: WebSocket, call_id: str):
    await retell_agent_websocket(websocket, call_id)