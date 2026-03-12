import shlex

from python.helpers.api import ApiHandler, Request
from python.tools.code_execution_tool import CodeExecution


class Terminal(ApiHandler):
    EXEC_COUNTER_KEY = "_terminal_exec_counter"
    SESSION_PATHS_KEY = "_terminal_session_paths"

    async def _run_code_execution(self, agent, args: dict) -> str:
        tool = CodeExecution(agent, "code_execution_tool", None, args, "", None)
        tool.log = tool.get_log_object()
        result = await tool.execute()
        return result.message

    def _next_execution_session(self, agent, session: int) -> int:
        counter = int(agent.get_data(self.EXEC_COUNTER_KEY) or 0) + 1
        agent.set_data(self.EXEC_COUNTER_KEY, counter)
        return session * 1000 + counter

    async def process(self, input: dict, request: Request) -> dict:
        ctxid = str(input.get("ctxid", ""))
        action = str(input.get("action", "command")).strip().lower()
        session = int(input.get("session", 0))
        command = str(input.get("command", ""))
        path = str(input.get("path", "")).strip()

        context = self.use_context(ctxid)
        agent = context.agent0
        session_paths = dict(agent.get_data(self.SESSION_PATHS_KEY) or {})

        if action == "command":
            if path:
                session_paths[session] = path
                agent.set_data(self.SESSION_PATHS_KEY, session_paths)

            working_path = session_paths.get(session, "")
            exec_session = self._next_execution_session(agent, session)
            exec_command = command
            if working_path:
                exec_command = f"cd {shlex.quote(working_path)} && {command}"

            args = {
                "runtime": "terminal",
                "session": exec_session,
                "code": exec_command,
                "reset": True,
            }
            try:
                output = await self._run_code_execution(agent, args)
            finally:
                await self._run_code_execution(
                    agent,
                    {
                        "runtime": "reset",
                        "session": exec_session,
                        "reset": True,
                    },
                )

            return {
                "ok": True,
                "session": session,
                "action": action,
                "output": output,
            }
        elif action == "output":
            return {
                "ok": True,
                "session": session,
                "action": action,
                "output": "",
            }
        elif action == "reset":
            session_paths.pop(session, None)
            agent.set_data(self.SESSION_PATHS_KEY, session_paths)
            return {
                "ok": True,
                "session": session,
                "action": action,
                "output": "",
            }
        else:
            return {
                "ok": False,
                "session": session,
                "output": "",
                "error": f"Unsupported terminal action: {action}",
            }
