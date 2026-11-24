# -*- coding: utf-8 -*-
"""崩点4 补证④：实读 _dB_anchor_recompute_data.json，核对 +e>50 列（字段 nGt50PlusE）
在 6 档上是实际数值还是空列/None/缺失；并用 trigger_details 的逐触发 wait 数组独立重算
（e=0 与 e=2.510999999 双算），判定 +e>50 是否与 nTrig、>50 列全等（判别力问题）。
只读；路径全常量 + 包含校验。"""
import json
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
WD = LEAD / "r2_unclosed_b_20261108"
OUT = WD / "_b_data_cells_out.txt"
P = LEAD / "dtrigger_round2_20261107" / "_dB_anchor_recompute_data.json"

with open(P, "rb") as f:
    raw = f.read()
data = json.loads(raw.decode("utf-8-sig"))

lines = []
lines.append(f"file = {P}")
lines.append(f"top_keys = {list(data.keys())}")

cells = data.get("cells", {})
details = data.get("trigger_details", {})
lines.append(f"cells ids = {list(cells.keys())}")
lines.append(f"trigger_details ids = {list(details.keys())}")
if details:
    any_id = next(iter(details))
    rows = details[any_id]
    lines.append(f"trigger_details['{any_id}'] type={type(rows).__name__} n={len(rows)}")
    if isinstance(rows, list) and rows:
        lines.append(f"sample row0 = {json.dumps(rows[0], ensure_ascii=False)[:400]}")

def find_wait(row):
    if isinstance(row, dict):
        for k, v in row.items():
            if "wait" in k.lower() and isinstance(v, (int, float)):
                return float(v)
    return None

lines.append("")
lines.append("【cells 字段逐档实读 + 由逐触发 wait 数组独立重算】")
for cid in sorted(cells.keys()):
    c = cells[cid]
    scal = {k: v for k, v in c.items() if not isinstance(v, (list, dict))}
    lines.append(f"fields({cid}) = {json.dumps(scal, ensure_ascii=False)[:420]}")
    n_trig = c.get("nTrig")
    n_ge100 = c.get("nGe100")
    n_e50 = c.get("nGt50PlusE")
    n_gt50 = c.get("nGt50", c.get("nGt50ms", "ABSENT"))
    rows = details.get(cid, [])
    waits = []
    if isinstance(rows, list):
        for r in rows:
            w = find_wait(r)
            if w is not None:
                waits.append(w)
    if waits and isinstance(n_trig, int):
        re_ge100 = sum(1 for w in waits if w >= 100.0)
        re_e50_0 = sum(1 for w in waits if w > 50.0)
        re_e50_e = sum(1 for w in waits if w + 2.510999999 > 50.0)
        wmin = min(waits)
        eq_trig = (n_e50 == n_trig)
        if isinstance(n_gt50, int):
            eq_gt50 = (n_e50 == n_gt50)
        else:
            eq_gt50 = "n/a(cells 无 >50 列字段)"
        lines.append(
            f"SUM {cid}: nTrig={n_trig} cells.nGe100={n_ge100} cells.nGt50PlusE={n_e50} cells.nGt50={n_gt50}"
            f" | 重算 >=100={re_ge100} +e>50(e=0)={re_e50_0} +e>50(e=2.510999999)={re_e50_e}"
            f" | min(wait)={wmin:.3f} | +e>50==nTrig? {eq_trig} | +e>50==>50? {eq_gt50}")
    else:
        lines.append(f"SUM {cid}: rows/wait 解析失败（waits n={len(waits)}，nTrig={n_trig!r}）")

lines.append("")
all_have = all(isinstance(cells[c].get("nGt50PlusE"), int) for c in cells)
none_any = any(cells[c].get("nGt50PlusE") is None for c in cells)
miss_any = any("nGt50PlusE" not in cells[c] for c in cells)
lines.append(f"判定：6 档 nGt50PlusE 全为整数 = {all_have}；任一档为 None = {none_any}；任一档字段缺失 = {miss_any}")

sc = data.get("selfcheck_all_pass", data.get("self_check_all_pass", "ABSENT"))
lines.append(f"selfcheck_all_pass = {sc}")
meta = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool)) and k not in ("cells",)}
lines.append(f"top 标量字段 = {json.dumps(meta, ensure_ascii=False)[:700]}")

txt = "\n".join(lines) + "\n"
assert OUT.is_relative_to(WD)
OUT.write_text(txt, encoding="utf-8")
print(txt)
