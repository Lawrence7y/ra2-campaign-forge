# -*- coding: utf-8 -*-
"""撤销 H42 重复追加（第 99–104 轮段已在 H38 归档中存在），并把 board 指针改成指向 H38。"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
MD = os.path.join(D,"R16_BASE","board_rebuild")
ARC = os.path.join(D,"BOARD_ARCHIVE.md")
def sha8(b): return hashlib.sha256(b).hexdigest().upper()[:16]

arc = open(ARC,"rb").read()
# 找到 H42 头的位置，截断到它之前（连同前面的 --- 分隔）
marker = "## 📦 H42 归档（2026-11-21，R16 Lead 执行·事故重建期）：看板第 99–104 轮段".encode("utf-8")
k = arc.find(marker)
assert k > 0, "未找到 H42 头"
# 往前退掉 "---\n\n"
head = arc[:k]
while head.endswith(b"\n"): head = head[:-1]
if head.endswith(b"---"): head = head[:-3]
while head.endswith(b"\n"): head = head[:-1]
head = head + b"\n"
open(ARC,"wb").write(head)
print("archive 撤销 H42:", len(arc), "→", len(head), "B  sha", sha8(head))

L = open(os.path.join(MD,"board_final.md"),"rb").read().decode("utf-8").split("\n")
i = next(i for i,l in enumerate(L) if "第 99–104 轮" in l and l.startswith("> 📦"))
L[i] = "> 📦 ## 🔴 第 99–104 轮（2026-11-20 20:4x）· 91 行 ④ 补写成文：13.78% → 19.29% 已归档至 BOARD_ARCHIVE.md（2026-11-20 21:44，逐字搬，missing=0；本次由 Lead 执行，卫生员 H38）"
out = ("\n".join(L)+"\n").encode("utf-8")
open(os.path.join(MD,"board_final.md"),"wb").write(out)
print("board 指针改指 H38:", len(out), "B  行数", len(L), " sha", sha8(out))
