# LBF Platform for Claude Code and Codex

Gives Claude Code or Codex the tools and know-how to drive the Let's Be Frank reporting platform: client
data, monthly reports, the task board and the content planner.

## Install

The easy way: in the platform, open My settings, **Connect your agent**, click the button, and paste the
copied message into Claude Code or Codex. It runs the steps below for you.

### Claude Code, by hand

```
claude plugin marketplace add Atab-Group/lbf-claude
claude plugin marketplace update lbf
claude plugin install lbf@lbf --scope user
echo '{"api_key":"<your lbf_ key>"}' | claude plugin configure lbf@lbf --values-stdin
```

Then type `/reload-plugins`. Every step is safe to run again; to change your key, run only the last line.
The key is kept in your system's credential store (on Linux, Claude Code's own credentials file).

### Codex, by hand

```
codex plugin marketplace add Atab-Group/lbf-claude
codex plugin add lbf@lbf
echo "export LBF_API_KEY='<your lbf_ key>'" >> ~/.zshrc    # ~/.bashrc on Linux
```

Then start Codex from a new terminal. Codex reads the key from `LBF_API_KEY`, so the Codex desktop app only
sees it when launched from a terminal that has it set.

Then ask: "list my LBF clients".

Your key sees the clients you manage and can take actions on them (create tasks, generate reports, update
planner dates). Revoke it in the platform any time.

## What's inside

```
.claude-plugin/marketplace.json     Claude Code marketplace
.agents/plugins/marketplace.json    Codex marketplace
plugins/lbf/
  .claude-plugin/plugin.json        Claude Code manifest (key as a sensitive setting)
  .mcp.json                         Claude Code MCP server
  .codex-plugin/plugin.json         Codex manifest
  codex.mcp.json                    Codex MCP server (key from LBF_API_KEY)
  skills/                           shared: lbf-platform, client-review, reports, tasks, planner, connect
```

Server: `https://lbf-reporting-platform.vercel.app/api/mcp/mcp`. Bump `version` in
`.codex-plugin/plugin.json` on every change, because Codex caches plugins by version.

Not yet supported: the Claude and ChatGPT chat apps (they need OAuth, which the platform does not have).
