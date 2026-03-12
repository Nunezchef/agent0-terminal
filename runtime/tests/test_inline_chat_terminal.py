import importlib
import importlib.util
import sys
import threading
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class InlineChatTerminalTemplateTests(unittest.TestCase):
    def test_chat_bottom_actions_include_terminal_button(self) -> None:
        template_path = (
            PROJECT_ROOT / "webui" / "components" / "chat" / "input" / "bottom-actions.html"
        )
        content = template_path.read_text(encoding="utf-8")
        self.assertIn('id="chat_terminal"', content)
        self.assertIn(">Terminal</p>", content)
        self.assertIn("$store.chatInput.openTerminal()", content)
        self.assertNotIn('id="chat_terminal_log"', content)

    def test_input_store_opens_terminal_modal(self) -> None:
        template_path = PROJECT_ROOT / "webui" / "components" / "chat" / "input" / "input-store.js"
        content = template_path.read_text(encoding="utf-8")
        self.assertIn(
            'openModal("modals/terminal/terminal.html")',
            content,
        )
        self.assertNotIn('callJsonApi("/terminal_log_insert"', content)
        self.assertNotIn("appendTerminalLogToChat", content)

    def test_terminal_modal_imports_modal_store(self) -> None:
        modal_path = PROJECT_ROOT / "webui" / "components" / "modals" / "terminal" / "terminal.html"
        content = modal_path.read_text(encoding="utf-8")
        self.assertIn(
            'import { store as terminalStore } from "/components/modals/terminal/terminal-store.js";',
            content,
        )
        self.assertIn('class="terminal-actions"', content)
        self.assertIn('title="Clear terminal"', content)
        self.assertIn('title="Restart session"', content)
        self.assertIn('title="Kill session"', content)
        self.assertIn('title="Insert terminal log"', content)
        self.assertIn('title="Mobile keys"', content)
        self.assertIn("$store.terminalModal.killSession()", content)
        self.assertIn("$store.terminalModal.insertTerminalLog()", content)
        self.assertIn("$store.terminalModal.toggleMobileKeys()", content)
        self.assertIn("x-show=\"$store.terminalModal.mobileKeysOpen\"", content)
        self.assertIn("$store.terminalModal.sendSpecialKey('arrow_up')", content)
        self.assertIn("$store.terminalModal.sendSpecialKey('enter')", content)
        self.assertIn("$store.terminalModal.sendSpecialKey('space')", content)
        self.assertNotIn('data-modal-footer', content)

    def test_terminal_modal_store_uses_terminal_api(self) -> None:
        store_path = PROJECT_ROOT / "webui" / "components" / "modals" / "terminal" / "terminal-store.js"
        content = store_path.read_text(encoding="utf-8")
        self.assertIn('createStore("terminalModal"', content)
        self.assertIn('getNamespacedClient("/terminal")', content)
        self.assertIn('/vendor/xterm/xterm.js', content)
        self.assertNotIn("cdn.jsdelivr.net", content)
        self.assertIn("folderPath", content)
        self.assertIn('container.addEventListener("mousedown"', content)
        self.assertIn("requestAnimationFrame(() => this.terminal?.focus())", content)
        self.assertIn("const xtermModulePromise = import(XTERM_URL);", content)
        self.assertIn("const fitAddonModulePromise = import(FIT_ADDON_URL);", content)
        self.assertIn("this.terminal.clear();", content)
        self.assertNotIn("await this.detach();", content)
        self.assertIn('"terminal_restart"', content)
        self.assertIn('"terminal_kill"', content)
        self.assertIn('"terminal_resize"', content)
        self.assertIn("term.onResize", content)
        self.assertIn("this.sendResize()", content)
        self.assertIn('"terminal_exit"', content)
        self.assertIn("window.closeModal()", content)
        self.assertIn('callJsonApi("/terminal_log_insert"', content)
        self.assertIn("drawMessageToolSimple({", content)
        self.assertIn("Terminal history from the current chat terminal session:", content)
        self.assertIn('addEventListener("pointerenter"', content)
        self.assertIn('addEventListener("pointerleave"', content)
        self.assertIn('addEventListener("touchstart"', content)
        self.assertIn('addEventListener("touchend"', content)
        self.assertIn("setPageScrollLock(true)", content)
        self.assertIn("setPageScrollLock(false)", content)
        self.assertIn('addEventListener("keydown"', content)
        self.assertIn("navigator.clipboard.writeText", content)
        self.assertIn("navigator.clipboard.readText", content)
        self.assertIn("this.terminal.selectAll()", content)
        self.assertIn('window.localStorage?.getItem("darkMode")', content)
        self.assertIn("new MutationObserver", content)
        self.assertIn("applyTerminalTheme()", content)
        self.assertIn("mobileKeysOpen", content)
        self.assertIn("toggleMobileKeys()", content)
        self.assertIn("sendSpecialKey(key)", content)
        self.assertIn("arrow_up", content)
        self.assertIn("space", content)
        self.assertIn("ctrl_c", content)
        self.assertIn("this.socketClient.emit(\"terminal_input\", { input })", content)
        self.assertIn("brightGreen", content)
        self.assertIn("brightBlue", content)

    def test_terminal_websocket_handler_exists(self) -> None:
        handler_path = PROJECT_ROOT / "python" / "websocket_handlers" / "terminal_handler.py"
        content = handler_path.read_text(encoding="utf-8")
        self.assertIn("class TerminalHandler(WebSocketHandler):", content)
        self.assertIn("terminal_open", content)
        self.assertIn("terminal_input", content)
        self.assertIn("terminal_output", content)
        self.assertIn("terminal_restart", content)
        self.assertIn("terminal_kill", content)
        self.assertIn("terminal_exit", content)
        self.assertIn("terminal_resize", content)
        self.assertIn("LocalInteractiveSession(cwd=base_path, echo=True, cols=cols, rows=rows)", content)
        self.assertIn('self.sessions: dict[str, dict[str, Any]] = {}', content)
        self.assertIn('self.sid_to_session: dict[str, str] = {}', content)
        self.assertIn('"attached_sids": set()', content)
        self.assertIn('"output_history":', content)
        self.assertIn("await record[\"shell\"].resize(cols=cols, rows=rows)", content)

    def test_terminal_log_tool_exists(self) -> None:
        tool_path = PROJECT_ROOT / "python" / "tools" / "terminal_log.py"
        content = tool_path.read_text(encoding="utf-8")
        self.assertIn("class TerminalLog(Tool):", content)
        self.assertIn("terminal", content)

    def test_terminal_log_insert_api_exists(self) -> None:
        api_path = PROJECT_ROOT / "python" / "api" / "terminal_log_insert.py"
        content = api_path.read_text(encoding="utf-8")
        self.assertIn("class TerminalLogInsert(ApiHandler):", content)
        self.assertIn("TerminalLog(", content)
        self.assertIn('"tool": "TerminalLog"', content)
        self.assertIn('"mode": mode', content)
        self.assertIn('"content": content', content)
        self.assertIn('agent.hist_add_message(False, content={', content)

    def test_terminal_modal_uses_agent_zero_theme_tokens(self) -> None:
        modal_path = PROJECT_ROOT / "webui" / "components" / "modals" / "terminal" / "terminal.html"
        content = modal_path.read_text(encoding="utf-8")
        self.assertIn("var(--color-background)", content)
        self.assertIn("var(--color-border)", content)
        self.assertIn("var(--color-primary)", content)
        self.assertIn("--terminal-bg", content)
        self.assertIn("--terminal-fg", content)
        self.assertIn(".terminal-mobile-keys", content)
        self.assertIn(".terminal-mobile-key", content)
        self.assertIn(".terminal-xterm .xterm-viewport", content)
        self.assertIn("background-color: var(--terminal-bg) !important;", content)
        self.assertIn("overscroll-behavior: contain;", content)
        self.assertIn('/vendor/xterm/xterm.css', content)
        self.assertNotIn("background: #0d1117;", content)

    def test_local_interactive_session_supports_echo_flag(self) -> None:
        path = PROJECT_ROOT / "python" / "helpers" / "shell_local.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("def __init__(self, cwd: str|None = None, echo: bool = False, cols: int = 120, rows: int = 32):", content)
        self.assertIn("cols=self.cols", content)
        self.assertIn("rows=self.rows", content)
        self.assertIn("async def resize(self, cols: int, rows: int):", content)

    def test_tty_session_has_terminal_defaults_and_resize(self) -> None:
        path = PROJECT_ROOT / "python" / "helpers" / "tty_session.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn('self.env.setdefault("TERM", "xterm-256color")', content)
        self.assertIn('self.env.setdefault("COLORTERM", "truecolor")', content)
        self.assertIn("async def resize(self, cols: int, rows: int):", content)
        self.assertIn("def is_alive(self):", content)
        self.assertIn("fcntl.ioctl", content)


class InlineChatTerminalApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_terminal_api_proxies_terminal_runtime(self) -> None:
        terminal_path = PROJECT_ROOT / "python" / "api" / "terminal.py"
        api_stub = types.ModuleType("python.helpers.api")
        code_exec_stub = types.ModuleType("python.tools.code_execution_tool")

        class FakeApiHandler:
            def __init__(self, app, thread_lock):
                self.app = app
                self.thread_lock = thread_lock

        api_stub.ApiHandler = FakeApiHandler
        api_stub.Request = object
        code_exec_stub.CodeExecution = object

        saved_api = sys.modules.get("python.helpers.api")
        saved_code_exec = sys.modules.get("python.tools.code_execution_tool")
        sys.modules["python.helpers.api"] = api_stub
        sys.modules["python.tools.code_execution_tool"] = code_exec_stub

        try:
            spec = importlib.util.spec_from_file_location(
                "test_inline_terminal_api_module",
                terminal_path,
            )
            terminal_module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(terminal_module)
        finally:
            if saved_api is None:
                del sys.modules["python.helpers.api"]
            else:
                sys.modules["python.helpers.api"] = saved_api
            if saved_code_exec is None:
                del sys.modules["python.tools.code_execution_tool"]
            else:
                sys.modules["python.tools.code_execution_tool"] = saved_code_exec

        calls: list[dict[str, object]] = []

        class FakeCodeExecution:
            def __init__(self, agent, name, method, args, message, loop_data, **kwargs):
                self._call = {
                    "agent": agent,
                    "name": name,
                    "method": method,
                    "args": args,
                    "message": message,
                }
                calls.append(self._call)

            def get_log_object(self):
                return "fake-log"

            async def execute(self, **kwargs):
                self._call["log"] = self.log
                self._call["kwargs"] = kwargs
                return SimpleNamespace(message="shell output", additional=None)

        handler = terminal_module.Terminal(app=None, thread_lock=threading.RLock())
        state = {}

        class FakeAgent:
            def get_data(self, key):
                return state.get(key)

            def set_data(self, key, value):
                state[key] = value

        handler.use_context = lambda ctxid, create_if_not_exists=True: SimpleNamespace(agent0=FakeAgent())
        terminal_module.CodeExecution = FakeCodeExecution

        response = await handler.process(
            {
                "ctxid": "ctx-1",
                "action": "command",
                "session": 7,
                "command": "pwd",
                "path": "/tmp/project",
            },
            None,
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["session"], 7)
        self.assertEqual(response["output"], "shell output")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["name"], "code_execution_tool")
        self.assertEqual(calls[0]["log"], "fake-log")
        self.assertEqual(calls[0]["args"]["runtime"], "terminal")
        self.assertEqual(calls[0]["args"]["session"], 7001)
        self.assertTrue(calls[0]["args"]["reset"])
        self.assertIn("cd /tmp/project && pwd", calls[0]["args"]["code"])
        self.assertEqual(
            calls[1]["args"],
            {
                "runtime": "reset",
                "session": 7001,
                "reset": True,
            },
        )

    async def test_terminal_log_condenses_noisy_output_chunks(self) -> None:
        tool_path = PROJECT_ROOT / "python" / "tools" / "terminal_log.py"
        files_stub = types.ModuleType("python.helpers.files")
        projects_stub = types.ModuleType("python.helpers.projects")
        settings_stub = types.ModuleType("python.helpers.settings")
        tool_stub = types.ModuleType("python.helpers.tool")

        files_stub.normalize_a0_path = lambda value: value
        projects_stub.get_context_project_name = lambda context: None

        class FakeResponse:
            def __init__(self, message, break_loop, additional=None):
                self.message = message
                self.break_loop = break_loop
                self.additional = additional

        class FakeTool:
            def __init__(self, agent, name, method, args, message, loop_data, **kwargs):
                self.agent = agent

        settings_root = {}
        settings_stub.get_settings = lambda: {"workdir_path": settings_root["path"]}
        tool_stub.Tool = FakeTool
        tool_stub.Response = FakeResponse

        saved_files = sys.modules.get("python.helpers.files")
        saved_projects = sys.modules.get("python.helpers.projects")
        saved_settings = sys.modules.get("python.helpers.settings")
        saved_tool = sys.modules.get("python.helpers.tool")
        sys.modules["python.helpers.files"] = files_stub
        sys.modules["python.helpers.projects"] = projects_stub
        sys.modules["python.helpers.settings"] = settings_stub
        sys.modules["python.helpers.tool"] = tool_stub

        try:
            spec = importlib.util.spec_from_file_location(
                "test_terminal_log_module",
                tool_path,
            )
            terminal_log_module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(terminal_log_module)
        finally:
            if saved_files is None:
                del sys.modules["python.helpers.files"]
            else:
                sys.modules["python.helpers.files"] = saved_files
            if saved_projects is None:
                del sys.modules["python.helpers.projects"]
            else:
                sys.modules["python.helpers.projects"] = saved_projects
            if saved_settings is None:
                del sys.modules["python.helpers.settings"]
            else:
                sys.modules["python.helpers.settings"] = saved_settings
            if saved_tool is None:
                del sys.modules["python.helpers.tool"]
            else:
                sys.modules["python.helpers.tool"] = saved_tool

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_root["path"] = tmpdir
            log_dir = Path(tmpdir) / "terminal" / "ctx-1"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "session-20260303T033955Z.log"
            log_path.write_text(
                "\n".join(
                    [
                        "[SESSION START] 20260303T033955Z cwd=/a0/usr/workdir",
                        "[OUTPUT] Workin",
                        "[OUTPUT] •",
                        "[OUTPUT] Working",
                        "[OUTPUT] Working",
                        "[OUTPUT] orking",
                        "[OUTPUT] Preparing to invoke skill (4s • esc to interrupt)",
                        "[OUTPUT] P",
                        "[OUTPUT] Pr",
                        '[COMMAND] print("Hello, world!")',
                        "[OUTPUT] Hello, world!",
                        "[VIEWER DETACH] reason=client_close",
                    ]
                ),
                encoding="utf-8",
            )

            tool = terminal_log_module.TerminalLog(
                SimpleNamespace(context=SimpleNamespace(id="ctx-1")),
                "TerminalLog",
                None,
                {},
                "",
                None,
            )
            result = await tool.execute(mode="latest")

        self.assertIn("Working", result.message)
        self.assertIn("Preparing to invoke skill", result.message)
        self.assertIn('[COMMAND] print("Hello, world!")', result.message)
        self.assertIn("Hello, world!", result.message)
        self.assertNotIn("[OUTPUT]", result.message)
        self.assertNotIn("[VIEWER DETACH]", result.message)
