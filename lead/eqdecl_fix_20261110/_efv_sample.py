# _efv_sample.py — 复核员自己的精确率抽样：从修版件全量 findings（我自己的实跑产物）
# 里分层比例抽样 33 条（Hamilton 配额，每文件至少 1），种子固定，输出带 ±3 行上下文供人工判。
import io
import json
import random
from collections import defaultdict

BASE = r"D:/Project/ra2-campaign-forge"
b = json.load(io.open(BASE + r"/lead/eqdecl_fix_20261110/_efv_full_fixed.json", encoding="utf-8"))
findings = b["findings_full"]
N = len(findings)
print("total findings:", N)

by_file = defaultdict(list)
for i, f in enumerate(findings):
    by_file[f["file"]].append(i)

TARGET = 33
files = sorted(by_file, key=lambda k: -len(by_file[k]))
quota = {k: 1 for k in files}
rest = TARGET - len(files)
# Hamilton：按占比分余数
import math
exact = {k: len(by_file[k]) / N * rest for k in files}
flo = {k: int(math.floor(v)) for k, v in exact.items()}
left = rest - sum(flo.values())
order = sorted(files, key=lambda k: exact[k] - flo[k], reverse=True)
for k in order[:left]:
    flo[k] += 1
for k in files:
    quota[k] += flo[k]
assert sum(quota.values()) == TARGET, quota

rng = random.Random(20261110)
picked = []
for k in files:
    picked += rng.sample(by_file[k], quota[k])
picked.sort()

def read_ctx(rel, line, rad=3):
    with io.open(BASE + "/" + rel, encoding="utf-8") as f:
        lines = f.read().split("\n")
    lo, hi = max(1, line - rad), min(len(lines), line + rad)
    return [f"{rel}:{n}| {lines[n-1]}" for n in range(lo, hi + 1)]

out = []
for i in picked:
    f = findings[i]
    out.append({
        "idx": i, "file": f["file"], "line": f["line"], "ftype": f["failure_type"],
        "text": f["text"], "context": read_ctx(f["file"], f["line"]),
    })
dest = BASE + r"/lead/eqdecl_fix_20261110/_efv_sample33.json"
with io.open(dest, "w", encoding="utf-8") as w:
    json.dump({"seed": 20261110, "target": TARGET, "quotas": quota, "sample": out},
              w, ensure_ascii=False, indent=1)
print("quotas:", json.dumps(quota, ensure_ascii=False))
print("written:", dest)
for x in out:
    print(f"--- #{x['idx']} {x['file']}:{x['line']} [{x['ftype']}]")
    print("   ", x["text"][:200])
