# Compatibility

`agent0-terminal` is a patch-based add-on, so compatibility depends on the target Agent Zero checkout matching the code layout expected by the patch.

## Expected Baseline

- Agent Zero repository root contains:
  - `run_ui.py`
  - `python/`
  - `webui/`
- The terminal-related files touched by the patch are still close to the upstream `main` branch layout
- The target is a git checkout that can accept `git apply`

## Known Constraints

- A heavily customized Agent Zero checkout may reject the patch
- Local changes in the same files can cause patch conflicts
- The installer intentionally stops if `git apply --check` fails

## If The Patch Does Not Apply

1. Review the exact failure from `git apply --check`
2. Compare your local files with the touched files listed in the README
3. Apply the patch manually or refresh the patch against your current Agent Zero baseline

## Touched Areas

- `python/helpers/`
- `python/api/`
- `python/tools/`
- `python/websocket_handlers/`
- `tests/`
- `webui/components/chat/input/`
- `webui/components/modals/terminal/`
- `webui/vendor/xterm/`
