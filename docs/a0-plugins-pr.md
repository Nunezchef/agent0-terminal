# a0-plugins Submission Draft

This repo is now ready to be submitted to the Agent Zero plugin index.

Source index:
- https://github.com/agent0ai/a0-plugins

Relevant index rules:
- Add exactly one new folder under `plugins/<your-plugin-name>/`
- Include only `index.yaml` and an optional square `thumbnail.*`
- The plugin repository must contain `plugin.yaml` at its root
- The index folder name must match the remote `plugin.yaml` `name` field

## Proposed PR Title

```text
Add terminal0 plugin
```

## Files To Add In The `a0-plugins` PR

```text
plugins/terminal0/index.yaml
```

## `plugins/terminal0/index.yaml`

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

`terminal0` is a plugin-packaged terminal integration for Agent Zero that adds a real PTY-backed modal terminal with persistent sessions, TUI support, and explicit `TerminalLog` integration.

The plugin repository includes the required root `plugin.yaml` (`name: terminal0`), and this PR adds exactly one plugin folder under `plugins/terminal0/` with `index.yaml`.
```

## Notes

- No thumbnail is included in the first submission.
- The current distribution model is plugin-packaged runtime install into Agent Zero core paths.
- The plugin is installable from repository + installer and indexable in marketplace.
