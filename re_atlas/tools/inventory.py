"""R0-a: corpus inventory for docs/re and sibling evidence dirs.

Emits a JSON index of every markdown/text artifact with cheap structural
metadata: size, heading count, hex-address density, and top-level headings.
Read-only: prints JSON to stdout, caller redirects.
"""

import json
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"
CORPUS_DIRS = [
    r"docs\re",
    r"docs\re\atlas_rev",
    r"lead\goal3_audit",
]

HEX_RE = re.compile(r"0x[0-9A-Fa-f]{4,8}")
HEAD_RE = re.compile(r"^(#{1,3})\s+(.*)$")


def scan_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    heads = []
    for line in text.splitlines():
        m = HEAD_RE.match(line.strip())
        if m:
            heads.append((len(m.group(1)), m.group(2).strip()[:120]))
    hexes = HEX_RE.findall(text)
    vas = set()
    for h in hexes:
        try:
            vas.add(int(h, 16))
        except ValueError:
            continue
    return {
        "rel": os.path.relpath(path, ROOT).replace("\\", "/"),
        "bytes": len(text.encode("utf-8", errors="replace")),
        "lines": text.count("\n") + 1,
        "hex_total": len(hexes),
        "hex_distinct": len(vas),
        "h1": [t for lv, t in heads if lv == 1][:3],
        "h2_count": sum(1 for lv, t in heads if lv == 2),
        "h2": [t for lv, t in heads if lv == 2][:40],
    }


def main():
    out = []
    for d in CORPUS_DIRS:
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        for name in sorted(os.listdir(full)):
            if not name.lower().endswith((".md", ".txt")):
                continue
            rec = scan_file(os.path.join(full, name))
            if rec:
                out.append(rec)
    out.sort(key=lambda r: r["hex_distinct"], reverse=True)
    print(json.dumps(out, ensure_ascii=False, indent=1))


main()
