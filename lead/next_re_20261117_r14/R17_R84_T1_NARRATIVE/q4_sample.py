#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""q4_sample.py — R45-T1 Q4：剔掉 Q3 之后 P0 还剩什么，30 件抽样逐件看

输入（只读）：narrative_candidates.tsv / should_exclude.tsv / files_tier_Cprime.tsv
输出（只写本目录）：q4_sample.tsv / q4_sample.json

抽样规则（写死、无随机种子、任何人可复现）：
  剩余候选（4,493 - Q3 排除）按 rel 升序排序，第 k 件取 idx = floor((k+0.5)*N/30)，k=0..29。
  —— 等距抽样，不是"挑好看的"。
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q2q3_types as Q  # 复用 read_head / feats（只读函数）

OUT = os.path.dirname(os.path.abspath(__file__))
RE_VA_LEAD = re.compile(r"^\s*(0x)?[0-9A-Fa-f]{6,8}\s*[:\t ]")
RE_VA2 = re.compile(r"^\s*0x[0-9A-Fa-f]{6,8}\s{2,}")
RE_ANYVA = re.compile(r"(?m)^\s*(0x)?[0-9A-Fa-f]{6,8}\s{2,}\S")
RE_DISASM = re.compile(r"(?m)^\s*(mov|push|pop|call|jmp|je|jne|lea|cmp|test|add|sub|ret|and|or|xor)\s+\S", re.I)


def main():
    cand = [l.split("\t") for l in open(os.path.join(OUT, "narrative_candidates.tsv"),
                                         encoding="utf-8").read().splitlines()[1:]]
    excl = set(l.split("\t")[0] for l in open(os.path.join(OUT, "should_exclude.tsv"),
                                             encoding="utf-8").read().splitlines()[1:])
    rest = sorted([r for r in cand if r[0] not in excl], key=lambda r: r[0])
    N = len(rest)
    idx = [int((k + 0.5) * N / 30) for k in range(30)]
    sample = [rest[i] for i in idx]

    rows = []
    for r in sample:
        rel, nbytes, cn_ratio = r[0], int(r[1]), float(r[3])
        h = Q.read_head(rel)
        if h is None:
            rows.append(dict(rel=rel, bytes=nbytes, cn_ratio=cn_ratio, status="未取得"))
            continue
        text = h.decode("utf-8", "replace")
        ft = Q.feats(text)
        lead_va = ft["va"]
        body_va = len(RE_ANYVA.findall(text))
        dis = len(RE_DISASM.findall(text))
        # 判"像不像对象抄本"：正文里有地址流水或指令流水，且不是只有标题里提一句地址
        score = 0
        why = []
        if lead_va / max(ft["n"], 1) >= 0.25:
            score += 3
            why.append(f"行首VA占{lead_va}/{ft['n']}")
        elif lead_va > 0:
            score += 1
            why.append(f"行首VA {lead_va}/{ft['n']}")
        if body_va - lead_va >= 5:
            score += 2
            why.append(f"正文(缩进)VA行 {body_va - lead_va}")
        if dis >= 10:
            score += 2
            why.append(f"指令流水行 {dis}")
        if ft["tab_frac"] >= 0.5:
            score += 2
            why.append(f"TAB表行 {ft['tabline']}/{ft['n']}")
        verdict = "像对象抄本" if score >= 3 else ("混合(叙述+地址点缀)" if score >= 1 else "像叙述/判词")
        rows.append(dict(rel=rel, bytes=nbytes, cn_ratio=cn_ratio, narr_frac=round(ft["narr_frac"], 3),
                         lead_va=lead_va, body_va=body_va, disasm=dis, tabline=ft["tabline"],
                         n=ft["n"], verdict=verdict, note="; ".join(why) or "无地址/指令流水",
                         first=ft["first"][:100]))

    with open(os.path.join(OUT, "q4_sample.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("rel\tbytes\tcn_ratio\tnarr_frac\tlead_va\tbody_va\tdisasm_lines\ttab_rows\tn_lines\tverdict\tnote\tfirst_line\n")
        for x in rows:
            if x.get("status") == "未取得":
                fh.write(f'{x["rel"]}\t{x["bytes"]}\t{x["cn_ratio"]}\t\t\t\t\t\t\t未取得\t内容未取得\t\n')
                continue
            fh.write(f'{x["rel"]}\t{x["bytes"]}\t{x["cn_ratio"]}\t{x["narr_frac"]}\t{x["lead_va"]}\t{x["body_va"]}'
                     f'\t{x["disasm"]}\t{x["tabline"]}\t{x["n"]}\t{x["verdict"]}\t{x["note"]}\t{x["first"]}\n')

    like = [x for x in rows if x.get("verdict") == "像对象抄本"]
    out = dict(N_rest=N, sample_n=len(rows), idx=idx,
               rest_n_bytes=sum(int(r[1]) for r in rest),
               verdict_counts={v: sum(1 for x in rows if x.get("verdict") == v)
                               for v in ("像对象抄本", "混合(叙述+地址点缀)", "像叙述/判词", "未取得")},
               like_obj=[dict(rel=x["rel"], bytes=x["bytes"], note=x["note"]) for x in like],
               sample=rows)
    json.dump(out, open(os.path.join(OUT, "q4_sample.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "sample"}, ensure_ascii=False, indent=1))
    for x in rows:
        print(f'  {x["verdict"]:16s} {x["bytes"]:9d} cn={x["cn_ratio"]:.2f} {x["rel"]}')
        print(f'        {x.get("note","")} | {x.get("first","")[:80]}')


if __name__ == "__main__":
    main()
