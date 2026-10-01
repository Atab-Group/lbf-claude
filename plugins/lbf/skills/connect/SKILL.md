---
name: connect
description: Use when the lbf tools are missing, return 401 or unauthorized, the person wants to change or rotate their LBF key, or asks how to set up, update or check the LBF plugin in Claude Code or Codex.
---

# Connecting and fixing the LBF plugin

## Check the connection

Call `list_clients`. If it returns clients, the connection works.

If the lbf tools are not there at all:
- **Claude Code:** ask the person to type `/reload-plugins`, or restart Claude Code.
- **Codex:** the key is read from the `LBF_API_KEY` environment variable when Codex starts. Ask the person
  to quit Codex and start it again from a new terminal.

## The key is wrong, expired or revoked

The platform answers `unauthorized` (HTTP 401). The person needs a fresh key: in the platform, avatar (top
right), My settings, Connect your agent, then the button. It copies a setup message to paste here.

If they paste only a key starting `lbf_`:
- **Claude Code:** run `echo '{"api_key":"<their key>"}' | claude plugin configure lbf@lbf --values-stdin`,
  then ask them to type `/reload-plugins`.
- **Codex:** in their shell profile (`~/.zshrc` on macOS, `~/.bashrc` on Linux), replace any line that
  sets `LBF_API_KEY` with `export LBF_API_KEY='<their key>'`, then ask them to restart Codex from a new
  terminal.

Never print the key back, and never write it anywhere other than those two places.

## Updating the plugin

- **Claude Code:** `claude plugin marketplace update lbf`, `claude plugin update lbf@lbf`, then
  `/reload-plugins`.
- **Codex:** `codex plugin marketplace upgrade lbf`, then `codex plugin add lbf@lbf`, then restart Codex.

## Not supported yet

The Claude and ChatGPT chat apps cannot use this plugin yet: they need a sign-in flow the platform does
not have. It works in Claude Code (terminal, IDE, desktop app Code tab) and in Codex.
