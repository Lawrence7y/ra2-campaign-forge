# -*- coding: utf-8 -*-
"""Independent re-derivation for EXIT_CENSUS audit. Read-only on the data root.
Run with: python -I -X utf8 <absolute path of this file>
"""
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

D = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
OUT = Path("D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261105/EXIT_CENSUS_77a0d667")


def jload(p):
    try:
        return json.loads(p.read_bytes().decode("utf-8-sig")), None
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


def txt(p):
    try:
        return p.read_bytes().decode("utf-8", errors="replace")
    except Exception as e:
        return "<READFAIL %s: %s>" % (type(e).__name__, e)


dirs = sorted([p for p in D.iterdir() if p.is_dir() and p.name.startswith("archive_T")], key=lambda p: p.name)
print("=" * 100)
print("SECTION 1: archive_T* glob (D.iterdir, is_dir, startswith)")
print("COUNT =", len(dirs))
for i, p in enumerate(dirs, 1):
    print("  %2d. %s" % (i, p.name))

print("=" * 100)
print("SECTION 2: per-dir final_exit / cleanup_failures / error.txt / except_post hashes")
rows = []
for p in dirs:
    rl = p / "qc151_run_log.json"
    if not rl.exists():
        fe, cf, parse = "缺", "缺", None
    else:
        obj, err = jload(rl)
        if err is not None:
            fe, cf, parse = "解析失败", "解析失败", err
        else:
            fe = obj.get("final_exit", "<NO_KEY>")
            cf = obj.get("cleanup_failures", "<NO_KEY>")
            parse = None
    et = p / "error.txt"
    et_exists = et.exists()
    et_size = et.stat().st_size if et_exists else -1
    et_text = txt(et) if et_exists else ""
    et_type_lines = [ln for ln in et_text.splitlines() if ln.strip().lower().startswith("type")]
    et_where_lines = [ln for ln in et_text.splitlines() if ln.strip().lower().startswith("where")]
    et_repr_lines = [ln for ln in et_text.splitlines() if ln.strip().lower().startswith("repr")]
    eps = sorted([q for q in p.rglob("except_post_*.txt") if q.is_file()], key=lambda q: str(q))
    ep_info = []
    for q in eps:
        h = hashlib.sha256(q.read_bytes()).hexdigest()
        body = txt(q)
        ep_info.append((q.relative_to(p).as_posix(), h, "EXCEPTION_SINGLE_STEP" in body, "007CFC9F" in body,
                        [ln for ln in body.splitlines() if "Error code" in ln or "Exception occurred" in ln]))
    nested_et = [q.relative_to(p).as_posix() for q in p.rglob("error.txt") if q != et]
    rows.append(dict(dir=p.name, final_exit=fe, cleanup_failures=cf, parse=parse,
                     error_exists=et_exists, error_size=et_size, error_text=et_text,
                     et_type=et_type_lines, et_where=et_where_lines, et_repr=et_repr_lines,
                     ep=ep_info, nested_error=nested_et))
    print("\n--- %s ---" % p.name)
    print("  final_exit=%r cleanup_failures=%r parse_err=%r" % (fe, cf, parse))
    print("  error.txt exists=%s size=%s nested_error.txt=%s" % (et_exists, et_size, nested_et))
    for ln in et_type_lines + et_where_lines + et_repr_lines:
        print("  error.txt LINE: %s" % ln)
    print("  except_post count=%d" % len(ep_info))
    for name, h, ess, addr, siglines in ep_info:
        print("    %s sha256=%s ESS=%s 007CFC9F=%s sig=%s" % (name, h, ess, addr, siglines))

print("=" * 100)
print("SECTION 3: final_exit histogram (independent)")
hist = defaultdict(list)
for r in rows:
    hist[str(r["final_exit"])].append(r["dir"])
for k in sorted(hist, key=lambda x: (x != "0", x)):
    print("  %-5s : %2d  %s" % (k, len(hist[k]), ", ".join(hist[k])))
print("  TOTAL:", sum(len(v) for v in hist.values()))

print("=" * 100)
print("SECTION 4: error.txt type-line distribution (independent)")
type_hist = Counter()
for r in rows:
    if not r["error_exists"] or r["error_size"] == 0:
        type_hist["<无/缺/空>"] += 1
    else:
        t = r["et_type"][0].strip() if r["et_type"] else "<no type line>"
        type_hist[t] += 1
for k, v in sorted(type_hist.items()):
    print("  %-60s %2d" % (k, v))

print("=" * 100)
print("SECTION 5: D question - final_exit=0 dirs with NON-EMPTY error.txt")
zeros = [r for r in rows if str(r["final_exit"]) == "0"]
print("  final_exit=0 count =", len(zeros), ":", ", ".join(r["dir"] for r in zeros))
flagged = []
for r in zeros:
    st = "缺" if not r["error_exists"] else ("非空(%d bytes)" % r["error_size"] if r["error_size"] > 0 else "存在但0字节")
    print("  %-18s error.txt=%s" % (r["dir"], st))
    if r["error_exists"] and r["error_size"] > 0:
        flagged.append(r["dir"])
print("  FLAGGED (final_exit=0 AND non-empty error.txt) =", flagged)

print("=" * 100)
print("SECTION 6: C question - all except_post in 37 archives: sha256 groups & signature")
all_hashes = Counter()
for r in rows:
    for name, h, ess, addr, siglines in r["ep"]:
        all_hashes[(h, ess, addr, tuple(siglines))] += 1
print("  distinct (sha256, ESS, 007CFC9F, siglines) combos =", len(all_hashes))
for k, v in all_hashes.items():
    print("  n=%2d sha256=%s ESS=%s 007CFC9F=%s sig=%s" % (v, k[0], k[1], k[2], list(k[3])))
print("  total except_post files in 37 archives =", sum(all_hashes.values()))
print("  dirs with 0 except_post =", [r["dir"] for r in rows if len(r["ep"]) == 0])

print("=" * 100)
print("SECTION 7: B question - final_exit=19 dirs, FULL error.txt + products")
for r in rows:
    if str(r["final_exit"]) != "19":
        continue
    p = D / r["dir"]
    print("\n########", r["dir"], "########")
    print("  --- qc151_run_log.json full ---")
    print("  " + txt(p / "qc151_run_log.json").replace("\n", "\n  ") if (p / "qc151_run_log.json").exists() else "  缺")
    print("  --- error.txt full (exists=%s) ---" % (p / "error.txt").exists())
    if (p / "error.txt").exists():
        print("  " + r["error_text"].replace("\n", "\n  "))
    else:
        print("  缺")
    print("  --- directory file list ---")
    for q in sorted(p.iterdir()):
        print("    %s %s" % ("DIR " if q.is_dir() else "FILE", q.name + ("" if q.is_dir() else " (%d bytes)" % q.stat().st_size)))
    print("  --- qc151_fields.json : selected exit/budget/nav/win/term keys ---")
    f = p / "qc151_fields.json"
    if f.exists():
        obj, err = jload(f)
        if err:
            print("    解析失败:", err)
        else:
            def emit_items(items):
                for it in items:
                    if isinstance(it, dict) and "group" in it and "key" in it:
                        gk = "%s.%s" % (it.get("group"), it.get("key"))
                        if any(s in gk.upper() for s in ("BUDGET", "NAV", "WIN", "TERM", "META", "MANIFEST", "EXCEPT", "S4")):
                            print("    %s = %s" % (gk, json.dumps(it.get("value"), ensure_ascii=False)[:400]))
                    else:
                        print("    UNEXPECTED ITEM %s" % json.dumps(it, ensure_ascii=False)[:300])
            def walk(o, prefix=""):
                if isinstance(o, dict):
                    for k, v in o.items():
                        walk(v, prefix + "." + str(k) if prefix else str(k))
                elif isinstance(o, list):
                    print("    %s = %s" % (prefix, json.dumps(o, ensure_ascii=False)[:300]))
                else:
                    print("    %s = %r" % (prefix, o))
            if isinstance(obj, list):
                emit_items(obj)
            elif isinstance(obj, dict):
                for key in sorted(obj.keys()):
                    if any(s in key.upper() for s in ("BUDGET", "NAV", "WIN", "TERM", "META", "MANIFEST", "EXCEPT", "S4")):
                        walk(obj[key], "    " + key)
            else:
                print("    解析失败: unexpected root type %s" % type(obj).__name__)
    else:
        print("    缺")
    print("  --- *console*.log full text (or 缺) ---")
    logs = sorted(p.glob("*console*"))
    if not logs:
        print("    缺")
    for lg in logs:
        print("    FILE %s (%d bytes)" % (lg.name, lg.stat().st_size))
        t = txt(lg)
        print("    " + t.replace("\n", "\n    ")[:8000])

print("=" * 100)
print("SECTION 8: full error.txt of 3 sampled trips with non-empty error.txt (repr truncation check)")
samples = [r for r in rows if r["error_exists"] and r["error_size"] > 0][:3]
for r in samples:
    print("\n######## FULL error.txt:", r["dir"], "size", r["error_size"], "########")
    print(r["error_text"])
    print("######## END", r["dir"], "########")
print("=" * 100)
print("DONE")
