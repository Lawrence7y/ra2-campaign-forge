"""S5 · 诊断：T1 的 9 行 / E9-only 7 行身份、T3 的失败原因构成、族内（同族已裁标签）区分力。

§8.1 ⑳：族级判据判别力须按「族内随机」算。本卡的"族"就是 P0 残差池；
它的已裁标签集来自 `P0_RESIDUAL\RESIDUAL_ADJUDICATION.tsv`（同一建池过程产生的 FUNC/NOT_FUNC）。
用它在**池内**量 D 的区分力，才是 D 真正的判别力；对 .text 随机的 11.8× 只证明 D≈建池条件。
"""
import json
import os
import pickle
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import EVIDENCE, HERE, RESIDUAL_ADJ, load_lines, norm_addr
import s3_channels as _s3

img = _s3.img
chan = pickle.load(open(os.path.join(HERE, "channels.pkl"), "rb"))
meas = pickle.load(open(os.path.join(HERE, "measure.pkl"), "rb"))
rows = meas["rows"]
A_call, A_jmp, B, C = chan["A_call"], chan["A_jmp"], chan["B"], chan["C"]
JCC = chan["jcc"]

out = {}

# ---- 1. T1 的 9 行身份（通道 C = .data 初值指向）----
t1 = [r for r in rows if r["tier"] == "T1"]
det = []
for r in t1:
    va = r["va"]
    slots = chan["c_data_ptrs"].get(va, [])
    det.append(dict(va=f"{va:08X}", A_call=r["A_call"], A_jmp=r["A_jmp"], B=r["B"], C=r["C"],
                    C_rdata=r["C_rdata"], jcc=r["jcc"], d1=r["d1"], d2=r["d2"],
                    data_slots=[f"{s:08X}" for s in slots[:6]],
                    n_slots=len(slots), first_bytes=img.bytes_hex(va, 16)))
out["tier1_detail"] = det

# ---- 2. E9-only（A_jmp 但无 A_call/B/C）----
jonly = [r for r in rows if r["A_jmp"] and not (r["A_call"] or r["B"] or r["C"])]
out["jmp_only"] = [dict(va=f"{r['va']:08X}", tier=r["tier"], d1=r["d1"], d2=r["d2"],
                        jcc=r["jcc"], first_bytes=img.bytes_hex(r["va"], 16)) for r in jonly]

# ---- 3. T2 / T3 的 d2_why 构成 ----
out["t2_d2_why"] = dict(Counter(r["d2_why"] for r in rows if r["tier"] == "T2"))
out["t3_d2_why"] = dict(Counter(r["d2_why"] for r in rows if r["tier"] == "T3"))
out["t3_d1_fail_by_pred"] = dict(Counter(
    "d1_ok_but_d2_fail" if r["d1"] else "d1_fail" for r in rows if r["tier"] == "T3"))

# ---- 4. 族内已裁标签集上的四通道命中率（真正的判别力）----
lab = []
for ln in load_lines(RESIDUAL_ADJ)[1:]:
    p = ln.split("\t")
    if len(p) < 4:
        continue
    a = int(norm_addr(p[0]), 16)
    if p[2].strip() in ("FUNC", "NOT_FUNC"):
        lab.append((a, p[2].strip(), p[3].strip()))
lab_set = {a for a, _, _ in lab}
# 只用与池同源的：ENUM UNDECIDABLE 里已被 RESIDUAL 裁过、且已进 coverage 的那批
pool = set(r["va"] for r in rows)


def hit_stats(labels):
    sv = [a for a, v, _ in labels if v == "FUNC"]
    nv = [a for a, v, _ in labels if v == "NOT_FUNC"]

    def rate(addrs, fn):
        return (sum(1 for a in addrs if fn(a)) / len(addrs) * 100.0) if addrs else None

    r = dict(n_func=len(sv), n_not_func=len(nv))
    for name, fn in (("A_call", lambda a: a in A_call), ("B", lambda a: a in B),
                     ("C", lambda a: a in C),
                     ("d1", lambda a: _s3.chan_d(a)["d1"]),
                     ("d2", lambda a: _s3.chan_d(a)["d2"]),
                     ("D", lambda a: _s3.chan_d(a)["d"])):
        r["FUNC_" + name] = round(rate(sv, fn) or 0, 2)
        r["NOTFUNC_" + name] = round(rate(nv, fn) or 0, 2)
    return r


out["family_labeled_all"] = hit_stats(lab)
out["labeled_total"] = len(lab_set)

# ---- 5. T3 抽样（看是否真的不像入口）----
t3 = [r for r in rows if r["tier"] == "T3"]
out["t3_sample"] = [dict(va=f"{r['va']:08X}", d1=r["d1"], pad=r["pad"], d2=r["d2"],
                         d2_why=r["d2_why"], jcc=r["jcc"],
                         prev16=img.bytes_hex(r["va"] - 16, 16),
                         here32=img.bytes_hex(r["va"], 32)) for r in t3[:20]]

with open(os.path.join(EVIDENCE, "s5_diag.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in out.items() if k not in ("tier1_detail", "t3_sample")},
                 ensure_ascii=False, indent=2))
print("--- tier1 detail ---")
for d in det:
    print(json.dumps(d, ensure_ascii=False))
