#!/usr/bin/env python3
"""Build the monthly report PDF from a pack and a copy file.

    build.py --pack pack.json --copy copy.json --out out/

Reads template/report.html (never changes it), renders the pages listed in
pack.pages in that order, writes out/report.html and prints it to
out/report.pdf with headless Chrome or Chromium. Standard library only.

It stops with a clear message when:
  - a placeholder in copy.json names a key that is not in pack.figures

Placeholders: {key} prints display, {key.mom} the MoM change with its sign,
{key.change} the same change without its sign (after "rose" or "fell"),
{key.prev} last month's display.
  - a takeaway line holds a digit outside a placeholder
  - copy.json has no takeaway for a page in pack.pages
"""

import argparse
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "report.html"

PAGE_KEYS = [
    "cover", "key-outcomes", "meta-ads", "google-ads", "instagram", "facebook", "tiktok",
    "linkedin", "emailers", "what-worked", "content-insights", "competitors", "looking-ahead",
]

# Longest takeaway that still fits on two lines at the template's size.
TAKEAWAY_MAX = 190


class BuildError(Exception):
    pass


# ---------------------------------------------------------------- placeholders

PLACEHOLDER = re.compile(r"\{([A-Za-z0-9_.]+)\}")


def resolve_placeholder(token, figures, where):
    if token in figures:
        return figures[token]["display"]
    for suffix in ("mom", "prev", "change"):
        base = token[: -(len(suffix) + 1)]
        if token.endswith("." + suffix) and base in figures:
            part = figures[base].get("prev" if suffix == "prev" else "mom")
            if not part or part.get("display") in (None, ""):
                raise BuildError(
                    f"{where}: {{{token}}} asks for the {suffix} of '{base}', but the pack has none for it this month."
                )
            if suffix == "change":
                # the MoM change without its sign, for copy such as "views fell {ig.views.change}"
                return part["display"].lstrip("+-− ")
            return part["display"]
    raise BuildError(f"{where}: placeholder {{{token}}} is not a key in pack.figures.")


def fill_text(text, figures, where, takeaway=False):
    if not isinstance(text, str):
        raise BuildError(f"{where}: expected text, got {type(text).__name__}.")
    if takeaway:
        bare = PLACEHOLDER.sub("", text)
        if re.search(r"\d", bare):
            raise BuildError(
                f"{where}: the takeaway holds a number typed by hand ({text!r}). "
                "Put every figure in through a placeholder such as {ig.views}."
            )
    out = PLACEHOLDER.sub(lambda m: resolve_placeholder(m.group(1), figures, where), text)
    leftover = PLACEHOLDER.sub("", text)
    if "{" in leftover or "}" in leftover:
        raise BuildError(f"{where}: stray brace in {text!r}. Placeholders look like {{ig.views}}.")
    return out


def fill_copy(node, figures, where):
    """Resolve placeholders in every string of a copy entry."""
    if isinstance(node, str):
        return fill_text(node, figures, where)
    if isinstance(node, list):
        return [fill_copy(v, figures, f"{where}[{i}]") for i, v in enumerate(node)]
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            out[k] = fill_text(v, figures, f"{where}.{k}", takeaway=True) if k == "takeaway" else fill_copy(v, figures, f"{where}.{k}")
        return out
    return node


# ---------------------------------------------------------------- template engine
#
# {{path}}                       escaped value; dotted paths, looked up from the innermost scope out
# {{#each path limit=N}}..{{/each}}   repeat for each item (at most N); {{@n}} is the 1-based index
# {{#if path}}..{{else}}..{{/if}}     truthy test; {{#unless path}}..{{/unless}}
# {{> name}}                     include <template data-partial="name">

TAG = re.compile(r"\{\{(.*?)\}\}", re.S)
MISSING = object()


def parse(src):
    root = []
    stack = [("root", None, root, None)]
    pos = 0
    for m in TAG.finditer(src):
        if m.start() > pos:
            stack[-1][2].append(("text", src[pos:m.start()]))
        pos = m.end()
        tag = m.group(1).strip()
        if tag.startswith("#"):
            kind, _, rest = tag[1:].partition(" ")
            args = rest.split()
            node = {"kind": kind, "path": args[0] if args else "", "opts": dict(a.split("=", 1) for a in args[1:]), "body": [], "else": []}
            stack[-1][2].append(("block", node))
            stack.append((kind, node, node["body"], tag))
        elif tag == "else":
            kind, node, _, _ = stack[-1]
            stack[-1] = (kind, node, node["else"], tag)
        elif tag.startswith("/"):
            if stack[-1][0] != tag[1:]:
                raise BuildError(f"template: {{{{{tag}}}}} closes {stack[-1][0]!r}")
            stack.pop()
        else:
            stack[-1][2].append(("var", tag))
    if len(stack) != 1:
        raise BuildError(f"template: {stack[-1][0]!r} block not closed")
    if pos < len(src):
        root.append(("text", src[pos:]))
    return root


def lookup(scopes, path):
    if path in ("this", "."):
        return scopes[-1]
    parts = path.split(".")
    for scope in reversed(scopes):
        if isinstance(scope, dict) and parts[0] in scope:
            value = scope[parts[0]]
            for p in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(p)
                elif isinstance(value, list) and p.isdigit() and int(p) < len(value):
                    value = value[int(p)]
                else:
                    return None
            return value
    return None


def truthy(v):
    return v not in (None, "", [], {}, False)


def render(nodes, scopes):
    out = []
    for kind, val in nodes:
        if kind == "text":
            out.append(val)
        elif kind == "var":
            v = lookup(scopes, val)
            out.append("" if v is None else html.escape(str(v), quote=True))
        else:
            node = val
            value = lookup(scopes, node["path"])
            if node["kind"] == "each":
                items = value if isinstance(value, list) else []
                limit = int(node["opts"].get("limit", 0)) or len(items)
                items = items[:limit]
                if items:
                    for i, item in enumerate(items):
                        out.append(render(node["body"], scopes + [{"@n": i + 1, "@count": len(items)}, item]))
                else:
                    out.append(render(node["else"], scopes))
            elif node["kind"] == "if":
                out.append(render(node["body"] if truthy(value) else node["else"], scopes))
            elif node["kind"] == "unless":
                out.append(render(node["else"] if truthy(value) else node["body"], scopes))
            else:
                raise BuildError(f"template: unknown block #{node['kind']}")
    return "".join(out)


# ---------------------------------------------------------------- images

class Assets:
    def __init__(self, out_dir, base_dir):
        self.dir = out_dir / "assets"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.base = base_dir
        self.cache = {}
        self.failed = []

    def get(self, url):
        """Return a path relative to out/ for the image, or None (the page shows a neutral block)."""
        if not url:
            return None
        if url in self.cache:
            return self.cache[url]
        try:
            data, ext = self._fetch(url)
            if not data or not looks_like_image(data):
                raise ValueError("not an image")
            name = f"img-{len(self.cache) + 1:02d}{ext}"
            (self.dir / name).write_bytes(data)
            rel = f"assets/{name}"
        except Exception as exc:  # any failure leaves a placeholder block
            self.failed.append(f"{url}: {exc}")
            rel = None
        self.cache[url] = rel
        return rel

    def _fetch(self, url):
        if url.startswith(("http://", "https://")):
            req = urllib.request.Request(url, headers={"User-Agent": "lbf-report-build/1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read(25 * 1024 * 1024)
                ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
            ext = mimetypes.guess_extension(ctype) or Path(url.split("?")[0]).suffix or ".img"
            return data, ".jpg" if ext == ".jpe" else ext
        path = Path(url[7:] if url.startswith("file://") else url)
        if not path.is_absolute():
            path = self.base / path
        return path.read_bytes(), path.suffix or ".img"


def looks_like_image(data):
    head = data[:64].lstrip()
    return (
        data[:8] == b"\x89PNG\r\n\x1a\n"
        or data[:3] == b"\xff\xd8\xff"
        or data[:6] in (b"GIF87a", b"GIF89a")
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
        or head.startswith(b"<svg")
        or head.startswith(b"<?xml")
    )


# ---------------------------------------------------------------- page context

ICONS = [("instagram", "instagram"), ("facebook", "facebook"), ("tiktok", "tiktok"), ("linkedin", "linkedin"),
         ("meta", "meta"), ("google", "google"), ("email", "email")]


def icon_for(label):
    low = (label or "").lower()
    for needle, icon in ICONS:
        if needle in low:
            return icon
    return "none"


def attach_figures(node, figures):
    """Every dict with a 'figure' key gets 'f', the figure itself (or a blank one)."""
    if isinstance(node, list):
        for v in node:
            attach_figures(v, figures)
    elif isinstance(node, dict):
        if isinstance(node.get("figure"), str):
            key = node["figure"]
            if key not in figures:
                raise BuildError(f"pack: page lists figure '{key}', which is not in pack.figures.")
            node["f"] = figures[key]
        for k, v in list(node.items()):
            if k != "f":
                attach_figures(v, figures)


def bar_pct(rows, field):
    values = [r.get(field) or 0 for r in rows]
    top = max(values) if values else 0
    for r, v in zip(rows, values):
        r["barPct"] = f"{(v / top * 100) if top else 0:.1f}"
        r["barSmall"] = top and v / top < 0.18


STAT_WORDS = {"views": "view", "likes": "like", "saves": "save", "shares": "share",
              "purchases": "purchase", "clicks": "click", "comments": "comment", "reposts": "repost"}
COUNT_WORD = re.compile(r"(?<![\d.,])([+\-]?[\d][\d.,]*[KkMm]?)\s+(" + "|".join(STAT_WORDS) + r")\b")


def counted(display, plural):
    """'1' share, '0' shares, '2.3K' views: singular only for exactly one."""
    if display in (None, ""):
        return None
    word = STAT_WORDS[plural] if str(display).lstrip("+") == "1" else plural
    return f"{display} {word}"


def singularise(text):
    """Fix '1 shares' in a line the server built, such as an ad's '1 purchases · R67'."""
    if not isinstance(text, str):
        return text
    return COUNT_WORD.sub(lambda m: counted(m.group(1), m.group(2)), text)


def stat_lines(p):
    parts1 = [counted(p.get("viewsDisplay"), "views"), counted(p.get("likesDisplay"), "likes")]
    parts2 = [counted(p.get("savesDisplay"), "saves"), counted(p.get("sharesDisplay"), "shares")]
    p["statLine1"] = " · ".join(x for x in parts1 if x)
    p["statLine2"] = " · ".join(x for x in parts2 if x)


def short_name(post):
    words = (post.get("caption") or "").split()
    name = " ".join(words[:6])
    return name + ("…" if len(words) > 6 else "") if name else f"{post.get('format') or 'Post'} · {post.get('dateLabel') or ''}".strip(" ·")


def prep_posts(posts, names, omit, assets, slots):
    out = []
    for p in posts or []:
        if not isinstance(p, dict) or p.get("id") in omit:
            continue
        p = dict(p)
        p["name"] = names.get(p.get("id")) or p.get("name") or short_name(p)
        p["img"] = assets.get(p.get("imageUrl"))
        stat_lines(p)
        for line in ("line1", "line2"):
            p[line] = singularise(p.get(line))
        out.append(p)
    return out[:slots]


def page_context(key, pack, copy_pages, omit, assets):
    figures = pack["figures"]
    raw = json.loads(json.dumps((pack.get("page") or {}).get(key) or {}))
    attach_figures(raw, figures)
    cp = copy_pages.get(key) or {}
    names = dict(cp.get("postNames") or {})
    ctx = {"page": raw, "copy": cp, "takeaway": cp.get("takeaway", "")}

    if key == "key-outcomes":
        for t in raw.get("channelTiles") or []:
            t["icon"] = icon_for(t.get("label"))
        for t in raw.get("paidTiles") or []:
            t["icon"] = icon_for(t.get("label"))
        top = raw.get("topPost")
        if top and top.get("id") not in omit:
            top["img"] = assets.get(top.get("imageUrl"))
            top["platformLabel"] = (top.get("platform") or "").replace("_", " ")
            stat_lines(top)
        else:
            raw["topPost"] = None
        ctx["foot"] = f"{pack['monthLabel']} · % changes are against {pack['prevMonthLabel']}"
    elif key == "meta-ads":
        raw["ads"] = prep_posts(raw.get("ads"), {}, omit, assets, 5)
    elif key == "google-ads":
        bar_pct(raw.get("searchTerms") or [], "clicks")
    elif key in ("instagram", "facebook"):
        raw["shot"] = assets.get(raw.get("screenshotUrl"))
        tile = raw.get("followersTile") or {}
        for part in ("new", "total"):
            if tile.get(part):
                if tile[part] not in figures:
                    raise BuildError(f"pack: {key}.followersTile.{part} names '{tile[part]}', which is not in pack.figures.")
                tile[part + "F"] = figures[tile[part]]
        raw["posts"] = prep_posts(raw.get("posts"), names, omit, assets, 2)
        ctx["footCenter"] = raw.get("audienceLine")
    elif key == "tiktok":
        raw["videos"] = prep_posts(raw.get("videos"), names, omit, assets, 3)
    elif key == "linkedin":
        bar_pct(raw.get("industries") or [], "pct")
    elif key == "emailers":
        funnel = raw.get("funnel") or {}
        bar_pct(funnel.get("steps") or [], "value")
        raw["creative"] = assets.get(raw.get("creativeUrl"))
        ctx["foot"] = raw.get("benchmarksLine")
    elif key == "what-worked":
        picks = {p.get("id"): p for p in cp.get("posts") or [] if isinstance(p, dict)}
        names.update({i: p.get("name") for i, p in picks.items() if p.get("name")})
        posts = prep_posts(raw.get("posts"), names, omit, assets, 3)
        for p in posts:
            p["why"] = (picks.get(p.get("id")) or {}).get("why")
            p["how"] = (picks.get(p.get("id")) or {}).get("how")
        raw["posts"] = posts
    elif key == "content-insights":
        bar_pct(raw.get("formats") or [], "avgReach")
        raw["formatLine"] = " · ".join(
            f"{f.get('countDisplay')} {f.get('format')}" for f in (raw.get("formats") or [])[:4] if f.get("countDisplay")
        )
    elif key == "looking-ahead":
        raw["keyDates"] = (raw.get("keyDates") or cp.get("keyDates")
                           or (pack.get("notes") or {}).get("keyDates") or [])
        blocks = [b for b in cp.get("blocks") or [] if isinstance(b, dict)]
        cp["blocks"] = blocks
        # no key dates: the blocks take the full width in two columns; with dates, two columns from four blocks
        raw["blocksTwoCols"] = len(blocks) >= (4 if raw["keyDates"] else 2)

    if "foot" not in ctx:
        ctx["foot"] = raw.get("footLine") or f"{pack['monthLabel']} · MoM is against {pack['prevMonthLabel']}"
    return ctx


# ---------------------------------------------------------------- main

def load_json(path, what):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BuildError(f"{what} file not found: {path}")
    except json.JSONDecodeError as exc:
        raise BuildError(f"{what} is not valid JSON: {exc}")


def split_template(src):
    pages = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(
        r'<template data-page="([a-z-]+)"([^>]*)>(.*?)</template>', src, re.S)}
    partials = {m.group(1): m.group(2) for m in re.finditer(
        r'<template data-partial="([a-z-]+)">(.*?)</template>', src, re.S)}
    shell = re.sub(r"<template data-(?:page|partial)=.*?</template>\s*", "", src, flags=re.S)
    if "<!--PAGES-->" not in shell:
        raise BuildError("template: <!--PAGES--> marker missing")
    return shell, pages, partials


def expand_partials(body, partials):
    for _ in range(5):
        new = re.sub(r"\{\{>\s*([a-z-]+)\s*\}\}", lambda m: partials[m.group(1)], body)
        if new == body:
            break
        body = new
    return body


def find_chrome():
    candidates = [os.environ.get("CHROME_BIN")] + [
        shutil.which(n) for n in ("google-chrome", "chromium", "chromium-browser", "google-chrome-for-testing")
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise BuildError(
        "No Chrome or Chromium found. Install one, or set CHROME_BIN to its path. "
        "Tried CHROME_BIN, google-chrome, chromium, chromium-browser, google-chrome-for-testing. "
        "out/report.html is written and can be printed by hand."
    )


def print_pdf(html_path, pdf_path):
    chrome = find_chrome()
    with tempfile.TemporaryDirectory(prefix="lbf-chrome-") as profile:
        cmd = [
            chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            f"--user-data-dir={profile}", "--no-pdf-header-footer", "--hide-scrollbars",
            "--run-all-compositor-stages-before-draw", "--virtual-time-budget=15000",
            f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri(),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if res.returncode != 0 or not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise BuildError(f"Chrome could not print the PDF (exit {res.returncode}).\n{res.stderr[-1500:]}")


def report_fit(html_path):
    """Read back what the page's fit script did, so a shrink or an overflow is never silent."""
    chrome = find_chrome()
    with tempfile.TemporaryDirectory(prefix="lbf-chrome-") as profile:
        res = subprocess.run([
            chrome, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={profile}",
            "--window-size=1280,720", "--virtual-time-budget=15000", "--dump-dom", html_path.resolve().as_uri(),
        ], capture_output=True, text=True, timeout=180)
    dom = res.stdout
    if 'data-fitted="1"' not in dom:
        print("warning: could not confirm that every page fits; look at each page of the PDF.", file=sys.stderr)
        return
    for m in re.finditer(r'<section class="page[^"]*" data-page="([a-z-]+)"([^>]*)>', dom):
        key, attrs = m.group(1), m.group(2)
        over = 'data-overflow="1"' in attrs
        fit = re.search(r'data-fit="([\d.]+)"', attrs)
        if over:
            print(f"warning: the {key} page still runs past its footer at 80% size. Shorten its copy.", file=sys.stderr)
        elif fit:
            print(f"warning: the {key} page was shrunk to {round(float(fit.group(1)) * 100)}% to fit. "
                  "Shorter copy would print larger.", file=sys.stderr)


def build(pack_path, copy_path, out_dir):
    pack = load_json(pack_path, "pack")
    copy = load_json(copy_path, "copy")
    if pack.get("schemaVersion") != 1:
        raise BuildError(f"pack.schemaVersion is {pack.get('schemaVersion')!r}; this template reads version 1.")
    for field in ("client", "month", "monthLabel", "prevMonthLabel", "pages", "figures"):
        if field not in pack:
            raise BuildError(f"pack has no '{field}'. Save the pack exactly as get_report_pack returned it.")

    pages = pack["pages"]
    unknown = [p for p in pages if p not in PAGE_KEYS]
    if unknown:
        raise BuildError(f"pack.pages has page keys this template does not know: {unknown}")

    figures = pack["figures"]
    copy_pages_in = copy.get("pages") or {}
    copy_pages = {}
    for key in pages:
        if key == "cover":
            continue
        entry = copy_pages_in.get(key)
        if not isinstance(entry, dict) or not str(entry.get("takeaway") or "").strip():
            raise BuildError(f"copy.json has no takeaway for page '{key}'. Every page in pack.pages needs one.")
        copy_pages[key] = fill_copy(entry, figures, f"copy.pages.{key}")
        if len(copy_pages[key]["takeaway"]) > TAKEAWAY_MAX:
            print(f"warning: the {key} takeaway is {len(copy_pages[key]['takeaway'])} characters; "
                  f"over {TAKEAWAY_MAX} it may not fit on two lines.", file=sys.stderr)
    omit = set(copy.get("omitPosts") or [])

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if (out_dir / "assets").exists():
        shutil.rmtree(out_dir / "assets")
    assets = Assets(out_dir, Path(pack_path).resolve().parent)

    shell, templates, partials = split_template(TEMPLATE.read_text(encoding="utf-8"))
    client = dict(pack["client"])
    data_uri = client.get("logoDataUri")
    if isinstance(data_uri, str) and re.match(r"data:image/(png|jpeg|webp|gif|svg\+xml);base64,[A-Za-z0-9+/=\s]+$", data_uri):
        client["logo"] = data_uri
    else:
        client["logo"] = assets.get(client.get("logoUrl"))
    root = {k: v for k, v in pack.items() if k not in ("page",)}
    root["client"] = client

    sections = []
    for key in pages:
        if key not in templates:
            raise BuildError(f"template has no layout for page '{key}'")
        attrs, body = templates[key]
        meta = dict(re.findall(r'data-([a-z]+)="([^"]*)"', attrs))
        ctx = page_context(key, pack, copy_pages, omit, assets)
        ctx.update({"pageKey": key, "kicker": meta.get("kicker"), "title": meta.get("title"), "icon": meta.get("icon")})
        tree = parse(expand_partials(body, partials))
        sections.append(render(tree, [root, ctx]).strip())

    doc = shell.replace("<!--PAGES-->", "\n".join(sections))
    html_path = out_dir / "report.html"
    html_path.write_text(doc, encoding="utf-8")
    print(f"wrote {html_path} ({len(sections)} pages: {', '.join(pages)})")
    for url in assets.failed:
        print(f"note: image not loaded, a neutral block is shown instead: {url}", file=sys.stderr)
    for m in pack.get("missing") or []:
        print(f"note: still missing: {m.get('message') or m.get('key')}", file=sys.stderr)

    pdf_path = out_dir / "report.pdf"
    if pdf_path.exists():
        pdf_path.unlink()
    print_pdf(html_path, pdf_path)
    print(f"wrote {pdf_path}")
    report_fit(html_path)


def main():
    ap = argparse.ArgumentParser(description="Build the monthly report PDF from pack.json and copy.json.")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--copy", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    try:
        build(args.pack, args.copy, args.out)
    except BuildError as exc:
        print(f"build stopped: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
