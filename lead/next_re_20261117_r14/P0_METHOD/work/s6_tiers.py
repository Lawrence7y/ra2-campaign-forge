"""S6 · 最终分档 + 独立正集对照 + 交付 TSV/抽样证据。

三档规则（比「D 失败即 NOT_FUNC」严格，理由见 PROGRESS §5）：
  T1（可判 FUNC）   : A_call ∨ B ∨ C            —— 有独立外部证据指向该地址
  T3（可判 NOT_FUNC）: ¬bnd ∨ jcc ∨ (¬d1 ∧ ¬pad_jmp ∧ fall)
        ¬bnd    : 在全 .text 线性反汇编（覆盖 100%）里不是指令边界 ⇒ 不可能是入口（纪律 7）
        jcc     : 是指令边界 jcc 的目的地 ⇒ 函数体内标签
        ¬d1∧¬pad_jmp∧fall : 前面既无终止符也无 jmp 隔断，且前一条指令顺流进入该地址 ⇒ 可达、非入口
  T2（疑似入口，不得判 FUNC，也不得判 NOT_FUNC）: 其余

为什么 T3 不用「d 失败」一刀切：d 失败里有 (a) 裸 `C3`（可能是极短的合法函数或共享尾声）、
(b) `jmp_out` 尾跳桩（**按契约就是真入口**，如 _initterm thunk 与转发桩）。这两类若判 NOT_FUNC
就是把真入口判死 —— 正是 ADJ4/ADJ5「结构证据当主判据」的同型错误。

独立正集：`P0_INITTERM/INITTERM_TABLE.tsv` 的 3,944 项 —— 由 `_initterm` 逐槽 `call eax` 保证
「启动时被调用一次」，是**不依赖任何结构判据**的真入口集，且该卡已证「0/3,944 是 E8/E9 直接目标」
⇒ 与本池同一总体类型。这才是 D 通道召回率的无偏估计。
"""
import json
import os
import pickle
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import ATLAS, EVIDENCE, HERE, R14, load_lines, norm_addr
import s3_channels as _s3

img = _s3.img
md = _s3.md
chan = pickle.load(open(os.path.join(HERE, "channels.pkl"), "rb"))
A_call, A_jmp, B, C, JCC = chan["A_call"], chan["A_jmp"], chan["B"], chan["C"], chan["jcc"]
C_rd = chan["C_rdata_extra"]
starts = _s3.starts

import bisect


def is_boundary(va):
    i = bisect.bisect_left(starts, va)
    return i < len(starts) and starts[i] == va


TERM = {"ret", "retf", "int3", "hlt", "ud2"}


def mnemonic_ending(va):
    r = _s3.insn_ending_at(va)
    if r is None:
        return None, None
    return _s3._mnemonic(r[0], r[1]), r[0]


def pad_jmp(va):
    """padding（0..15 字节 90/CC）之前是否紧跟无条件 jmp（建池条件里的弱形态）。"""
    k = 0
    while k < 15:
        b = img.read(va - k - 1, 1)
        if b is None or b[0] not in (0x90, 0xCC):
            break
        k += 1
    q = va - k
    mn, _ = mnemonic_ending(q)
    return (k >= 1 or k == 0) and mn == "jmp"


def features(va):
    d = _s3.chan_d(va)
    mn_prev, _ = mnemonic_ending(va)
    fall = (mn_prev is not None and mn_prev not in TERM and mn_prev != "jmp")
    f = dict(
        va=va, bnd=is_boundary(va), A_call=va in A_call, A_jmp=va in A_jmp,
        B=va in B, C=va in C, C_rdata=va in C_rd, jcc=va in JCC,
        d1=d["d1"], pad=d["pad"], d2=d["d2"], d2_why=d["d2_why"], d=d["d"],
        pad_jmp=pad_jmp(va), fall=fall, prev_mn=mn_prev,
    )
    # 三档
    if f["A_call"] or f["B"] or f["C"]:
        f["tier"] = "T1"
    elif (not f["bnd"]) or f["jcc"] or ((not f["d1"]) and (not f["pad_jmp"]) and f["fall"]):
        f["tier"] = "T3"
    else:
        f["tier"] = "T2"
    # 卡面字面口径（仅供并列对照）：D 失败即 T3
    if f["A_call"] or f["B"] or f["C"]:
        f["tier_literal"] = "T1"
    elif f["d"]:
        f["tier_literal"] = "T2"
    else:
        f["tier_literal"] = "T3"
    return f


# ---------------- 四个集合 ----------------
pool_rows = [int(ln.split("\t")[0], 16) for ln in load_lines(os.path.join(EVIDENCE, "pool_1669.tsv"))[1:] if ln.strip()]
pool = sorted(pool_rows)

meas = pickle.load(open(os.path.join(HERE, "measure.pkl"), "rb"))
rand = [r["va"] for r in meas["rand"]]

initterm = []
for ln in load_lines(os.path.join(R14, "P0_INITTERM", "INITTERM_TABLE.tsv"))[1:]:
    p = ln.split("\t")
    if len(p) >= 3 and p[2].strip():
        initterm.append(int(norm_addr(p[2]), 16))
initterm = sorted(set(initterm))

atlas = sorted({int(norm_addr(ln.split("\t")[0]), 16) for ln in load_lines(ATLAS)[1:] if ln.strip()})

print(f"pool {len(pool)}  rand {len(rand)}  initterm {len(initterm)}  atlas {len(atlas)}")

F_pool = [features(v) for v in pool]
F_rand = [features(v) for v in rand]
F_init = [features(v) for v in initterm]
F_atlas = [features(v) for v in atlas]

# ---------------- 分档统计 ----------------
tc = Counter(f["tier"] for f in F_pool)
tl = Counter(f["tier_literal"] for f in F_pool)
T = {k: [f for f in F_pool if f["tier"] == k] for k in ("T1", "T2", "T3")}

def rate(lst, key):
    return round(100.0 * sum(1 for f in lst if f[key]) / len(lst), 2) if lst else None

num = dict(
    pool=len(pool),
    tiers=dict(T1=tc["T1"], T2=tc["T2"], T3=tc["T3"]),
    tiers_literal=dict(T1=tl["T1"], T2=tl["T2"], T3=tl["T3"]),
    tier1_via=dict(C=tc["T1"], A_call=sum(1 for f in T["T1"] if f["A_call"]),
                   B=sum(1 for f in T["T1"] if f["B"]),
                   A_jmp_only=sum(1 for f in F_pool if f["A_jmp"] and not (f["A_call"] or f["B"] or f["C"]))),
    tier3_breakdown=dict(
        not_boundary=sum(1 for f in T["T3"] if not f["bnd"]),
        jcc_target=sum(1 for f in T["T3"] if f["jcc"]),
        fallthrough_into=sum(1 for f in T["T3"] if f["bnd"] and not f["jcc"] and not f["d1"] and not f["pad_jmp"] and f["fall"]),
    ),
    tier2_d2_why=dict(Counter(f["d2_why"] for f in T["T2"])),
    tier2_d1=sum(1 for f in T["T2"] if f["d1"]),
    tier2_pad_jmp_only=sum(1 for f in T["T2"] if not f["d1"] and f["pad_jmp"]),
    # 独立正集（真入口）上的四通道命中率 = 召回率
    initterm_recall=dict(A_call=rate(F_init, "A_call"), A_jmp=rate(F_init, "A_jmp"),
                         B=rate(F_init, "B"), C=rate(F_init, "C"),
                         d1=rate(F_init, "d1"), d2=rate(F_init, "d2"), d=rate(F_init, "d"),
                         bnd=rate(F_init, "bnd"),
                         would_be_T1=rate(F_init, "tier") if False else
                         round(100.0 * sum(1 for f in F_init if f["tier"] == "T1") / len(F_init), 2),
                         would_be_T3=round(100.0 * sum(1 for f in F_init if f["tier"] == "T3") / len(F_init), 2)),
    # 边界判据的跨实现交叉验证
    atlas_boundary_pct=rate(F_atlas, "bnd"),
    initterm_boundary_pct=rate(F_init, "bnd"),
    random_boundary_pct=rate(F_rand, "bnd"),
    pool_boundary_pct=rate(F_pool, "bnd"),
)

# 独立正集里被判 T3 的（= 判据假阴性，必须逐条报告）
fn = [f for f in F_init if f["tier"] == "T3"]
num["initterm_false_notfunc"] = len(fn)
num["initterm_false_notfunc_sample"] = [
    dict(va=f"{f['va']:08X}", bnd=f["bnd"], jcc=f["jcc"], d1=f["d1"], d2_why=f["d2_why"],
         prev_mn=f["prev_mn"], bytes16=img.bytes_hex(f["va"], 16)) for f in fn[:12]]

# ---------------- 交付 TSV ----------------
def write_features(name, fl, with_tier=True):
    cols = ["address", "tier", "tier_literal", "bnd", "A_call", "A_jmp", "B", "C", "C_rdata",
            "jcc", "d1", "pad", "d2", "d2_why", "D", "pad_jmp", "fall", "prev_mn", "bytes16"]
    with open(os.path.join(EVIDENCE, name), "w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for f in fl:
            fh.write("\t".join([f"{f['va']:08X}", f["tier"], f["tier_literal"],
                                str(int(f["bnd"])), str(int(f["A_call"])), str(int(f["A_jmp"])),
                                str(int(f["B"])), str(int(f["C"])), str(int(f["C_rdata"])),
                                str(int(f["jcc"])), str(int(f["d1"])), str(f["pad"]),
                                str(int(f["d2"])), f["d2_why"], str(int(f["d"])),
                                str(int(f["pad_jmp"])), str(int(f["fall"])),
                                str(f["prev_mn"]), img.bytes_hex(f["va"], 16)]) + "\n")


write_features("pool_features.tsv", F_pool)
write_features("random_features.tsv", F_rand)
write_features("initterm_features.tsv", F_init)

with open(os.path.join(EVIDENCE, "s6_tiers.json"), "w", encoding="utf-8") as fh:
    json.dump(num, fh, ensure_ascii=False, indent=2)
print(json.dumps(num, ensure_ascii=False, indent=2))
