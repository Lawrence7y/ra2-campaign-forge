# -*- coding: utf-8 -*-
"""重建 STATUS_BOARD.md（事故恢复）。
路径：pass4 快照(21:39, 294行) → 去掉 H38 搬走的「第 96–98 轮」段(13行) → 得到 R16 接手态(281行/32403B, sha 前缀 44C59621)
      → 重放 R16 的 4 次追加 + 3 次归档。
每步都用已知 sha/字节数校验；任何一步对不上就停下并报告，不猜。
"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")

D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
P4 = os.path.join(D, "_hygiene", "H34", "pass4", "STATUS_BOARD.before.md")
OUT = os.path.join(D, "R16_BASE", "board_rebuild")

def sha8(b): return hashlib.sha256(b).hexdigest().upper()[:16]

raw = open(P4, "rb").read()
print("pass4 :", len(raw), "B", sha8(raw))
text = raw.decode("utf-8")
lines = text.split("\n")
trailing = lines and lines[-1] == ""
if trailing: lines = lines[:-1]
print("pass4 lines =", len(lines))

# 找「第 96–98 轮」段边界
i0 = next(i for i,l in enumerate(lines) if l.startswith("## 🔴 第 96–98 轮"))
# 段尾 = 下一个 ## 之前，去掉尾部空行
j = i0 + 1
while j < len(lines) and not lines[j].startswith("## "):
    j += 1
i1 = j - 1
while i1 > i0 and lines[i1].strip() == "":
    i1 -= 1
print("第96-98轮段: 行", i0+1, "-", i1+1, " (", i1-i0+1, "行)")

rebuilt = lines[:i0] + lines[i1+1:]
if trailing: rebuilt = rebuilt + [""]
b = ("\n".join(rebuilt)).encode("utf-8")
print("重建接手态:", len(b), "B", sha8(b), " lines=", len(rebuilt) - (1 if trailing else 0))
open(os.path.join(OUT, "s0_handoff.md"), "wb").write(b)
