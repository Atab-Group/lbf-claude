---
name: lbf-monthly-report
description: Use when an account manager asks to build, make or redo the monthly report for a Let's Be Frank client, for example "build the monthly report for <client>", "build the October report for <client>", "make <client>'s report". Turns the platform's report pack, the two Meta Content overview screenshots and the account manager's notes into a PDF in the agency's 13-page layout, printed by the platform.
---

# Build a client's monthly report

You build one client's report for one month as a PDF. The platform supplies every figure in a JSON
"pack". You write the words (the "copy") and send them to `render_report`. The platform fills its
fixed layout, checks every printed number against the pack, prints the PDF and saves it in the app's
report list. You never calculate, round or type a figure yourself, and nothing runs on this machine.

Files in this folder:

- `pack.schema.json`: the shape of the pack, with the rules that bind the pack and the copy.
- `copy.schema.json`: the exact shape `render_report` accepts as `copy`. It is generated from the
  platform's own check, so it is always current.
- `fixtures/`: a fictional client ("Sample Trail Run"): a full pack and its copy, and a small one, to
  see what good copy looks like.

## Before you start

- The `lbf` MCP tools must answer. If `get_report_pack` fails or the tools are missing, **stop and say
  so**. Never build a report from memory, from an old pack, or from figures read off a screenshot alone.
- Use `list_clients` to turn the client's name into its slug. Months are `YYYY-MM`.
- Write tools return a job handle. Poll `get_job` until it is `done`, then read `result`. A refusal in
  `result` is a normal answer: read it, never retry it unchanged.

## The steps

### 1. Read the pack

The account manager names the client and the month, attaches the two Meta Business Suite "Content
overview" screenshots (Instagram and Facebook, both for the report month) and adds any notes.

Call `get_report_pack` with `{clientRef, month}`. Read `pages`, `missing`, `notes` and `figures`.
Keep this first answer: its Instagram and Facebook figures are the synced ones you compare the
screenshots against in step 2 (a figure whose `source` is not `screenshot`).

If the client has a content calendar Google Sheet (the account manager names it, or it is in the
client's documents), read the month's tab (in Claude Code with the `gws` tool, elsewhere with the
Google Drive connector). Call `save_content_calendar` with
`{clientRef, month, rows: [{date, pillar, format?, title?}]}`, `date` as `YYYY-MM-DD`. If the sign-in
fails, carry on without it: the Content insights page then has no calendar pillars.

### 2. Screenshots

If a screenshot is missing, ask for it once. If there is none, carry on: that page shows a neutral
block, and the synced figures stay.

1. Read each card. For each figure, read the number **and** the change printed beside it ("↓ 36.5%"
   is `-36.5`, "↑ 19.8%" is `19.8`).
   - Instagram card: views, from organic, from ads, reach, content interactions.
   - Facebook card: views, from organic, from ads, viewers, content interactions, watch time.
   - **The Instagram card's headline "Views" can include Facebook views.** The small split beside it
     shows this. Save the Instagram-only number, and use the "Total" in the views breakdown when it
     matches it.
   - Write each figure as the plain number in full (55614, not 55.6K). Watch time in whole minutes
     (2h 28m is 148).
2. **Ask the account manager only about a figure you are unsure of**: one that is cut off, blurred, or
   shown only rounded ("55.6K" with no full number). Ask once, for all of them together. Every other
   figure is saved straight away, with no confirm step.
   - With nobody to ask (an unattended run), leave an unsure figure out. The synced figure stays in
     the report. Name the figure you left out in the final message.
3. Where the surface can upload a file, send each screenshot with `create_upload` (kind `screenshot`,
   `clientRef`, `month`, `platform`, `contentType`, `sizeBytes`), PUT the bytes to the returned link,
   and keep its `uploadId`.
4. Call `save_screenshot_figures` once for `instagram` and once for `facebook`:
   ```
   {clientRef, month, platform: "instagram" | "facebook",
    figures: {views?, reach?, interactions?, followers?, viewsOrganic?, viewsAds?, viewers?, watchTimeMinutes?},
    changes?: {the same keys},
    uploadId?, note?}
   ```
   `changes` are the signed percent printed beside each figure. A change needs its figure: never send a
   change alone.
5. Compare each saved figure with the synced figure of the same key from step 1. **The screenshot
   figure is the one the report prints.** Note every pair that differs by more than 10% for the final
   message. If step 1's figure was already from a screenshot (saved earlier), there is no synced figure
   to compare: say so.

### 3. Competitors

For each competitor (the handles in `page.competitors.rows`, or `competitor_instagram` from
`get_client_overview`), look up the Instagram follower count on the web. A public profile page gives
it in its description ("2,870 Followers"). Note the page and today's date.

Call `save_competitor_followers` with
`{clientRef, month, rows: [{handle, name?, followers, rounded?, sourceUrl?, readOn?}]}`.
`followers` is a whole number. **When the profile shows the count only rounded ("38K"), save
`followers: 38000` with `rounded: true`.** It prints as "~38K", and its "vs last month" shows a dash,
because only exact counts are compared. Do not ask the account manager for an exact count.

### 4. Key dates

Call `get_report_pack` again, now that the figures are saved. `page["looking-ahead"].keyDates` holds
the client's planner dates for the next month (the account manager's and the planner agent's). Use
them as they are. Only when that list is empty, write `keyDates` in the copy from the account
manager's notes (`notes.keyDates`, `notes.lookAhead`, or the chat).

### 5. Write the copy

Write the copy for every page in `pack.pages` except `cover` (rules below; the shape is
`copy.schema.json`; an example is `fixtures/sample-copy.json`). Name every post, video and ad by its
`ref` from the pack (`ig1`, `fb2`, `tt1`, `ad1`), never by its `id`.

### 6. Render

1. Call `render_report` with `{clientRef, month, copy}`. Poll `get_job` until `done`.
2. `result.rendered` false with `result.problems`: each problem names the page and what is wrong (an
   unknown ref or placeholder, a missing takeaway, a number typed by hand, a page that ran over). Fix
   **all** of them in the copy and call `render_report` again.
3. `result.refused`: `report-sent` (the month's report was already sent) or `in-flight` (the platform
   is building that month now), or `forbidden`. Tell the account manager; do not retry. `conflict`
   means the deck changed while yours was being saved: call `render_report` once more.
4. `result.rendered` true: `pdfUrl` (works for 7 days), `pages`, `revision`, `warnings`. A warning that
   a page was shrunk to fit means its copy is long: shorten it and render again.

Every render is saved as a new revision of the month's report in the app. Earlier revisions are kept.

### 7. Final message

Give the account manager:

1. The PDF link (`pdfUrl`) and the revision number.
2. A table of the screenshot figures you read: platform, figure, number, change.
3. Every screenshot figure that differs from the synced figure by more than 10%: both numbers.
4. What could not be filled: `pack.missing`, figures you left out, images that did not load, and any
   competitor you could not read.

### Changes

The account manager asks for changes in plain words. Change the copy only, call `render_report` again
and give the new link. A figure that looks wrong is not edited in the copy: say which figure, and check
it at the source (the screenshot, or the platform).

Nothing is sent to the client. The account manager sends the PDF themselves, from their own email.

## Writing the copy

### What each page needs

| Page | Fields |
|---|---|
| every page but `cover` | `takeaway` |
| `instagram`, `facebook`, `tiktok` | `postNames`: `{ref: short name}` for the posts the page lists |
| `google-ads` | `nextLine`, optional: "Next: ..." |
| `what-worked` | `posts`: `[{ref, name, why, how}]` for the posts the pack lists, in its order |
| `content-insights` | `doMore`, `keep`, `rework` |
| `looking-ahead` | `blocks`: `[{heading, text}]`, every one is shown; `keyDates`: `[{dateLabel, label}]`, only when the pack has none |
| top level | `omitPosts`: refs of pack posts to leave out |

The pack decides which posts, ads and videos a page shows. You name them and may leave one out with
`omitPosts`; you never pick other posts.

### Figures: placeholders only

Every figure in your text goes in as a placeholder that names a key in `pack.figures`:

- `{ig.views}` prints the figure ("73.5K")
- `{ig.views.mom}` prints the change on last month with its sign ("-12.4%")
- `{ig.views.change}` prints the same change without its sign, for "rose" or "fell" ("12.4%")
- `{ig.views.prev}` prints last month's figure

A takeaway with any digit outside a placeholder is refused. In every other line (`why`, `how`, blocks),
any printed number the pack does not hold is refused too. No hand-typed figures anywhere.

### Copy rules

- One heading and **one short takeaway line** per page. Aim for one line; two at most (about 190
  characters). The core point first.
- Every comparison is against **last month**. Never against the same month last year or an average you
  worked out.
- Report what happened and what is planned. Lead with the wins; pair a weak result with what we are
  doing about it.
- **Never suggest moving content from one platform to another.**
- **No invented reasons.** "Why it worked" rests on something visible in the post (what it shows, its
  format, its timing, a tag) or in its own figures. If nothing visible explains it, say what it showed
  and stop.
- Use "rose" or "fell" with `{key.change}`, so a sign never doubles up ("fell -12%").
- Looking ahead and every "planned" line come **only from the account manager's notes**: the chat and
  `pack.notes`. Do not add plans of your own. If there are no notes, ask for them before writing that
  page; with nobody to ask, write only what the notes and key dates hold.
- Speak as the agency to its client: "we", the client's name, plain words. UK spelling.
- **No em dashes.** Use a colon, a comma or a full stop.
- Post names are short and describe the post ("Ridge line carousel"), with no figures in them.

## Pages

`pack.pages` lists the pages this client has data for, in order. A page not in the list is not built.
Never add sample data to fill a page.

| Key | What the page shows |
|---|---|
| `cover` | client logo, month, data date |
| `key-outcomes` | follower tiles per channel, paid tiles with their cells, the top post |
| `meta-ads` | five headline cards, top five ads by spend |
| `google-ads` | five cards, campaign table, top search terms |
| `instagram`, `facebook` | the Content overview screenshot, large; new followers; top two posts |
| `tiktok` | four cards, engagement list, top three videos |
| `linkedin` | four cards, top posts table, visitor industries |
| `emailers` | four rate cards against benchmarks, the list-to-click funnel |
| `what-worked` | up to three posts: why it worked, how we do more of it |
| `content-insights` | pillar table, average reach by format, do more / keep / rework |
| `competitors` | Instagram followers for us and each competitor |
| `looking-ahead` | key dates in a left column, then every plan block; without dates the blocks use the full width in two columns |

## When something is off

- A problem says a placeholder is unknown: check the key against `pack.figures`; the figure may not
  exist for this client this month. Rewrite the line without it.
- `{key.mom}` or `{key.change}` is refused: the pack has no last-month figure for it. Do not compare.
- A problem says a ref is unknown: use only the refs the pack lists on that page.
- A warning says an image did not load: the stored image is gone or the link failed. The page shows a
  neutral block; name it in the final message.
- Never start the platform's own report run (`generate_report`, `build_report`, `start_report`) from
  this skill.
