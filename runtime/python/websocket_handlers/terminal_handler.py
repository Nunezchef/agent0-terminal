from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any

from python.helpers.shell_local import LocalInteractiveSession
from python.helpers.shell_ssh import clean_string
from python.helpers.websocket import WebSocketHandler
from python.helpers import settings


class TerminalHandler(WebSocketHandler):
    MAX_HISTORY_CHARS = 200_000

    def __init__(self, socketio, lock) -> None:
        super().__init__(socketio, lock)
        self.sessions: dict[str, dict[str, Any]] = {}
        self.sid_to_session: dict[str, str] = {}

    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["terminal_open", "terminal_input", "terminal_close", "terminal_restart", "terminal_resize", "terminal_kill"]

    async def on_disconnect(self, sid: str) -> None:
        await self._detach_sid(sid, reason="disconnect")

    async def process_event(
        self, event_type: str, data: dict[str, Any], sid: str
    ):
        if event_type == "terminal_open":
            return await self._open_terminal(data, sid)
        if event_type == "terminal_input":
            return await self._send_input(data, sid)
        if event_type == "terminal_close":
            await self._detach_sid(sid, reason="client_close")
            return self.result_ok({"closed": True})
        if event_type == "terminal_restart":
            return await self._restart_terminal(data, sid)
        if event_type == "terminal_resize":
            return await self._resize_terminal(data, sid)
        if event_type == "terminal_kill":
            return await self._kill_terminal(sid)
        return self.result_error(
            code="UNSUPPORTED_EVENT",
            message=f"Unsupported terminal event: {event_type}",
        )

    async def _open_terminal(self, data: dict[str, Any], sid: str):
        await self._detach_sid(sid, reason="reopen")
        ctxid, base_path = self._resolve_context(data)
        cols, rows = self._resolve_size(data)
        session_key = self._make_session_key(ctxid, base_path)
        record = self.sessions.get(session_key)
        if not record:
            record = await self._create_session(ctxid, base_path, session_key, cols, rows)
        else:
            await record["shell"].resize(cols=cols, rows=rows)
            record["cols"] = cols
            record["rows"] = rows
        self._attach_sid(record, session_key, sid)
        return self.result_ok(self._session_payload(record))

    async def _restart_terminal(self, data: dict[str, Any], sid: str):
        await self._detach_sid(sid, reason="restart")
        ctxid, base_path = self._resolve_context(data)
        cols, rows = self._resolve_size(data)
        session_key = self._make_session_key(ctxid, base_path)
        await self._destroy_session(session_key, reason="restart")
        record = await self._create_session(ctxid, base_path, session_key, cols, rows)
        self._attach_sid(record, session_key, sid)
        return self.result_ok(self._session_payload(record))

    async def _send_input(self, data: dict[str, Any], sid: str):
        session_key = self.sid_to_session.get(sid)
        record = self.sessions.get(session_key or "")
        if not record:
            return self.result_error(
                code="NO_SESSION",
                message="Terminal session is not open",
            )

        payload = str(data.get("input", ""))
        if not payload:
            return self.result_ok({})

        self._record_input(record, payload)
        await record["shell"].send_input(payload)
        return self.result_ok({})

    async def _resize_terminal(self, data: dict[str, Any], sid: str):
        session_key = self.sid_to_session.get(sid)
        record = self.sessions.get(session_key or "")
        if not record:
            return self.result_error(
                code="NO_SESSION",
                message="Terminal session is not open",
            )

        try:
            cols = max(2, int(data.get("cols", 0)))
            rows = max(1, int(data.get("rows", 0)))
        except (TypeError, ValueError):
            return self.result_error(
                code="INVALID_SIZE",
                message="Terminal resize requires numeric cols and rows",
            )

        await record["shell"].resize(cols=cols, rows=rows)
        record["cols"] = cols
        record["rows"] = rows
        return self.result_ok({"cols": cols, "rows": rows})

    async def _kill_terminal(self, sid: str):
        session_key = self.sid_to_session.get(sid)
        if not session_key:
            return self.result_ok({"closed": True})

        record = self.sessions.get(session_key)
        if record:
            await self._emit_terminal_exit(record, reason="killed")
        await self._destroy_session(session_key, reason="killed")
        return self.result_ok({"closed": True})

    def _resolve_context(self, data: dict[str, Any]) -> tuple[str, str]:
        ctxid = str(data.get("ctxid", "")).strip() or "default"
        requested_path = str(data.get("path", "")).strip()
        base_path = requested_path or settings.get_settings()["workdir_path"]
        return ctxid, base_path

    def _make_session_key(self, ctxid: str, base_path: str) -> str:
        return f"{ctxid}::{base_path}"

    def _resolve_size(self, data: dict[str, Any]) -> tuple[int, int]:
        try:
            cols = max(2, int(data.get("cols", 120)))
            rows = max(1, int(data.get("rows", 32)))
        except (TypeError, ValueError):
            cols = 120
            rows = 32
        return cols, rows

    def _session_payload(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "opened": True,
            "path": record["path"],
            "log_path": record["log_path"],
            "output_history": record["output_history"],
        }

    async def _create_session(
        self, ctxid: str, base_path: str, session_key: str, cols: int, rows: int
    ) -> dict[str, Any]:
        terminal_dir = os.path.join(base_path, "terminal", ctxid)
        os.makedirs(terminal_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_path = os.path.join(terminal_dir, f"session-{timestamp}.log")

        shell = LocalInteractiveSession(cwd=base_path, echo=True, cols=cols, rows=rows)
        await shell.connect()

        record = {
            "ctxid": ctxid,
            "path": base_path,
            "log_path": log_path,
            "shell": shell,
            "reader_task": None,
            "input_buffer": "",
            "attached_sids": set(),
            "output_history": "",
            "cols": shell.cols,
            "rows": shell.rows,
        }
        self.sessions[session_key] = record
        self._write_log(record, f"[SESSION START] {timestamp} cwd={base_path}")
        record["reader_task"] = asyncio.create_task(self._pump_output(session_key))
        await shell.send_input("\n")
        return record

    def _attach_sid(self, record: dict[str, Any], session_key: str, sid: str) -> None:
        record["attached_sids"].add(sid)
        self.sid_to_session[sid] = session_key

    async def _detach_sid(self, sid: str, *, reason: str) -> None:
        session_key = self.sid_to_session.pop(sid, None)
        if not session_key:
            return
        record = self.sessions.get(session_key)
        if not record:
            return
        record["attached_sids"].discard(sid)
        self._write_log(record, f"[VIEWER DETACH] reason={reason}")

    async def _destroy_session(self, session_key: str, *, reason: str) -> None:
        record = self.sessions.pop(session_key, None)
        if not record:
            return

        for attached_sid in list(record["attached_sids"]):
            self.sid_to_session.pop(attached_sid, None)
        record["attached_sids"].clear()

        task = record.get("reader_task")
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._write_log(record, f"[SESSION END] reason={reason}")
        await record["shell"].close()

    async def _pump_output(self, session_key: str) -> None:
        while session_key in self.sessions:
            record = self.sessions.get(session_key)
            if not record:
                return

            chunk = await record["shell"].read_raw(timeout=0.2)
            if not chunk:
                if not record["shell"].is_alive():
                    await self._handle_process_exit(session_key)
                    return
                continue

            record["output_history"] = self._trim_output_history(
                f'{record["output_history"]}{chunk}'
            )
            for attached_sid in list(record["attached_sids"]):
                await self.emit_to(
                    attached_sid,
                    "terminal_output",
                    {"output": chunk},
                )

            cleaned = clean_string(chunk)
            if cleaned.strip():
                self._write_log(record, f"[OUTPUT] {cleaned}")

    async def _handle_process_exit(self, session_key: str) -> None:
        record = self.sessions.get(session_key)
        if not record:
            return
        await self._emit_terminal_exit(record, reason="process_exit")
        await self._destroy_session(session_key, reason="process_exit")

    async def _emit_terminal_exit(self, record: dict[str, Any], *, reason: str) -> None:
        for attached_sid in list(record["attached_sids"]):
            await self.emit_to(
                attached_sid,
                "terminal_exit",
                {"reason": reason},
            )

    def _trim_output_history(self, value: str) -> str:
        if len(value) <= self.MAX_HISTORY_CHARS:
            return value
        return value[-self.MAX_HISTORY_CHARS :]

    def _record_input(self, record: dict[str, Any], payload: str) -> None:
        buffer = str(record.get("input_buffer", ""))
        for char in payload:
            if char in ("\b", "\x7f"):
                buffer = buffer[:-1]
                continue
            if char in ("\r", "\n"):
                if buffer.strip():
                    self._write_log(record, f"[COMMAND] {buffer}")
                buffer = ""
                continue
            if char >= " " or char == "\t":
                buffer += char
        record["input_buffer"] = buffer

    def _write_log(self, record: dict[str, Any], line: str) -> None:
        with open(record["log_path"], "a", encoding="utf-8") as handle:
            handle.write(f"{line}\n")
