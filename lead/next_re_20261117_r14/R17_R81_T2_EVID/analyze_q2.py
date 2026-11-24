#!/usr/bin/env python3
"""R44-T2-EVID 执行员脚本：Q2 分布 + Q5 正控(Python 实现) + Q3 分层抽样 + Q4 内容判据。
只读 lead\；写只写本目录。不看 why 列做 Q3 判定。
"""
import csv, os, re, json, collections, math

LEAD = r"D:\Project\ra2-campaign-forge\lead"
TSV = os.path.join(LEAD, "next_re_20261117_r14", "R17_R78_T1_RECLASS", "files_excluded_prime.tsv")
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID")
os.makedirs(OUT, exist_ok=True)

def load():
    rows = []
    with open(TSV, "r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f, delimiter="\t")
        for r in rd:
            rows.append(r)
    return rows

def is_evid(rel):
    return "evidence" in rel.lower()

def undead_evid(rows):
    return [r for r in rows if r["label"] == "UNDECIDED" and is_evid(r["rel"])]

# ---- basename 形态：优先级 stdout>stderr>_out>report>result>其他 ----
def bn_form(r):
    bn = os.path.basename(r["rel"]).lower()
    if "stdout" in bn:
        return "stdout"
    if "stderr" in bn:
        return "stderr"
    if "_out" in bn:
        return "_out"
    if "report" in bn:
        return "report"
    if "result" in bn:
        return "result"
    return "其他"

def evid_parent_card(rel):
    # EVIDENCE 段之前最近的目录；若为通用段则上溯到形如 W\d+/S\d+/RE-/D\d+/C\d+/R\d+ 的卡名
    parts = rel.split("/")
    idx = None
    for i, p in enumerate(parts):
        if p.lower() == "evidence":
            idx = i
            break
    if idx is None:
        return "?"
    generic = {"_audit", "sandbox", "baseline_v14", "build_out"}
    card_re = re.compile(r"^(W\d+|S\d+|RE-|D\d+|C\d+|R\d+|M\d+|A\d+)", re.I)
    for j in range(idx - 1, -1, -1):
        p = parts[j]
        if p in generic:
            continue
        if card_re.match(p):
            return p
    # 否则取 index1（轮次下的第一层）
    return parts[1] if len(parts) > 1 else "?"

def topcard(rel):
    parts = rel.split("/")
    return parts[1] if len(parts) > 1 else "?"

def rnd(rel):
    parts = rel.split("/")
    return parts[0] if parts else "?"

def main():
    rows = load()
    ue = undead_evid(rows)
    n_all_undecided = sum(1 for r in rows if r["label"] == "UNDECIDED")
    tot_b = sum(int(r["bytes"]) for r in ue)
    print("TOTAL_ROWS", len(rows))
    print("ALL_UNDECIDED", n_all_undecided)
    print("UNDEAD_EVID_N", len(ue))
    print("UNDEAD_EVID_BYTES", tot_b)

    # basename 形态
    c = collections.Counter(bn_form(r) for r in ue)
    cb = collections.Counter()
    for r in ue:
        cb[bn_form(r)] += int(r["bytes"])
    print("\nBASENAME_FORM")
    for k in ["stdout", "stderr", "_out", "report", "result", "其他"]:
        print(f"  {k}\t{c[k]}\t{cb[k]}")

    # 扩展名
    ce = collections.Counter(r["ext"] for r in ue)
    ceb = collections.Counter()
    for r in ue:
        ceb[r["ext"]] += int(r["bytes"])
    print("\nEXT")
    for k, v in ce.most_common():
        print(f"  {k}\t{v}\t{ceb[k]}")

    # 顶层卡（轮次下第一层目录）
    cc = collections.Counter(topcard(r["rel"]) for r in ue)
    ccb = collections.Counter()
    for r in ue:
        ccb[topcard(r["rel"])] += int(r["bytes"])
    print("\nTOPCARD_TOP15")
    for k, v in cc.most_common(15):
        print(f"  {k}\t{v}\t{ccb[k]}")

    # EVIDENCE 父卡（卡名，更精确）
    cp = collections.Counter(evid_parent_card(r["rel"]) for r in ue)
    print("\nEVID_PARENT_CARD_TOP15")
    for k, v in cp.most_common(15):
        print(f"  {k}\t{v}")

    # 轮次
    cr = collections.Counter(rnd(r["rel"]) for r in ue)
    print("\nROUND")
    for k, v in cr.most_common():
        print(f"  {k}\t{v}")

    # 写中间清单供 Q3/Q4
    with open(os.path.join(OUT, "_undead_evid.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["rel", "ext", "bytes", "mtime_ns", "family", "label", "layer", "in_tier_C_old", "bnform", "topcard", "evidparent"])
        for r in ue:
            w.writerow([r["rel"], r["ext"], r["bytes"], r["mtime_ns"], r["family"], r["label"], r["layer"], r["in_tier_C_old"], bn_form(r), topcard(r["rel"]), evid_parent_card(r["rel"])])
    print("\nWROTE _undead_evid.tsv", len(ue))

if __name__ == "__main__":
    main()
