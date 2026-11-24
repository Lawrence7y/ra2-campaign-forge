# -*- coding: utf-8 -*-
# _wlv_fence.py — 独立核 §2② 围栏块锚回：逐行 == 比对 + 区段标题 + 是否别处实验
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
d = ROOT / "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md"
p = ROOT / "lead/matrix_reach_20261109/_mr_probe1_out.txt"
dl = d.read_text(encoding="utf-8").split("\n")
pl = p.read_text(encoding="utf-8").split("\n")
def L(lines, n):
    return lines[n-1] if 1 <= n <= len(lines) else "<OOR>"
pairs = [(69,159),(70,169),(71,173)]
print("=== 交付件 :69/:70/:71 与 _mr_probe1_out.txt :159/:169/:173 逐行 == ===")
for a,b in pairs:
    da, pb = L(dl,a), L(pl,b)
    print(f"delivery:{a} == probe:{b} ? {da == pb}")
    print(f"   delivery={da!r}")
    print(f"   probe   ={pb!r}")
print("\n=== _mr_probe1_out.txt:156-159 区段标题 ===")
for n in range(156,160):
    print(f"  :{n} {L(pl,n)!r}")
print("\n=== 围栏块 3 行是否落在 :157 的 P1 W1 实验区段内 ===")
# 找下一个 ===== 分隔标题
nxt = None
for n in range(160, 220):
    if L(pl,n).startswith("P2 ") or (L(pl,n).startswith("=") and n>160 and "P2" in L(pl,n+1)):
        nxt = n; break
print("  下一个实验标题行（P2）附近：")
for n in range(175,190):
    s=L(pl,n)
    if s and not set(s)<=set("= "):
        print(f"    :{n} {s!r}")
print("\n=== 交付件 :65 事件行 / :68 出处行 / :74 落哪一行 ===")
for n in (65,68,74):
    print(f"  delivery:{n} {L(dl,n)!r}")
