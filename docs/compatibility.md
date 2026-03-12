# Compatibility

`terminal0` is plugin-packaged but installs runtime payload files into Agent Zero core paths.

## Expected target

- Agent Zero checkout with:
  - `run_ui.py`
  - `python/`
  - `webui/`
- writable filesystem for the target checkout
- git checkout (needed for rollback patch generation and reverse apply)

## Plugin/index compatibility

- Plugin manifest uses `name: terminal0`
- For `a0-plugins` index, folder should be:
  - `plugins/terminal0/`
- Index metadata file should be `index.yaml` (not plugin.yaml)

## Known constraints

- Because this plugin modifies core files, heavily customized Agent Zero trees may diverge.
- Re-run installer after Agent Zero upgrades.
- Keep rollback patch backups under `.terminal0/backups`.
