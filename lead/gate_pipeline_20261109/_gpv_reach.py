# -*- coding: utf-8 -*-
r"""_gpv_reach.py — ③ 补充：K7/K8 分支可达性 + conflicts[] 登记内容核对。
若 K8 永不可达，则「未消解 0」是空结论（没有裁决器会失败）。
做法：穷举构造文本/词表组合，统计每个 K 规则在 74 条 + 构造样本上实际触发次数；
再定向构造 CRLF / 词表不对齐样本试图触发 K7/K8。
零真机、零采样。
"""
import collections
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_pipeline_20261109"
sys.path.insert(0, str(WD))
import _gp_pipeline as P

g7, n13, T = P.load_predicates()

# ---- (1) 74 条语料上 K1..K9 实际触发次数 ----
import importlib.util
spec = importlib.util.spec_from_file_location("_gpv_reg", WD / "_gp_regression.py")
reg = importlib.util.module_from_spec(spec)
# 为不覆盖交付件，先备份再还原（本件只读统计，不落盘）
baks = {p: p.read_bytes() for p in [WD / "_gp_regression_out.txt", WD / "_gp_regression_out.json"]}
try:
    spec.loader.exec_module(reg)
finally:
    for p, b in baks.items():
        p.write_bytes(b)

counter = collections.Counter()
unresolved_cases = []
for it in reg.CORPUS:
    r = P.gate_check(it["text"], it["tokens"], WD, g7, n13, T, root=ROOT)
    for row in r["_rows"]:
        for k in row["rules"]:
            counter[k] += 1
    if r["summary"]["unresolved"]:
        unresolved_cases.append((it["id"], r["summary"]["unresolved"]))
print("===== 74 条语料上 K1–K9 触发次数 =====")
print(json.dumps(dict(sorted(counter.items())), ensure_ascii=False))
print("UNRESOLVED_CASES =", unresolved_cases, "TOTAL =", sum(v for _, v in unresolved_cases))

# ---- (2) 定向构造：能否触发 K7 (RAISE) / K8 (FAIL_CLOSED + unresolved) ----
print("\n===== 定向构造 K7 / K8 可达性 =====")
CASES = []
# CRLF 造成 (token,pos) 失配：N13 gpos 与 R10 pos 不同
for label, text, toks in [
    ("CRLF_neg", "前一行说明\r\n不宣告 X 已生效", T),
    ("CRLF_assert", "前一行说明\r\n本笔已入账", T),
    ("CRLF_2line", "不宣告 X 已生效\r\n但 Y 已入账", T),
    ("CRLF_mixed", "未核 grep 结果：已生效 0 命中\r\n本笔已入账", T),
    # 词表不对齐：tokens 只含一个词，N13 三词仍在 tok_set 内
    ("vocab_partial", "已入账 已生效", ["已入账"]),
    ("vocab_partial2", "不宣告已生效", ["已入账"]),   # r10 不扫已生效，n13 扫
    ("vocab_c07", "本件已填，已入账", ["已填"]),
    ("n13_default_only", "### 1(c) 有没有已入账的？", ["已入账", "已生效"]),
]:
    r = P.gate_check(text, toks, WD, g7, n13, T, root=ROOT)
    CASES.append({"label": label, "text": text, "tokens": toks,
                  "verdict": r["verdict"], "summary": r["summary"],
                  "rows": [(x["token"], x["pos"], x["r10"], x["r12"], x["n13"],
                            x["verdict"], x["rules"]) for x in r["_rows"]],
                  "conflicts": [(c["token"], c["pos"], c["r10"], c["n13"],
                                 c["resolved"], c["final"]) for c in r["conflicts"]]})
    print("  %-18s verdict=%-6s rows=%s" % (label, r["verdict"], CASES[-1]["rows"]))
    if r["summary"]["unresolved"] or r["summary"]["raise"]:
        print("       ★ unresolved=%d raise=%d conflicts=%s" %
              (r["summary"]["unresolved"], r["summary"]["raise"], CASES[-1]["conflicts"]))

allrows = [(c["label"], row) for c in CASES for row in c["rows"]]
print("\nK7_RAISE_SEEN =", any("K7" in row[6] for _, row in allrows))
print("K8_UNRESOLVED_SEEN =", any("K8" in row[6] for _, row in allrows))
print("FAIL_CLOSED_SEEN =", any(row[5] == "FAIL_CLOSED" for _, row in allrows))

# ---- (3) conflicts[] 是否保留双方原意见（§3(b) 附加不变量） ----
print("\n===== conflicts[] 登记内容（BOUND 5 处冲突）=====")
bound = (ROOT / "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md").read_text(encoding="utf-8")
r = P.gate_check(bound, T, WD, g7, n13, T, root=ROOT)
print("BOUND conflicts_n =", len(r["conflicts"]))
for c in r["conflicts"]:
    print("  pos=%-6d tok=%s r10=%-5s r12=%-6s n13=%-5s resolved=%s final=%-5s rules=%s" %
          (c["pos"], c["token"], c["r10"], c["r12"], c["n13"],
           c["resolved"], c["final"], ",".join(c["rules"])))
print("全部保留 r10 与 n13 两列原意见 =",
      all(("r10" in c and "n13" in c and "r12" in c) for c in r["conflicts"]))
