#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Q1 · A 笔 114 件的方向。
规则出处（逐字引用 R17_R84_T2_EVID2\q3_final.py:2）：
  # Q3 定稿：规则=目录内“已裁件”>=3 且同向占比>=75% => 该目录平票件随多数派
及 decide_dir 实现（q3_final.py:17-23）：
  def decide_dir(d, minn=3, q=0.75):
      c=dec[d]; n=c["对象抄本"]+c["过程输出"]
      if n<minn: return None
      o,p=c["对象抄本"],c["过程输出"]
      maj=max(o,p); lab="对象抄本" if o>p else ("过程输出" if p>o else None)
      if lab is None or maj/n<q: return None
      return lab,n,maj/n
产物 q3_final.txt / q3_summary.txt 只给了「114 件 / 1995960 B」这个合计，**没有逐件方向**，
故按同一规则原样重跑（本脚本），并把该规则的两个参数（minn=3, q=0.75）记为默认值。
输入（全部只读）：
  R17_R81_T2_EVID\_verdicts.tsv 列 rel/verdict/O/P/reason
  R17_R81_T2_EVID\_undead_evid.tsv 列 rel/bytes
输出：majority_114.tsv 列 rel/bytes/verdict/parent_dir/majority_basis
      q1_majority.json 汇总
"""
from __future__ import annotations
import csv, json, os, sys
from collections import defaultdict, Counter

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
EVID = os.path.join(R14, "R17_R81_T2_EVID")
HERE = os.path.dirname(os.path.abspath(__file__))
MINN, Q = 3, 0.75


def load(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def parent(rel):
    p = os.path.dirname(rel)
    return p.replace("\\", "/") if p else "(root)"


vd = load(os.path.join(EVID, "_verdicts.tsv"))
ud = {r["rel"].replace("\\", "/"): int(r["bytes"]) for r in load(os.path.join(EVID, "_undead_evid.tsv"))}

dec = defaultdict(Counter)
for r in vd:
    if r["verdict"] in ("对象抄本", "过程输出"):
        dec[parent(r["rel"])][r["verdict"]] += 1
tie = [r for r in vd if r["verdict"] == "无法判定"]


def decide_dir(d, minn=MINN, q=Q):
    c = dec[d]
    n = c["对象抄本"] + c["过程输出"]
    if n < minn:
        return None
    o, p = c["对象抄本"], c["过程输出"]
    lab = "对象抄本" if o > p else ("过程输出" if p > o else None)
    if lab is None or (max(o, p) / n) < q:
        return None
    return lab, n, max(o, p) / n


res, unres = [], []
for r in tie:
    rel = r["rel"].replace("\\", "/")
    dd = decide_dir(parent(rel))
    if dd:
        res.append((rel, dd))
    else:
        unres.append(rel)

# 完整性核对：规则命中的 114 件必须与 q3_final.txt 的 114/1995960 完全对上
res.sort()
tot_bytes = sum(ud[rel] for rel, _ in res)
out = os.path.join(HERE, "majority_114.tsv")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write("rel\tbytes\tverdict\tparent_dir\tmajority_basis\n")
    for rel, (lab, n, ratio) in res:
        o, p = dec[parent(rel)]["对象抄本"], dec[parent(rel)]["过程输出"]
        basis = f"n_decided={n};obj={o};proc={p};share={ratio:.4f}"
        f.write(f"{rel}\t{ud[rel]}\t{lab}\t{parent(rel)}\t{basis}\n")

vc = Counter(lab for _, (lab, _, _) in res)
vb = Counter()
for rel, (lab, _, _) in res:
    vb[lab] += ud[rel]

# 兼容名字形态（"/EVIDENCE" 以大小写不敏感匹配）检查：114 件里有多少不在 /EVIDENCE/ 下
evid_dir_name = sum(1 for rel, _ in res if "/evidence/" in rel.lower())
# 附：仅目录名含 EVIDENCE（大小写不敏感）的平票件，重跑一遍看是否也是 114
res_evid = [(rel, decide_dir(parent(rel))) for rel in (r["rel"].replace("\\", "/") for r in tie)
            if "/evidence/" in rel.lower()]
res_evid = [(rel, dd) for rel, dd in res_evid if dd]

summary = {
    "rule_source": r"R17_R84_T2_EVID2\q3_final.py:2 与 :17-23",
    "rule_params": {"minn": MINN, "q": Q, "denominator": "父目录内已裁件(对象抄本+过程输出)"},
    "tie_total": len(tie),
    "covered": len(res),
    "covered_bytes": tot_bytes,
    "unresolved": len(unres),
    "unresolved_bytes": sum(ud[r] for r in unres),
    "verdict_counts": dict(vc),
    "verdict_bytes": dict(vb),
    "covered_all_under_EVIDENCE": len(res) - evid_dir_name == 0,
    "evidence_only_rerun": {"n": len(res_evid), "bytes": sum(ud[r] for r, _ in res_evid)},
    "parent_dirs": len({parent(r) for r, _ in res}),
}
with open(os.path.join(HERE, "q1_majority.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
