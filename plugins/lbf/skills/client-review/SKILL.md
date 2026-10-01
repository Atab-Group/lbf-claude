---
name: client-review
description: Use when the person asks how an LBF client is doing, wants a monthly performance read, a comparison across platforms or months, or an explanation of a spike or drop. Builds a grounded review from the lbf tools.
---

# A client performance review

Read `lbf-platform` first if you have not this session.

## Pull, in this order

1. `list_clients` for the slug, then `get_sync_status`: if the last sync is stale or failed, say so up
   front, because every number below depends on it. Do not run `sync_client` unless the person asks.
2. `get_client_overview` for the month: the headline numbers and the connected channels.
3. For each channel that matters, `get_platform_detail`, and `get_platform_series` for the trend.
4. `get_posts` for what was published and what worked. `get_demographics` if audience is the question.
5. Paid: `get_paid_performance`, then `get_paid_breakdown` for campaigns. Only if the client runs ads.
6. Spikes and drops: `get_daily_series` with one `metric` at a time (an unfiltered call is very large),
   or `list_daily_metrics` to see what is available.

Pull the previous month too when the person wants a change explained.

## Write it up

- Lead with the two or three things that matter, each with its number and the month.
- Compare against the previous month, and say what drove the change when the data shows it (a post, a
  campaign, a paused ad).
- Organic and paid are separate: never add paid reach into organic.
- Flag gaps honestly: a platform not connected, a metric the platform does not report, a stale sync.
- If the review is for the client, use the agency voice (lead with wins, pair a weak result with the move
  we are making) and no em dashes.
