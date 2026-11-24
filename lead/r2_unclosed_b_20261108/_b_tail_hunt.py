# -*- coding: utf-8 -*-
"""崩点2 补证②：lead/ 全树 + 仓库根一级散件逐件实算 SHA256，
查找两个争议尾串（26f3fb61829756dfeecf / b6f95763794）是否出现在任一文件摘要中
（含 endswith 判定），以定位尾串真实归属/成因。只读；路径全常量 + 包含校验。"""
import hashlib, time
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
WD = LEAD / "r2_unclosed_b_20261108"
OUT = WD / "_b_tail_hunt_out.txt"
TAILS = ["26f3fb61829756dfeecf", "b6f95763794"]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

t0 = time.time()
n_hashed = 0
n_skipped = 0
hits = []
paths = [p for p in LEAD.rglob("*") if p.is_file()
         and ".git" not in p.parts and ".mimosa" not in p.parts
         and "__pycache__" not in p.parts]
paths += [p for p in ROOT.iterdir() if p.is_file()]
for p in paths:
    try:
        if p.stat().st_size > 200_000_000:
            n_skipped += 1
            continue
        d = sha256_file(p)
        n_hashed += 1
        for t in TAILS:
            pos = d.find(t)
            if pos >= 0:
                hits.append((str(p), d, p.stat().st_size, t, pos, d.endswith(t)))
    except (OSError, PermissionError):
        n_skipped += 1

lines = []
lines.append(f"hashed_files={n_hashed} skipped={n_skipped} elapsed={time.time()-t0:.1f}s")
lines.append("scope = lead/ 全树（剔除 .git/.mimosa/__pycache__，>200MB 跳过） + 仓库根一级散件")
for t in TAILS:
    th = [h for h in hits if h[3] == t]
    lines.append(f"tail {t}: 摘要含该尾的文件数 = {len(th)}")
    for h in th:
        lines.append(f"  HIT file={h[0]} sha256={h[1]} bytes={h[2]} pos={h[4]} 尾{len(h[3])}位(endswith)={h[5]}")
if not hits:
    lines.append("NO_DIGEST_HIT: 两尾串均未出现在范围内任何文件的 SHA256 摘要中")
txt = "\n".join(lines) + "\n"
assert OUT.is_relative_to(WD)
OUT.write_text(txt, encoding="utf-8")
print(txt)
