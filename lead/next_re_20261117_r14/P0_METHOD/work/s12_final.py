"""S12 · 最终分档（含通道 C 的「函数指针表 vs 跳表」精化）与交付 TSV。

通道 C 精化规则（阈值由 S9/S10/S11 的实测标定，见 PROGRESS §4）：
  设该 4 字节项所在的「连续 code-pointer 串」（相邻 4B 项都指向 .text 的最大区间）长度为 L：
  - 若 L ≥ 32 且「串内目标在 coverage 的占比」< 50% 且「串内目标 16B 对齐占比」< 50%
      ⇒ 判 **C_LABEL**（switch 跳表形态：其项是函数体内 case 标签，不得判 FUNC）
  - 否则 ⇒ **C_FN**（函数指针表形态）
  标定依据：0x86E000..0x875000 串 L=6908、in_coverage 0.41%、16B 对齐 6.5%、指令边界 34.8%、
  d1 4.3% ⇒ 与「真入口」总体（_initterm 3,944 项：d1 98.9%、指令边界 99.9%）截然不同。
  而被采纳的两例串长只有 3，且同串其它项**已在 coverage**（0x6CA6A0/0x6CA730）或是 CRT
  locale 初始化表（"LC_MONETARY"/"LC_NUMERIC"）。

三档（最终）：
  T1 可判 FUNC     : A_call ∨ B ∨ C_FN
  T3 可判 NOT_FUNC : ¬bnd ∨ jcc-target ∨ (¬d1 ∧ ¬pad_jmp ∧ fallthrough)
  T2 疑似入口      : 其余（含 7 个被降级的 C_LABEL 行）
"""
import bisect
import json
import os
import pickle
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import COVERAGE, EVIDENCE, HERE, R14, load_lines, norm_addr
import s3_channels as s3

img = s3.img
md = s3.md
chan = pickle.load(open(os.path.join(HERE, "channels.pkl"), "rb"))
A_call, A_jmp, B, C, JCC = chan["A_call"], chan["A_jmp"], chan["B"], chan["C"], chan["jcc"]
c_ptrs = chan["c_data_ptrs"]
starts = s3.starts

cov = set()
for ln in load_lines(COVERAGE)[1:]:
    if ln.strip():
        cov.add(int(norm_addr(ln.split("\t")[0]), 16))

TERM = {"ret", "retf", "int3", "hlt", "ud2"}
DATA_LO, DATA_HI = 0x812000, 0xB79BE4


def is_boundary(va):
    i = bisect.bisect_left(starts, va)
    return i < len(starts) and starts[i] == va


def prev_info(va):
    r = s3.insn_ending_at(va)
    if r is None:
        return None, None
    return s3._mnemonic(r[0], r[1]), r[0]


def pad_lead(va):
    k = 0
    while k < 15:
        b = img.read(va - k - 1, 1)
        if b is None or b[0] not in (0x90, 0xCC):
            break
        k += 1
    return k


def pad_jmp(va):
    k = pad_lead(va)
    mn, _ = prev_info(va - k)
    return mn == "jmp"


def run_of(slot):
    """slot 所在的连续 code-pointer 串（key 为 slot 本身，值域是其目标）。"""
    lo = slot
    while lo - 4 >= DATA_LO and img.in_text(img.u32(lo - 4) or 0):
        lo -= 4
    hi = slot
    while hi + 4 < DATA_HI and img.in_text(img.u32(hi + 4) or 0):
        hi += 4
    tg = [img.u32(q) for q in range(lo, hi + 4, 4)]
    return lo, hi, tg


def c_class(va):
    """返回 (C_ok, kind, detail)。"""
    slots = c_ptrs.get(va, [])
    best = None
    for slot in slots:
        lo, hi, tg = run_of(slot)
        L = len(tg)
        in_cov = sum(1 for t in tg if t in cov) / L * 100.0
        al = sum(1 for t in tg if t % 16 == 0) / L * 100.0
        label = (L >= 32 and in_cov < 50.0 and al < 50.0)
        rec = dict(slot=f"{slot:08X}", run=[f"{lo:08X}", f"{hi:08X}"], L=L,
                   pct_cov=round(in_cov, 2), pct_aligned=round(al, 2),
                   kind=("C_LABEL" if label else "C_FN"))
        if best is None or (not label and best["kind"] == "C_LABEL"):
            best = rec
    if best is None:
        return False, "C_NONE", {}
    return best["kind"] == "C_FN", best["kind"], best


def features(va):
    d = s3.chan_d(va)
    mn, _ = prev_info(va)
    fall = (mn is not None and mn not in TERM and mn != "jmp")
    f = dict(va=va, bnd=is_boundary(va), A_call=va in A_call, A_jmp=va in A_jmp,
             B=va in B, C=va in C, jcc=va in JCC, d1=d["d1"], pad=d["pad"],
             d2=d["d2"], d2_why=d["d2_why"], d=d["d"], pad_jmp=pad_jmp(va),
             fall=fall, prev_mn=mn)
    f["C_ok"], f["C_kind"], f["C_detail"] = c_class(va) if f["C"] else (False, "C_NONE", {})
    if f["A_call"] or f["B"] or f["C_ok"]:
        f["tier"] = "T1"
    elif (not f["bnd"]) or f["jcc"] or ((not f["d1"]) and (not f["pad_jmp"]) and f["fall"]):
        f["tier"] = "T3"
    else:
        f["tier"] = "T2"
    # 卡面字面口径（A∨B∨C 原样，不精化；D 失败即三档）
    f["tier_literal"] = "T1" if (f["A_call"] or f["B"] or f["C"]) else ("T2" if f["d"] else "T3")
    return f


pool = sorted(int(ln.split("\t")[0], 16) for ln in
              load_lines(os.path.join(EVIDENCE, "pool_1669.tsv"))[1:] if ln.strip())
meas = pickle.load(open(os.path.join(HERE, "measure.pkl"), "rb"))
rand = [r["va"] for r in meas["rand"]]

initterm = sorted({int(norm_addr(ln.split("\t")[2]), 16)
                   for ln in load_lines(os.path.join(R14, "P0_INITTERM", "INITTERM_TABLE.tsv"))[1:]
                   if len(ln.split("\t")) >= 3 and ln.split("\t")[2].strip()})

F_pool = [features(v) for v in pool]
F_rand = [features(v) for v in rand]
F_init = [features(v) for v in initterm]

tc = Counter(f["tier"] for f in F_pool)
tl = Counter(f["tier_literal"] for f in F_pool)
T = {k: [f for f in F_pool if f["tier"] == k] for k in ("T1", "T2", "T3")}

# jcc 距离（证明 jcc 目标是同函数体内标签）
jcc_sites = {}
code = img.read(img.text_start, img.text["raw_size"])
for insn in md.disasm(code, img.text_start):
    if insn.address >= img.text_end:
        break
    if insn.id and insn.mnemonic.startswith("j") and insn.mnemonic != "jmp" and insn.operands \
            and insn.operands[0].type == 2:
        jcc_sites.setdefault(insn.operands[0].imm & 0xFFFFFFFF, []).append(insn.address)

dist = []
for f in T["T3"]:
    if f["jcc"] and f["va"] in jcc_sites:
        dist.append(min(abs(f["va"] - s) for s in jcc_sites[f["va"]]))

num = dict(
    pool=len(pool),
    tiers_final=dict(T1=tc["T1"], T2=tc["T2"], T3=tc["T3"]),
    tiers_literal=dict(T1=tl["T1"], T2=tl["T2"], T3=tl["T3"]),
    t1_rows=[dict(va=f"{f['va']:08X}", kind=f["C_kind"], detail=f["C_detail"],
                  bytes=img.bytes_hex(f["va"], 16)) for f in T["T1"]],
    c_label_demoted=[dict(va=f"{f['va']:08X}", kind=f["C_kind"], detail=f["C_detail"])
                     for f in F_pool if f["C"] and not f["C_ok"]],
    t3_breakdown=dict(jcc=sum(1 for f in T["T3"] if f["jcc"]),
                      fallthrough=sum(1 for f in T["T3"] if not f["jcc"] and f["bnd"]
                                      and not f["d1"] and not f["pad_jmp"] and f["fall"]),
                      not_boundary=sum(1 for f in T["T3"] if not f["bnd"])),
    t3_jcc_distance=dict(n=len(dist), median=(sorted(dist)[len(dist) // 2] if dist else None),
                         max=(max(dist) if dist else None),
                         pct_within_4KB=round(100.0 * sum(1 for d in dist if d <= 4096) / len(dist), 2) if dist else None),
    t2_d2_why=dict(Counter(f["d2_why"] for f in T["T2"])),
    t2_d1_true=sum(1 for f in T["T2"] if f["d1"]),
    t2_pad_jmp=sum(1 for f in T["T2"] if not f["d1"] and f["pad_jmp"]),
    adj_units=dict(decidable=tc["T1"] + tc["T3"], undecidable=tc["T2"]),
    # 独立正集（_initterm 3,944 真入口）召回率
    initterm_recall=dict(
        A_call=round(100.0 * sum(1 for f in F_init if f["A_call"]) / len(F_init), 2),
        B=round(100.0 * sum(1 for f in F_init if f["B"]) / len(F_init), 2),
        C=round(100.0 * sum(1 for f in F_init if f["C"]) / len(F_init), 2),
        C_ok=round(100.0 * sum(1 for f in F_init if f["C_ok"]) / len(F_init), 2),
        d1=round(100.0 * sum(1 for f in F_init if f["d1"]) / len(F_init), 2),
        d2=round(100.0 * sum(1 for f in F_init if f["d2"]) / len(F_init), 2),
        bnd=round(100.0 * sum(1 for f in F_init if f["bnd"]) / len(F_init), 2),
        tier_T1=round(100.0 * sum(1 for f in F_init if f["tier"] == "T1") / len(F_init), 2),
        tier_T3=round(100.0 * sum(1 for f in F_init if f["tier"] == "T3") / len(F_init), 2)),
    # 随机基线（16B 对齐 1,000）
    random_rates=dict(A_call=round(100.0 * sum(1 for f in F_rand if f["A_call"]) / len(F_rand), 2),
                      A_jmp=round(100.0 * sum(1 for f in F_rand if f["A_jmp"]) / len(F_rand), 2),
                      B=round(100.0 * sum(1 for f in F_rand if f["B"]) / len(F_rand), 2),
                      C=round(100.0 * sum(1 for f in F_rand if f["C"]) / len(F_rand), 2),
                      C_ok=round(100.0 * sum(1 for f in F_rand if f["C_ok"]) / len(F_rand), 2),
                      d1=round(100.0 * sum(1 for f in F_rand if f["d1"]) / len(F_rand), 2),
                      d2=round(100.0 * sum(1 for f in F_rand if f["d2"]) / len(F_rand), 2),
                      d=round(100.0 * sum(1 for f in F_rand if f["d"]) / len(F_rand), 2),
                      bnd=round(100.0 * sum(1 for f in F_rand if f["bnd"]) / len(F_rand), 2)),
    pool_rates=dict(A_call=round(100.0 * sum(1 for f in F_pool if f["A_call"]) / len(F_pool), 2),
                    A_jmp=round(100.0 * sum(1 for f in F_pool if f["A_jmp"]) / len(F_pool), 2),
                    A_any=round(100.0 * sum(1 for f in F_pool if f["A_call"] or f["A_jmp"]) / len(F_pool), 2),
                    B=round(100.0 * sum(1 for f in F_pool if f["B"]) / len(F_pool), 2),
                    C=round(100.0 * sum(1 for f in F_pool if f["C"]) / len(F_pool), 2),
                    C_ok=round(100.0 * sum(1 for f in F_pool if f["C_ok"]) / len(F_pool), 2),
                    d1=round(100.0 * sum(1 for f in F_pool if f["d1"]) / len(F_pool), 2),
                    d2=round(100.0 * sum(1 for f in F_pool if f["d2"]) / len(F_pool), 2),
                    d=round(100.0 * sum(1 for f in F_pool if f["d"]) / len(F_pool), 2)),
    pool_hits=dict(A_call=sum(1 for f in F_pool if f["A_call"]),
                   A_jmp=sum(1 for f in F_pool if f["A_jmp"]),
                   B=sum(1 for f in F_pool if f["B"]),
                   C=sum(1 for f in F_pool if f["C"]),
                   C_ok=sum(1 for f in F_pool if f["C_ok"]),
                   d1=sum(1 for f in F_pool if f["d1"]),
                   d2=sum(1 for f in F_pool if f["d2"]),
                   d=sum(1 for f in F_pool if f["d"])),
    random_hits=dict(A_call=sum(1 for f in F_rand if f["A_call"]),
                     A_jmp=sum(1 for f in F_rand if f["A_jmp"]),
                     B=sum(1 for f in F_rand if f["B"]),
                     C=sum(1 for f in F_rand if f["C"]),
                     C_ok=sum(1 for f in F_rand if f["C_ok"]),
                     d1=sum(1 for f in F_rand if f["d1"]),
                     d2=sum(1 for f in F_rand if f["d2"]),
                     d=sum(1 for f in F_rand if f["d"])),
)
with open(os.path.join(EVIDENCE, "s12_final.json"), "w", encoding="utf-8") as f:
    json.dump(num, f, ensure_ascii=False, indent=2)
pickle.dump(dict(F_pool=F_pool, F_rand=F_rand, F_init=F_init), open(os.path.join(HERE, "final.pkl"), "wb"))
print(json.dumps(num, ensure_ascii=False, indent=2))
