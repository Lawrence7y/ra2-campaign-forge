#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C09 atlas 空洞分析 —— Lead 统一三通道口径 R14-R1（可复跑）。

通道定义（owner() = 函数区间包含判定，R14 §6-17）：
   call32 : 全 .text E8 rel32 目标，owner(target)==None
   jmp32  : E9 rel32 目标，owner==None
   jmp8   : EB rel8  目标，owner==None

每行格式（R14-R1）：
   address(hex8) TAB chan(call32|jmp32|jmp8) TAB first_insn TAB referencing_sites TAB note

独立通道：sweep_independent（自写 PE + capstone skipdata=True 按操作码字节 E8/E9/EB），
         与 collect.py 通道 A（atlas entry+size）不同源。

疑似真入口判据（R14-R1 严格，不放宽）：16 对齐 + 前驱 nop/ret/jmp + 首指令非分支标签。
"""
import os, sys, json, bisect, struct
from collections import defaultdict, Counter
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C10_census")
WORK = os.path.join(CARD, "work")
EVID = os.path.join(CARD, "EVIDENCE")
sys.path.insert(0, WORK)
import sweep_independent as SI
import capstone

# ---- atlas 函数区间（通道 A，仅用于 owner 判定）----
fa = os.path.join(ATLAS, "function_atlas.tsv")
lines = open(fa, encoding="utf-8", errors="replace").read().splitlines()
hdr = lines[0].split("\t")
rows = []
for ln in lines[1:]:
    if not ln.strip():
        continue
    r = dict(zip(hdr, ln.split("\t")))
    rows.append((int(r["entry"], 16), int(r["size"])))
rows.sort()
starts = [va for va, _ in rows]
sizes = dict(rows)

# 本片边界（用于限制扫描目标范围）
LO, HI = 0x773500, 0x7E038D


def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + sizes[starts[i]] else None


atlas_entries = set(starts)

# ---- 独立字节扫：目标 -> {chan: [sites]} ----
pe = SI.RawPE()
chans, stats = SI.sweep(pe)
calls = chans["call32"]; jmps = chans["jmp32"]; jmps8 = chans["jmp8"]
refs = defaultdict(lambda: defaultdict(list))
for ch, tab in (("call32", calls), ("jmp32", jmps), ("jmp8", jmps8)):
    for tgt, slist in tab.items():
        if LO <= tgt < HI and owner(tgt) is None:
            refs[tgt][ch] = sorted(set(slist))
print("sweep insns:", stats["insns"], "targets-in-slice-holes:", len(refs))

# ---- 反汇编器（首指令 / 前驱）----
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
md.detail = False


def first_insns(va, n=3):
    try:
        d = pe.read(va, 32)
    except Exception:
        return "", "", False
    out = []; first = ""
    for insn in md.disasm(d, va):
        if insn.id == 0:
            continue
        if not first:
            first = insn.mnemonic
        out.append("%s %s" % (insn.mnemonic, insn.op_str))
        if len(out) >= n:
            break
    return " ; ".join(out), first, True


BRANCH_LIKE = {"test", "cmp", "je", "jne", "jz", "jnz", "jg", "jge", "jl", "jle", "ja", "jae",
               "jb", "jbe", "js", "jns", "jo", "jno", "jp", "jnp", "jecxz", "loop", "loope", "loopne", "jcxz"}


def prev_kind(va):
    """前驱：nop 填充 / ret / jmp / other。
    1) target 前连续 >=2 个 0x90 -> nop
    2) 从 target-32(16 对齐) 线性反汇编找 end==target 的指令：ret/retn->ret, jmp->jmp
    3) 否则 other
    """
    align_start = (va - 32) & ~0xF
    try:
        buf = pe.read(align_start, va - align_start + 8)
    except Exception:
        return "other", "unreadable"
    pre = buf[:va - align_start]
    k = 0
    for c in reversed(pre):
        if c == 0x90:
            k += 1
        else:
            break
    if k >= 2:
        return "nop", "preceded by %d nops" % k
    last = None
    for insn in md.disasm(buf, align_start):
        if insn.id == 0:
            continue
        if insn.address >= va:
            break
        if insn.address + insn.size == va:
            last = insn
    if last is not None:
        if last.mnemonic in ("ret", "retn"):
            return "ret", "prev=%s %s" % (last.mnemonic, last.op_str)
        if last.mnemonic == "jmp":
            return "jmp", "prev=jmp %s" % last.op_str
        return "other", "prev=%s %s" % (last.mnemonic, last.op_str)
    return "other", "no-insn-ends-at-target"


def site_list(sites):
    return ",".join("%08X" % s for s in sorted(set(sites)))


rows_out = []; full = []
for tgt in sorted(refs):
    fi, first_mn, readable = first_insns(tgt)
    pk, pk_reason = prev_kind(tgt)
    align16 = (tgt % 16 == 0)
    branch_label = first_mn in BRANCH_LIKE
    entry_like = align16 and pk in ("nop", "ret", "jmp") and not branch_label
    for ch in ("call32", "jmp32", "jmp8"):
        if ch not in refs[tgt]:
            continue
        sites = refs[tgt][ch]
        sites_in_fn = sum(1 for s in sites if owner(s) is not None)
        if ch == "call32":
            note = "E8 rel32 直接调用目标；最强入口证据"
        elif ch == "jmp32":
            note = ("疑函数内分支标签（首指令 %s）" % first_mn) if branch_label else \
                   ("E9 rel32 目标；首指令 %s" % (first_mn or "?"))
        else:
            sites_in_hole = len(sites) - sites_in_fn
            loc = "引用站点在洞内 %d/%d（函数内 %d/%d）" % (sites_in_hole, len(sites), sites_in_fn, len(sites))
            note = ("短跳；%s；首指令 %s%s" % (loc, first_mn or "?", " 疑函数内分支" if branch_label else ""))
        note += "；align16=%d prev=%s" % (1 if align16 else 0, pk)
        rec = dict(target=tgt, chan=ch, first=fi, sites=sites, note=note,
                   first_mn=first_mn, align16=align16, prev=pk, prev_reason=pk_reason,
                   branch_label=branch_label, entry_like=entry_like,
                   sites_in_fn=sites_in_fn, readable=readable)
        full.append(rec); rows_out.append(rec)

order = {"call32": 0, "jmp32": 1, "jmp8": 2}
rows_out.sort(key=lambda r: (r["target"], order[r["chan"]]))
with open(os.path.join(CARD, "atlas_gaps.tsv"), "w", encoding="utf-8") as f:
    for r in rows_out:
        f.write("%08X\t%s\t%s\t%s\t%s\n" % (
            r["target"], r["chan"],
            r["first"].replace("\t", " ").replace("\n", " ") or "-",
            site_list(r["sites"]), r["note"].replace("\t", " ").replace("\n", " ")))

with open(os.path.join(EVID, "gap_channels.tsv"), "w", encoding="utf-8") as f:
    f.write("target\tchan\tfirst_insn\tn_sites\tsites_in_fn\talign16\tprev\tprev_reason\tfirst_mn\tbranch_label\tentry_like\tnote\treferencing_sites\n")
    for r in rows_out:
        f.write("%08X\t%s\t%s\t%d\t%d\t%d\t%s\t%s\t%s\t%d\t%d\t%s\t%s\n" % (
            r["target"], r["chan"], r["first"].replace("\t", " "), len(r["sites"]),
            r["sites_in_fn"], 1 if r["align16"] else 0, r["prev"], r["prev_reason"],
            r["first_mn"], 1 if r["branch_label"] else 0, 1 if r["entry_like"] else 0,
            r["note"].replace("\t", " "), site_list(r["sites"])))

json.dump(dict(lo=hex(LO), hi=hex(HI), n_insn=stats["insns"], n_targets=len(refs),
               rows=[dict(target=hex(r["target"]), chan=r["chan"], first=r["first"],
                          sites=[hex(s) for s in r["sites"]], note=r["note"],
                          first_mn=r["first_mn"], align16=r["align16"], prev=r["prev"],
                          prev_reason=r["prev_reason"], branch_label=r["branch_label"],
                          entry_like=r["entry_like"], sites_in_fn=r["sites_in_fn"]) for r in full]),
          open(os.path.join(WORK, "gap_full.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- 统计 ----
cnt = Counter(r["chan"] for r in rows_out)
uniq = {ch: len(set(r["target"] for r in rows_out if r["chan"] == ch)) for ch in ("call32", "jmp32", "jmp8")}
naddr = len(set(r["target"] for r in rows_out))
call_t = set(r["target"] for r in rows_out if r["chan"] == "call32")
jmp32_good = set(r["target"] for r in rows_out if r["chan"] == "jmp32" and not r["branch_label"])
jmp32_bad = set(r["target"] for r in rows_out if r["chan"] == "jmp32" and r["branch_label"])
c_style = call_t | jmp32_good
strict_t = set(r["target"] for r in rows_out if r["entry_like"])
stats_out = dict(rows=len(rows_out), chan_rows=dict(cnt), uniq_targets=uniq,
                 total_distinct_addresses=naddr,
                 call32_targets=len(call_t), jmp32_good=len(jmp32_good),
                 jmp32_branch_label=len(jmp32_bad),
                 c_style_suspect=len(c_style),
                 r14_strict_suspect=len(strict_t),
                 suspect_list=[hex(x) for x in sorted(strict_t)],
                 align16_targets=len(set(r["target"] for r in rows_out if r["align16"])),
                 prev_breakdown=dict(Counter(r["prev"] for r in rows_out)))
json.dump(stats_out, open(os.path.join(WORK, "gap_stats.json"), "w", encoding="utf-8"), indent=1)
print("== gap stats ==")
print(json.dumps(stats_out, indent=1))
