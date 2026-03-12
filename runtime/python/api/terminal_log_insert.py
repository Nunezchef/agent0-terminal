from pathlib import Path

from python.helpers.api import ApiHandler, Request
from python.helpers import files, projects, settings
from python.tools.terminal_log import TerminalLog


class TerminalLogInsert(ApiHandler):
    def _terminal_dir(self, agent) -> Path:
        context = agent.context
        project_name = projects.get_context_project_name(context)
        if project_name:
            base = files.normalize_a0_path(projects.get_project_folder(project_name))
        else:
            base = settings.get_settings()["workdir_path"]
        return Path(base) / "terminal" / context.id

    async def process(self, input: dict, request: Request) -> dict:
        ctxid = str(input.get("ctxid", ""))
        mode = str(input.get("mode", "tail") or "tail").lower()
        lines = max(1, int(input.get("lines", 100) or 100))
        session = str(input.get("session", "") or "")

        context = self.use_context(ctxid)
        agent = context.agent0

        tool = TerminalLog(agent, "TerminalLog", None, {"mode": mode, "lines": str(lines)}, "", None)
        result = await tool.execute(mode=mode, lines=lines, session=session)
        content = str(result.message or "(empty)")

        selected_session = session
        if not selected_session:
            logs = sorted(self._terminal_dir(agent).glob("session-*.log"))
            if logs:
                selected_session = logs[-1].name

        agent.hist_add_message(False, content={
            "tool_name": "TerminalLog",
            "tool_result": (
                "Terminal history from the current chat terminal session:\n"
                f"Session: {selected_session or '(latest)'}\n"
                f"Mode: {mode} ({lines} lines)\n\n"
                f"{content}"
            ),
            "mode": mode,
            "lines": lines,
            "session": selected_session,
        })

        return {
            "ok": True,
            "tool": "TerminalLog",
            "mode": mode,
            "lines": lines,
            "session": selected_session,
            "content": content,
        }
