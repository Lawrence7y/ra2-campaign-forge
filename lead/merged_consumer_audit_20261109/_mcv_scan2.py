# -*- coding: utf-8 -*-
# _mcv_scan2.py -- INDEPENDENT consumer rescan, efficient (step 2/3).
# Runs: python -I -B -X utf8 <abs>/_mcv_scan2.py > <abs>/_mcv_scan2_out.txt
# Fresh implementation; does NOT import/reuse author's scripts.
# Traversal: os.walk, PRUNE set + DEPTH CAP. Two passes: CAP=6 (author's scale) and
# CAP=99 (effectively uncapped). A byte-level prefilter skips regex work on files that
# cannot contain any link-family / binding_rec token. Prints stdout only; writes nothing.
import os, re, sys

ROOT = "D:\\Project\\ra2-campaign-forge"
PRUNE = {"__pycache__", ".git", ".mimosa", "node_modules", ".tmp", ".workbuddy",
         ".zcode", ".zcode-watch", ".dsh-watch", ".pi", ".commandcode",
         ".blind1_tmp", "%TEMP%qc95rev_pyc", "venv", ".venv", "site-packages"}
SKIP = "merged_consumer_audit_20261109"
MAX_BYTES = 400000

# discriminating byte tokens -- a file must contain at least one to be regex-scanned
KEY = (b"link", b"verified_path", b"recomputed", b"r11_scan_plus", b"samedoc_link",
       b"SAMEDOC_LINK", b"members")

PATS = [
    ("link_triple_call", re.compile(r"\blink_triple\s*\(")),
    ("dot_or_bare_link_call", re.compile(r"(?:^|[^.\w])\blink\s*\(|\.\s*link\s*\(")),
    ("import_relinked",  re.compile(r"_re_linked")),
    ("import_sllink",    re.compile(r"_sl_link")),
    ("samedoc_link",     re.compile(r"samedoc_link|SAMEDOC_LINK")),
    ("verified_path",    re.compile(r"verified_path")),
    ("recomputed",       re.compile(r"recomputed")),
    ("path_subscript",   re.compile(r"\[\s*[\"']path[\"']\s*\]")),
    ("path_get",         re.compile(r"\.get\(\s*[\"']path[\"']")),
    ("bytes_subscript",  re.compile(r"\[\s*[\"']bytes[\"']\s*\]")),
    ("members",          re.compile(r"members")),
    ("r11_scan_plus",    re.compile(r"r11_scan_plus")),
    ("match_true_guard", re.compile(r"\bmatch\b.{0,24}(?:is|==)\s*(?:not\s+)?True|"
                                    r"(?:is|==)\s*(?:not\s+)?True.{0,24}\bmatch\b")),
]

def scan(cap):
    rows = []
    dv = sc = pr = sb = prefilter_skips = 0
    for cur, dirs, files in os.walk(ROOT):
        rel_dir = cur[len(ROOT):].lstrip("\\/")
        depth = 0 if not rel_dir else rel_dir.count(os.sep) + 1
        dv += 1
        kept = [d for d in dirs if d not in PRUNE]
        pr += len(dirs) - len(kept)
        dirs[:] = kept
        if depth >= cap:
            dirs[:] = []
        for fn in files:
            if not fn.endswith(".py"):
                continue
            fp = cur + os.sep + fn
            if SKIP in fp:
                continue
            rel = fp[len(ROOT) + 1:]
            try:
                sz = os.path.getsize(fp)
                if sz > MAX_BYTES:
                    sb += 1
                    continue
                with open(fp, "rb") as f:
                    data = f.read()
            except Exception as e:
                rows.append((rel, {"ERR": str(e)}))
                continue
            sc += 1
            if not any(k in data for k in KEY):
                prefilter_skips += 1
                continue
            lines = data.decode("utf-8", "replace").splitlines()
            hits = {}
            for name, pat in PATS:
                ln = [i + 1 for i, L in enumerate(lines) if pat.search(L)]
                if ln:
                    hits[name] = ln[:30]
            if hits:
                rows.append((rel, hits))
    return {"cap": cap, "dirsVisited": dv, "scannedPy": sc, "prunedItems": pr,
            "skippedBig": sb, "prefilterSkips": prefilter_skips, "rows": rows}

def main():
    r6, r99 = scan(6), scan(99)
    for s in (r6, r99):
        print("CAP=%d dirsVisited=%d scannedPy=%d prunedItems=%d skippedBig=%d prefilterSkips=%d hitFiles=%d" %
              (s["cap"], s["dirsVisited"], s["scannedPy"], s["prunedItems"],
               s["skippedBig"], s["prefilterSkips"], len(s["rows"])))
    # (a) files that CALL link()/link_triple()
    for s in (r6, r99):
        callers = [(rel, h) for rel, h in s["rows"]
                   if "link_triple_call" in h or "dot_or_bare_link_call" in h]
        print("\nCAP=%d files_with_linkCALL=%d" % (s["cap"], len(callers)))
        for rel, h in sorted(callers):
            print("  %s | ltc=%s link=%s" % (rel, h.get("link_triple_call"),
                                              h.get("dot_or_bare_link_call")))
    # (b) files reading verified_path / path / bytes subscript
    for s in (r6, r99):
        readers = [(rel, h) for rel, h in s["rows"]
                   if any(k in h for k in ("verified_path", "path_subscript", "path_get",
                                           "bytes_subscript", "recomputed"))]
        print("\nCAP=%d files_reading_pathish=%d" % (s["cap"], len(readers)))
    # (c) match=True guard files
    print("\n=== MATCH_TRUE_GUARD FILES (CAP99) ===")
    for rel, h in sorted(r99["rows"]):
        if "match_true_guard" in h:
            print("  %s | guard_lines=%s" % (rel, h["match_true_guard"]))
    # cross-depth difference: anything beyond cap=6 that is link-relevant
    set6 = {rel for rel, _ in r6["rows"]}
    extras = [(rel, h) for rel, h in r99["rows"] if rel not in set6]
    print("\nFILES_ONLY_IN_CAP99_depthGT6 = %d" % len(extras))
    nlink = 0
    for rel, h in sorted(extras):
        if any(k in h for k in ("link_triple_call", "dot_or_bare_link_call",
                                "import_relinked", "import_sllink", "samedoc_link",
                                "r11_scan_plus", "verified_path")):
            nlink += 1
            print("  LINK-RELEVANT_BEYOND_CAP6: %s hits=%s" % (rel, sorted(h)))
    print("LINK_RELEVANT_BEYOND_CAP6_COUNT = %d" % nlink)
    print("EXIT=0")

main()
