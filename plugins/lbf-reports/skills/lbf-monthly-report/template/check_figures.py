#!/usr/bin/env python3
"""List every number in the report PDF that the pack does not hold.

    check_figures.py --pack pack.json --pdf out/report.pdf

Reads the PDF text with pdftotext (poppler-utils), takes every number-like
token, and looks for it among the numbers in the pack's own strings: figure
displays, MoM and previous-month displays, row *Display fields, labels, dates
and lines. A token found nowhere in the pack is listed with its page.
Exit 0 when the list is empty, 1 when it is not, 2 when it cannot run.
Standard library only.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys

# A number with an optional sign directly in front: +160, -6, 4,632.50, 0.11
NUMBER = re.compile(r"(?<![\d.,])[+\-]?\d+(?:[.,]\d+)*")
SKIP_KEYS = {"imageUrl", "permalink", "logoUrl", "screenshotUrl", "creativeUrl", "id", "slug", "month", "value"}


def normalise(text):
    for ch in ("\u2212", "\u2013", "\u2011"):
        text = text.replace(ch, "-")
    return text.replace("\u00a0", " ").replace("\u202f", " ")


def tokens(text):
    return [m.group(0).rstrip(".,") for m in NUMBER.finditer(normalise(text))]


def pack_strings(node, key=None):
    if key in SKIP_KEYS or (isinstance(key, str) and key.startswith("_")):
        return
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from pack_strings(v, k)
    elif isinstance(node, list):
        for v in node:
            yield from pack_strings(v, key)


def main():
    ap = argparse.ArgumentParser(description="List numbers in the report PDF that are not in the pack.")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--pdf", required=True)
    args = ap.parse_args()

    if not shutil.which("pdftotext"):
        print("pdftotext is not installed, so the PDF text cannot be read. "
              "Install poppler-utils (apt install poppler-utils, or brew install poppler) and run again.",
              file=sys.stderr)
        sys.exit(2)
    try:
        pack = json.load(open(args.pack, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read the pack: {exc}", file=sys.stderr)
        sys.exit(2)

    known = set()
    for s in pack_strings(pack):
        for t in tokens(s):
            known.add(t)
            known.add(t.lstrip("+-"))  # a pack "-6%" may print as "6%" after "fell"

    res = subprocess.run(["pdftotext", "-layout", args.pdf, "-"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"pdftotext failed: {res.stderr.strip()}", file=sys.stderr)
        sys.exit(2)

    unknown = []
    pages = res.stdout.split("\f")
    for n, page in enumerate(pages, 1):
        for line in page.splitlines():
            for t in tokens(line):
                if t not in known:
                    unknown.append((n, t, line.strip()))

    count = sum(len(tokens(p)) for p in pages)
    if not unknown:
        print(f"ok: all {count} numbers in the PDF are in the pack.")
        sys.exit(0)
    print(f"{len(unknown)} number(s) in the PDF are not in the pack:")
    for n, t, line in unknown:
        print(f"  page {n}: {t!r} in: {line[:110]}")
    sys.exit(1)


if __name__ == "__main__":
    main()
