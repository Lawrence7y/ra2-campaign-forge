"""S4 · 池内命中 / 随机基线 / 富集倍数 / 三档分档 / 正负对照。

随机基线口径（与池同质）：.text 内 16B 对齐地址抽 1,000 个（seed 固定）。
富集倍数 = 池内命中率 / 随机命中率；<2 即判「本池无区分力」（§8.2 技术④ 同质对照原则）。
"""
import json
import os
import pickle
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import ATLAS, EVIDENCE, HERE, Image, RESIDUAL_ADJ, load_lines, new_md, norm_addr
import s3_channels as _s3  # 复用**同一份**通道实现，保证池/基线判据同源同码

img = _s3.img
md = _s3.md
chan = pickle.load(open(os.path.join(HERE, "channels.pkl"), "rb"))
assert chan["tested"] > 0
A_call = chan["A_call"]
A_jmp = chan["A_jmp"]
JCC = chan["jcc"]
B = chan["B"]
C = chan["C"]
C_rdata = chan["C_rdata_extra"]

pool = []
for ln in load_lines(os.path.join(EVIDENCE, "pool_1669.tsv"))[1:]:
    if ln.strip():
        pool.append(int(ln.split("\t")[0], 16))
pool.sort()
assert len(pool) == 1669, len(pool)


def evalA(va):
    return va in A_call, (va in A_jmp and va not in A_call)


def evalB(va):
    return va in B


def evalC(va):
    return va in C, va in C_rdata


_cache = {}


def evalD(va):
    if va in _cache:
        return _cache[va]
    r = _s3.chan_d(va)
    _cache[va] = r
    return r


rows = []
for va in pool:
    ac, aj = evalA(va)
    b = evalB(va)
    c, cx = evalC(va)
    dd = evalD(va)
    if ac or b or c:
        tier = "T1"
    elif dd["d"]:
        tier = "T2"
    else:
        tier = "T3"
    rows.append(dict(va=va, A_call=ac, A_jmp=aj, B=b, C=c, C_rdata=cx,
                     jcc=va in JCC, **{k: dd[k] for k in ("d1", "pad", "d2", "d2_why", "d")},
                     tier=tier))

# ---------------- 随机基线：.text 内 16B 对齐 1,000 个 ----------------
rng = random.Random(20261119)
align_slots = list(range(img.text_start, img.text_end - 16, 16))
rand_addrs = rng.sample(align_slots, 1000)
rand = []
for va in rand_addrs:
    ac, aj = evalA(va)
    c, cx = evalC(va)
    dd = evalD(va)
    rand.append(dict(va=va, A_call=ac, A_jmp=aj, B=va in B, C=c, d1=dd["d1"], d2=dd["d2"], d=dd["d"]))


def rate(lst, key):
    return sum(1 for r in lst if r[key]) / len(lst)


channels = [
    ("A_call", "指令边界 E8 call rel32 目标"),
    ("A_jmp", "指令边界 E9 jmp rel32 目标"),
    ("A_any", "A_call ∪ A_jmp"),
    ("B", "自写 RTTI 定界的虚表槽值"),
    ("C", ".data 4B 初值指向该地址"),
    ("C_any", "C ∪ .rdata 非虚表槽指针"),
    ("d1", "硬边界（ret/retf/int3/hlt/ud2，可隔 ≤15B 90/CC padding；不含 jmp）"),
    ("d2", "体自洽（≥2 指令、≤4096B 到 ret、无 jmp-out）"),
    ("d", "D1 ∧ D2（= 通道 D）"),
]
num = {"pool": len(pool), "random": len(rand_addrs)}

tbl = []
for key, desc in channels:
    if key == "A_any":
        p_hit = sum(1 for r in rows if r["A_call"] or r["A_jmp"])
        r_hit = sum(1 for r in rand if r["A_call"] or r["A_jmp"])
    elif key == "C_any":
        p_hit = sum(1 for r in rows if r["C"] or r["C_rdata"])
        r_hit = sum(1 for r in rand if r["C"] or r.get("C_rdata"))
    else:
        p_hit = sum(1 for r in rows if r[key])
        r_hit = sum(1 for r in rand if r[key])
    pr, rr = p_hit / len(rows), r_hit / len(rand)
    enr = (pr / rr) if rr > 0 else None
    tbl.append(dict(channel=key, desc=desc, pool_hits=p_hit, pool_rate=round(100 * pr, 2),
                    rand_hits=r_hit, rand_rate=round(100 * rr, 2),
                    enrichment=(round(enr, 3) if enr is not None else None),
                    discriminating=("N/A" if enr is None else ("NO" if enr < 2 else "YES"))))

# ---------------- 三档 ----------------
t1 = [r for r in rows if r["tier"] == "T1"]
t2 = [r for r in rows if r["tier"] == "T2"]
t3 = [r for r in rows if r["tier"] == "T3"]
t1_break = dict(
    A_call=sum(1 for r in t1 if r["A_call"]), B=sum(1 for r in t1 if r["B"]),
    C=sum(1 for r in t1 if r["C"]),
    A_jmp_only=sum(1 for r in rows if (not (r["A_call"] or r["B"] or r["C"])) and r["A_jmp"]),
)
t3_break = dict(
    d1_fail=sum(1 for r in t3 if not r["d1"]), d2_fail=sum(1 for r in t3 if not r["d2"]),
    both_fail=sum(1 for r in t3 if not r["d1"] and not r["d2"]),
    jcc_target=sum(1 for r in t3 if r["jcc"]),
    pred_nop_pad0=sum(1 for r in t3 if r["pad"] == 0),
)

# ---------------- 正负对照 ----------------
atlas_entries = []
for ln in load_lines(ATLAS)[1:]:
    p = ln.split("\t")
    if p and p[0].strip():
        atlas_entries.append(int(p[0].strip(), 16))
atlas_entries.sort()
atlas_set = set(atlas_entries)

pos = []
for va in atlas_entries:
    if va in A_call and va in B:
        pos.append(va)
    if len(pos) >= 5:
        break
if len(pos) < 5:
    for va in atlas_entries:
        if (va in A_call or va in B) and va not in pos:
            pos.append(va)
        if len(pos) >= 5:
            break

neg = []
for ln in load_lines(RESIDUAL_ADJ)[1:]:
    p = ln.split("\t")
    if len(p) < 4:
        continue
    if p[2].strip() == "NOT_FUNC" and "internal" in p[3].strip().lower():
        neg.append(int(norm_addr(p[0]), 16))
neg = sorted(set(neg))[:5]
if len(neg) < 5:  # 库若无 internal_label 子类则退到任一 NOT_FUNC
    for ln in load_lines(RESIDUAL_ADJ)[1:]:
        p = ln.split("\t")
        if len(p) >= 3 and p[2].strip() == "NOT_FUNC":
            v = int(norm_addr(p[0]), 16)
            if v not in neg:
                neg.append(v)
        if len(neg) >= 5:
            break
    neg = sorted(neg)[:5]

ctrl = []
for va in pos:
    ac, aj = evalA(va)
    c, cx = evalC(va)
    dd = evalD(va)
    ctrl.append(dict(kind="POS", va=va, A_call=ac, A_jmp=aj, B=va in B, C=c, D=dd["d"],
                     ok=(ac or va in B or c), atlas_in=va in atlas_set))
for va in neg:
    ac, aj = evalA(va)
    c, cx = evalC(va)
    dd = evalD(va)
    ctrl.append(dict(kind="NEG", va=va, A_call=ac, A_jmp=aj, B=va in B, C=c, D=dd["d"],
                     ok=(not (ac or va in B or c)), atlas_in=va in atlas_set))

num.update(
    tiers=dict(T1=len(t1), T2=len(t2), T3=len(t3)),
    tier1_breakdown=t1_break, tier3_breakdown=t3_break,
    ctrl_pos=f"{sum(1 for c in ctrl if c['kind']=='POS' and c['ok'])}/{len(pos)}",
    ctrl_neg=f"{sum(1 for c in ctrl if c['kind']=='NEG' and c['ok'])}/{len(neg)}",
    ctrl_expected_len=len(pos) + len(neg),
    pool_jcc_targets=sum(1 for r in rows if r["jcc"]),
)
num["random_jcc_targets"] = sum(1 for r in rand if r["va"] in JCC)

# ---------------- 输出 ----------------
with open(os.path.join(HERE, "measure.pkl"), "wb") as f:
    pickle.dump(dict(rows=rows, rand=rand, tbl=tbl, num=num, ctrl=ctrl, C_rdata=C_rdata), f)

with open(os.path.join(EVIDENCE, "channel_hits_pool.tsv"), "w", encoding="utf-8") as f:
    f.write("address\tA_call\tA_jmp\tB\tC\tC_rdata\tjcc\td1\tpad\td2\td2_why\tD\ttier\tfirst_bytes8\n")
    for r in rows:
        f.write("\t".join([
            f"{r['va']:08X}", str(int(r["A_call"])), str(int(r["A_jmp"])), str(int(r["B"])),
            str(int(r["C"])), str(int(r["C_rdata"])), str(int(r["jcc"])), str(int(r["d1"])),
            str(r["pad"]), str(int(r["d2"])), r["d2_why"], str(int(r["d"])), r["tier"],
            img.bytes_hex(r["va"], 8)]) + "\n")

with open(os.path.join(EVIDENCE, "random_baseline.tsv"), "w", encoding="utf-8") as f:
    f.write("address\tA_call\tA_jmp\tB\tC\td1\td2\tD\tjcc\n")
    for r in rand:
        f.write("\t".join([f"{r['va']:08X}", str(int(r["A_call"])), str(int(r["A_jmp"])),
                           str(int(r["B"])), str(int(r["C"])), str(int(r["d1"])),
                           str(int(r["d2"])), str(int(r["d"])),
                           str(int(r["va"] in JCC))]) + "\n")

with open(os.path.join(EVIDENCE, "controls.tsv"), "w", encoding="utf-8") as f:
    f.write("kind\taddress\tA_call\tA_jmp\tB\tC\tD\tjudged_ok\n")
    for c in ctrl:
        f.write("\t".join([c["kind"], f"{c['va']:08X}", str(int(c["A_call"])),
                           str(int(c["A_jmp"])), str(int(c["B"])), str(int(c["C"])),
                           str(int(c["D"])), str(int(c["ok"]))]) + "\n")

with open(os.path.join(EVIDENCE, "s4_numbers.json"), "w", encoding="utf-8") as f:
    json.dump(num, f, ensure_ascii=False, indent=2)

print(json.dumps(num, ensure_ascii=False, indent=2))
print("\nchannel table")
for t in tbl:
    print(f"  {t['channel']:7s} pool {t['pool_hits']:5d}/{t['pool_rate']:6.2f}%  "
          f"rand {t['rand_hits']:4d}/{t['rand_rate']:6.2f}%  enrichment {t['enrichment']}  {t['discriminating']}")
