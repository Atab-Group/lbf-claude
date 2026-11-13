---
name: monthly-report
description: Use when the person wants to do a client's monthly report end to end from Claude Code: pull the month's data, upload the Meta screenshots and their notes and start the report, watch it and open the finished deck, ask for a change to a page, upload a client document or a polished deck, or push the deck to Canva.
---

# The monthly report, start to finish

Read `lbf-platform` first if you have not this session. Every step below uses the `lbf` tools, scoped to
the clients this person manages. The platform's own report agent writes the deck; you give it inputs, ask
it for changes, and move the files. You never write the pages yourself.

Confirm the client and the month back to the person before any step that starts work. A month is
`YYYY-MM`; the report for a month is written after that month has closed.

## 1. Pull the month's data

1. `list_clients` for the slug.
2. Read what the person asks about: `get_client_overview`, `get_platform_detail`, `get_paid_breakdown`, or
   the generic loop `get_options`, `get_fields`, `get_data`.
3. For everything as files, `export_bundle_link` gives a zip of CSV and JSON. Fetch it with the same
   `Authorization: Bearer` header this plugin connects with.

## 2. Upload the screenshots and notes, and start the report

The start inputs are the Instagram and Facebook overview screenshots from Meta Business Suite for the
month, the month's highlights, and the look-ahead notes.

1. For each screenshot, `create_upload` returns a one-time upload link. PUT the file to it (for example
   `curl -T instagram.png "<link>"`), or give the link to the person to open in a browser.
2. `start_report` with the client, the month, the two uploads, the highlights and the look-ahead notes.
3. If the month has not closed in the platform yet, the answer says the report is waiting for the month to
   close and will start on its own. Tell the person that.

If `create_upload` or `start_report` is not in your tool list, the platform has not shipped it yet: tell
the person to start the report in the app.

## 3. Watch it and open the finished deck

1. Poll `get_job` with the `jobId` from `start_report`. A report takes up to an hour: tell the person it is
   running and check back, rather than polling for the whole hour.
2. When it is ready, `get_report_deck` gives links to the PDF, the PPTX and one PNG per page. They work for
   15 minutes with a plain GET and no Authorization header, so download them straight away (for example
   `curl -o deck.pdf "<pdf url>"`). Ask again for fresh links; never keep old ones.
3. `pdf.url` is null while the PDF of the newest version is still rendering: the PPTX link works already.

## 4. Change a page

1. `list_report_pages` shows the pages and their ids.
2. `request_report_edit` with the client, the month and the change in the person's own words, one change
   per call ("make the Instagram takeaway shorter", "swap the top post for the reel"). Pass `pageId` to
   point it at one page.
3. The platform's report agent makes the change as the person, on the same thread as the report editor in
   the app, so it waits behind anything they are already asking it there. Poll `get_job`; its `turn` field
   shows the agent's progress and its answer.
4. Then `get_report_deck` for the new files.

A sent report cannot be changed, and a report being rewritten cannot be changed until it lands: the answer
says so in `refused`.

## 5. Upload a client document or a polished deck

1. `create_upload` for the file, then PUT it to the link.
2. `add_client_document` for a PDF or markdown document about the client (a scope of work, a brief). The
   report agent reads it from then on.
3. `add_reference_deck` for a polished deck the team made by hand, for one month. The report agent looks at
   it when writing later months.

If either verb is not in your tool list, the platform has not shipped it yet: tell the person to upload it
in the app.

## 6. Push the deck to Canva

`push_report_to_canva` with the client and the month. Every push makes a NEW Canva design, so push once,
when the person says the deck is final. Poll `get_job`; the result carries `canvaUrl`. `pushed: false` with
a reason means the client has reached its monthly Canva limit, or a report run is still going: tell the
person, do not retry.

## Sending

Do not send from here. Sending to the client is held for a person to approve in the app.
