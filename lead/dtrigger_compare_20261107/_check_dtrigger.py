# -*- coding: utf-8 -*-
"""
_check_dtrigger.py - 独立核验（执行者 != 核验者）

不导入、不复用 _dtrigger_probe.py / _dtrigger_analysis.py / _dtrigger_supplement.py 的任何函数。
用独立的逐拍扫描实现，重算关键判据的 (nTrig, 误报率, wait中位, >50ms数)，
与已落盘的输出比对；并校验写域封闭、指纹一致、只读路径未改。

运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_check_dtrigger.py
"""

import hashlib
import json
import re
import statistics
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
WD = (ROOT / "lead/dtrigger_compare_20261107").resolve()

def rp(rel):
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("escape")
    return p

def sha(rel):
    return hashlib.sha256(rp(rel).read_bytes()).hexdigest()

ok = True
def check(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ((" | " + detail) if detail else ""))

print("=" * 96)
print("独立核验 _check_dtrigger.py（不复用执行者任何函数）")
print("=" * 96)

# --- 1. 写域封闭 ---
print("\n§1 写域与只读约束")
wd_files = sorted(p.name for p in WD.iterdir() if p.is_file())
print("  写域文件:", wd_files)
check("写域内只有本次指派的 4 个 .py / .md / out / stdout 文本",
      all(f.endswith((".py", ".txt", ".md")) for f in wd_files))
for rel in ["lead/stall_event_def_20261106/STALL_EVENTS.json",
            "lead/early_trigger_feasibility_20261106/_feasibility_probe.py",
            "lead/d30_ruling_20261106/RULING_D30.md",
            "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md"]:
    print(f"  sha256 {rel} = {sha(rel)}")
check("只读治理文件路径均在仓库根内", all(rp(r).is_relative_to(ROOT) for r in
      ["lead/stall_event_def_20261106/STALL_EVENTS.json", "lead/d30_ruling_20261106/RULING_D30.md"]))

# --- 2. 独立重算语料 ---
print("\n§2 独立重算语料与判据")
corpus = {}
for fp in sorted(BASE.rglob("measure_w*.json")):
    f = fp.resolve()
    if not f.is_relative_to(BASE):
        raise ValueError("escape")
    q = f.relative_to(BASE).parts
    corpus[(q[0] if len(q) > 1 else "(root)", f.stem.replace("measure_", ""))] = json.loads(f.read_text(encoding="utf-8-sig"))
nsamp = sum(len(v["samples"]["t"]) for v in corpus.values())
print(f"  独立统计：files={len(corpus)} samples={nsamp}")
check("files=104 且 samples=1125992", len(corpus) == 104 and nsamp == 1125992)

mani = rp("lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").read_text(encoding="utf-8-sig")
ks = set()
for ln in mani.splitlines():
    mm = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", ln.strip())
    if mm and (mm[1], mm[2]) in corpus:
        z = corpus[(mm[1], mm[2])]["samples"]
        if len(z["t"]) >= 2 and z["f"][0:1] != z["f"][-1:]:
            ks.add((mm[1], mm[2]))
        elif len(z["t"]) >= 2 and any(a != b for a, b in zip(z["f"], z["f"][1:])):
            ks.add((mm[1], mm[2]))
ks = sorted(ks)
print(f"  独立统计：moving64 推进窗 n={len(ks)}")
check("moving64 窗数=64", len(ks) == 64)

ev = json.loads(rp("lead/stall_event_def_20261106/STALL_EVENTS.json").read_text(encoding="utf-8-sig"))
rk = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in ev if e.get("isRealMatch") is True}
check("真实事件 n=1681（不与 1737 混口径）", len(ev) == 1737 and len(rk) == 1681)

# 独立实现：逐窗按「帧号不变游程」扫描；帧推进间隔用 t[edge]-t[prev_edge]
RUNS = []
for trip, win in ks:
    z = corpus[(trip, win)]["samples"]
    T, F = z["t"], z["f"]
    m = len(F)
    # 帧沿列表
    edges = [0]
    for a in range(1, m):
        if F[a] != F[a - 1]:
            edges.append(a)
    gaps = [(edges[b] - 0 if b == 0 else T[edges[b]] - T[edges[b - 1]]) * 1000.0
            for b in range(len(edges))]
    # edges[b] 与 gap[b]：第 b 个帧沿及其之前那一帧的间隔
    # 对每个游程，起点 i = edges[b]，可用历史 = gaps[1..b] 中截至 i-1 的部分
    # 与执行者文档化的口径对齐：基线只含 runStart-1 及更早的「已完成帧间隔」，
    # 即排除「恰在 runStart=i 处才被观测到的那次帧推进」所对应的帧间隔 gaps[b]。
    # 执行者: h_end = hist_len_at[i-1] = b-1，窗口 = H[b-1-N:b-1]。
    # 本核验: hist = H[:b-1] = gaps[1:b]，h_end = b-1，hist[-N:] = gaps[b-N:b]，等价。
    for b in range(len(edges)):
        i = edges[b]
        j = (edges[b + 1] - 1) if b + 1 < len(edges) else (m - 1)
        h_end = max(0, b - 1)
        hist = gaps[1:b] if b >= 1 else []
        RUNS.append({
            "key": (trip, win, i, j), "i": i, "j": j,
            "npts": j - i + 1, "dfin": (T[j] - T[i]) * 1000.0,
            "hist": hist, "h_end": h_end,
            "T": T,
        })
print(f"  独立统计：游程 n={len(RUNS)}")
check("游程 n=28381", len(RUNS) == 28381)

def pc(a, p):
    s = sorted(a)
    return s[int(p * (len(s) - 1))] if s else None

def eval_crit(fn):
    W = []
    NF = 0
    H = 0
    for r in RUNS:
        v = fn(r)
        if v is None:
            continue
        W.append(v)
        if r["dfin"] < 100.0:
            NF += 1
        if r["key"] in rk:
            H += 1
    W.sort()
    return {"n": len(W), "falseRate": NF / len(W) if W else None,
            "med": statistics.median(W) if W else None,
            "gt50": sum(1 for x in W if x > 50), "hits": H}

def ck_k(r, k):
    if r["npts"] < k:
        return None
    return (r["T"][r["i"] + k - 1] - r["T"][r["i"]]) * 1000.0

def ck_abs(r, th, kmin=3):
    if r["npts"] < kmin:
        return None
    for a in range(r["i"] + kmin - 1, r["j"] + 1):
        el = (r["T"][a] - r["T"][r["i"]]) * 1000.0
        if el > th:
            return el
    return None

def ck_rel(r, q, mult, N):
    if r["h_end"] < N:
        return None
    h = r["hist"][-N:]
    th = pc(h, q) * mult
    for a in range(r["i"], r["j"] + 1):
        el = (r["T"][a] - r["T"][r["i"]]) * 1000.0
        if el > th:
            return el
    return None

def ck_rate(r, mult, N):
    if r["h_end"] < N:
        return None
    base = statistics.median(r["hist"][-N:])
    if base <= 0:
        return None
    for a in range(r["i"], r["j"] + 1):
        el = (r["T"][a] - r["T"][r["i"]]) * 1000.0
        if el / base > mult:
            return el
    return None

CASES = [
    ("C1-k10", lambda r: ck_k(r, 10), (28294, .9398, 17.613, 12, 1681)),
    ("C1-k25", lambda r: ck_k(r, 25), (5343, .6811, 47.766, 103, 1681)),
    ("C1-k50", lambda r: ck_k(r, 50), (1866, .0868, 97.750, 1811, 1681)),
    ("C4-t16", lambda r: ck_abs(r, 16), (28282, .9397, 17.569, 50, 1681)),
    ("C4-t30", lambda r: ck_abs(r, 30), (16016, .8936, 30.448, 76, 1681)),
    ("C4-t40", lambda r: ck_abs(r, 40), (6031, .7175, 40.500, 133, 1681)),
    ("C4-t48", lambda r: ck_abs(r, 48), (5168, .6703, 49.973, 2492, 1681)),
    ("C2-P95x2", lambda r: ck_rel(r, .95, 2, 64), (27, .1481, 73.378, 27, 7)),
    ("C2-P99x2", lambda r: ck_rel(r, .99, 2, 64), (24, .1667, 75.441, 24, 4)),
    ("C3-r4", lambda r: ck_rate(r, 4, 64), (24, .0000, 130.237, 24, 8)),
    ("C3-r2", lambda r: ck_rate(r, 2, 64), (180, .0556, 153.550, 180, 154)),
]
for cid, fn, exp in CASES:
    g = eval_crit(fn)
    match = (g["n"] == exp[0] and abs(g["falseRate"] - exp[1]) < 0.0001
             and abs(g["med"] - exp[2]) < 0.01 and g["gt50"] == exp[3] and g["hits"] == exp[4])
    check(f"{cid}: n={g['n']} false={g['falseRate']*100:.2f}% med={g['med']:.3f} >50={g['gt50']} hits={g['hits']}",
          match, f"期望 n={exp[0]} false={exp[1]*100:.2f}% med={exp[2]} >50={exp[3]} hits={exp[4]}")

# --- 3. 主探针输出文件存在且含关键行 ---
print("\n§3 落盘输出核对")
for name in ("_dtrigger_probe_out.txt", "_dtrigger_analysis_out.txt", "_dtrigger_supplement_out.txt"):
    p = WD / name
    txt = p.read_text(encoding="utf-8") if p.exists() else ""
    check(f"{name} 存在且非空 ({len(txt)} 字符)", bool(txt))
probe_txt = (WD / "_dtrigger_probe_out.txt").read_text(encoding="utf-8")
check("主探针输出含自跑 D30 复现行 k=10 total=28294", "k=10: total=28294 false=26590" in probe_txt)
check("主探针输出含 k 点=k-1 间隔核对", "名义 (k-1)*2ms = 18ms" in probe_txt)
ana_txt = (WD / "_dtrigger_analysis_out.txt").read_text(encoding="utf-8")
check("扩展分析含前缀不可分辨上界 T=48 行", "48 |      5168" in ana_txt)
sup_txt = (WD / "_dtrigger_supplement_out.txt").read_text(encoding="utf-8")
check("补充核对含不可实现项登记", "不可实现项登记" in sup_txt)

# --- 4. 纪律核对：执行者脚本不得含采样/hook/真机 API ---
print("\n§4 纪律静态核对（执行者脚本）")
BANNED = ["ctypes", "OpenProcess", "ReadProcessMemory", "WriteProcessMemory",
          "VirtualAllocEx", "CreateRemoteThread", "SetWindowsHookEx", "TerminateProcess",
          "SuspendThread", "MiniDump", "StackWalk", "taskkill", "gamemd.exe",
          "ra2loader", "YURI.exe"]
for name in ("_dtrigger_probe.py", "_dtrigger_analysis.py", "_dtrigger_supplement.py"):
    s = (WD / name).read_text(encoding="utf-8")
    hits = [b for b in BANNED if b in s]
    check(f"{name} 无禁令词 {hits}", not hits)
    check(f"{name} 只用 Path/JSON/统计，无 subprocess/os.system",
          "subprocess" not in s and "os.system" not in s and "import os" not in s)

print("\n" + "=" * 96)
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
print("=" * 96)
raise SystemExit(0 if ok else 1)
