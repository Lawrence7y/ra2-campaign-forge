"""Publish-time trimmer: reduce the RTTI dump to what the public repo may carry.

The full symbols.json lists every vtable slot of every class, which is close to
a whole vtable dump. What the knowledge base actually needs is, per class:
name, vtable VA, slot count, base chain. That is metadata, not code listing.

Read-only input; prints trimmed JSON to stdout.
"""

import json

SRC = r"D:\Project\ra2-campaign-forge\re_atlas\evidence\rtti\symbols.json"


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    rows = []
    for _k, c in d["classes"].items():
        rows.append({
            "name": c["name"],
            "vtable": c.get("vtable_va"),
            "slots": len(c.get("vfuncs") or []),
            "bases": c.get("bases"),
        })
    rows.sort(key=lambda r: r["name"])
    out = {
        "source": "re_atlas/tools/trim_rtti.py over ra2re rtti",
        "image_base": d.get("image_base"),
        "text_sha256": d.get("text_sha256"),
        "diagnostics": d.get("diagnostics"),
        "class_count": len(rows),
        "note": "per-class metadata only; vfunc slot addresses intentionally omitted",
        "classes": rows,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))


main()
