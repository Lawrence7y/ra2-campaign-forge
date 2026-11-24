#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C07 atlas 空洞分析 —— Lead 统一口径 R14-R1（可复跑，严格判据版）。

通道定义（Lead 2026-11-17 裁定 R14-R1，C01-C03 审计实证）：
  chan=call32 : 全 .text 线性扫 E8 rel32 目标，owner(target)==None（最强入口证据，必收）
  chan=jmp32  : E9 rel32 目标，owner==None（若首指令是 test/cmp/je/jle 等，note 标「疑函数内分支标签」）
  chan=jmp8   : EB rel8  目标，owner==None（单独收；note 标引用站点是否在洞内 / 首指令）

atlas_gaps.tsv 每行：address(hex8) TAB chan TAB first_insn TAB referencing_sites TAB note
同一地址被多通道命中 → 每通道一行。

【疑似真入口判据 —— R14-R1 严格版，前三片审计实证】
  必须同时满足：
    (1) 16 字节对齐 (target % 16 == 0)
    (2) 前驱为 nop 填充 / ret / jmp（线性扫描最近真指令，跳过连续 nop/int3）
    (3) 首指令不像循环体分支标签（BRANCH_LIKE 集合）
  仅靠「有 E8/E9 指向」不足以称真入口。

方法：
  - 独立通道（不依赖 function_atlas.tsv 的 entry+size 做解码）：capstone skipdata=True 全 .text 逐条
    反汇编，按 insn.bytes[0] 区分 E8/E9/EB；只记录 mnemonic=call/jmp 且 op 为立即地址的目标。
  - owner(target) 用「函数区间包含」判据（R14 §6-17），不用 entry_at_or_before。
  - boundary_check 超 max_bytes 返回 unknown（保留 None 不当 False）（R14 §6-3）。
  - 全量输出 work/gap_full.json（不截断）+ EVIDENCE/gap_channels.tsv + atlas_gaps.tsv。
"""
import os, sys, json, bisect, re
from collections import defaultdict, Counter
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C07_census")
WORK  = os.path.join(CARD, "work")
EVID  = os.path.join(CARD, "EVIDENCE")
sys.path.insert(0, os.path.join(ROOT, "lead\\next_re_20261116_r12\\_lead_audit"))
import audit_lib
import capstone

gaps = json.load(open(os.path.join(WORK, "gaps_raw.json"), encoding="utf-8"))
lo, hi = int(gaps["lo"], 16), int(gaps["hi"], 16)

# ---- atlas 函数区间（区间包含判据）----
rows, hdr = audit_lib.load_func_atlas()
starts = [va for va, _ in rows]
sizes  = {va: int(rec["size"]) for va, rec in rows}
def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + sizes[starts[i]] else None
atlas_entries = set(starts)

# ---- 复用 collect.py 已算的 boundary ----
boundary_map = {}
for g in gaps["gaps"]:
    t = g["target"]
    if t not in boundary_map or boundary_map[t] is None:
        boundary_map[t] = g["boundary"]

# ---- 全 .text 独立逐条复扫 + 建立指令起点表（skipdata=True）----
b = audit_lib.Bin()
text = b.text
tlo, thi = text["va"], text["va"] + text["rawsize"]
m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
m.skipdata = True; m.detail = False
data = b.pe.__data__[text["raw"]:text["raw"] + text["rawsize"]]

refs = defaultdict(lambda: defaultdict(list))   # target -> chan -> [sites]
insn_start = []                                 # 所有真指令起点（升序）
insn_info = {}                                  # addr -> (mn, op, size, bytes)
n_insn = 0
hextgt = re.compile(r'^0x[0-9A-Fa-f]+$')
for insn in m.disasm(data, text["va"]):
    if insn.id == 0:
        continue
    n_insn += 1
    insn_start.append(insn.address)
    insn_info[insn.address] = (insn.mnemonic, insn.op_str, insn.size, insn.bytes)
    mn = insn.mnemonic
    if mn not in ("call", "jmp") or not hextgt.match(insn.op_str):
        continue
    try: tgt = int(insn.op_str, 16)
    except Exception: continue
    if not (lo <= tgt < hi):
        continue
    op0 = insn.bytes[0] if insn.bytes else None
    if mn == "call" and op0 == 0xE8: ch = "call32"
    elif mn == "jmp" and op0 == 0xE9: ch = "jmp32"
    elif mn == "jmp" and op0 == 0xEB: ch = "jmp8"
    else: continue
    refs[tgt][ch].append(insn.address)
print("full rescan insns:", n_insn, "targets-in-slice:", len(refs))

# ---- 首指令（序言 / 分支标签判定）----
mm = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mm.detail = False; mm.skipdata = True
def first_insns(va, n=3):
    try: d = b.read(va, 32)
    except Exception: return "", "", False
    out = []; first_mn = ""
    for insn in mm.disasm(d, va):
        if insn.id == 0: continue
        if not first_mn: first_mn = insn.mnemonic
        out.append("%s %s" % (insn.mnemonic, insn.op_str))
        if len(out) >= n: break
    return " ; ".join(out), first_mn, True

BRANCH_LIKE = {"test","cmp","je","jne","jz","jnz","jg","jge","jl","jle","ja","jae",
               "jb","jbe","js","jns","jo","jno","jp","jnp","jecxz","loop","loope","loopne",
               "jcxz"}

# ---- 前驱判定（严格）：跳过连续 nop/int3 填充后，最近真指令是否为 ret/jmp；或字节全是填充 ----
def pred_info(t):
    """返回 (pred_kind, pred_desc, gap_bytes)：
    pred_kind ∈ {'ret','jmp','pad','jcc','plain','byte-pad','byte-gap','none'}"""
    i = bisect.bisect_left(insn_start, t) - 1
    if i < 0:
        return "none", "", t - text["va"]
    j = i
    cur = t
    pad_seen = False
    # 跳过恰好紧邻且为 nop/int3 的填充指令
    while j >= 0:
        pa = insn_start[j]
        pm, po, psz, pbytes = insn_info[pa]
        if pa + psz == cur and pm in ("nop", "int3"):
            pad_seen = True
            cur = pa
            j -= 1
            continue
        break
    if j < 0:
        return "pad", "alignment-pad", t - cur
    pa = insn_start[j]
    pm, po, psz, pbytes = insn_info[pa]
    gap = cur - (pa + psz)
    desc = "%s %s @%08X" % (pm, po, pa)
    if gap > 0:
        # 检查字节间隙是否全是填充字节
        try: gb = b.read(pa + psz, gap)
        except Exception: gb = b""
        if gb and all(x in (0x90, 0xCC, 0x00) for x in gb):
            return "byte-pad", desc + " (+%d fill)" % gap, gap
        return "byte-gap", desc + " (+%d)" % gap, gap
    if pm in ("ret", "retf", "retn"):
        return "ret", desc, 0
    if pm == "jmp":
        return "jmp", desc, 0
    if pm in ("nop", "int3"):
        return "pad", desc, 0
    if pm.startswith("j") or pm.startswith("loop"):
        return "jcc", desc, 0
    return "plain", desc, 0

def site_list_str(sites):
    return ",".join("%08X" % s for s in sorted(set(sites)))

rows_out = []
full = []
suspect_addrs = set()
for tgt in sorted(refs):
    if owner(tgt) is not None:
        continue                      # 严格：只在 atlas 空洞收
    fi, first_mn, readable = first_insns(tgt)
    boundary = boundary_map.get(tgt)
    pk, pdesc, pgap = pred_info(tgt)
    align16 = (tgt % 16 == 0)
    # ---- 疑似真入口三条件 ----
    is_suspect = align16 and (pk in ("ret", "jmp", "pad", "byte-pad")) and (first_mn not in BRANCH_LIKE)
    if is_suspect:
        suspect_addrs.add(tgt)
    for ch in ("call32", "jmp32", "jmp8"):
        if ch not in refs[tgt]:
            continue
        sites = sorted(set(refs[tgt][ch]))
        sites_in_fn = sum(1 for s in sites if owner(s) is not None)
        if ch == "call32":
            note = "E8 rel32 调用目标；align16=%s 前驱=%s 首指令=%s%s" % (
                "Y" if align16 else "N", pk, first_mn or "?", " [疑似真入口]" if is_suspect else "")
        elif ch == "jmp32":
            if first_mn in BRANCH_LIKE:
                note = "疑函数内分支标签（首指令 %s）" % first_mn
            else:
                note = "E9 rel32 目标；align16=%s 前驱=%s 首指令=%s%s" % (
                    "Y" if align16 else "N", pk, first_mn or "?", " [疑似真入口]" if is_suspect else "")
        else:  # jmp8
            sites_in_hole = len(sites) - sites_in_fn
            loc = "引用站点在洞内 %d/%d（函数内 %d/%d）" % (sites_in_hole, len(sites), sites_in_fn, len(sites))
            note = "短跳；%s；首指令 %s；align16=%s 前驱=%s" % (
                loc, first_mn or "?", "Y" if align16 else "N", pk)
            if first_mn in BRANCH_LIKE:
                note += "（疑函数内分支）"
        rec = dict(target=tgt, chan=ch, first=fi, sites=sites, note=note,
                   boundary=boundary, sites_in_fn=sites_in_fn, first_mn=first_mn,
                   align16=align16, pred_kind=pk, pred_desc=pdesc, is_suspect=is_suspect,
                   readable=readable)
        full.append(rec); rows_out.append(rec)

order = {"call32":0,"jmp32":1,"jmp8":2}
rows_out.sort(key=lambda r: (r["target"], order[r["chan"]]))
with open(os.path.join(CARD, "atlas_gaps.tsv"), "w", encoding="utf-8") as f:
    for r in rows_out:
        fi = (r["first"] or "-").replace("\t"," ").replace("\n"," ")
        note = r["note"].replace("\t"," ").replace("\n"," ")
        f.write("%08X\t%s\t%s\t%s\t%s\n" % (r["target"], r["chan"], fi, site_list_str(r["sites"]), note))

with open(os.path.join(EVID, "gap_channels.tsv"), "w", encoding="utf-8") as f:
    f.write("target\tchan\tfirst_insn\tn_sites\tsites_in_fn\tboundary\tfirst_mn\talign16\tpred_kind\tpred_desc\tis_suspect\tnote\treferencing_sites\n")
    for r in rows_out:
        f.write("%08X\t%s\t%s\t%d\t%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            r["target"], r["chan"], r["first"].replace("\t"," "), len(r["sites"]),
            r["sites_in_fn"], "unknown" if r["boundary"] is None else str(r["boundary"]).lower(),
            r["first_mn"], "1" if r["align16"] else "0", r["pred_kind"],
            r["pred_desc"].replace("\t"," "), "1" if r["is_suspect"] else "0",
            r["note"].replace("\t"," "), site_list_str(r["sites"])))
json.dump(dict(lo=hex(lo), hi=hex(hi), n_insn=n_insn, n_targets=len(refs),
               rows=[dict(target=hex(r["target"]), chan=r["chan"], first=r["first"],
                          sites=[hex(s) for s in r["sites"]], note=r["note"],
                          boundary=r["boundary"], sites_in_fn=r["sites_in_fn"],
                          first_mn=r["first_mn"], align16=r["align16"],
                          pred_kind=r["pred_kind"], pred_desc=r["pred_desc"],
                          is_suspect=r["is_suspect"]) for r in full]),
           open(os.path.join(WORK, "gap_full.json"), "w", encoding="utf-8"),
           ensure_ascii=False, indent=1)

cnt = Counter(r["chan"] for r in rows_out)
uniq = {ch: len(set(r["target"] for r in rows_out if r["chan"]==ch)) for ch in ("call32","jmp32","jmp8")}
call_tg = set(r["target"] for r in rows_out if r["chan"]=="call32")
jmp32_bad = set(r["target"] for r in rows_out if r["chan"]=="jmp32" and r["first_mn"] in BRANCH_LIKE)
jmp32_good = set(r["target"] for r in rows_out if r["chan"]=="jmp32" and r["first_mn"] not in BRANCH_LIKE)
suspect_by_chan = {ch: len([r for r in rows_out if r["chan"]==ch and r["is_suspect"]]) for ch in ("call32","jmp32","jmp8")}
stats = dict(
    rows=len(rows_out), chan_rows=dict(cnt), uniq_targets=uniq,
    total_distinct_addresses=len(set(r["target"] for r in rows_out)),
    call32_targets=len(call_tg), jmp32_good=len(jmp32_good), jmp32_branch_label=len(jmp32_bad),
    suspect_entries=len(suspect_addrs), suspect_by_chan_rows=suspect_by_chan,
    suspect_criteria="align16 AND pred in {ret,jmp,pad,byte-pad} AND first_mn not in BRANCH_LIKE",
)
json.dump(stats, open(os.path.join(WORK,"gap_stats.json"),"w",encoding="utf-8"), indent=1)
print("== gap stats (R14-R1 strict) ==")
print(json.dumps(stats, indent=1, ensure_ascii=False))
