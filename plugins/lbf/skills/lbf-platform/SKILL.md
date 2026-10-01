---
name: lbf-platform
description: Use whenever the person asks about a Let's Be Frank (LBF) client, their social or paid numbers, reports, tasks, planner dates, or anything on the LBF reporting platform. Explains how the lbf tools behave and the house rules for using them.
---

# Driving the LBF reporting platform

The `lbf` MCP tools are the Let's Be Frank reporting platform itself. They answer with live data, scoped
to the clients this person manages (founders see every client). Treat them as the source of truth: never
estimate a number you could read.

## Start every client question the same way

1. **`list_clients`** first. It returns each client's `slug`, which every other tool takes as `clientRef`.
   Never guess a slug from a display name.
2. **`describe_metrics`** before interpreting a metric you have not met: it says what the metric means on
   each platform.
3. For a slice the purpose-built reads do not cover, use the generic loop: `get_options`, then
   `get_fields`, then `get_data`.

A client the person cannot see answers `error(client-not-found)`, exactly like a client that does not
exist. Say they may not manage that client rather than insisting it is missing.

## Months

Every `month` is `YYYY-MM`. Leave it out for the current month: the platform works on South African time
(Africa/Johannesburg), so never compute "this month" yourself. Always state which month a figure is
for, and check the `month` field in the answer matches the month you asked for.

## Reads answer now, writes answer with a job

- A read returns its data straight away.
- A write (create a task, generate a report, sync, planner changes) returns a **job handle**. Poll
  `get_job` with the `jobId` every 5 to 10 seconds until the status is `done`, `failed` or `rejected`.
  Read the handle's `note` for what to do next.
- The three planner date tools usually come back already `done`.
- `held-for-approval` means a person must act in the platform; polling will not move it.
- Match on the `jobId`, not on `kind`: `add_planner_date` shows up as kind `add_client_date`.
- `accepted: false` or `refused` inside a `done` job is a normal answer, not a crash. Read `failures`,
  `problems` or `refused` and tell the person what the platform objected to.

## Errors

Tool errors read `error(<code>): <message>`. Only `error(internal)` is worth one retry. Every other code
will refuse again until you change the call, so fix the input or explain it to the person.

Pass an `idempotencyKey` on a write you might retry, so a retry never creates a second job.

## Rules that are easy to get wrong

- **Never start a report, a sync or a delete unless the person asked for it**, for that client and month.
  A report run spends model budget and replaces the current draft; a sync spends the client's metered
  data calls for the month.
- **Never send a report from here.** Tell the person to open the report in the platform and send it
  there. `send_report` only queues a request that someone must approve in the app.
- **Null is not zero.** A missing metric means the platform does not report it, not that it was 0.
- **Money is South African rand (ZAR).**
- **Client-facing copy uses no em dashes**: use a colon or a comma. UK spelling.
- **Reports speak as the agency to its client**: lead with wins, pair a weak result with what we are
  doing about it, never change a figure.

## Ignore these tools if you see them

Tools for the platform's own report-writing agent (`month_briefing`, `write_page`, `submit_deck` and
similar) only work inside the platform. From here they answer `error(not-bound)`. Do not call them.

## Related skills

`client-review` for a performance read, `reports` for report status and generation, `tasks` for the task
board, `planner` for content dates and post proposals, `connect` if the tools are missing or failing.
