# -*- coding: utf-8 -*-
# _mcv_scan.py -- INDEPENDENT consumer rescan (step 2/3).
# Runs: python -I -X utf8 <abs>/_mcv_scan.py   (stdout captured by shell redirection)
# Fresh implementation; does NOT import or reuse the author's _mc_scan.py / _mc_count.py.
# Traversal: os.walk with PRUNE set + DEPTH CAP. Two passes: CAP=6 (mimic) and CAP=99
# (effectively uncapped) so that anything hidden by the cap is detected.
# This script NEVER writes a file; it only prints to stdout.
import os, re, sys

ROOT = "D:\\Project\\ra2-campaign-forge"
PRUNE = {"__pycache__", ".git", ".mimosa", "node_modules", ".tmp", ".workbuddy",
         ".zcode", ".zcode-watch", ".dsh-watch", ".pi", ".commandcode",
         ".blind1_tmp", "%TEMP%qc95rev_pyc", "venv", ".venv", "site-packages"}
MAX_BYTES = 400000
SKIP_MARK = "\\merged_consumer_audit_20261109\\"

PATS = [
    ("link_triple_call", re.compile(r"\blink_triple\s*\(")),
    ("link_call",        re.compile(r"(?<!def )(?<![\w.])\blink\s*\(")),
    ("dot_link_call",    re.compile(r"\.\s*link\s*\(")),
    ("import_relinked",  re.compile(r"_re_linked")),
    ("import_sllink",    re.compile(r"_sl_link")),
    ("samedoc_link_tok", re.compile(r"samedoc_link|SAMEDOC_LINK")),
    ("verified_path",    re.compile(r"verified_path")),
    ("recomputed",       re.compile(r"recomputed")),
    ("path_subscript",   re.compile(r"\[\s*[\"']path[\"']\s*\]")),
    ("path_get",         re.compile(r"\.get\(\s*[\"']path[\"']")),
    ("match_tok",        re.compile(r"match")),
    ("bytes_subscript",  re.compile(r"\[\s*[\"']bytes[\"']\s*\]")),
    ("members",          re.compile(r"members")),
    ("r11_scan_plus_tok",re.compile(r"r11_scan_plus")),
    ("tier_tok",         re.compile(r"tier")),
]

def scan(cap):
    rows = []
    dv = sc = pr = sb = 0
    for cur, dirs, files in os.walk(ROOT):
        rel_dir = cur[len(ROOT):].lstrip("\\/")
        depth = 0 if not rel_dir else rel_dir.count(os.sep) + 1
        dv += 1
        kept = []
        for d in dirs:
            if d in PRUNE:
                pr += 1
                continue
            kept.append(d)
        dirs[:] = kept
        if depth >= cap:
            dirs[:] = []
        for fn in files:
            if not fn.endswith(".py"):
                continue
            fp = cur + os.sep + fn
            if SKIP_MARK in fp:
                continue
            try:
                if os.path.getsize(fp) > MAX_BYTES:
                    sb += 1
                    continue
                with open(fp, "rb") as f:
                    data = f.read()
            except Exception as e:
                rows.append((fp[len(ROOT) + 1:], {"ERR": str(e)}))
                continue
            sc += 1
            lines = data.decode("utf-8", "replace").splitlines()
            hits = {}
            for name, pat in PATS:
                ln = [i + 1 for i, L in enumerate(lines) if pat.search(L)]
                if ln:
                    hits[name] = ln[:40]
            rows.append((fp[len(ROOT) + 1:], hits))
    return {"cap": cap, "dirsVisited": dv, "scannedPy": sc, "prunedItems": pr,
            "skippedBig": sb, "rows": rows}

def main():
    results = {}
    for cap in (6, 99):
        results[cap] = scan(cap)
    for cap in (6, 99):
        s = results[cap]
        print("CAP=%d dirsVisited=%d scannedPy=%d prunedItems=%d skippedBig=%d" %
              (cap, s["dirsVisited"], s["scannedPy"], s["prunedItems"], s["skippedBig"]))
    for cap in (6, 99):
        s = results[cap]
        callers = [(rel, h) for rel, h in s["rows"]
                   if any(k in h for k in ("link_triple_call", "dot_link_call", "link_call"))]
        print("\nCAP=%d files_with_linkCALL=%d" % (cap, len(callers)))
        for rel, h in callers:
            print("  %s | ltc=%s dot=%s bare=%s" %
                  (rel, h.get("link_triple_call"), h.get("dot_link_call"), h.get("link_call")))
    set6 = {rel for rel, _ in results[6]["rows"]}
    extras = [(rel, h) for rel, h in results[99]["rows"] if rel not in set6]
    print("\nFILES_ONLY_IN_CAP99_depthGT6 = %d" % len(extras))
    for rel, h in extras:
        if any(k in h for k in ("link_triple_call", "dot_link_call", "link_call",
                                "import_relinked", "import_sllink", "samedoc_link_tok")):
            print("   LINK-RELEVANT_BEYOND_CAP6: %s hits=%s" % (rel, sorted(h)))
    # Full census rows (compact one-line each) so downstream analysis can be done offline.
    print("\n=== FULL_ROWS_CAP99 ===")
    for rel, h in results[99]["rows"]:
        if h:
            print("ROW %s :: %s" % (rel, ";".join("%s=%s" % (k, ",".join(str(x) for x in v))
                                                   for k, v in sorted(h.items()))))
    print("EXIT=0")

main()
