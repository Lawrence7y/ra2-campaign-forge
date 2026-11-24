#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W35 helper: compare real_pre.json vs real_post.json and write REAL_DIR_PROOF.txt."""
from __future__ import annotations

import json
from pathlib import Path

W39 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W39_mapselmd_live2")
OUT = W39 / "out"


def main() -> int:
    pre = json.loads((OUT / "real_pre.json").read_text(encoding="utf-8"))
    post = json.loads((OUT / "real_post.json").read_text(encoding="utf-8"))
    am = {x["rel"]: x for x in pre["files"]}
    bm = {x["rel"]: x for x in post["files"]}
    added = sorted(set(bm) - set(am))
    removed = sorted(set(am) - set(bm))
    changed = [k for k in sorted(set(am) & set(bm)) if am[k] != bm[k]]
    identical_tree = (pre["files"] == post["files"])

    lines = [
        "# REAL_DIR_PROOF - D:\\Project\\ra2-campaign-forge\\ra2youli",
        f"PRE : file_count={pre['file_count']} total_bytes={pre['total_bytes']} maplike_count={pre['maplike_count']}",
        f"POST: file_count={post['file_count']} total_bytes={post['total_bytes']} maplike_count={post['maplike_count']}",
        f"added={len(added)} {added[:10]}",
        f"removed={len(removed)} {removed[:10]}",
        f"changed={len(changed)} {changed[:10]}",
        f"IDENTICAL_TREE={identical_tree}",
        "",
        "Key reference SHA-256 (POST):",
        f"  RA2MD.INI             = {bm['RA2MD.INI']['sha256']}",
        f"  gamemd.exe            = {bm['gamemd.exe']['sha256']}",
        f"  ddraw.dll             = {bm['ddraw.dll']['sha256']}",
        f"  ra2forge_install.json = {bm['ra2forge_install.json']['sha256']}",
    ]
    text = "\n".join(lines) + "\n"
    (W39 / "REAL_DIR_PROOF.txt").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if identical_tree else 1


if __name__ == "__main__":
    raise SystemExit(main())
