import { createStore } from "/js/AlpineStore.js";
import * as shortcuts from "/js/shortcuts.js";

function el(tag, className = "", text = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

const model = {
  nextSession: 9000,
  sessions: {},
  terminals: {},

  getContextId() {
    return globalThis.getContext?.() || shortcuts.getCurrentContextId?.() || "";
  },

  getSessionId(ctxid) {
    if (!this.sessions[ctxid]) {
      this.sessions[ctxid] = this.nextSession;
      this.nextSession += 1;
    }
    return this.sessions[ctxid];
  },

  ensureCard(ctxid) {
    const existing = this.terminals[ctxid];
    if (existing && existing.group?.isConnected) {
      return existing;
    }

    const session = this.getSessionId(ctxid);
    const history = document.querySelector("#chat-history");
    if (!history) {
      throw new Error("Chat history not available");
    }

    const group = el("div", "message-group message-group-left");
    const container = el(
      "div",
      "message-container ai-container terminal-inline-container",
    );
    const message = el("div", "message message-code-exe message-inline-terminal");
    const body = el("div", "message-body inline-terminal-shell");
    const header = el("div", "inline-terminal-header");
    const title = el("div", "inline-terminal-title", `Terminal [${session}]`);
    const status = el("div", "inline-terminal-status", "Idle");
    const actions = el("div", "inline-terminal-actions");
    const clearButton = el("button", "btn-icon-action inline-terminal-action");
    const resetButton = el("button", "btn-icon-action inline-terminal-action");
    const closeButton = el("button", "btn-icon-action inline-terminal-action");
    const output = el("pre", "inline-terminal-output");
    const form = el("form", "inline-terminal-form");
    const prompt = el("span", "inline-terminal-prompt", "$");
    const input = document.createElement("input");

    clearButton.type = "button";
    clearButton.title = "Clear output";
    clearButton.innerHTML = '<span class="material-symbols-outlined">ink_eraser</span>';

    resetButton.type = "button";
    resetButton.title = "Reset session";
    resetButton.innerHTML = '<span class="material-symbols-outlined">restart_alt</span>';

    closeButton.type = "button";
    closeButton.title = "Close terminal";
    closeButton.innerHTML = '<span class="material-symbols-outlined">close</span>';

    input.type = "text";
    input.className = "inline-terminal-input";
    input.placeholder = "Run a bash command";
    input.autocomplete = "off";
    input.spellcheck = false;

    actions.append(clearButton, resetButton, closeButton);
    header.append(title, status, actions);
    form.append(prompt, input);
    body.append(header, output, form);
    message.appendChild(body);
    container.appendChild(message);
    group.appendChild(container);
    history.appendChild(group);

    const refs = {
      ctxid,
      session,
      group,
      status,
      output,
      form,
      input,
      clearButton,
      resetButton,
      closeButton,
      running: false,
    };

    clearButton.addEventListener("click", () => {
      refs.output.textContent = "";
      this.appendOutput(ctxid, "Output cleared.");
    });
    closeButton.addEventListener("click", () => this.close(ctxid));
    resetButton.addEventListener("click", async () => {
      await this.reset(ctxid);
    });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await this.runCommand(ctxid, refs.input.value);
    });

    this.terminals[ctxid] = refs;
    this.appendOutput(ctxid, `Connected to shell session ${session}.`);
    return refs;
  },

  focus(ctxid) {
    const refs = this.ensureCard(ctxid);
    refs.group.scrollIntoView({ behavior: "smooth", block: "end" });
    refs.input.focus();
    return refs;
  },

  async open() {
    const ctxid = this.getContextId();
    if (!ctxid) {
      throw new Error("No active chat context");
    }

    const refs = this.focus(ctxid);
    if (!refs.running && refs.output.textContent.trim().length === 0) {
      this.appendOutput(ctxid, `Connected to shell session ${refs.session}.`);
    }
  },

  setRunning(refs, running, label = "") {
    refs.running = running;
    refs.input.disabled = running;
    refs.resetButton.disabled = running;
    refs.status.textContent = running ? label || "Running..." : "Idle";
  },

  appendOutput(ctxid, text) {
    if (!text) return;
    const refs = this.ensureCard(ctxid);
    const normalized = refs.output.textContent ? `\n${text}` : text;
    refs.output.textContent += normalized;
    refs.output.scrollTop = refs.output.scrollHeight;
  },

  async runCommand(ctxid, rawCommand) {
    const command = String(rawCommand || "").trim();
    const refs = this.ensureCard(ctxid);
    if (!command || refs.running) {
      return;
    }

    refs.input.value = "";
    this.setRunning(refs, true, `Running: ${command}`);

    try {
      const response = await shortcuts.callJsonApi("/terminal", {
        ctxid,
        session: refs.session,
        action: "command",
        command,
      });
      this.appendOutput(ctxid, response.output || "(no output)");
    } catch (error) {
      this.appendOutput(ctxid, `Error: ${error.message || error}`);
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error running terminal command", error);
      }
    } finally {
      this.setRunning(refs, false);
      refs.input.focus();
    }
  },

  async reset(ctxid) {
    const refs = this.ensureCard(ctxid);
    if (refs.running) {
      return;
    }

    this.setRunning(refs, true, "Resetting...");
    try {
      await shortcuts.callJsonApi("/terminal", {
        ctxid,
        session: refs.session,
        action: "reset",
      });
      refs.output.textContent = "";
      this.appendOutput(ctxid, `Session ${refs.session} reset.`);
    } catch (error) {
      this.appendOutput(ctxid, `Reset failed: ${error.message || error}`);
      if (globalThis.toastFetchError) {
        globalThis.toastFetchError("Error resetting terminal session", error);
      }
    } finally {
      this.setRunning(refs, false);
      refs.input.focus();
    }
  },

  close(ctxid) {
    const refs = this.terminals[ctxid];
    if (!refs) return;
    refs.group.remove();
    delete this.terminals[ctxid];
  },
};

export const store = createStore("chatTerminal", model);
