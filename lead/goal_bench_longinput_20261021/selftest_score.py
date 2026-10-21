"""评分器自测：三种已知答案形态必须得到预期判定。"""
import json
import sys
from pathlib import Path

OUT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\goal_bench_longinput_20261021")
sys.path.insert(0, str(OUT))
sys.dont_write_bytecode = True

import importlib.util
spec = importlib.util.spec_from_file_location("sc", OUT / "score.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

truth = json.loads((OUT / "ground_truth_60k.json").read_text(encoding="utf-8"))
import re
truth["tail_marker_expected"] = re.search(r"EOF-MARKER-[0-9A-F]{4}", truth["tail120"]).group(0)

print("truth: bytes=%d canaries=%d cnt_addr=%d cnt_eof=%d marker=%s" % (
    truth["corpus_bytes"], truth["canary_count"], truth["count_0x0084F2BA"],
    truth["count_eof_marker"], truth["tail_marker_expected"]))

# --- 用例 1：完美答案 ---
perfect = {
    "canaries": truth["canaries"],
    "count_0x0084F2BA": truth["count_0x0084F2BA"],
    "count_eof_marker": truth["count_eof_marker"],
    "tail_marker": truth["tail_marker_expected"],
}
r1 = sc.score_one("60k", "TEST-perfect", json.dumps(perfect), truth)
print("\n[1] 完美答案 →", r1["verdict"], "score", r1["score"],
      "| canary", r1["canary_hit"], "| count", r1["count_hit"], "| tail", r1["tail_ok"])
assert r1["verdict"] == "PERFECT" and r1["score"] == 1.0, "完美答案应得 PERFECT/1.0"

# --- 用例 2：6 条 canary + 计数错一个 ---
half = {
    "canaries": {k: v for i, (k, v) in enumerate(truth["canaries"].items()) if i < 6},
    "count_0x0084F2BA": 99,
    "count_eof_marker": truth["count_eof_marker"],
    "tail_marker": truth["tail_marker_expected"],
}
r2 = sc.score_one("60k", "TEST-half", json.dumps(half), truth)
print("[2] 半数 canary →", r2["verdict"], "score", r2["score"],
      "| canary", r2["canary_hit"], "| count", r2["count_hit"])
assert r2["canary_hit"] == 6 and r2["count_hit"] == 1

# --- 用例 3：空回复 ---
r3 = sc.score_one("60k", "TEST-empty", "", truth)
print("[3] 空回复 →", r3["verdict"], "score", r3["score"], "| delivered", r3["delivered"])
assert r3["verdict"] == "NO_JSON" and r3["delivered"] is False

# --- 用例 4：自然语言里夹 JSON（带围栏）---
wrapped = "我读完了文件，结果如下：\n\n```json\n" + json.dumps(perfect) + "\n```\n\n以上。"
r4 = sc.score_one("60k", "TEST-fenced", wrapped, truth)
print("[4] 围栏 JSON →", r4["verdict"], "score", r4["score"])
assert r4["verdict"] == "PERFECT"

# --- 用例 5：编造 canary（值错）---
fake = dict(perfect)
fake["canaries"] = {k: "FAKE-" + k for k in truth["canaries"]}
r5 = sc.score_one("60k", "TEST-fake", json.dumps(fake), truth)
print("[5] 全部编造 →", r5["verdict"], "score", r5["score"], "| canary", r5["canary_hit"])
assert r5["canary_hit"] == 0 and r5["verdict"] == "POOR"

print("\n=== 评分器自测 5/5 通过 ===")
