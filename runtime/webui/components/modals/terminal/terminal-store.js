import { createStore } from "/js/AlpineStore.js";
import * as shortcuts from "/js/shortcuts.js";
import { drawMessageToolSimple } from "/js/messages.js";
import { getNamespacedClient } from "/js/websocket.js";

const XTERM_URL = "/vendor/xterm/xterm.js";
const FIT_ADDON_URL = "/vendor/xterm/addon-fit.js";
const xtermModulePromise = import(XTERM_URL);
const fitAddonModulePromise = import(FIT_ADDON_URL);

const model = {
  isModalOpen: false,
  activeContextId: "",
  activeFolderPath: "",
  logPath: "",
  error: null,
  terminal: null,
  fitAddon: null,
  themeObserver: null,
  resizeObserver: null,
  socketClient: null,
  outputHandler: null,
  exitHandler: null,
  focusHandler: null,
  keydownTarget: null,
  keydownHandler: null,
  scrollGuardTarget: null,
  scrollLockTarget: null,
  pointerEnterHandler: null,
  pointerLeaveHandler: null,
  touchStartHandler: null,
  touchEndHandler: null,
  touchStartY: null,
  pageScrollLocked: false,
  resizeTimer: null,
  xtermReady: null,
  sessionActive: false,
  mobileKeysOpen: false,

  prepare({ ctxid, folderPath }) {
    this.activeContextId = ctxid || "";
    this.activeFolderPath = folderPath || "$WORK_DIR";
    this.logPath = "";
    this.error = null;
    this.sessionActive = false;
    this.mobileKeysOpen = false;
    this.pageScrollLocked = false;
  },

  async attach() {
    this.isModalOpen = true;
    this.error = null;
    try {
      await this.ensureTerminal();
      await this.requestSession("terminal_open");
    } catch (error) {
      this.error = error?.message || "Failed to start terminal";
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error opening terminal", error);
      }
    }
  },

  async detach() {
    this.isModalOpen = false;
    if (this.socketClient) {
      try {
        await this.socketClient.emit("terminal_close", {});
      } catch (_error) {
        // ignore close failures during teardown
      }
      if (this.outputHandler) {
        this.socketClient.off("terminal_output", this.outputHandler);
      }
      if (this.exitHandler) {
        this.socketClient.off("terminal_exit", this.exitHandler);
      }
      await this.socketClient.disconnect();
    }
    this.outputHandler = null;
    this.exitHandler = null;
    this.socketClient = null;
    this.logPath = "";
    this.sessionActive = false;
    this.mobileKeysOpen = false;
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    }
    if (this.themeObserver) {
      this.themeObserver.disconnect();
      this.themeObserver = null;
    }
    if (this.resizeTimer) {
      clearTimeout(this.resizeTimer);
      this.resizeTimer = null;
    }
    const container = document.getElementById("terminal-xterm");
    if (container && this.focusHandler) {
      container.removeEventListener("mousedown", this.focusHandler);
    }
    this.focusHandler = null;
    this.removeKeyboardShortcuts();
    this.removeScrollGuards();
    this.setPageScrollLock(false);
    if (this.terminal) {
      this.terminal.dispose();
      this.terminal = null;
    }
    this.fitAddon = null;
    this.xtermReady = null;
  },

  async ensureTerminal() {
    if (this.xtermReady) {
      await this.xtermReady;
      return;
    }

    this.xtermReady = (async () => {
      const container = document.getElementById("terminal-xterm");
      if (!container) {
        throw new Error("Terminal container not found");
      }

      const [{ Terminal }, { FitAddon }] = await Promise.all([
        xtermModulePromise,
        fitAddonModulePromise,
      ]);
      const term = new Terminal({
        cursorBlink: true,
        cursorStyle: "block",
        disableStdin: false,
        fontFamily: this.getTerminalFont(),
        fontSize: 13,
        convertEol: false,
        scrollback: 2000,
        theme: this.getTerminalTheme(),
      });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(container);
      fitAddon.fit();

      this.terminal = term;
      this.fitAddon = fitAddon;
      this.focusHandler = () => {
        this.focusTerminal();
      };
      container.addEventListener("mousedown", this.focusHandler);
      this.installKeyboardShortcuts(container);
      this.installScrollGuards(container);

      term.onData((input) => {
        if (!this.sessionActive) return;
        if (!this.socketClient?.isConnected()) return;
        this.socketClient.emit("terminal_input", { input }).catch((error) => {
          console.error("Terminal input error", error);
        });
      });
      term.onResize(() => {
        this.sendResize();
      });

      this.resizeObserver = new ResizeObserver(() => {
        try {
          this.fitAddon?.fit();
          this.sendResize();
        } catch (_error) {
          // ignore fit errors during modal teardown
        }
      });
      this.resizeObserver.observe(container);
      this.applyTerminalTheme();
      this.installThemeObserver();
      this.focusTerminal();
    })();

    try {
      await this.xtermReady;
    } catch (error) {
      this.xtermReady = null;
      throw error;
    }
  },

  parseRequestResult(response) {
    const first = response?.results?.[0];
    if (!first) {
      throw new Error("Terminal server returned no result");
    }
    if (!first.ok) {
      const details = first.error || {};
      throw new Error(details.error || "Terminal request failed");
    }
    return first.data || {};
  },

  async requestSession(eventType) {
    if (!this.socketClient) {
      this.socketClient = getNamespacedClient("/terminal");
    }
    if (!this.outputHandler) {
      this.outputHandler = (envelope) => {
        const output = envelope?.data?.output || "";
        if (output && this.terminal) {
          this.terminal.write(output);
        }
      };
      await this.socketClient.on("terminal_output", this.outputHandler);
    }
    if (!this.exitHandler) {
      this.exitHandler = (envelope) => {
        const reason = envelope?.data?.reason || "process_exit";
        this.handleTerminalExit(reason);
      };
      await this.socketClient.on("terminal_exit", this.exitHandler);
    }
    const response = await this.socketClient.request(eventType, {
      ctxid: this.activeContextId,
      path: this.activeFolderPath,
      ...this.getTerminalDimensions(),
    });
    const data = this.parseRequestResult(response);
    this.logPath = data.log_path || "";
    if (this.terminal) {
      this.terminal.clear();
      if (data.output_history) {
        this.terminal.write(data.output_history);
      }
    }
    this.setSessionActive(true);
    this.error = null;
    this.focusTerminal();
    this.sendResize();
  },

  setSessionActive(active) {
    this.sessionActive = Boolean(active);
    if (this.terminal) {
      this.terminal.options.disableStdin = !this.sessionActive;
    }
  },

  installScrollGuards(container) {
    this.removeScrollGuards();
    const viewport = container.querySelector(".xterm-viewport");
    if (!viewport) return;
    this.scrollLockTarget =
      container.closest(".modal")?.querySelector(".modal-scroll") || null;

    this.pointerEnterHandler = () => {
      this.setPageScrollLock(true);
    };
    this.pointerLeaveHandler = () => {
      this.setPageScrollLock(false);
    };
    this.touchStartHandler = (event) => {
      this.touchStartY = event.touches?.[0]?.clientY ?? null;
      this.setPageScrollLock(true);
    };
    this.touchEndHandler = () => {
      this.touchStartY = null;
      this.setPageScrollLock(false);
    };

    viewport.addEventListener("pointerenter", this.pointerEnterHandler);
    viewport.addEventListener("pointerleave", this.pointerLeaveHandler);
    viewport.addEventListener("touchstart", this.touchStartHandler, { passive: true });
    viewport.addEventListener("touchend", this.touchEndHandler, { passive: true });
    viewport.addEventListener("touchcancel", this.touchEndHandler, { passive: true });
    this.scrollGuardTarget = viewport;
  },

  installKeyboardShortcuts(container) {
    this.removeKeyboardShortcuts();
    this.keydownHandler = async (event) => {
      const key = String(event.key || "").toLowerCase();
      const hasShortcutModifier = event.metaKey || event.ctrlKey;
      if (!hasShortcutModifier || event.altKey) return;
      if (!this.terminal) return;

      if (key === "c" && this.terminal.hasSelection()) {
        event.preventDefault();
        const selection = this.terminal.getSelection();
        if (selection) {
          await navigator.clipboard.writeText(selection);
        }
        return;
      }

      if (key === "v") {
        event.preventDefault();
        if (!this.sessionActive || !this.socketClient?.isConnected()) return;
        const text = await navigator.clipboard.readText();
        if (!text) return;
        await this.socketClient.emit("terminal_input", { input: text });
        return;
      }

      if (key === "a") {
        event.preventDefault();
        this.terminal.selectAll();
      }
    };
    container.addEventListener("keydown", this.keydownHandler);
    this.keydownTarget = container;
  },

  removeKeyboardShortcuts() {
    if (this.keydownTarget && this.keydownHandler) {
      this.keydownTarget.removeEventListener("keydown", this.keydownHandler);
    }
    this.keydownTarget = null;
    this.keydownHandler = null;
  },

  removeScrollGuards() {
    if (!this.scrollGuardTarget) return;
    this.setPageScrollLock(false);
    if (this.pointerEnterHandler) {
      this.scrollGuardTarget.removeEventListener("pointerenter", this.pointerEnterHandler);
    }
    if (this.pointerLeaveHandler) {
      this.scrollGuardTarget.removeEventListener("pointerleave", this.pointerLeaveHandler);
    }
    if (this.touchStartHandler) {
      this.scrollGuardTarget.removeEventListener("touchstart", this.touchStartHandler);
    }
    if (this.touchEndHandler) {
      this.scrollGuardTarget.removeEventListener("touchend", this.touchEndHandler);
      this.scrollGuardTarget.removeEventListener("touchcancel", this.touchEndHandler);
    }
    this.scrollGuardTarget = null;
    this.scrollLockTarget = null;
    this.pointerEnterHandler = null;
    this.pointerLeaveHandler = null;
    this.touchStartHandler = null;
    this.touchEndHandler = null;
    this.touchStartY = null;
  },

  setPageScrollLock(locked) {
    const next = Boolean(locked);
    if (this.pageScrollLocked === next) return;
    if (!this.scrollLockTarget) {
      this.pageScrollLocked = next;
      return;
    }
    this.pageScrollLocked = next;
    this.scrollLockTarget.style.overflowY = next ? "hidden" : "";
    this.scrollLockTarget.style.overscrollBehavior = next ? "contain" : "";
  },

  handleTerminalExit(reason) {
    this.setSessionActive(false);
    if (reason === "process_exit") {
      window.closeModal();
      return;
    }
    this.error = "Session ended";
    this.focusTerminal();
  },

  getTerminalDimensions() {
    if (!this.terminal) {
      return { cols: 120, rows: 32 };
    }
    return {
      cols: Math.max(2, Number(this.terminal.cols) || 120),
      rows: Math.max(1, Number(this.terminal.rows) || 32),
    };
  },

  sendResize() {
    if (!this.socketClient?.isConnected() || !this.terminal) return;
    if (this.resizeTimer) {
      clearTimeout(this.resizeTimer);
    }
    this.resizeTimer = setTimeout(() => {
      this.resizeTimer = null;
      const { cols, rows } = this.getTerminalDimensions();
      this.socketClient.emit("terminal_resize", { cols, rows }).catch((error) => {
        console.error("Terminal resize error", error);
      });
    }, 40);
  },

  installThemeObserver() {
    if (this.themeObserver || typeof MutationObserver === "undefined") return;
    const body = document.body;
    if (!body) return;
    this.themeObserver = new MutationObserver(() => {
      this.applyTerminalTheme();
    });
    this.themeObserver.observe(body, {
      attributes: true,
      attributeFilter: ["class"],
    });
  },

  applyTerminalTheme() {
    if (!this.terminal) return;
    this.terminal.options.theme = this.getTerminalTheme();
  },

  readCssVar(name, fallback, element = document.documentElement) {
    const value = globalThis.getComputedStyle?.(element)
      ?.getPropertyValue(name)
      ?.trim();
    return value || fallback;
  },

  getThemeHost() {
    return document.querySelector(".terminal-modal") || document.documentElement;
  },

  isDarkModeEnabled() {
    const stored = window.localStorage?.getItem("darkMode");
    if (stored === "false") return false;
    if (document.body?.classList.contains("light-mode")) return false;
    if (document.body?.classList.contains("dark-mode")) return true;
    return true;
  },

  getTerminalTheme() {
    const isDark = this.isDarkModeEnabled();
    const host = this.getThemeHost();
    const panel = this.readCssVar("--terminal-bg", isDark ? "#101418" : "#f8fafc", host);
    const foreground = this.readCssVar("--terminal-fg", isDark ? "#e6edf3" : "#0f172a", host);
    const primary = this.readCssVar("--terminal-cursor", isDark ? "#7cc7ff" : "#2563eb", host);
    const selectionBackground = this.readCssVar(
      "--terminal-selection",
      isDark ? "#7cc7ff33" : "#2563eb22",
      host,
    );
    return {
      background: panel,
      foreground,
      cursor: primary,
      cursorAccent: panel,
      selectionBackground,
      black: isDark ? "#111827" : "#1f2937",
      red: isDark ? "#f87171" : "#b91c1c",
      green: isDark ? "#4ade80" : "#15803d",
      yellow: isDark ? "#facc15" : "#a16207",
      blue: isDark ? "#60a5fa" : "#1d4ed8",
      magenta: isDark ? "#c084fc" : "#7c3aed",
      cyan: isDark ? "#22d3ee" : "#0f766e",
      white: isDark ? "#e5e7eb" : "#e5e7eb",
      brightBlack: isDark ? "#6b7280" : "#6b7280",
      brightRed: isDark ? "#fca5a5" : "#dc2626",
      brightGreen: isDark ? "#86efac" : "#16a34a",
      brightYellow: isDark ? "#fde047" : "#ca8a04",
      brightBlue: isDark ? "#93c5fd" : "#2563eb",
      brightMagenta: isDark ? "#d8b4fe" : "#8b5cf6",
      brightCyan: isDark ? "#67e8f9" : "#0891b2",
      brightWhite: isDark ? "#f9fafb" : "#ffffff",
    };
  },

  getTerminalFont() {
    return this.readCssVar("--font-family-code", '"Roboto Mono", "Fira Code", monospace');
  },

  focusTerminal() {
    if (!this.terminal) return;
    requestAnimationFrame(() => this.terminal?.focus());
  },

  async clearOutput() {
    if (!this.terminal) return;
    this.terminal.clear();
    this.error = null;
    this.focusTerminal();
  },

  async resetSession() {
    try {
      await this.ensureTerminal();
      await this.requestSession("terminal_restart");
      this.error = null;
      this.focusTerminal();
    } catch (error) {
      this.error = error?.message || "Failed to reset terminal";
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error resetting terminal", error);
      }
    }
  },

  async killSession() {
    if (!this.socketClient?.isConnected()) {
      this.handleTerminalExit("killed");
      return;
    }
    try {
      await this.socketClient.request("terminal_kill", {});
    } catch (error) {
      this.error = error?.message || "Failed to kill terminal session";
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error killing terminal", error);
      }
    }
  },

  buildTerminalLogContent(payload) {
    const mode = String(payload?.mode || "tail");
    const lines = Number(payload?.lines || 0);
    const session = String(payload?.session || "");
    const content = String(payload?.content || "(empty)");
    const details = [
      "Terminal history from the current chat terminal session:",
      session ? `Session: ${session}` : "",
      `Mode: ${mode}${lines ? ` (${lines} lines)` : ""}`,
      "",
      content,
    ].filter(Boolean);
    return details.join("\n");
  },

  appendTerminalLogToProcess(payload) {
    const id = `terminal-log-${Date.now()}`;
    const content = this.buildTerminalLogContent(payload);
    drawMessageToolSimple({
      id,
      type: "tool",
      heading: "A0: Using tool 'TerminalLog'",
      content,
      kvps: {
        _tool_name: "TerminalLog",
        mode: String(payload?.mode || "tail"),
        lines: String(payload?.lines || ""),
        session: String(payload?.session || ""),
      },
      timestamp: Date.now() / 1000,
      agentno: 0,
      code: "LOG",
    });
  },

  async insertTerminalLog() {
    try {
      const response = await shortcuts.callJsonApi("/terminal_log_insert", {
        ctxid: this.activeContextId,
        mode: "tail",
        lines: 100,
      });
      this.appendTerminalLogToProcess(response);
      this.error = null;
    } catch (error) {
      this.error = error?.message || "Failed to insert terminal log";
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error inserting terminal log", error);
      }
    }
  },

  toggleMobileKeys() {
    this.mobileKeysOpen = !this.mobileKeysOpen;
    this.focusTerminal();
  },

  sendSpecialKey(key) {
    if (!this.sessionActive || !this.socketClient?.isConnected()) return;

    const keyMap = {
      arrow_up: "\x1b[A",
      arrow_down: "\x1b[B",
      arrow_left: "\x1b[D",
      arrow_right: "\x1b[C",
      enter: "\r",
      space: " ",
      tab: "\t",
      esc: "\x1b",
      ctrl_c: "\x03",
    };

    const input = keyMap[String(key)];
    if (!input) return;
    this.socketClient.emit("terminal_input", { input }).catch((error) => {
      console.error("Terminal special key error", error);
    });
    this.focusTerminal();
  },
};

export const store = createStore("terminalModal", model);
