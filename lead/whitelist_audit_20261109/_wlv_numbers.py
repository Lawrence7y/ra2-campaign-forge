# -*- coding: utf-8 -*-
# _wlv_numbers.py — 独立核：未登记项数 / P01-P05 逐字比对 / 正负样本构成 / 守卫词
import json, re, sys
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead/whitelist_audit_20261109"
sys.path.insert(0, str(ROOT / "lead/gate_r9sem_20261109"))
import _r9s_predicates as R9S
import _r9s_samples as S

out = json.loads((WDIR / "_wlv_regress_out.json").read_text(encoding="utf-8"))
rows = out["all_rows"]
items = [(r["domain"], e["token"]) for r in rows for e in r["per_element"]]
n_items = len(items)
reg = set(R9S.SPECS.keys())
reg_items = [x for x in items if x[1] in reg]
unreg_items = [x for x in items if x[1] not in reg]
print("=== 未登记项数独立核对 ===")
print(f"  n_items = {n_items}")
print(f"  已登记 token 的项 = {len(reg_items)}   (token 集合 = {sorted(reg)})")
print(f"  未登记 token 的项 = {len(unreg_items)}")
print(f"  302 - 5(白名单条目数) = {n_items-5}")
print(f"  302 - 10(已登记项数) = {n_items-10}")
print(f"  distinct 未登记 token 串数 = {len(set(t for _,t in unreg_items))}")
print(f"  → 报告写『297 项 token 未登记』与实算 {len(unreg_items)} 是否一致: {len(unreg_items)==297}")

print("\n=== P01–P05 与真实主件：整块逐字 / 逐行命中 ===")
mains = {
 "P01": ROOT/"lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
 "P02": ROOT/"lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md",
 "P03": ROOT/"lead/n11_wording_fix_20261108/N11_WORDING_FIX.md",
 "P04": ROOT/"lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
 "P05": ROOT/"lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
}
for s in S.POS[:5]:
    real = mains[s["id"]].read_text(encoding="utf-8", errors="replace")
    block = s["text"]
    whole = block in real
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    real_lines = set(l.strip() for l in real.split("\n") if l.strip())
    hit = sum(1 for l in lines if l in real_lines)
    print(f"  {s['id']}: whole_block_verbatim={whole}  line_hits={hit}/{len(lines)}  why自称逐字={'逐字' in s['why']}")

print("\n=== 正负样本：是否全部为 _r9s_samples.py 硬编码字面量 ===")
src = (ROOT/"lead/gate_r9sem_20261109/_r9s_samples.py").read_text(encoding="utf-8")
for s in S.SAMPLES:
    # 每条 text 是否作为字面量出现在样本源码（取前 24 字符判断）
    frag = s["text"][:24].replace("\n","\\n")
    print(f"  {s['id']}: text_len={len(s['text']):4d}  src_literal_frag={frag in src}  expect={s['expect']}", end="")
    if s["expect"]:
        ok, layer, _ = R9S.r9s_element_present(s["text"], s["token"])
        print(f"  layer={layer}")
    else:
        print()

print("\n=== 负样本守卫词/占位词计数（独立复算，按 _r9s_predicates.py:86-92 词表）===")
PENDING_RE = R9S.PENDING_RE
PLACEHOLDER_RE = R9S.PLACEHOLDER_RE
cnt = 0
ids = []
for s in S.NEG:
    # 复核轮口径：text 含 PENDING_RE 命中，或含占位词
    has = bool(PENDING_RE.search(s["text"]))
    for tok in ["待","略","TBD","N/A","未","如何","？","?"]:
        pass
    # 用与 _r9sv_extra.py 口径近似：PENDING_RE.search(text) 或 PLACEHOLDER 词在 text
    ph = any(w in s["text"] for w in ["待定","待指定","略","TBD","待补","待验","待查","未采集","未验","尚未","输出未","无法判定","不可判定","需进一步","如何","拟做","计划"])
    if has or ph:
        cnt += 1; ids.append(s["id"])
print(f"  含守卫/占位词 = {cnt}/{len(S.NEG)}  ids={ids}")
print("  注：报告引用 _r9sv_extra_stdout.txt:3 = 13/24；本处为独立近似口径，见输出")
