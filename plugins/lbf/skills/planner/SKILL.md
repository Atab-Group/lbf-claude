---
name: planner
description: Use when the person asks about an LBF client's content planner: key dates for a month, adding, changing or removing a date, or drafting a month of proposed posts.
---

# The content planner

Read `lbf-platform` first if you have not this session.

## Dates

- `get_planner_context` for the client and month shows the dates already held and what the client has
  connected. Pass `months: 3` to look three months ahead.
- `add_planner_date`, `update_planner_date`, `remove_planner_date` usually come back already `done`.
  A removed date is gone; adding it again makes a new one.
- Only add a date you can stand behind: a real public holiday, a client event, a launch. Say where it
  comes from.

## Proposing a month of posts

1. Read `get_planner_context`, the client's last report (`list_report_pages`) and recent `get_posts` to
   see what worked.
2. One post per confirmed date, only on platforms the client has connected, in the client's voice. No em
   dashes. Never invent a performance figure. Never name a competitor in post copy.
3. Each post: platform, format, time of day, the idea plainly enough for a designer, and a rationale
   tied to the client's goals.
4. Call `propose_planner_posts` ONCE with the whole month. It is held for the account manager, who
   approves or rejects it on the client's planner page. A second call replaces the first.

To change one post in a month already installed, use `update_planner_post` (one post per call, matched by
its `dateName`). `accepted: false` lists which rule refused it.
