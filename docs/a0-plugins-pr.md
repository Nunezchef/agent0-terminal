# a0-plugins Submission Draft

This repo is now ready to be submitted to the Agent Zero plugin index.

Source index:
- https://github.com/agent0ai/a0-plugins

Relevant index rules:
- Add exactly one new folder under `plugins/<your-plugin-name>/`
- Include only `plugin.yaml` and an optional square `thumbnail.*`
- The plugin repository must contain `plugin.yaml` at its root

## Proposed PR Title

```text
Add Agent0 Terminal plugin
```

## Files To Add In The `a0-plugins` PR

```text
plugins/agent0-terminal/plugin.yaml
```

## `plugins/agent0-terminal/plugin.yaml`

```yaml
title: Agent0 Terminal
description: PTY-backed terminal modal for Agent Zero with persistent sessions, TUI support, and TerminalLog integration.
github: https://github.com/Nunezchef/agent0-terminal
tags:
  - development
  - cli
  - tools
  - files
  - workflow
```

## Suggested PR Body

```md
This PR adds `agent0-terminal` to the Agent Zero plugin index.

Plugin repo:
https://github.com/Nunezchef/agent0-terminal

`agent0-terminal` is a standalone add-on for Agent Zero that adds a real PTY-backed terminal modal with persistent sessions, TUI support, and explicit `TerminalLog` integration.

The plugin repository includes the required root `plugin.yaml`, and this PR adds exactly one plugin folder under `plugins/agent0-terminal/`.
```

## Notes

- No thumbnail is included in the first submission.
- The current distribution model is patch-based: users install the add-on into an existing Agent Zero checkout.
- This is plugin-indexable now, even though installation is still a patch workflow rather than a one-click in-app install.
