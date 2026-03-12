from pathlib import Path

from python.helpers import files, projects, settings
from python.helpers.tool import Tool, Response


class TerminalLog(Tool):
    def _condense_output_lines(self, values: list[str]) -> list[str]:
        filtered: list[str] = []

        for raw in values:
            text = str(raw or "").strip()
            if not text:
                continue
            if text == "•":
                continue
            if text.startswith("•") and text[1:].strip().isdigit():
                continue

            if filtered:
                prev = filtered[-1]
                if text == prev:
                    continue
                if text.startswith(prev):
                    filtered[-1] = text
                    continue
                if prev.endswith(text) and len(text) <= max(12, len(prev) // 2):
                    continue

            filtered.append(text)

        return filtered

    def _render_terminal_log(self, content: str) -> str:
        rendered: list[str] = []
        output_buffer: list[str] = []

        def flush_output() -> None:
            nonlocal output_buffer
            if not output_buffer:
                return
            rendered.extend(self._condense_output_lines(output_buffer))
            output_buffer = []

        for line in content.splitlines():
            if line.startswith("[OUTPUT] "):
                output_buffer.append(line[len("[OUTPUT] ") :])
                continue

            flush_output()

            if line.startswith("[COMMAND] "):
                rendered.append(line)
                continue

            if line.startswith("[SESSION START]"):
                continue
            if line.startswith("[SESSION END]"):
                continue
            if line.startswith("[VIEWER DETACH]"):
                continue

            stripped = line.strip()
            if stripped:
                rendered.append(stripped)

        flush_output()
        return "\n".join(rendered)

    def _terminal_dir(self) -> Path:
        context = self.agent.context
        project_name = projects.get_context_project_name(context)
        if project_name:
            base = files.normalize_a0_path(projects.get_project_folder(project_name))
        else:
            base = settings.get_settings()["workdir_path"]
        return Path(base) / "terminal" / context.id

    async def execute(self, mode="latest", lines=200, session="", **kwargs):
        terminal_dir = self._terminal_dir()
        if not terminal_dir.exists():
            return Response(message="No terminal logs found.", break_loop=False)

        logs = sorted(terminal_dir.glob("session-*.log"))
        if not logs:
            return Response(message="No terminal logs found.", break_loop=False)

        target = next((p for p in logs if p.name == session), None) if session else logs[-1]
        if not target:
            return Response(message=f"Terminal log not found: {session}", break_loop=False)

        content = target.read_text(encoding="utf-8", errors="replace")
        selected_mode = str(mode or "latest").lower()

        if selected_mode == "list":
            return Response(
                message="\n".join(path.name for path in logs),
                break_loop=False,
            )

        lines_int = max(1, int(lines))
        if selected_mode == "tail":
            content = "\n".join(content.splitlines()[-lines_int:])
        elif selected_mode == "commands":
            content = "\n".join(
                line for line in content.splitlines() if line.startswith("[COMMAND]")
            )
        else:
            content = self._render_terminal_log(content)

        if selected_mode == "tail":
            content = self._render_terminal_log(content)

        return Response(message=content or "(empty)", break_loop=False)
