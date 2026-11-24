# -*- coding: utf-8 -*-
r"""_gpv_regress.py — 独立复现 74 条合成语料回归（第五步(d) 数据可复现性）。
安全做法：不动态 exec 文件文本；用 importlib 正常 import 原脚本到独立模块名，
先备份两个既有输出，跑完立即按字节还原（不修改任何既有交付件内容），
并另存本次实跑副本为 _gpv_ 前缀。逐条 74 条不放宽、不缩小。
另核：v1 朴素并集留盘证据内部一致性；gate_check 完整 verdict 口径；报告次序。
零真机、零采样；只读 protected 件，写只落本写域。
"""
import hashlib
import importlib.util
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_pipeline_20261109"
sys.path.insert(0, str(WD))

TARGETS = [WD / "_gp_regression_out.txt", WD / "_gp_regression_out.json"]
BACKUP = {}
for t in TARGETS:
    BACKUP[t] = t.read_bytes()
BEFORE = {str(t): (hashlib.sha256(b).hexdigest(), len(b)) for t, b in BACKUP.items()}
print("BEFORE_DELIVERABLE_FP =", json.dumps(BEFORE, ensure_ascii=False, sort_keys=True))

# 正常模块加载（importlib 从文件加载是 Python 标准导入，非 eval/exec 外部文本）
spec = importlib.util.spec_from_file_location("_gpv_repro_mod", WD / "_gp_regression.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)         # 原脚本顶层即执行全 74 条逐条跑 + print
    FRESH = {t: t.read_bytes() for t in TARGETS}   # 本次实跑产物（在还原前抓取）
finally:
    for t, b in BACKUP.items():
        t.write_bytes(b)                  # 按字节还原，交付件内容不变
    # 另存本次实跑副本（_gpv_ 前缀），stdout 已由外层重定向
    (WD / "_gpv_repro_out.json").write_bytes(FRESH[TARGETS[1]])
    (WD / "_gpv_repro_out.txt").write_bytes(FRESH[TARGETS[0]])

AFTER = {str(t): (hashlib.sha256(t.read_bytes()).hexdigest(), len(t.read_bytes()))
         for t in TARGETS}
print("AFTER_DELIVERABLE_FP =", json.dumps(AFTER, ensure_ascii=False, sort_keys=True))
print("DELIVERABLE_UNCHANGED =", BEFORE == AFTER)

payload = mod.payload
print("\n===== 复现结果（本会话实跑，corpus_n=%d）=====" % len(mod.CORPUS))
print("REPRO_STAT =", json.dumps(payload["single_layer_vs_chain"], ensure_ascii=False, sort_keys=True))
print("REPRO_CONFLICTS =", payload["chain_conflicts_total"],
      "UNRESOLVED =", payload["chain_unresolved_total"])
print("REPRO_BY_FAMILY =", json.dumps(payload["by_family"], ensure_ascii=False, sort_keys=True))

claim = {"naive": (34, 33, 7), "r10": (35, 20, 19), "r12": (39, 0, 35),
         "n13": (71, 0, 3), "chain": (69, 2, 3)}
match = {}
for m, (ok, fp, fn) in claim.items():
    s = payload["single_layer_vs_chain"][m]
    match[m] = (s["ok"], s["fp"], s["fn"]) == (ok, fp, fn)
print("REPRO_MATCH_CLAIM =", json.dumps(match, ensure_ascii=False),
      "ALL =", all(match.values()))
c = payload["single_layer_vs_chain"]["chain"]["ok"]
n = payload["single_layer_vs_chain"]["n13"]["ok"]
print("CHAIN_VS_N13 = %d vs %d  => 合成链更差 %d 条" % (c, n, n - c))

# ---- v1 朴素并集留盘证据（脚本未留盘 → 只能核对 JSON，如实记「未重跑」） ----
v1 = json.loads((WD / "_gp_regression_v1_union_out.json").read_text(encoding="utf-8"))
rows = v1["rows"]
fp_rows = [r for r in rows if r["expect"] == "PASS" and r["chain"] == "CATCH"]
print("\n===== v1 朴素并集留盘证据（未重跑，脚本未留盘）=====")
print("V1 corpus_n=", len(rows),
      " stat=", json.dumps(v1["single_layer_vs_chain"], ensure_ascii=False, sort_keys=True))
print("V1 chain FP rows =", len(fp_rows))
print("V1 FP 逐条 r10/n13 =",
      json.dumps([{"id": r["id"], "r10": r["r10"], "n13": r["n13"]}
                  for r in fp_rows], ensure_ascii=False))
print("V1 script present =", (WD / "_gp_regression_v1_union.py").exists())

# ---- gate_check 完整 verdict 口径（R9/R11 独立项也并入） ----
P, g7, n13, T = mod.P, mod.g7, mod.n13, mod.T
full = {}
for it in mod.CORPUS:
    r = P.gate_check(it["text"], it["tokens"], WD, g7, n13, T, root=ROOT)
    v = r["verdict"].split("+")[0]
    full[v] = full.get(v, 0) + 1
print("\n===== gate_check 完整 verdict 分布（74 条）=====")
print("FULL_VERDICT_DIST =", json.dumps(full, ensure_ascii=False, sort_keys=True))
r_demo = P.gate_check("grep 结果：已生效 0 命中", T, WD, g7, n13, T, root=ROOT)
print("FULL_VERDICT_DEMO_K9 =", r_demo["verdict"],
      "R9/R11 =", [p["rule_id"] + ":" + p["msg"][:34]
                   for p in r_demo["problems"] if p["rule_id"] in ("R9", "R11")],
      "rows =", [(x["token"], x["verdict"], x["rules"]) for x in r_demo["_rows"]])

# ---- 报告次序（§3(c) 声明 conflicts 按 pos 升序） ----
it = next(x for x in mod.CORPUS if x["id"] == "N13-N07")
r = P.gate_check(it["text"], it["tokens"], WD, g7, n13, T, root=ROOT)
print("\n===== 报告次序 =====")
print("N13-N07 rows =", [(x["token"], x["pos"]) for x in r["_rows"]])
print("N13-N07 conflicts =", [(c["token"], c["pos"]) for c in r["conflicts"]])
print("rows pos ascending =",
      [x["pos"] for x in r["_rows"]] == sorted(x["pos"] for x in r["_rows"]))
print("conflicts pos ascending =",
      [c["pos"] for c in r["conflicts"]] == sorted(c["pos"] for c in r["conflicts"]))
