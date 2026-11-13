---
name: monthly-report
description: Use when the person wants to do a client's monthly report end to end from Claude: pull the month's data, upload the Meta screenshots and notes and start the report, watch it, download the finished deck, ask for a change to a page, edit the deck themselves and upload their own version, upload a client document or a polished deck, or push the deck to Canva. Also carries the do's and don'ts for how LBF runs reports.
---

# The monthly report, start to finish

Read `lbf-platform` first if you have not this session. Every step below uses the `lbf` tools, scoped to
the clients this person manages. The platform's own report agent writes the deck. You give it inputs, ask
it for changes, move the files, and, when the person wants to, hand back a deck they edited themselves.

If a tool named below is not in your tool list, the platform has not shipped it yet: say so and tell the
person to do that step in the app.

## The month at a glance

1. The month closes (South African time). The platform re-pulls the month's data.
2. The account manager gives the start inputs: the Instagram and Facebook screenshots, the highlights and
   the look-ahead notes. A report does not run until they start it.
3. The report agent writes the deck (up to an hour).
4. The team reviews it: asks for changes, or downloads it, edits it and uploads their own version.
5. The final deck goes to Canva once.
6. A person sends it from the app.

## 1. Pull the month's data

1. `list_clients` for the slug.
2. Read what the person asks about: `get_client_overview`, `get_platform_detail`, `get_paid_breakdown`, or
   the generic loop `get_options`, `get_fields`, `get_data`.
3. For everything as files, `export_bundle_link` gives a zip of CSV and JSON. Fetch it with the same
   `Authorization: Bearer` header this connection uses.

## 2. Upload the screenshots and notes, and start the report

The start inputs are the Instagram and Facebook overview screenshots from Meta Business Suite for the whole
month, the month's highlights, and the look-ahead notes.

1. For each screenshot, `create_upload` returns a one-time upload link. PUT the file to it (for example
   `curl -T instagram.png "<link>"`), or give the link to the person to open in a browser.
2. `start_report` with the client, the month, the two uploads, the highlights and the look-ahead notes.
3. If the month has not closed yet, the answer says the report is waiting and will start on its own once
   it closes. Tell the person that.

## 3. Watch it and download the deck

1. Poll `get_job` with the `jobId` from `start_report`. A report takes up to an hour: tell the person it is
   running and check back later, rather than polling for the whole hour.
2. When it is ready, `get_report_deck` gives links to the PPTX, the PDF and one PNG per page. They work for
   15 minutes with a plain GET and no Authorization header, so download them straight away (for example
   `curl -o deck.pptx "<pptx url>"`). Ask again for fresh links; never keep old ones.
3. `pdf.url` is null while the PDF of the newest version is still rendering. The PPTX link already works.

## 4. Change a page through the report agent

1. `list_report_pages` shows the pages and their ids.
2. `request_report_edit` with the client, the month and the change in the person's own words, one change
   per call ("make the Instagram takeaway shorter", "swap the top post for the reel"). Pass `pageId` to
   point it at one page.
3. The report agent makes the change as the person, on the same thread as the report editor in the app.
   Poll `get_job`; its `turn` field shows the agent's progress and its answer.
4. Then `get_report_deck` for the new files.

## 5. Use your own version of the deck

When the person would rather edit the deck themselves (in PowerPoint, Keynote or Canva):

1. Download the PPTX with `get_report_deck` (step 3).
2. The person edits it on their own machine.
3. `create_upload` with kind `report_deck` and the file's size, PUT the PPTX or PDF to the link.
4. `upload_report_deck` with the client, the month and the `uploadId`. Their file becomes the month's
   current deck: `get_report_deck` now returns it, `push_report_to_canva` pushes it, the app shows it as
   the team's own file, and the report agent learns from it for later months.
5. To go back to the platform's deck, `revert_report_deck`. The platform's deck is always kept.

While their own file is the current deck, `request_report_edit` refuses: the agent cannot edit their file
page by page. Edit the file and upload it again, or revert first.

## 6. Upload a client document or a polished deck

1. `create_upload` for the file, then PUT it to the link.
2. `add_client_document` for a PDF or markdown document about the client (a scope of work, a brief). The
   report agent reads it from then on.
3. `add_reference_deck` for a polished deck the team made by hand for a past month. The report agent looks
   at it when it writes later months. This does not change the current deck: use step 5 for that.

## 7. Push the deck to Canva

`push_report_to_canva` with the client and the month. It pushes whatever the current deck is, the
platform's or the team's own. Every push makes a NEW Canva design, so push once, when the person says the
deck is final. Poll `get_job`; the result carries `canvaUrl`. `pushed: false` with a reason means the
client has reached its monthly Canva limit or a report run is still going: tell the person, do not retry.

## Do

- **Confirm the client and the month back to the person** before any step that starts work or changes the
  deck.
- **Read every number from the tools.** Null means the platform does not report it; it is not zero. Money
  is rand (ZAR).
- **Use the whole month's overview screenshots** from Meta Business Suite, one for Instagram and one for
  Facebook, for the month being reported.
- **Keep the highlights and notes in the account manager's words.** Lead with wins; pair a weak result
  with what the team is doing about it.
- **Ask for one change per edit request**, and point it at a page when you can.
- **Download deck links straight away**, and ask again when they expire.
- **Upload the person's own version** when they have edited the deck outside the platform, so the app,
  Canva and next month's report all see the same file.
- **Pass an `idempotencyKey`** on any write you might retry.
- **Tell the person what a refusal says.** A `refused` or `accepted: false` answer is the platform
  explaining itself.

## Don't

- **Don't start or regenerate a report to check or fix something.** A run spends model budget and
  replaces the draft. Run one only when the person asks, for that client and month.
- **Don't send the report.** Sending is done by a person in the app.
- **Don't push to Canva to preview.** Every push is a new design and counts against the monthly limit.
- **Don't change a figure** in copy, and don't invent one the tools did not return.
- **Don't retry a refusal.** Only `error(internal)` is worth one retry.
- **Don't mix clients or months.** An upload belongs to one client and one month.
- **Don't keep download links** or paste them into other places. They expire in 15 minutes.
- **Don't use em dashes in client copy.** Use a colon or a comma, and UK spelling.
- **Don't ask the report agent for edits while the team's own file is current.** Edit the file, or revert
  first.
