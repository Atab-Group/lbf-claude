---
name: lbf-monthly-report
description: Use when an account manager asks to build, make or redo the monthly report for a Let's Be Frank client, for example "build the monthly report for <client>", "build the October report for <client>", "make <client>'s report". Turns the platform's report pack, the two Meta Content overview screenshots and the account manager's notes into a PDF in the agency's 13-page layout.
---

# Build a client's monthly report

You build one client's report for one month as a PDF. The platform supplies every figure in a JSON
"pack". You write the words. `template/build.py` puts both into the fixed layout and prints the PDF.
You never calculate, round or type a figure yourself.

Files in this folder:

- `pack.schema.json`: the shape of the pack and of `copy.json`, with the rules that bind them.
- `template/report.html`: the 13 page layouts. Never edit it for a client.
- `template/build.py`: makes `out/report.html` and `out/report.pdf`.
- `template/check_figures.py`: lists every number in the PDF that is not in the pack.
- `fixtures/`: a fictional client ("Sample Trail Run") to see what a full pack and copy look like.

## Before you start

- The `lbf` MCP tools must answer. If `get_report_pack` fails or the tools are missing, **stop and say
  so**. Never build a report from memory, from an old pack, or from figures read off a screenshot alone.
- You need Python 3 and Chrome or Chromium on this machine (`build.py` finds `google-chrome`,
  `chromium`, `chromium-browser` or `google-chrome-for-testing`, or the path in `CHROME_BIN`), and
  `pdftotext` (poppler-utils) for the figure check.
- Work in a folder of its own, for example `~/lbf-reports/<client-slug>-<YYYY-MM>/`. The skill folder
  is read-only for you.
- Use `list_clients` to turn the client's name into its slug. Months are `YYYY-MM`.

## The steps

### 1. The account manager asks

They name the client and the month, attach the two Meta Business Suite "Content overview" screenshots
(one for Instagram, one for Facebook, both for the report month) and add any notes. If a screenshot is
missing, ask for it once. If they say there is none, carry on: that page shows a neutral block.

### 2. Read the pack and the content calendar

1. Call `get_report_pack` (client, month). Read `pages`, `missing` and `notes`.
2. If the client has a content calendar Google Sheet (the account manager names it, or it is in the
   client's documents), read it:
   - In Claude Code, with the `gws` command-line tool, signed in as the user:
     `gws drive files list --params '{"q": "name contains \"calendar\"", "pageSize": 20}'` to find it,
     then `gws sheets +read --spreadsheet <id> --range "<tab>"` for the month's tab.
   - On other surfaces, with the Google Drive connector.
   - If the sign-in fails, say so and carry on without it. The Content insights page then has no
     calendar pillars.
3. Turn the month's rows into `{date, pillar, format, title}` (date as `YYYY-MM-DD`) and call
   `save_content_calendar` (client, month, rows). Tell the account manager which rows did not match a
   post; do not guess a match for them.

### 3. One confirm table

1. Read both screenshots: views, from organic, from ads, reach (Instagram) or viewers (Facebook),
   content interactions, and watch time where it shows. Read exactly what is printed.
2. For each competitor (the handles in `page.competitors.rows`, or `competitor_instagram` from
   `get_client_overview`), look up the Instagram follower count on the web (the public profile). Note
   the page you read it from and today's date.
3. Show **one** table: the screenshot figures for each platform, then each competitor with its count and
   source. Where a count is rounded ("12.4K") or missing, write "please type the exact number" in that
   cell. The account manager types those numbers from the Instagram app.
4. Wait for a yes or corrections. This is the only stop before the PDF.
5. On yes:
   - Where the surface can upload a file, send each screenshot with `create_upload` (kind `screenshot`,
     month, platform, contentType, sizeBytes), PUT the bytes to the returned link, and keep the
     `upload_id`.
   - Call `save_screenshot_figures` (client, month, platform, figures, upload_id?) once for `instagram`
     and once for `facebook`. `upload_id` is optional.
   - Call `save_competitor_followers` (client, month, rows), one row per handle, with the count, the
     source link and the date read.
   - Writes return a job handle: poll `get_job` until `done`, and read any refusal.

The argument names above are the plan's. The tool schema is the final word on spelling: the platform
names the client `clientRef` and the upload `uploadId`.

### 4. Build the PDF

1. Call `get_report_pack` again, now that the figures are saved. Save the answer as `pack.json`
   **exactly as returned**. Do not edit it.
2. Write `copy.json` (shape in `pack.schema.json` under `copy`; an example is
   `fixtures/sample-copy.json`). One entry per page in `pack.pages`, except `cover`.
3. Run:
   ```
   python3 <skill>/template/build.py --pack pack.json --copy copy.json --out out/
   python3 <skill>/template/check_figures.py --pack pack.json --pdf out/report.pdf
   ```
   `build.py` stops and says why when a placeholder names a key that is not in `pack.figures`, when a
   takeaway holds a number typed by hand, or when a page in `pack.pages` has no takeaway. Fix
   `copy.json` and run it again. `check_figures.py` must print `ok`. If it lists a number, find it in
   `copy.json` and replace it with a placeholder or take it out.
4. Show the PDF (`out/report.pdf`). Also tell the account manager what `pack.missing` still lists and
   which images did not load (the build prints both).

### 5. Changes

The account manager asks for changes in plain words. Edit `copy.json` only, then run `build.py` and
`check_figures.py` again and show the new PDF. A figure that looks wrong is not edited in the copy:
say which figure, and check it at the source (the screenshot table, or the platform).

### 6. Upload

Only on the account manager's yes:

1. `create_upload` with kind `report_deck`, the month, contentType `application/pdf` and the file's
   sizeBytes. PUT the PDF bytes to the link.
2. `upload_report_deck` (client, month, upload_id). Poll `get_job` until `done`.

Nothing is sent to the client. The account manager sends the PDF themselves, from their own email.

## Writing copy.json

### What each page needs

| Page | Fields |
|---|---|
| every page but `cover` | `takeaway` |
| `instagram`, `facebook`, `tiktok` | `postNames`: `{post id: short name}` for the posts the pack lists |
| `google-ads` | `nextLine`, optional: "Next: ..." |
| `what-worked` | `posts`: `[{id, name, why, how}]` for the posts the pack lists, in its order |
| `content-insights` | `doMore`, `keep`, `rework` |
| `looking-ahead` | `blocks`: up to three `{heading, text}` |
| top level | `omitPosts`: ids of pack posts to leave out |

The pack decides which posts, ads and videos a page shows. You name them and may leave one out with
`omitPosts`; you never pick other posts.

### Figures: placeholders only

Every figure in your text goes in as a placeholder that names a key in `pack.figures`:

- `{ig.views}` prints the figure ("73.5K")
- `{ig.views.mom}` prints the change on last month with its sign ("-12.4%")
- `{ig.views.change}` prints the same change without its sign, for "rose" or "fell" ("12.4%")
- `{ig.views.prev}` prints last month's figure

A takeaway with any digit outside a placeholder is refused by `build.py`. Other lines (`why`, `how`,
blocks) are not refused, but `check_figures.py` lists any number in them that the pack does not hold,
and the rule is the same: no hand-typed figures anywhere.

### Copy rules

- One heading and **one short takeaway line** per page, directly under the heading. Aim for one line;
  two at most (about 190 characters). The core point first.
- Every comparison is against **last month**. Never against the same month last year or an average you
  worked out.
- Report what happened and what is planned. Lead with the wins; pair a weak result with what we are
  doing about it.
- **Never suggest moving content from one platform to another.**
- **No invented reasons.** "Why it worked" rests on something visible in the post (what it shows, its
  format, its timing, a tag) or in its own figures. If nothing visible explains it, say what it showed
  and stop.
- Use "rose" or "fell" with `{key.change}`, so a sign never doubles up ("fell -12%").
- Looking ahead and every "planned" line come **only from the account manager's notes**: the notes in
  the chat and `pack.notes` (`lookAhead`, `highlights`, `keyDates`). Do not add plans of your own. If
  there are no notes, ask for them before writing that page.
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
| `looking-ahead` | key dates, up to three plan blocks |

Post and ad images sit in 4:5 frames, cropped to fill. None is wider than square.

## When something is off

- `build.py` says a placeholder is unknown: check the key against `pack.figures`; the figure may not
  exist for this client this month. Rewrite the line without it.
- `{key.mom}` or `{key.change}` is refused: the pack has no last-month figure for it. Do not compare.
- An image shows as a grey block: the link was empty or failed. Call `get_report_pack` again for fresh
  links (they last 7 days) and rebuild.
- No Chrome found: install Chrome or Chromium, or set `CHROME_BIN`. `out/report.html` is already written.
- Never start the platform's own report run (`generate_report`, `build_report`, `start_report`) from
  this skill.
