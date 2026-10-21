"""v2 评分：拆 RAW_RESULTS_v2.md，按档位分别对照 truth，离线评分。"""
import importlib.util
import json
import re
import sys
from pathlib import Path

OUT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\goal_bench_longinput_20261021")
ANS = OUT / "answers"
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("sc", OUT / "score.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

raw = (ANS / "RAW_RESULTS_v2.md").read_text(encoding="utf-8")
blocks = re.split(r"^### (\d+k)/(\S+)\s+\(model=([^)]+)\)\s*$", raw, flags=re.M)

runs = []
for i in range(1, len(blocks) - 3, 4):
    tier, name, model, body = blocks[i], blocks[i + 1], blocks[i + 2], blocks[i + 3]
    runs.append((tier.strip(), name.strip(), model.strip(), body))

print(f"parsed {len(runs)} runs\n")

truths = {
    "60k": json.loads((OUT / "ground_truth_60k.json").read_text(encoding="utf-8")),
    "240k": json.loads((OUT / "ground_truth_240k.json").read_text(encoding="utf-8")),
}
for t in truths.values():
    if "tail_marker_expected" not in t:
        m = re.search(r"EOF-MARKER-[0-9A-F]{4}", t.get("tail120", ""))
        t["tail_marker_expected"] = m.group(0) if m else ""

for tier, t in truths.items():
    print(f"[truth {tier}] bytes={t['corpus_bytes']:,} canary={t['canary_count']} "
          f"cnt_addr={t['count_0x0084F2BA']} cnt_eof={t['count_eof_marker']} tail={t['tail_marker_expected']}")
print()

results = []
for tier, name, model, body in runs:
    t = truths.get(tier)
    if t is None:
        print(f"SKIP unknown tier {tier}")
        continue
    (ANS / f"{name}_{tier}.txt").write_text(body, encoding="utf-8")
    r = sc.score_one(tier, name, body, t)
    r["model"] = model
    results.append(r)

print(f"{'tier':6} {'name':26} {'verdict':9} {'score':>6} {'canary':>8} {'cnt':>5} {'tail':>6}  wrong")
for r in sorted(results, key=lambda x: (x["tier"], x["model"])):
    det = r.get("canary_detail", {})
    wrong = [k for k, v in det.items() if not v["ok"]]
    w = ",".join(wrong) if wrong else "-"
    print(f"{r['tier']:6} {r['model']:26} {r['verdict']:9} {r['score']:>6} "
          f"{str(r.get('canary_hit','-'))+'/'+str(r.get('canary_total','-')):>8} "
          f"{str(r.get('count_hit','-'))+'/2':>5} {str(r.get('tail_ok','-')):>6}  {w}")

(OUT / "score_v2.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

# 按档汇总
print("\n=== 按档汇总 ===")
for tier in ("60k", "240k"):
    rs = [r for r in results if r["tier"] == tier]
    if not rs:
        continue
    perfect = sum(1 for r in rs if r["verdict"] == "PERFECT")
    avg = sum(r["score"] for r in rs) / len(rs)
    print(f"{tier}: {len(rs)} 次运行，PERFECT {perfect} 次，平均分 {avg:.3f}")

print(f"\nwrote {OUT / 'score_v2.json'}")
