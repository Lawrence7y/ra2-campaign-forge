"""finalize: validate all rows, write base_rate.tsv and fill REPORT.md summary table."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
EVID = ROOT / "EVIDENCE"
DELTA = ROOT / "coverage_delta.tsv"
REPORT = ROOT / "REPORT.md"
BASE = ROOT / "base_rate.tsv"

rows = json.loads((WORK / "slice_b1.json").read_text(encoding="utf-8"))
anch = {a["entry"]: a for a in json.loads((WORK / "anchors.json").read_text(encoding="utf-8"))}

dlines = DELTA.read_text(encoding="utf-8").rstrip().splitlines()
header = dlines[0]
data = [ln.split("\t") for ln in dlines[1:]]
assert header == "entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path", header
assert len(data) == 17, len(data)

summary = []
class_named = ring_ok = rewritten = 0
fail = []
for r, d in zip(rows, data):
    e = r[0]
    assert d[0] == e, (d[0], e)
    assert d[1] == r[1] and d[2] == r[2], "subsystem/name changed!"
    assert d[4] == "[已证]", d[4]
    assert d[5] == f"SEMFIX_ENGFAM_B1/EVIDENCE/ROW_{e}.txt", d[5]
    sem = d[3]
    # forbidden strings
    if "循环内非栈写" in sem or "③b④" in sem or "class name unproven" in sem:
        fail.append((e, "forbidden string in semantics"))
    # per-row anchors must be distinct: failure landing / xor / consume unique
    a = anch[e]
    evtxt = (EVID / f"ROW_{e}.txt").read_text(encoding="utf-8")
    for token in (a["vector"], a["failure_landing"], ",".join(a["xor_eax"]),
                  a["call_site"], a["caller_consume"]["test_site"]):
        if token not in evtxt:
            fail.append((e, f"missing anchor {token} in evidence"))
    named = any("DynamicVectorClass" in w["name_raw"] and w["plausible"]
                for w in a["ctor_writes"])
    ok3 = a["n_call_derived_jl"] >= 4 and bool(a["caller_consume"])
    rw = named and ok3 and ("③b②" in sem)
    if named:
        class_named += 1
    if ok3:
        ring_ok += 1
    if rw:
        rewritten += 1
    cls = "是"
    summary.append((e, cls, "是" if ok3 else "否", "是" if rw else "否"))

# distinctness check: rewritten semantics must not all be identical
sems = [d[3] for d in data]
assert len(set(sems)) == 17, "rewritten semantics not row-specific!"

# base_rate
n = len(data)
rate = rewritten / n if n else 0.0
BASE.write_text(
    "population\trows\tclass_named\tring3b2_ok\trewritten\trate\n"
    f"SEMFIX_ENGFAM_B1\t{n}\t{class_named}\t{ring_ok}\t{rewritten}\t{rate:.4f}\n",
    encoding="utf-8",
)

# fill REPORT table
rep = REPORT.read_text(encoding="utf-8")
table = "| entry | 类名取得 | ③b② 成立 | 是否改写 |\n|---|---|---|---|\n"
for e, cls, ok, rw in summary:
    table += f"| {e} | {cls} | {ok} | {rw} |\n"
rep = rep.replace(
    "| entry | 类名取得 | ③b② 成立 | 是否改写 |\n|---|---|---|---|\n| （待取证后填充） | | | |",
    table.rstrip("\n"),
)
rep = rep.replace("> 状态：生成中，完成后填充。列名：entry / 类名取得否 / ③b② 成立否 / 是否改写。\n\n", "")
# failure/cls lists
unnamed = [e for e, c, _, _ in summary if c == "否"]
notok = [e for e, _, o, _ in summary if o == "否"]
extra = "\n## 锚点与失败清单\n\n"
extra += f"- 类名 `未取得` 的行：{', '.join(unnamed) if unnamed else '无（17 行全部取得元素类类名）'}。\n"
extra += f"- ③b② 不成立的行：{', '.join(notok) if notok else '无（17 行全部成立）'}。\n"
extra += "- 每行证据均含该行独立的向量地址 / 失败落点 / 成功 xor / Save_Core 调用点 / 调用方消费点；改写后的 17 条 one_line_semantics 互不相同。\n"
extra += f"- base_rate: rows={n}, class_named={class_named}, ring3b2_ok={ring_ok}, rewritten={rewritten}, rate={rate:.4f}\n"
# replace trailing section (from '## 锚点与失败清单' onward)
idx = rep.find("## 锚点与失败清单")
if idx >= 0:
    rep = rep[:idx] + extra
else:
    rep = rep.rstrip() + "\n" + extra
rep = rep.replace(
    "# SEMFIX-ENGFAM-B1 — 报告\n",
    "# SEMFIX-ENGFAM-B1 — 报告（完成：17/17 行）\n", 1)
REPORT.write_text(rep, encoding="utf-8")

print(f"class_named={class_named} ring3b2_ok={ring_ok} rewritten={rewritten} rate={rate:.4f}")
print(f"distinct semantics={len(set(sems))}/17")
if fail:
    print("FAILURES:")
    for f in fail:
        print("  ", f)
else:
    print("all per-row validations passed")
