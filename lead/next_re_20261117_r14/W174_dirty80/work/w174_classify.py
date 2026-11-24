#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump per-site context for classification of the 179 [+0x80] writes.
Uses M3 function intervals (union atlas+call targets) for function bodies.
For each site prints:
  - function entry, site, source kind/value
  - last 16 instructions before site (linear), first 4 after
  - presence of a forward conditional jump over the site (skips write)
  - presence of a backward/forward conditional jump whose TARGET is the site
  - presence of cmp/test within the 10 instructions before
Classification rule (documented, reproducible):
  a: src_kind==imm and src==0
  d: src_kind==reg  (register value written)
  b: src_kind==imm and src==1 and (has a gating conditional jump over the site
     OR a cmp/test within the 10 preceding instructions feeding a jcc)
  c: src_kind==imm and src==1 and no such gating comparison detected
"""
import os, sys, json, bisect
import pefile, capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, "lead", "next_re_20261116_r12", "_lead_audit"))
import audit_lib

with open(os.path.join(HERE, "..", "EVIDENCE", "w174_writes.json"), "r", encoding="utf-8") as f:
    D = json.load(f)
writes = D["writesA"]

b = audit_lib.Bin()
pe = b.pe
IB = b.image_base
T = b.sec(".text")
TEXT = pe.__data__[T["raw"]:T["raw"]+T["rawsize"]]
TV = T["va"]

def md():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True; m.skipdata = True
    return m
MD = md()

# M3 intervals
rows, _ = audit_lib.load_func_atlas()
atlas_entries = sorted([e for e, _ in rows])
calls, jmps, _ = audit_lib.sweep_calls(b)
union = sorted(set(atlas_entries) | set(t for t in calls if TV <= t < TV+len(TEXT)))
def func_range(va):
    i = bisect.bisect_right(union, va) - 1
    if i < 0: return None
    lo = union[i]
    hi = union[i+1] if i+1 < len(union) else TV+len(TEXT)
    return lo, hi

COND = {"je","jne","jz","jnz","jg","jge","jl","jle","ja","jae","jb","jbe",
        "js","jns","jo","jno","jp","jnp","jpe","jpo","jcxz","jecxz","loop","loope","loopne"}
CMPSET = {"cmp","test"}

def disasm_range(lo, hi):
    data = TEXT[lo-TV:hi-TV]
    out = []
    for insn in MD.disasm(data, lo):
        if insn.id == 0: continue
        out.append(insn)
    return out

results = []
context_lines = []
for d in writes:
    va = d["va"]
    fr = func_range(va)
    if not fr:
        cls = "?"
        results.append(dict(va=va, cls=cls, why="no func range"))
        continue
    lo, hi = fr
    insns = disasm_range(lo, hi)
    idx = None
    for k, insn in enumerate(insns):
        if insn.address == va:
            idx = k; break
    if idx is None:
        # site not on a decoded boundary within the function range - unusual
        cls = "?" if d["src_kind"] != "imm" else ("a" if d["src"]==0 else "c")
        results.append(dict(va=va, cls=cls, why="site not decoded in func range", fn=lo))
        continue
    pre = insns[max(0, idx-16):idx]
    post = insns[idx+1:idx+5]
    site_insn = insns[idx]
    # gating: forward conditional jump J with J.addr < va < J.target
    gate_over = [i for i in pre if i.mnemonic in COND and i.op_str.startswith("0x")
                 and int(i.op_str,16) > va]
    # conditional jump targeting the site
    gate_target = [i for i in insns if i.address < va and i.mnemonic in COND
                   and i.op_str.startswith("0x") and int(i.op_str,16) == va]
    # cmp/test in last 10
    cmps = [i for i in pre[-10:] if i.mnemonic in CMPSET]
    # classification
    if d["src_kind"] == "imm" and d["src"] == 0:
        cls = "a"; why = "write 0"
    elif d["src_kind"] == "reg":
        cls = "d"; why = "register value"
    else:
        # imm 1 (or other imm)
        if gate_over or gate_target or cmps:
            cls = "b"; why = "gated"
        else:
            cls = "c"; why = "ungated"
    results.append(dict(va=va, cls=cls, why=why, fn=lo,
                        gate_over=[i.address for i in gate_over],
                        gate_target=[i.address for i in gate_target],
                        cmps=[i.address for i in cmps],
                        src=d["src"], src_kind=d["src_kind"], base=d["base"]))
    # context dump (full, for all sites)
    context_lines.append("=== %08X fn=%08X cls=%s why=%s src=%s:%s ===" % (
        va, lo, cls, why, d["src_kind"], d["src"]))
    for i in pre:
        marker = " >>JUMP" if (i.mnemonic in COND and i.op_str.startswith("0x") and int(i.op_str,16) > va) else ""
        marker += " >>CMP" if i.mnemonic in CMPSET else ""
        context_lines.append("  %08X  %-8s %s%s" % (i.address, i.mnemonic, i.op_str, marker))
    context_lines.append("  %08X  %-8s %s   <== SITE" % (site_insn.address, site_insn.mnemonic, site_insn.op_str))
    for i in post:
        context_lines.append("  %08X  %-8s %s" % (i.address, i.mnemonic, i.op_str))

with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_context.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(context_lines)+"\n")

with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_results.tsv"),"w",encoding="utf-8") as f:
    f.write("va\tcls\twhy\tfn\tsrc_kind\tsrc\tbase\tgate_over\tgate_target\tcmps\n")
    for r in results:
        f.write("%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            r["va"], r["cls"], r["why"],
            ("%08X"%r["fn"]) if r.get("fn") else "",
            r.get("src_kind",""), str(r.get("src","")), r.get("base",""),
            " ".join("%08X"%x for x in r.get("gate_over",[])),
            " ".join("%08X"%x for x in r.get("gate_target",[])),
            " ".join("%08X"%x for x in r.get("cmps",[]))))

from collections import Counter
print("counts:", Counter(r["cls"] for r in results))
print("imm1 sites:", sum(1 for r in results if r.get("src")==1 and r.get("src_kind")=="imm"))
