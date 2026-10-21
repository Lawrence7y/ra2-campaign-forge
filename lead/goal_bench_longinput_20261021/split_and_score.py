"""把 RAW_RESULTS_60k.md 拆成逐模型文件，然后离线评分。"""
import json
import re
import sys
from pathlib import Path

OUT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\goal_bench_longinput_20261021")
ANS = OUT / "answers"
raw = (ANS / "RAW_RESULTS_60k.md").read_text(encoding="utf-8")

# 按 "### <name>  (model=<id>)" 切块
blocks = re.split(r"^### (\S+)\s+\(model=([^)]+)\)\s*$", raw, flags=re.M)
# blocks[0] 是标题前的内容；之后每 3 个一组：name, model, body
pairs = []
for i in range(1, len(blocks) - 2, 3):
    name, model, body = blocks[i], blocks[i + 1], blocks[i + 2]
    pairs.append((name.strip(), model.strip(), body))

print(f"parsed {len(pairs)} model blocks")
for name, model, body in pairs:
    (ANS / f"{name}_60k.txt").write_text(body, encoding="utf-8")
    print(f"  {name:26} model={model:44} body={len(body)} B")

# 调用评分器
sys.dont_write_bytecode = True
import importlib.util
spec = importlib.util.spec_from_file_location("sc", OUT / "score.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

truth = json.loads((OUT / "ground_truth_60k.json").read_text(encoding="utf-8"))
truth["tail_marker_expected"] = re.search(r"EOF-MARKER-[0-9A-F]{4}", truth["tail120"]).group(0)

print("\n=== 离线评分（对照 ground_truth_60k.json）===")
print(f"标准答案：canary={truth['canary_count']} 条, count_0x0084F2BA={truth['count_0x0084F2BA']}, "
      f"count_eof={truth['count_eof_marker']}, tail={truth['tail_marker_expected']}")
print()
results = []
for name, model, _ in pairs:
    raw_text = (ANS / f"{name}_60k.txt").read_text(encoding="utf-8")
    r = sc.score_one("60k", name, raw_text, truth)
    r["model"] = model
    results.append(r)
    det = r.get("canary_detail", {})
    wrong = [k for k, v in det.items() if not v["ok"]]
    print(f"{name:26} {r['verdict']:8} score={r['score']:<5} "
          f"canary={r.get('canary_hit','-')}/{r.get('canary_total','-')} "
          f"count={r.get('count_hit','-')}/2 tail={r.get('tail_ok','-')}"
          + (f"  wrong={wrong}" if wrong else ""))

(OUT / "score_60k.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nwrote {OUT / 'score_60k.json'}")
