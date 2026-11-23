---
name: reports
description: Use when the person asks about an LBF client's monthly report that already exists: whether it exists, its status, what is in it, whether it is ready to send, or adding a chart page. Not for building, making or doing a month's report: that is the lbf-monthly-report skill.
---

# Monthly reports

Read `lbf-platform` first if you have not this session.

A report moves `queued`, then `generating`, then `ready`, then `sent`.

## Checking on a report

- `list_report_pages` for the client and month: which pages the current draft has.
- `review_report` (a job) checks the stored deck's layout and structure. On the result, `fitToSend` says
  whether it may go to the client and `fitToSendReason` says why not. It changes nothing.
- `build_report` (a job) shows which pages a report WOULD have, without calling a model or storing
  anything. Use it to preview.

## Generating

**Building, making or doing a month's report is the `lbf-monthly-report` skill** (plugin `lbf-reports`):
the account manager's screenshots and notes in, a PDF out. Use it for "make / build / do the October
report for <client>". If that skill is not installed, say so and point them to My settings, Connect your
agent, in the platform; do not fall back to `generate_report`.

`generate_report` is the platform's older automatic run. Call it only when the person names it: "run the
platform's report generation", "press Generate", "regenerate it in the platform". Only for that client
and month. Confirm the client and month back to them first if
there is any doubt, because a run replaces the current draft.

1. Call `generate_report` with `clientRef` and `month`.
2. Poll `get_job`. The run takes up to an hour; the handle's `progress` shows it moving. Tell the person it
   is running and check back rather than polling for the whole hour.
3. `refused: 'run-conflict'` means a run for that client and month is already going. That is normal: tell
   them, do not retry.
4. When it is `ready`, the account manager reviews it in the platform.

## Custom chart pages

`edit_report_chart` adds a chart as a query, not as numbers you supply. Discover the vocabulary with
`get_options` and `get_fields` (or `list_daily_metrics` for daily data) first. `accepted: false` lists
exactly what would be accepted. A sent report cannot be changed.

## Sending

Do not send from here. Tell the person to open the report in the platform and send it there.
