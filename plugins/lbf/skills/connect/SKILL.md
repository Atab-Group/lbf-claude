---
name: connect
description: Use when the lbf tools are missing, return 401 or unauthorized, the person wants to change or rotate their LBF key, or asks how to set up or check the LBF plugin.
---

# Connecting and fixing the LBF plugin

## Check the connection

Call `list_clients`. If it returns clients, the connection works. If the lbf tools are not available at
all, ask the person to type `/reload-plugins`, then try again.

## The key is wrong, expired or revoked

The platform answers `unauthorized` (HTTP 401). The person needs a fresh key:

1. In the platform, open their avatar (top right), then My settings, then Connect your Claude.
2. Click Connect Claude. It copies a setup message; they paste it here and you run it.
3. Or, if they paste only a key starting `lbf_`, run:
   `echo '{"api_key":"<their key>"}' | claude plugin configure lbf@lbf --values-stdin`
   then ask them to type `/reload-plugins`.

Never print the key back, and never write it to any file.

## Updating the plugin

`claude plugin marketplace update lbf` then `claude plugin update lbf@lbf`, then `/reload-plugins`.

## Not supported yet

The Claude chat app and claude.ai cannot use this plugin yet: they need a sign-in flow the platform does
not have. It works in Claude Code, in the terminal or the desktop app's Code tab.
