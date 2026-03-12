# Runtime Integration Notes

`terminal0` installs runtime payload files into Agent Zero core paths to provide a seamless in-app terminal experience.

The plugin currently does not define extension hook scripts under `usr/extensions/*`.

Instead, it installs:

- websocket handler: `python/websocket_handlers/terminal_handler.py`
- terminal APIs/tools: `python/api/terminal.py`, `python/api/terminal_log_insert.py`, `python/tools/terminal_log.py`
- UI integration: chat input wiring + modal terminal components

This keeps terminal behavior native to the Agent Zero chat flow while being distributed as a plugin package.
