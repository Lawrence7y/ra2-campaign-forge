# -*- coding: utf-8 -*-
"""
_check_metrics.py - 独立核验者（执行者 != 核验者）

不 import、不复用 _dtrigger_metrics.py 的任何函数/常量。用另一种数据组织方式
（逐窗预计算帧沿 edges[] 与 gaps[]，按游程索引 b 遍历）独立重算全部 26 档可执行文件判据的
triggers / falseTriggers / falseTriggerRate / realHits / missedReal /
latencyP50Ms / latencyP95Ms / latencyMaxMs / within50msRate，
逐字段与 CRITERIA_METRICS.json 比对；并核对写域封闭、JSON 键集合、只读文件指纹、
输出字节数与 SHA256。

运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_check_metrics.py
"""

import hashlib
import json
import re
import statistics
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANI = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EV = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
WD = (ROOT / "lead/dtrigger_compare_20261107").resolve()
MJ = WD / "CRITERIA_METRICS.json"
OUTS = ["_dtrigger_metrics.py", "_dtrigger_metrics_stdout.txt",
        "_dtrigger_metrics_out.txt", "CRITERIA_METRICS.json", "_check_metrics.py"]

ok = True
def check(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ((" | " + detail) if detail else ""))

print("=" * 100)
print("独立核验 _check_metrics.py（不复用执行者任何函数；逐窗帧沿/间隔预计算实现）")
print("=" * 100)

# --- 1. 写域与只读约束 ---
print("\n§1 写域封闭 / 指纹")
for n in OUTS:
    p = WD / n
    print(f"  {n}: bytes={p.stat().st_size if p.exists() else 'MISSING'} "
          f"sha256={hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'MISSING'}")
check("5 个本次文件均存在且非空", all((WD / n).exists() and (WD / n).stat().st_size > 0 for n in OUTS))
for rel in ["lead/stall_event_def_20261106/STALL_EVENTS.json",
            "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt",
            "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md"]:
    p = (ROOT / rel).resolve()
    print(f"  只读 {rel}: sha256={hashlib.sha256(p.read_bytes()).hexdigest()}")
check("只读治理文件均在仓库根内", all((ROOT / r).resolve().is_relative_to(ROOT) for r in
      ["lead/stall_event_def_20261106/STALL_EVENTS.json", "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt"]))
# 静态核对：只查「实际执行语句」（import / 函数调用 / 属性访问），
# 不查出现在 docstring、注释、或本核验者自身禁令词字面量列表里的字符串。
import ast
for n in ("_dtrigger_metrics.py", "_check_metrics.py"):
    tree = ast.parse((WD / n).read_text(encoding="utf-8"))
    bad = []
    banned_modules = {"ctypes", "subprocess", "os", "win32api", "win32process", "ctypes.windll"}
    banned_calls = {"OpenProcess", "ReadProcessMemory", "WriteProcessMemory",
                    "VirtualAllocEx", "CreateRemoteThread", "SetWindowsHookEx",
                    "TerminateProcess", "SuspendThread", "MiniDump", "StackWalk",
                    "system", "popen", "taskkill"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in banned_modules:
                    bad.append("import " + a.name)
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in banned_modules:
                bad.append("from " + str(node.module))
        elif isinstance(node, ast.Call):
            f = node.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if nm in banned_calls:
                bad.append("call " + nm)
    check(f"{n} AST 无禁令 import/调用", not bad, str(bad))

# --- 2. 独立重算语料（帧沿实现，与执行者的逐点 hlen[] 不同） ---
print("\n§2 独立重算语料（帧沿 edges/gaps 实现）")
corpus = {}
for fp in sorted(BASE.rglob("measure_w*.json")):
    f = fp.resolve()
    if not f.is_relative_to(BASE):
        raise ValueError("escape")
    q = f.relative_to(BASE).parts
    corpus[(q[0] if len(q) > 1 else "(root)", f.stem[len("measure_"):])] = json.loads(f.read_text(encoding="utf-8-sig"))
nsamp = sum(len(v["samples"]["t"]) for v in corpus.values())
print(f"  files={len(corpus)} samples={nsamp}")
check("files=104 且 samples=1125992", len(corpus) == 104 and nsamp == 1125992)

ks = set()
for ln in MANI.read_text(encoding="utf-8-sig").splitlines():
    mm = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if mm and (mm[1], mm[2]) in corpus:
        z = corpus[(mm[1], mm[2])]["samples"]
        if len(z["t"]) >= 2 and any(a != b for a, b in zip(z["f"], z["f"][1:])):
            ks.add((mm[1], mm[2]))
ks = sorted(ks)
print(f"  moving64 windows={len(ks)}")
check("moving64 窗数=64", len(ks) == 64)

ev = json.loads(EV.read_text(encoding="utf-8-sig"))
rk = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in ev if e.get("isRealMatch") is True}
check("STALL_EVENTS 全量=1737 且 real=1681", len(ev) == 1737 and len(rk) == 1681)

# R[b] = dict(key,i,j,npts,dfin,gaps_before(=hist[:b-1]),og,T)
# 帧沿：edges[0]=0；edges[b] 为第 b 次帧号首次变化处。
# gaps[b] = t[edges[b]]-t[edges[b-1]]（b>=1）；游程 b 的可用历史 = gaps[1:b]（共 b-1 条）。
RUNS = []
for trip, win in ks:
    z = corpus[(trip, win)]["samples"]
    T, F = z["t"], z["f"]
    m = len(F)
    edges = [0]
    for a in range(1, m):
        if F[a] != F[a - 1]:
            edges.append(a)
    gaps = []
    for b in range(1, len(edges)):
        gaps.append((T[edges[b]] - T[edges[b - 1]]) * 1000.0)
    for b in range(len(edges)):
        i = edges[b]
        j = edges[b + 1] - 1 if b + 1 < len(edges) else m - 1
        RUNS.append({
            "key": (trip, win, i, j), "i": i, "j": j, "npts": j - i + 1,
            "dfin": (T[j] - T[i]) * 1000.0,
            "hist": gaps[:max(0, b - 1)],       # 与执行者 he=hist_len_at[i-1]=b-1 等价
            "og": (T[i] - T[i - 1]) * 1000.0 if i > 0 else None,
            "T": T,
        })
print(f"  runs={len(RUNS)}  real-key alignment={sum(1 for r in RUNS if r['key'] in rk)}")
check("runs=28381 且 1681 real key 逐条精确对齐", len(RUNS) == 28381 and
      sum(1 for r in RUNS if r["key"] in rk) == 1681)

def pc(sorted_a, p):
    return sorted_a[int(p * (len(sorted_a) - 1))] if sorted_a else None

def r6(v):
    return round(v, 6)

# --- 判据：独立实现，函数签名与执行者不同 ---
def g_k(r, k):
    return r["i"] + k - 1 if r["npts"] >= k else None

def g_rel(r, q, mult, N, cap=None):
    h = r["hist"][-N:] if len(r["hist"]) >= N else None
    if h is None:
        return None
    th = pc(sorted(h), q) * mult
    if cap is not None:
        th = min(th, cap)
    T = r["T"]
    for x in range(r["i"], r["j"] + 1):
        if (T[x] - T[r["i"]]) * 1000.0 > th:
            return x
    return None

def g_rel_abs(r):
    h = r["hist"][-64:] if len(r["hist"]) >= 64 else None
    if h is None or r["og"] is None:
        return None
    th = pc(sorted(h), .95) * 2
    T = r["T"]
    for x in range(r["i"], r["j"] + 1):
        if (T[x] - T[r["i"]]) * 1000.0 + r["og"] > th:
            return x
    return None

def g_rate(r, mult, N, use_og):
    h = r["hist"][-N:] if len(r["hist"]) >= N else None
    if h is None or (use_og and r["og"] is None):
        return None
    b = statistics.median(h)
    if b <= 0:
        return None
    off = r["og"] if use_og else 0.0
    T = r["T"]
    for x in range(r["i"], r["j"] + 1):
        if (T[x] - T[r["i"]]) * 1000.0 + off > mult * b:
            return x
    return None

def g_abs(r, th):
    if r["npts"] < 3:
        return None
    T = r["T"]
    for x in range(r["i"] + 2, r["j"] + 1):
        if (T[x] - T[r["i"]]) * 1000.0 > th:
            return x
    return None

def g_hybrid(r):
    if r["npts"] < 10:
        return None
    T = r["T"]
    for x in range(r["i"] + 9, r["j"] + 1):
        if (T[x] - T[r["i"]]) * 1000.0 > 30.0:
            return x
    return None

CASES = []
for k in (10, 25, 50):
    CASES.append((f"C1-k{k}", lambda r, k=k: g_k(r, k)))
for qn, q in (("P95", .95), ("P99", .99)):
    for m in (2, 3):
        CASES.append((f"C2-{qn}x{m}", lambda r, q=q, m=m: g_rel(r, q, m, 64)))
CASES += [
    ("C2-abs-P95x2", g_rel_abs),
    ("C2-N16-P95x2", lambda r: g_rel(r, .95, 2, 16)),
    ("C2-cap40-P95x2", lambda r: g_rel(r, .95, 2, 64, 40.0)),
    ("C2-N16-P95x2-cap40", lambda r: g_rel(r, .95, 2, 16, 40.0)),
    ("C3-r1.5", lambda r: g_rate(r, 1.5, 64, False)),
    ("C3-r2", lambda r: g_rate(r, 2, 64, False)),
    ("C3-r4", lambda r: g_rate(r, 4, 64, True)),
    ("C3-r4-clean", lambda r: g_rate(r, 4, 64, False)),
    ("C3-r8", lambda r: g_rate(r, 8, 64, True)),
    ("C3-r8-clean", lambda r: g_rate(r, 8, 64, False)),
    ("C3-r12", lambda r: g_rate(r, 12, 64, True)),
    ("C3-N16-r1.5", lambda r: g_rate(r, 1.5, 16, False)),
    ("C3-N16-r2", lambda r: g_rate(r, 2, 16, False)),
]
for t in (16, 24, 30, 40, 48):
    CASES.append((f"C4-t{t}", lambda r, t=t: g_abs(r, t)))
CASES.append(("C5-k10t30", g_hybrid))

M = json.loads(MJ.read_text(encoding="utf-8"))
print("\n§3 逐档逐字段重算比对（26 档可执行判据）")
for cid, fn in CASES:
    trig = fals = w50 = 0
    hits = set()
    lat = []
    for r in RUNS:
        x = fn(r)
        if x is None:
            continue
        trig += 1
        if r["dfin"] < 100.0:
            fals += 1
        if r["key"] in rk:
            hits.add(r["key"])
            L = (r["T"][x] - r["T"][r["i"]]) * 1000.0
            lat.append(L)
            if L <= 50.0:
                w50 += 1
    lat.sort()
    exp = {
        "triggers": trig, "falseTriggers": fals,
        "falseTriggerRate": r6(fals / trig) if trig else 0.0,
        "realHits": len(hits), "missedReal": len(rk) - len(hits),
        "latencyP50Ms": r6(statistics.median(lat)) if lat else 0.0,
        "latencyP95Ms": r6(pc(lat, .95)) if lat else 0.0,
        "latencyMaxMs": r6(lat[-1]) if lat else 0.0,
        "within50msRate": r6(w50 / len(rk)),
    }
    got = M.get(cid, {})
    diff = {k: (got.get(k), v) for k, v in exp.items() if got.get(k) != v}
    check(f"{cid}: trig={trig} false={fals} hits={len(hits)} latP50={exp['latencyP50Ms']:.3f} "
          f"within50={exp['within50msRate']:.6f}", not diff, str(diff) if diff else "9 字段全等")

# --- 4. JSON 键与不可实现项 ---
print("\n§4 JSON 结构与不可实现项")
ALL_IDS = {c for c, _ in CASES} | {"R1-PostHoc100", "U1-PhysicalS-Anchored",
           "U2-CrossWindow-History", "U3-InternalStateFlag", "U4-EndToEndSave"}
check("JSON 键集合恰为 31 个判据 id", set(M.keys()) == ALL_IDS,
      f"got={len(M.keys())} expected={len(ALL_IDS)}")
for cid in ("R1-PostHoc100", "U1-PhysicalS-Anchored", "U2-CrossWindow-History",
            "U3-InternalStateFlag", "U4-EndToEndSave"):
    check(f"{cid} 标记 notImplementable=true 且全零", M[cid].get("notImplementable") is True and
          M[cid]["triggers"] == 0 and M[cid]["latencyP50Ms"] == 0.0)
for cid, _ in CASES:
    check(f"{cid} 无不可实现标记且 JSON 可解析", M[cid].get("notImplementable") is False)

# --- 5. stdout 与落盘一致性 ---
print("\n§5 输出落盘一致性")
a = (WD / "_dtrigger_metrics_stdout.txt").read_bytes()
b = (WD / "_dtrigger_metrics_out.txt").read_bytes()
# 执行者在写 out.txt 之后又向 stdout 追加两行「输出已写」+ 结束声明，
# 故 out.txt 是 stdout 的严格前缀；核验两者共享主体且只差这两行。
tail = a[len(b):].decode("utf-8")
check("out.txt 是 stdout 的严格前缀且尾部仅含两行落盘说明+一行结束声明",
      a.startswith(b) and len(tail.strip().splitlines()) == 3 and
      tail.count("输出已写") == 2 and "执行者结束" in tail,
      f"len(stdout)={len(a)} len(out)={len(b)} tailLines={len(tail.strip().splitlines())}")
check("out.txt 含 1681/1681 对齐行", "精确对齐 n=1681/1681" in a.decode("utf-8"))
check("out.txt 含 exit 尾部说明", "零真机 / 零采样代码" in a.decode("utf-8"))

print("\n" + "=" * 100)
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
print("=" * 100)
raise SystemExit(0 if ok else 1)
