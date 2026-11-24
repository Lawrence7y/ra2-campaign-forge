# -*- coding: utf-8 -*-
# _mcf_scan.py — independent full-repo consumer scan with pruning + depth cap.
# READ-ONLY: prints stdout only, writes nothing. sys.dont_write_bytecode=True.
import sys
sys.dont_write_bytecode = True
import os, re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
PRUNE = {"__pycache__", ".git", ".mimosa", "node_modules", ".tmp", ".venv", "venv",
         "site-packages", ".pytest_cache", "dist", "build"}
DEPTH_CAP = 6
MAX_BYTES = 400000

RE_LINK_CALL = re.compile(r"\b(?:SL|sl|RE|re|P\.SL|mod|m)\.(?:link|link_triple)\s*\(")
RE_R11PLUS = re.compile(r"\br11_scan_plus\s*\(")
RE_R11 = re.compile(r"\br11_scan\s*\(")
RE_LINK_TRIPLE_ANY = re.compile(r"\blink_triple\s*\(")
RE_RELINKED = re.compile(r"_re_linked")
RE_VP = re.compile(r"verified_path")
RE_PATHSUB = re.compile(r"\[\s*[\"'](?:path|verified_path|recomputed|bytes)[\"']\s*\]")
RE_GETMATCH = re.compile(r"\.get\(\s*[\"']match[\"']")
RE_BYTESUB = re.compile(r"\[\s*[\"']bytes[\"']\s*\]")

stats = {"dirsVisited": 0, "scannedPy": 0, "prunedItems": 0}
rows = []

def walk(d, depth):
    if depth > DEPTH_CAP:
        return
    stats["dirsVisited"] += 1
    try:
        entries = sorted(os.scandir(d), key=lambda e: e.name)
    except OSError:
        return
    for e in entries:
        if e.name in PRUNE:
            stats["prunedItems"] += 1
            continue
        if e.is_dir(follow_symlinks=False):
            walk(e.path, depth + 1)
        elif e.is_file(follow_symlinks=False) and e.name.endswith(".py"):
            try:
                if e.stat().st_size > MAX_BYTES:
                    continue
                txt = Path(e.path).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            stats["scannedPy"] += 1
            rel = os.path.relpath(e.path, str(ROOT)).replace("\\", "/")
            lines = txt.splitlines()
            linkcalls = [(i + 1, l.strip()) for i, l in enumerate(lines) if RE_LINK_CALL.search(l)]
            r11plus = [(i + 1, l.strip()) for i, l in enumerate(lines) if RE_R11PLUS.search(l)]
            r11 = [(i + 1, l.strip()) for i, l in enumerate(lines) if RE_R11.search(l)]
            lt = [(i + 1, l.strip()) for i, l in enumerate(lines) if RE_LINK_TRIPLE_ANY.search(l)]
            relinked = bool(RE_RELINKED.search(txt))
            vp = [i + 1 for i, l in enumerate(lines) if RE_VP.search(l)]
            pathsub = [(i + 1, l.strip()) for i, l in enumerate(lines) if RE_PATHSUB.search(l)]
            getmatch = [i + 1 for i, l in enumerate(lines) if RE_GETMATCH.search(l)]
            bytessub = [i + 1 for i, l in enumerate(lines) if RE_BYTESUB.search(l)]
            if (linkcalls or r11plus or r11 or lt or relinked or vp or pathsub):
                rows.append(dict(rel=rel, linkcalls=linkcalls, r11plus=r11plus,
                                 r11=r11, lt=lt, relinked=relinked, vp=vp,
                                 pathsub=pathsub, getmatch=getmatch, bytessub=bytessub))

walk(str(ROOT), 0)
print("SCAN_STATS dirsVisited=%d scannedPy=%d prunedItems=%d depthCap=%d maxBytes=%d" % (
    stats["dirsVisited"], stats["scannedPy"], stats["prunedItems"], DEPTH_CAP, MAX_BYTES))
print("CANDIDATE_ROWS=%d" % len(rows))

# (a) real callers of link()/link_triple() — exclude producers, definitions, docstrings/comments, audit write domain
PRODUCERS = {"lead/r33e_merge_20261109/_re_linked.py", "lead/samedoc_link_20261109/_sl_link.py"}
def is_definition_or_comment(line):
    s = line.strip()
    return (s.startswith("#") or s.startswith("\"\"\"") or s.startswith("'''")
            or s.startswith("def ") or s.startswith("hunk "))

callers = []
for r in rows:
    if r["rel"] in PRODUCERS or "/merged_consumer_audit_20261109/" in r["rel"]:
        continue
    real = [(ln, s) for ln, s in r["linkcalls"] if not is_definition_or_comment(s)]
    if real:
        callers.append((r["rel"], real, r["relinked"]))
print("\n=== (a) REAL link()/link_triple() CALLERS (depthCap<=6) ===")
for rel, real, relinked in sorted(callers):
    print("  %-70s relinked=%s calls=%s" % (rel, relinked, [ln for ln, _ in real]))
print("COUNT(a)=%d" % len(callers))

# (b) r11_scan_plus callers (future surface), and r11_scan callers (NOT the plus surface)
plus = []
r11only = []
for r in rows:
    if "/merged_consumer_audit_20261109/" in r["rel"]:
        continue
    if r["r11plus"]:
        plus.append((r["rel"], r["r11plus"]))
    if r["r11"] and not r["r11plus"]:
        r11only.append((r["rel"], r["r11"]))
print("\n=== (b) r11_scan_plus() CALLERS ===")
for rel, c in sorted(plus):
    print("  %-70s %s" % (rel, [ln for ln, _ in c]))
print("COUNT(r11plus_callers)=%d" % len(plus))
print("\n=== (c) r11_scan() callers WITHOUT r11_scan_plus (NOT reachable from plus integration) ===")
for rel, c in sorted(r11only):
    print("  %-70s %s" % (rel, [ln for ln, _ in c]))
print("COUNT(r11_scan_only)=%d" % len(r11only))

# (d) files reading verified_path / path direct-subscript near match=True
print("\n=== (d) verified_path / bytes direct-subscript lines ===")
for r in rows:
    if "/merged_consumer_audit_20261109/" in r["rel"]:
        continue
    if r["vp"] or r["bytessub"]:
        print("  %-70s vp=%s bytes_sub=%s getmatch=%s" % (
            r["rel"], r["vp"][:12], r["bytessub"][:12], r["getmatch"][:12]))
print("EXIT=0")
