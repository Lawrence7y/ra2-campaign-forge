# -*- coding: utf-8 -*-
# _m5d_fp.py —— 交付轮独立核验（只读）：十件指纹（hashlib）+ 镜像区现状取证 + 绑定行输出
import hashlib, json

BASE = "D:/Project/ra2-campaign-forge/"
EXPECTED = {
    "lead/b2b_design_20261106/STATE_MATRIX.json": ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    "lead/b2b_design_20261106/B2B_DESIGN.md": ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    "lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md": ("b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b", 22048),
    "lead/v2_precision_fix_20261108/_pf2_findings_20261109.md": ("4aef8957094008262d980640836ab0aec3e797f892b25fe8ff02b6aa87957fe4", 7966),
    "lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md": ("6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818),
    "lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md": ("ec0fb8ec47cfb71be5b28bc8a76f9152a6cbd377e741e7be1902a0958fbba154", 42172),
    "lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md": ("441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923", 25095),
    "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py": ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

fails = 0
shas = {}
for rel, (exp_sha, exp_bytes) in EXPECTED.items():
    b = open(BASE + rel, "rb").read()
    sha = hashlib.sha256(b).hexdigest()
    shas[rel] = (sha, len(b))
    ok = (sha == exp_sha and len(b) == exp_bytes)
    if not ok:
        fails += 1
    print(f"[{'MATCH' if ok else 'MISMATCH'}] {rel}  bytes={len(b)}")
print(f"SUMMARY: {len(EXPECTED) - fails}/{len(EXPECTED)} MATCH, {fails} MISMATCH\n")

# 绑定行（格式：被核对象 SHA256 = <64hex>，字节数 = <n>）
for rel in ("lead/b2b_design_20261106/B2B_DESIGN.md", "lead/b2b_design_20261106/STATE_MATRIX.json"):
    sha, n = shas[rel]
    print(f"被核对象 SHA256 = {sha}，字节数 = {n}（{rel}）")
print()

b2b = open(BASE + "lead/b2b_design_20261106/B2B_DESIGN.md", encoding="utf-8").read()
sm = open(BASE + "lead/b2b_design_20261106/STATE_MATRIX.json", encoding="utf-8").read()
b2b_lines = b2b.splitlines()
sm_lines = sm.splitlines()
print(f"B2B_DESIGN.md 总行数 = {len(b2b_lines)}；STATE_MATRIX.json 总行数 = {len(sm_lines)}；json.loads 条目 = {len(json.loads(sm))}")
print(":144 含「下表与之逐行一致」 =", "下表与之逐行一致" in b2b_lines[143])
print(":146 表头列数 =", len([c for c in b2b_lines[145].split("|") if c.strip() != ""]), "（含 state/preState/condition/verdict/confidence/is_new/usableAsCrashEvidence）")
for ln in (148, 150, 151):
    print(f":{ln} 字符数 = {len(b2b_lines[ln-1])}")
for phrase in ("跑后任意", "任意文件状态"):
    b2b_hits = [i + 1 for i, l in enumerate(b2b_lines) if phrase in l]
    sm_hits = [i + 1 for i, l in enumerate(sm_lines) if phrase in l]
    print(f"「{phrase}」: B2B_DESIGN.md {len(b2b_hits)} 处（行{b2b_hits}）；STATE_MATRIX.json {len(sm_hits)} 处（行{sm_hits}）")
# 「」引号在 JSON 各行 condition 的分布（复核 F1 取证复跑）
hits = [i + 1 for i, l in enumerate(sm_lines) if "「" in l]
print(f"STATE_MATRIX.json 含「」的行 = {hits}")
