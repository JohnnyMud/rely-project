import json
from datetime import datetime, timezone

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models import CallAttempts, Transcripts


class TranscriptManager:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[WebSocket]] = {}
        self._messages: dict[str, list[dict[str, str]]] = {}

    async def connect(self, call_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._subscribers.setdefault(call_id, set()).add(websocket)
        for message in self._messages.get(call_id, []):
            await websocket.send_json(message)

    def disconnect(self, call_id: str, websocket: WebSocket) -> None:
        subscribers = self._subscribers.get(call_id)
        if not subscribers:
            return
        subscribers.discard(websocket)
        if not subscribers:
            self._subscribers.pop(call_id, None)

    async def publish(self, call_id: str, role: str, content: str) -> None:
        if not content:
            return

        message = {
            "call_id": call_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._messages.setdefault(call_id, []).append(message)

        stale_connections: list[WebSocket] = []
        for websocket in self._subscribers.get(call_id, set()):
            try:
                await websocket.send_json(message)
            except Exception:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            self.disconnect(call_id, websocket)

    async def replace_transcript(self, call_id: str, transcript: list[dict]) -> None:
        messages: list[dict[str, str]] = []
        previous_messages = self._messages.get(call_id, [])

        for index, item in enumerate(transcript):
            content = item.get("content")
            if not isinstance(content, str) or not content:
                continue

            role = str(item.get("role") or "agent").lower()
            if role in {"user", "patient", "caller"}:
                role = "user"
            else:
                role = "agent"

            previous_timestamp = (
                previous_messages[index].get("timestamp")
                if index < len(previous_messages)
                else None
            )
            messages.append(
                {
                    "call_id": call_id,
                    "role": role,
                    "content": content,
                    "timestamp": previous_timestamp
                    or datetime.now(timezone.utc).isoformat(),
                }
            )

        self._messages[call_id] = messages

        if messages != previous_messages:
            await self._broadcast_snapshot(call_id, messages)

    async def _broadcast_snapshot(
        self, call_id: str, messages: list[dict[str, str]]
    ) -> None:
        stale_connections: list[WebSocket] = []
        for websocket in self._subscribers.get(call_id, set()):
            try:
                await websocket.send_json(
                    {
                        "call_id": call_id,
                        "type": "transcript_snapshot",
                        "messages": messages,
                    }
                )
            except Exception:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            self.disconnect(call_id, websocket)

    async def _broadcast(self, call_id: str, message: dict[str, str]) -> None:
        stale_connections: list[WebSocket] = []
        for websocket in self._subscribers.get(call_id, set()):
            try:
                await websocket.send_json(message)
            except Exception:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            self.disconnect(call_id, websocket)

    def persist(self, call_id: str, db: Session) -> None:
        messages = self._messages.get(call_id, [])
        if not messages:
            return

        call_attempt = (
            db.query(CallAttempts)
            .filter(CallAttempts.retell_call_id == call_id)
            .first()
        )
        if call_attempt is None:
            return

        transcript_text = json.dumps(messages)
        transcript = db.query(Transcripts).filter(Transcripts.call_id == call_id).first()
        if transcript is None:
            transcript = Transcripts(
                call_id=call_id,
                patient_id=call_attempt.patient_id,
                transcript=transcript_text,
            )
            db.add(transcript)
        else:
            transcript.patient_id = call_attempt.patient_id
            transcript.transcript = transcript_text

        db.commit()


transcript_manager = TranscriptManager()
