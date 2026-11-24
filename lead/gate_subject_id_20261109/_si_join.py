# -*- coding: utf-8 -*-
"""_si_join.py — 把 gatescan 的 max~size 位点与写域下划线风险关联（只读本任务写域内两份 JSON）。"""
import json
from pathlib import Path

OUTD = Path(r"D:/Project/ra2-campaign-forge/lead/gate_subject_id_20261109")
gs = json.loads((OUTD / "_si_gatescan_out.json").read_text(encoding="utf-8"))
sc = json.loads((OUTD / "_si_scan_out.json").read_text(encoding="utf-8"))

rec_by_dir = {r["dir"]: r for r in sc["records"]}


def domain_of(rel_posix):
    """lead/<domain>/... -> 最近祖先写域记录；lead 根 -> lead；非 lead -> None。"""
    parts = rel_posix.split("/")
    if parts[0] != "lead":
        return None, None
    if len(parts) == 2:  # lead 下直接文件
        rec = rec_by_dir.get("lead")
        return "lead", rec
    for i in range(len(parts) - 1, 0, -1):
        d = "/".join(parts[:i + 1]) if i >= 1 else "lead"
        if d in rec_by_dir:
            return d, rec_by_dir[d]
    return "lead", rec_by_dir.get("lead")


def risk_of(rec):
    if rec is None:
        return "N/A(域外)"
    if rec["underCount"] > 0:
        return "HIGH(域内有下划线中间稿)"
    return "MED(域内暂无下划线件)"


def dump_sites(sites, title):
    print("== %s：%d 处 ==" % (title, len(sites)))
    seen_domains = {}
    for x in sites:
        d, rec = domain_of(x["file"])
        risk = risk_of(rec)
        seen_domains.setdefault((d, risk), 0)
        seen_domains[(d, risk)] += 1
        print("  [%s] %s:%d" % (risk, x["file"], x["line"]))
        print("      %s" % x["text"][:200])
    print("  -- 按域汇总 --")
    for (d, risk), n in sorted(seen_domains.items()):
        print("  %-46s %-30s %d 处" % (d, risk, n))
    print()


dump_sites(gs["leadPyMaxNearSizeSites"], "lead/ 内 max(...) 紧邻 st_size 的位点")
dump_sites(gs["rootPyMaxNearSizeSites"], "root/.tmp 内 max(...) 紧邻 st_size 的位点")

print("== smell 只命中文件按类型计数（lead+root） ==")
for name, items in sorted(gs["smellSummary"].items()):
    lead_n = sum(1 for it in items if it["file"].startswith("lead/"))
    root_n = len(items) - lead_n
    print("  %-18s lead=%d root=%d" % (name, lead_n, root_n))

print()
print("== md 文件里提及按大小/时间选件的（lead/ 内）：%d 件 ==" % len(gs["leadMdWithSizeMarks"]))
for s in gs["leadMdWithSizeMarks"]:
    marks = s.get("marks", [])
    first = marks[0] if marks else {}
    print("  %-78s marks=%-3d maxNear=%s L%s %s" % (
        s["file"], s.get("markCount", 0), first.get("ctxHasMax"),
        first.get("line"), (first.get("text") or "")[:110]))
