#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C02 全镜像普查 - 证据采集（可复跑）。
通道 A: function_atlas.tsv 逻辑行 1293..2584（1292 函数）。
通道 B: audit_lib.sweep_calls 全 .text skipdata=True 扫 call/jmp rel32（不依赖 atlas 的 entry+size）。
输出: EVIDENCE/ 原始证据 + work/evidence.json + work/meta.json + work/gaps_raw.tsv
"""
import os, sys, re, json, bisect
from collections import defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C02_census")
WORK  = os.path.join(CARD, "work")
EVID  = os.path.join(CARD, "EVIDENCE")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib

def jp(*a): return os.path.join(*a)

# ---------- 1. 切片（按文件物理行，不排序，忠于"按行号切"）----------
fa = jp(ATLAS, "function_atlas.tsv")
with open(fa, encoding="utf-8", errors="replace") as f:
    lines = f.read().splitlines()
hdr  = lines[0].split("\t")
data = [ln for ln in lines[1:] if ln.strip()]
print("atlas data rows:", len(data))
assert len(data) == 12916, "atlas 函数行数异常"

def parse(ln):
    p = ln.split("\t")
    rec = dict(zip(hdr, p))
    return dict(
        entry=int(rec["entry"], 16), size=int(rec["size"]),
        n_instr=int(rec["n_instr"]), n_callers=int(rec["n_callers"]),
        n_callees=int(rec["n_callees"]), is_fnptr=int(rec["is_fnptr"]),
        first_import=rec.get("first_import", ""),
        strings=rec.get("strings", ""),
        n_strings=int(rec.get("n_strings", "0") or 0),
    )

allf      = [parse(ln) for ln in data]
slicef    = allf[1292:2584]          # 逻辑行 1293..2584
assert len(slicef) == 1292
lo = min(f["entry"] for f in slicef)
hi = max(f["entry"] + f["size"] for f in slicef)

allf_sorted = sorted(allf, key=lambda f: f["entry"])
starts = [f["entry"] for f in allf_sorted]
atlas_entries = set(starts)

def owner(site):
    """站点归属：函数区间包含 entry <= site < entry+size；空洞返回 None。"""
    i = bisect.bisect_right(starts, site) - 1
    if i >= 0 and allf_sorted[i]["entry"] <= site < allf_sorted[i]["entry"] + allf_sorted[i]["size"]:
        return allf_sorted[i]["entry"]
    return None

# ---------- 2. Bin + 全 .text sweep（通道 B，skipdata=True）----------
bin_ = audit_lib.Bin()
text = bin_.text
text_lo, text_hi = text["va"], text["va"] + text["rawsize"]
calls, jmps, sweep_stats = audit_lib.sweep_calls(bin_)
print("sweep_stats:", sweep_stats)
assert sweep_stats["insns"] > 500000, "sweep 指令数异常，skipdata 可能未生效"

site2tgt = {}
for tgt, slist in calls.items():
    for s in slist: site2tgt[s] = tgt
all_sites = sorted(site2tgt)
site2jmp = {}
for tgt, slist in jmps.items():
    for s in slist: site2jmp[s] = tgt
all_jsites = sorted(site2jmp)

def sites_in(keys, table, a, b):
    i = bisect.bisect_left(keys, a); out = []
    while i < len(keys) and keys[i] < b:
        out.append((keys[i], table[keys[i]])); i += 1
    return out

# ---------- 3. vftable 槽 -> 函数入口 ----------
vtj = json.load(open(jp(ATLAS, "vtables_v2.json"), encoding="utf-8"))
def demangle(c):
    s = c
    if s.startswith(".?AV") or s.startswith(".?AU"): s = s[4:]
    if s.endswith("@@"): s = s[:-2]
    s = s.replace("?$", "T_")          # 模板前缀可辨识即可
    s = s.replace("@", "_")
    return s
vtmap = defaultdict(list)              # func entry -> [(class,slot,vt)]
vt_checked = 0
for v in vtj["vtables"]:
    vt = v["vt"]; cls = demangle(v.get("class", "?")); n = v.get("slots", 0)
    if n <= 0 or n > 400: continue
    for i in range(n):
        a = vt + 4 * i
        try: tgt = bin_.u32(a)
        except Exception: continue
        vt_checked += 1
        if text_lo <= tgt < text_hi:
            vtmap[tgt].append((cls, i, vt))

# ---------- 4. 已知名索引 ----------
known = defaultdict(set)              # addr -> set(names)
import glob
KW_SKIP = {"if","while","for","switch","JMP_THIS","JMP_STD","THISCALL","return","sizeof","PUSH_VAR32","PUSH_VAR64"}
for h in glob.glob(jp(ROOT, "YRpp", "**", "*.h"), recursive=True):
    cls = os.path.basename(h)[:-2]
    txt = open(h, encoding="utf-8", errors="replace").read()
    hl = txt.splitlines()
    for li, line in enumerate(hl):
        for m in re.finditer(r'JMP_(?:THIS|STD)\((0x[0-9A-Fa-f]+)\)', line):
            addr = int(m.group(1), 16)
            ctx = " ".join(hl[max(0, li-1):li+1])
            ids = [x for x in re.findall(r'\b([A-Za-z_]\w*)\s*\(', ctx) if x not in KW_SKIP]
            meth = ids[-1] if ids else cls
            known[addr].add(f"{cls}::{meth}")
    for m in re.finditer(r'INI_READ\(\s*(\w+)\s*,\s*(0x[0-9A-Fa-f]+)\s*\)', txt):
        known[int(m.group(2), 16)].add(f"{cls}::{m.group(1)}")
for md in glob.glob(jp(ROOT, "re_atlas", "kb", "*.md")):
    txt = open(md, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r'`0x([0-9A-Fa-f]{6,8})`[^\n`]{0,90}`([A-Za-z_][\w:]*(?:::\w+)?)`', txt):
        known[int(m.group(1), 16)].add(m.group(2))
    for m in re.finditer(r'`([A-Za-z_][\w:]*(?:::\w+)?)`\s*\|\s*`0x([0-9A-Fa-f]{6,8})`', txt):
        known[int(m.group(2), 16)].add(m.group(1))

modmap = {}
with open(jp(ATLAS, "module_attribution.tsv"), encoding="utf-8", errors="replace") as f:
    next(f)
    for ln in f:
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 4:
            modmap[int(p[0], 16)] = os.path.basename(p[3].replace("\\", "/"))
srcstr = {}
with open(jp(ATLAS, "source_files.tsv"), encoding="utf-8", errors="replace") as f:
    next(f)
    for ln in f:
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 2:
            try: srcstr[int(p[0], 16)] = os.path.basename(p[1].replace("\\", "/"))
            except Exception: pass

def known_of(entry): return sorted(known.get(entry, []))

# ---------- 5. 每函数证据汇总 ----------
E = []
for f in slicef:
    e, end = f["entry"], f["entry"] + f["size"]
    caller_ents = set()
    for s in calls.get(e, []):
        o = owner(s)
        if o is not None: caller_ents.add(o)
    callee_ents = set(t for s, t in sites_in(all_sites, site2tgt, e, end))
    jmp_tgts    = set(t for s, t in sites_in(all_jsites, site2jmp, e, end))
    rec = dict(f)
    rec["vt"] = vtmap.get(e, [])          # [[class,slot,vt],...]
    rec["module"] = modmap.get(e, "")
    rec["callers"] = sorted(caller_ents)
    rec["callees"] = sorted(callee_ents)
    rec["jmp_tgts"] = sorted(jmp_tgts)
    rec["callers_known"] = [[c, known_of(c)] for c in sorted(caller_ents) if known_of(c)]
    rec["callees_known"] = [[c, known_of(c)] for c in sorted(callee_ents) if known_of(c)]
    rec["self_known"] = known_of(e)
    E.append(rec)

json.dump(dict(lo=hex(lo), hi=hex(hi), n=len(E), funcs=E),
          open(jp(WORK, "evidence.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------- 6. atlas 空洞入口（通道 B）----------
gap_cands = set()
for tgt in calls:
    if lo <= tgt < hi: gap_cands.add(("call", tgt))
for tgt in jmps:
    if lo <= tgt < hi: gap_cands.add(("jmp", tgt))
gaps = []
for kind, tgt in sorted(gap_cands, key=lambda x: x[1]):
    if tgt in atlas_entries: continue
    boundary = None; why = "no-prior-entry"; from_entry = None
    i = bisect.bisect_left(starts, tgt) - 1
    for j in range(i, max(-1, i - 6), -1):
        fe = allf_sorted[j]["entry"]
        ok, insn, reason = audit_lib.boundary_check(bin_, fe, tgt)
        if "未判定" in reason:      # max_bytes bail -> unknown，不能当 False
            continue
        boundary = ok; why = reason; from_entry = fe
        break
    sites = sorted(set(calls.get(tgt, []) + jmps.get(tgt, [])))
    gaps.append(dict(target=tgt, kind=kind, n_sites=len(sites),
                     boundary=boundary, why=why, from_entry=from_entry,
                     owner=owner(tgt),            # None = 落在 atlas 空洞（严格判据）
                     is_call_tgt=tgt in calls,
                     sites=sites[:40]))
json.dump(dict(lo=hex(lo), hi=hex(hi), sweep=sweep_stats, gaps=gaps),
          open(jp(WORK, "gaps_raw.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
# 缓存 sweep 目标集合（目标->站点数），供后续独立分析，避免重复 sweep
json.dump(dict(calls={hex(k): len(v) for k, v in calls.items()},
               jmps={hex(k): len(v) for k, v in jmps.items()}),
          open(jp(WORK, "sweep_targets.json"), "w", encoding="utf-8"))

# ---------- 7. 人类可读 EVIDENCE ----------
with open(jp(EVID, "slice_raw.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tsize\tn_instr\tn_callers\tn_callees\tis_fnptr\tfirst_import\tn_strings\tstrings\n")
    for r in E:
        f.write("%08X\t%d\t%d\t%d\t%d\t%d\t%s\t%d\t%s\n" % (
            r["entry"], r["size"], r["n_instr"], r["n_callers"], r["n_callees"],
            r["is_fnptr"], r["first_import"], r["n_strings"], r["strings"]))
with open(jp(EVID, "vtmap_hits.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tclass\tslot\tvt\n")
    for r in E:
        for cls, slot, vt in r["vt"]:
            f.write("%08X\t%s\t%d\t%08X\n" % (r["entry"], cls, slot, vt))
with open(jp(EVID, "known_hits.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tkind\tnames\n")
    for r in E:
        if r["self_known"]: f.write("%08X\tself\t%s\n" % (r["entry"], " | ".join(r["self_known"])))
        for c, ns in r["callers_known"]:
            f.write("%08X\tcaller(%08X)\t%s\n" % (r["entry"], c, " | ".join(ns)))
        for c, ns in r["callees_known"]:
            f.write("%08X\tcallee(%08X)\t%s\n" % (r["entry"], c, " | ".join(ns)))
with open(jp(EVID, "callgraph.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tcallers\tcallees\tjmp_tgts\n")
    for r in E:
        f.write("%08X\t%s\t%s\t%s\n" % (r["entry"],
            ",".join("%08X" % x for x in r["callers"]),
            ",".join("%08X" % x for x in r["callees"]),
            ",".join("%08X" % x for x in r["jmp_tgts"])))
with open(jp(EVID, "gaps_raw.tsv"), "w", encoding="utf-8") as f:
    f.write("target\tkind\tn_sites\tboundary\towner\tis_call_tgt\tfrom_entry\twhy\n")
    for g in gaps:
        f.write("%08X\t%s\t%d\t%s\t%s\t%s\t%s\t%s\n" % (
            g["target"], g["kind"], g["n_sites"],
            "unknown" if g["boundary"] is None else str(g["boundary"]).lower(),
            "%08X" % g["owner"] if g["owner"] is not None else "HOLE",
            "1" if g["is_call_tgt"] else "0",
            "%08X" % g["from_entry"] if g["from_entry"] else "", g["why"]))

json.dump(dict(n=len(E), lo=hex(lo), hi=hex(hi), n_vt_checked=vt_checked,
               n_vt_slots_hit=sum(len(r["vt"]) for r in E),
               n_self_known=sum(1 for r in E if r["self_known"]),
               n_with_module=sum(1 for r in E if r["module"]),
               n_gaps=len(gaps), sweep=sweep_stats),
          open(jp(WORK, "meta.json"), "w", encoding="utf-8"), indent=1)
print("slice:", len(E), "range", hex(lo), hex(hi))
print("vt slots hit (funcs):", sum(1 for r in E if r["vt"]))
print("self known:", sum(1 for r in E if r["self_known"]), "module:", sum(1 for r in E if r["module"]))
print("gaps:", len(gaps))
