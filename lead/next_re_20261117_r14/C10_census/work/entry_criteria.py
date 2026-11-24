#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C10 真入口判据细查：对 call32/jmp32 洞目标按卡判据(e)逐条核验。
判据: 16字节对齐 + 前驱 nop/ret/jmp/int3 + 非 jcc 目的地址 + 有 push ebp/sub esp 序言。
输出 work/entry_criteria.json + EVIDENCE/entry_criteria.tsv
不依赖 atlas entry+size 来发现目标（目标来自 sweep_independent），owner 只做洞判定。
"""
import os, sys, json, bisect, struct, re
from collections import defaultdict
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C10_census")
WORK = os.path.join(CARD, "work")
EVID = os.path.join(CARD, "EVIDENCE")
sys.path.insert(0, WORK)
import sweep_independent as SI
import capstone

LO, HI = 0x773500, 0x7E038D
pe = SI.RawPE()

# atlas 区间（仅洞判定）
lines = open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8", errors="replace").read().splitlines()
hdr = lines[0].split("\t")
rows = []
for ln in lines[1:]:
    if not ln.strip(): continue
    r = dict(zip(hdr, ln.split("\t")))
    rows.append((int(r["entry"], 16), int(r["size"])))
rows.sort()
starts = [a for a, _ in rows]; sizes = dict(rows)
def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + sizes[starts[i]] else None

# 目标（独立通道）
chans, stats = SI.sweep(pe, want_jcc=True)
calls = chans["call32"]; jmps = chans["jmp32"]; jcc32 = chans.get("jcc32", {})

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True; md.detail = False

def read(va, n):
    try: return pe.read(va, n)
    except Exception: return b""

def insns_at(va, count=8, span=48):
    d = read(va, span); out = []
    for ins in md.disasm(d, va):
        if ins.id == 0: continue
        out.append("%s %s" % (ins.mnemonic, ins.op_str))
        if len(out) >= count: break
    return out

def prev_kind_ext(va):
    """前驱：nop(0x90)/int3(0xCC) 填充、ret、jmp、other。返回(kind,detail)。"""
    # 连续 0x90 或 0xCC
    pre = read(va - 64, 64)
    if not pre: return "other", "unreadable"
    tail = pre
    k90 = 0; kcc = 0
    for c in reversed(tail):
        if c == 0x90: k90 += 1
        elif c == 0xCC: kcc += 1
        else: break
    # 分别统计紧邻连续
    k = 0; fill = None
    for c in reversed(tail):
        if c in (0x90, 0xCC):
            if fill is None: fill = c
            if c == fill: k += 1
            else: break
        else: break
    if fill == 0x90 and k >= 2: return "nop", "preceded by %d nops" % k
    if fill == 0xCC and k >= 2: return "int3", "preceded by %d int3" % k
    # 找 end==target 的实指令
    align_start = (va - 32) & ~0xF
    buf = read(align_start, va - align_start + 8)
    last = None
    for ins in md.disasm(buf, align_start):
        if ins.id == 0: continue
        if ins.address >= va: break
        if ins.address + ins.size == va: last = ins
    if last:
        if last.mnemonic in ("ret", "retn"): return "ret", "prev=%s %s" % (last.mnemonic, last.op_str)
        if last.mnemonic == "jmp": return "jmp", "prev=jmp %s" % last.op_str
        return "other", "prev=%s %s" % (last.mnemonic, last.op_str)
    return "other", "no-insn-ends-at-target"

# jcc 目的地址集合（0F 8x rel32 与 7x rel8），用于"非 jcc 目的地址"判据
jcc_targets = set()
# 0F 8x rel32
for tgt, sites in jcc32.items():
    jcc_targets.add(tgt)
# 7x rel8: 全 .text 扫（capstone）
sec, data = pe.text_blob()
for ins in md.disasm(data, sec["va"]):
    if ins.id == 0: continue
    mn = ins.mnemonic
    if mn.startswith("j") and mn not in ("jmp",):
        # 取 rel8 或 rel32 目标
        op = ins.op_str
        if re.match(r'^0x[0-9A-Fa-f]+$', op):
            jcc_targets.add(int(op, 16))

PROLOGUE_FIRST = ("push", "sub", "mov", "lea", "xor", "and", "enter", "cli", "pushf")
def has_prologue(ins_list):
    """序言判据：前 6 条内出现 push ebp 或 sub esp,imm。"""
    joined = " ; ".join(ins_list[:6]).lower()
    if "push ebp" in joined: return True, "push ebp"
    if re.search(r'sub\s+esp\s*,', joined): return True, "sub esp"
    return False, ""

results = []
# 合并 call32 + jmp32 目标（jmp8 不计入真入口）
targets = defaultdict(set)
for t in calls: targets[t].add("call32")
for t in jmps: targets[t].add("jmp32")
for t in sorted(targets):
    if not (LO <= t < HI): continue
    if owner(t) is not None: continue   # 必须在洞中
    il = insns_at(t)
    pk, pkd = prev_kind_ext(t)
    align16 = (t % 16 == 0)
    is_jcc_tgt = t in jcc_targets
    pro, prowhy = has_prologue(il)
    first = il[0] if il else ""
    # 卡判据(e) 全部满足
    crit = align16 and pk in ("nop", "ret", "jmp", "int3") and (not is_jcc_tgt) and pro
    results.append(dict(target=t, chans=sorted(targets[t]), align16=align16, prev=pk, prev_detail=pkd,
                        is_jcc_target=is_jcc_tgt, prologue=pro, prologue_why=prowhy,
                        first=first, insns=" ; ".join(il), pass_all=crit,
                        n_call_sites=len(calls.get(t, [])), n_jmp_sites=len(jmps.get(t, []))))

# 输出
with open(os.path.join(EVID, "entry_criteria.tsv"), "w", encoding="utf-8") as f:
    f.write("target\tchans\talign16\tprev\tis_jcc_target\tprologue\tfirst\tpass_all\tn_call\tn_jmp\tinsns\n")
    for r in results:
        f.write("%08X\t%s\t%d\t%s\t%d\t%d\t%s\t%d\t%d\t%d\t%s\n" % (
            r["target"], ",".join(r["chans"]), r["align16"], r["prev"],
            r["is_jcc_target"], r["prologue"], r["first"].replace("\t"," "),
            r["pass_all"], r["n_call_sites"], r["n_jmp_sites"], r["insns"].replace("\t"," ")))
json.dump(dict(lo=hex(LO), hi=hex(HI), n_targets=len(results),
               pass_count=sum(1 for r in results if r["pass_all"]),
               pass_list=[hex(r["target"]) for r in results if r["pass_all"]],
               results=[dict(target=hex(r["target"]), **{k:v for k,v in r.items() if k!="target"}) for r in results]),
          open(os.path.join(WORK, "entry_criteria.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("call32/jmp32 洞目标(去重):", len(results))
print("判据(e)全通过 疑似真入口:", sum(1 for r in results if r["pass_all"]))
for r in results:
    mark = "PASS" if r["pass_all"] else "    "
    print("%s %08X %-12s A%d prev=%-5s jcc=%d pro=%d(%s) first=%s" % (
        mark, r["target"], ",".join(r["chans"]), r["align16"], r["prev"],
        r["is_jcc_target"], r["prologue"], r["prologue_why"], r["first"]))
