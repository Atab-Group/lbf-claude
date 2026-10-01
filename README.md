# LBF Platform for Claude Code

Gives Claude Code the tools and know-how to drive the Let's Be Frank reporting platform: client data,
monthly reports, the task board and the content planner.

## Install

The easy way: in the platform, open My settings, Connect your Claude, click **Connect Claude**, and paste
the copied message into Claude Code. Claude runs the steps below for you.

By hand:

```
claude plugin marketplace add Atab-Group/lbf-claude
claude plugin marketplace update lbf
claude plugin install lbf@lbf --scope user
echo '{"api_key":"<your lbf_ key>"}' | claude plugin configure lbf@lbf --values-stdin
```

Every step is safe to run again. To change your key later, run only the last line.

Then type `/reload-plugins` in Claude Code and ask "list my LBF clients".

Your key sees the clients you manage and can take actions on them. It is kept in your system's credential
store (on Linux, Claude Code's own credentials file), not in a settings file. Revoke it in the platform any time.

## What's inside

- `lbf` MCP server: the platform's tools (`https://lbf-reporting-platform.vercel.app/api/mcp/mcp`).
- Skills: `lbf-platform` (house rules), `client-review`, `reports`, `tasks`, `planner`, `connect`.

## Works in

Claude Code (terminal, IDE, desktop app Code tab). Not yet in the Claude chat app or claude.ai.
