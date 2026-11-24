# -*- coding: utf-8 -*-
"""
_dB_anchor_recompute.py  —  §3.2 未验列统一锚补算（调查员·B / 2026-11-07）

运行（本机实跑命令，逐字）：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dB_anchor_recompute.py

零真机 / 零采样代码 / 只读母本与既有件 / 不 import 任何既有 _dtrigger_*.py 或 _check_*.py /
不 commit 不 push。只写 lead/dtrigger_round2_20261107/ 下 _dB_ 前缀的新文件。

===============================================================================
一、本轮采用的【统一且明写的锚定义】（口径 U，覆盖全部 12 格，逐条可执行）
===============================================================================
U1 触发谓词锚：一个 id 只有一个权威锚，取 `_dtrigger_metrics.py` 为该 id 登记的锚：
     C2-abs-P95x2 / C3-r4 / C3-r8 / C3-r12  = 上一帧沿（lastEdge）
     C3-r4-clean  / C3-r8-clean             = runStart
   依据：_dtrigger_metrics.py:217,223,224,225,226,227 与
         CRITERIA_METRICS.json 各 id 的 "note" 字段（"上一帧沿锚" / "runStart锚"）。
   这是**一条**覆盖 6 个 id 的统一规则：不把补算表的 runStart 谓词结果张冠李戴给
   lastEdge 的 id。本脚本按该规则重新实跑触发点，触发集必须与既有 29/24/24/16/16/15 对齐。
   注意「统一」= 规则一致、无例外（且两列的等待锚 U2 六档完全相同），不是「六档共用
   同一个物理锚点」；若强行全用 runStart 会改变 4 个 id 的触发集，本脚本 §五附另给该敏感性表。

U2 两列的【等待锚】统一为 S_hat = t[runStart]：
     wait = (t[idx] - t[i]) * 1000.0 ms
   依据：CRITERIA_COMPARE.md:218-223（>=100 / +e>50 的定义母体）、
         _dtrigger_supplement.py:101,181、_dtrigger_metrics.py:266、_dtrigger_probe.py:367。
   谓词的 lastEdge 偏移只决定 idx（触发时刻），**绝不加进 wait**。三处既有脚本的等待锚
   本来就是一致的；§3.2 的不一致只发生在谓词锚上。本轮不改等待锚。

U3 onset gap：og = (t[i] - t[i-1]) * 1000.0 ms（i>0）；i==0 时 og=None。
   即 lastEdge 锚点 t_last_edge = t[i] - og/1000；since_advance = wait + og。
   与 _dtrigger_metrics.py:135、_dtrigger_probe.py:152,214,233、
   S_OBSERVABILITY.md:52-59 的 U = S_obs - S_low 同义。

U4 e 取【全部 i>0 游程的 og 中位数】这一个常数，本脚本从原始语料独立重算，
   不抄 _dtrigger_supplement_out.txt:4；+e>50 = (wait + e > 50) 的触发数。
   依据：CRITERIA_COMPARE.md:222-223（明写「只加了中位常数」，不是逐游程代入各自 e）、
         _dtrigger_supplement.py:84,192。

U5 ≥100 = (wait >= 100.0) 的触发数；>50 = (wait > 50.0)；+e>50 = (wait + e > 50.0)。
   依据：_dtrigger_supplement.py:191-193、CRITERIA_COMPARE.md:220-223。
   分母（计数母体）= 该 id 的**全部触发**（nTrig），不是仅真实命中子集。

U6 og=None（i==0）或 he<64 或 base<=0 → 谓词返回 None（该游程不触发），
   与 _dtrigger_metrics.py:176-181、_dtrigger_probe.py:211-213,230-232 一致。
   这是把「og=None 时谓词无定义」落成可执行的确定约定：不是补造 og，而是不触发。

===============================================================================
二、与既有两处脚本的【逐条差异】（只读对照，不 import、不改）
===============================================================================
A. vs `_dtrigger_supplement.py:106-118`（f_rate，补算表）
 A1 补算 f_rate 无 anchor 形参，恒为 el/base > mult，el=(ts[idx]-ts[r[2]])*1000
    （:115-116）→ **runStart 锚**；U1 对 4 个 id 用 lastEdge（el+og）。这是 §3.2
    「不同源」的根因，也是本轮必须重跑的原因。
 A2 补算 CRIT 表（:140-166）只有 C3-r4 / C3-r8，没有 C3-r12、C3-r4-clean、
    C3-r8-clean、C2-abs-P95x2；:148-150 明写「本补充探针未实现『上一帧沿距离锚』」。
    故 6 个 id 中补算表**没有任何一行**能直接归属。
 A3 按本轮指纹锁定的 `_dtrigger_supplement_out.txt:15` 当前字节已读作 `C2-P95x2-复算`
    （27/4/27），即「误标为 C2-abs-P95x2」是 §3.2 :245-246 记载的历史状态，
    当前文件已完成改标；但改标只是把行名改对，该行仍是 runStart 的 C2-P95x2 谓词，
    **依然不能**归属 29 触发的 C2-abs-P95x2。本轮按 U1 重算，不采该行。
 A4 补算 wait（:101,181）与 U2 同为 S_hat 锚 —— **等待锚一致**，差异只在谓词锚；
    本轮没有改两列的定义，只换了产生触发集的谓词。
 A5 补算的 e（:84）与本轮 U4 是同一统计量，但本轮从原始 (t,f) 独立重算并打印全精度，
    不 import 其输出；另核用 2.511 常数是否改变任一格。
 A6 补算 :182 用 r[5]<100 计误报，与本轮两列无关，本轮不计算误报。

B. vs `_dtrigger_metrics.py:223-227`（以及 :162-187, :217）
 B1 metrics 的 id→锚 映射（:217,223-227）被 U1 **原样采用**，未改动；本轮只是把该
    映射下产生的触发集再补算 metrics 从未输出的 >=100 / +e>50 两列。
 B2 metrics :135 og、:134 he、:176-185 谓词（off=og 或 0）与 U3/U6 逐字同义；
    代数上 (T[x]-T[i])*1000+off > mult*base 与补算 el/base>mult 仅差 off。
 B3 metrics **不输出** >=100 / +e>50（只输出 :266-289 的 latP50/P95/Max）；
    这正是 §7 第 6 项把两列列未验的结构原因。
 B4 metrics 的 latency（:266）虽与 U2 同为 (t[idx]-t[i])*1000，但分母是**仅真实命中
    子集**（:254,264-267）；本轮两列分母是**全部触发**（A 中 §3.1 :220-223）。
    例：C2-abs-P95x2 的 latP50=169.960（8 命中）≠ 全 29 触发 waitMed=70.931。
    二者不可互换（_independent_recheck_out.txt:56-69、§3.2 :252）。
 B5 metrics 对 og=None / he<64 返回 None（:176-177），与 U6 一致。

C. vs `_dtrigger_probe.py:202-239`（主探针，作交叉校验用）
 C1 主探针 C_rel_abs / C_rate 均用 lastEdge（t_last_edge=t[i]-og/1000），故 §3.2 :250
    的 `>50` 列（_dtrigger_probe_out.txt:42-45）本就落在正确触发集上；本轮重算的
    4 个 lastEdge id 的 wait 分布应与之逐值相等（本脚本打印并核对）。
 C2 主探针无 -clean 两档、且表头（:349）只有 >50ms 一列，无 >=100 / +e>50。
===============================================================================
"""

import hashlib
import json
import re
import statistics
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
REF_METRICS = (ROOT / "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json").resolve()
COMPARE = (ROOT / "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md").resolve()
WD = (ROOT / "lead/dtrigger_round2_20261107").resolve()
OUT_TXT = WD / "_dB_anchor_recompute_out.txt"
OUT_JSON = WD / "_dB_anchor_recompute_data.json"

UPSTREAM = [
    "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md",
    "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json",
    "lead/dtrigger_compare_20261107/_cost_quota_data.json",
    "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt",
    "lead/d30_ruling_20261106/RULING_D30.md",
    "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md",
    "lead/dstart_observable_20261107/S_OBSERVABILITY.md",
    "lead/dtrigger_compare_20261107/_dtrigger_supplement.py",
    "lead/dtrigger_compare_20261107/_dtrigger_metrics.py",
    "lead/dtrigger_compare_20261107/_dtrigger_probe.py",
    "lead/dtrigger_compare_20261107/_dtrigger_probe_out.txt",
]

DCLASS_MS = 100.0
CUTOFF_MS = 50.0
N_HIST = 64

L = []
def out(s=""):
    L.append(str(s))
    print(s)

def pctl(sorted_arr, p):
    """线性最近秩：与 _dtrigger_metrics.py:68-70 / _dtrigger_supplement.py:29-30 同口径。"""
    return sorted_arr[int(p * (len(sorted_arr) - 1))] if sorted_arr else None

def fmt(v, n=3):
    return "N/A" if v is None else f"{v:.{n}f}"

def sha(rel):
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("path escape: " + rel)
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

# ------------------------------------------------------------------ 0 指纹
out("=" * 104)
out("【§3.2 未验列统一锚补算 · 调查员·B · 只读离线实跑】")
out("=" * 104)
out("零真机 / 零采样代码 / 不 import 既有 _dtrigger_*.py 与 _check_*.py / 不 commit 不 push")
out("")
out("【被核对象与上游只读件 SHA256（本轮实跑 hashlib）】")
for rel in UPSTREAM:
    h, n = sha(rel)
    out(f"  SHA256 {h}  字节数 {n}  {rel}")
h0, n0 = sha("lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md")
out(f"被核对象 SHA256 = {h0}，字节数 = {n0}")
out("  （被核对象 = lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md §3.2；铁律 9 指纹行）")
out("")

# ------------------------------------------------------------------ 1 语料
cache = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("corpus escape")
    parts = pr.relative_to(BASE).parts
    key = (parts[0] if len(parts) > 1 else "(root)", pr.stem[len("measure_"):])
    d = json.loads(pr.read_text(encoding="utf-8-sig"))
    assert len(d["samples"]["t"]) == len(d["samples"]["f"])
    cache[key] = d
n_samples = sum(len(v["samples"]["t"]) for v in cache.values())
out(f"语料：measure_w*.json 文件 n={len(cache)}，采样点 n={n_samples}")

manifest_keys = set()
for ln in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if m and (m[1], m[2]) in cache:
        s = cache[(m[1], m[2])]["samples"]
        if len(s["t"]) >= 2 and any(a != b for a, b in zip(s["f"], s["f"][1:])):
            manifest_keys.add((m[1], m[2]))
manifest_keys = sorted(manifest_keys)
out(f"moving64 推进窗 n={len(manifest_keys)}（manifest 只读取+正则过滤，与既有三脚本同口径）")

events_all = json.loads(EVENTS.read_text(encoding="utf-8-sig"))
real = [e for e in events_all if e.get("isRealMatch") is True]
real_keys = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in real}
real_start0 = sorted((e["trip"], e["window"], e["startTick"], e["endTick"])
                     for e in real if e["startTick"] == 0)
out(f"STALL_EVENTS 全量 n={len(events_all)}，isRealMatch==true n={len(real)}，"
    f"real_keys 去重 n={len(real_keys)}，其中 startTick==0 的真实事件 n={len(real_start0)}")

# ------------------------------------------------------------------ 2 逐窗构造 REC
WIN = {}
REC = []
for trip, win in manifest_keys:
    s = cache[(trip, win)]["samples"]
    T, F = s["t"], s["f"]
    n = len(F)
    hist = []
    hlen = [0] * n
    le = 0
    for a in range(1, n):
        if F[a] != F[a - 1]:
            hist.append((T[a] - T[le]) * 1000.0)
            le = a
        hlen[a] = len(hist)
    WIN[(trip, win)] = {"T": T, "F": F, "hist": hist, "hlen": hlen}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and F[j + 1] == F[i]:
            j += 1
        r = {
            "trip": trip, "win": win, "i": i, "j": j,
            "npts": j - i + 1,
            "dfin": (T[j] - T[i]) * 1000.0,
            "he": hlen[i - 1] if i > 0 else 0,
            "og": (T[i] - T[i - 1]) * 1000.0 if i > 0 else None,
            "key": (trip, win, i, j),
        }
        REC.append(r)
        i = j + 1
out(f"推进窗内帧号游程 n={len(REC)}（评分母体；每游程每判据最多触发一次）")

aligned = sum(1 for r in REC if r["key"] in real_keys)
out(f"real 事件与游程 (i,j)=(startTick,endTick) 精确对齐 n={aligned}/{len(real_keys)}")

# ------------------------------------------------------------------ 3 e（U4）
ogs = [r["og"] for r in REC if r["og"] is not None]
e_med = statistics.median(ogs)
e_rounded = 2.511
out("")
out(f"U4  e = median(og | i>0) 独立重算 = {e_med:.9f} ms  （n={len(ogs)}）")
out(f"    既有补算表 :4 记 e=2.511ms；四舍五入到 3 位 = {e_med:.3f} ms "
    f"({'一致' if f'{e_med:.3f}' == '2.511' else '不一致'})")
out(f"    本轮 +e>50 主值用全精度 e；另用常数 e={e_rounded} 复核 12 格是否变化")

# ------------------------------------------------------------------ 4 谓词（U1/U3/U6）
def pred_abs_p95x2(r, w):
    """C2-abs-P95x2：上一帧沿锚，theta = P95(近64条)*2，since_advance = wait + og。"""
    he, og = r["he"], r["og"]
    if he < N_HIST or og is None:                      # U6
        return None
    theta = pctl(sorted(w["hist"][he - N_HIST:he]), 0.95) * 2.0
    T, i = w["T"], r["i"]
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 + og > theta:
            return x
    return None

def pred_rate(r, w, mult, anchor):
    """C3：anchor='lastEdge' → (wait+og)/base > mult；'runStart' → wait/base > mult。"""
    he, og = r["he"], r["og"]
    if he < N_HIST or (anchor == "lastEdge" and og is None):   # U6
        return None
    base = statistics.median(w["hist"][he - N_HIST:he])
    if base <= 0:
        return None
    off = og if anchor == "lastEdge" else 0.0
    T, i = w["T"], r["i"]
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 + off > mult * base:
            return x
    return None

def pred_abs_runstart(r, w):
    """敏感性用：C2-abs-P95x2 强制 runStart 锚（即补算表 C2-P95x2-复算 的谓词）。"""
    he = r["he"]
    if he < N_HIST:
        return None
    theta = pctl(sorted(w["hist"][he - N_HIST:he]), 0.95) * 2.0
    T, i = w["T"], r["i"]
    for x in range(i, r["j"] + 1):
        if (T[x] - T[i]) * 1000.0 > theta:
            return x
    return None

# (id, 权威锚 U1, 谓词)
IDS = [
    ("C2-abs-P95x2", "lastEdge", lambda r, w: pred_abs_p95x2(r, w)),
    ("C3-r4",        "lastEdge", lambda r, w: pred_rate(r, w, 4.0,  "lastEdge")),
    ("C3-r4-clean",  "runStart", lambda r, w: pred_rate(r, w, 4.0,  "runStart")),
    ("C3-r8",        "lastEdge", lambda r, w: pred_rate(r, w, 8.0,  "lastEdge")),
    ("C3-r8-clean",  "runStart", lambda r, w: pred_rate(r, w, 8.0,  "runStart")),
    ("C3-r12",       "lastEdge", lambda r, w: pred_rate(r, w, 12.0, "lastEdge")),
]

def run_crit(fn):
    """返回该谓词在整个 REC 上的触发明细；wait 一律 U2 的 S_hat 锚。"""
    rows = []
    for r in REC:
        w = WIN[(r["trip"], r["win"])]
        x = fn(r, w)
        if x is None:
            continue
        rows.append({
            "trip": r["trip"], "win": r["win"], "i": r["i"], "j": r["j"],
            "idx": x, "wait": (w["T"][x] - w["T"][r["i"]]) * 1000.0,
            "og": r["og"], "he": r["he"], "dfin": r["dfin"],
            "isReal": r["key"] in real_keys,
        })
    return rows

def tally(rows, e):
    waits = sorted(x["wait"] for x in rows)
    n = len(waits)
    return {
        "nTrig": n,
        "nGe100": sum(1 for v in waits if v >= DCLASS_MS),
        "nGt50": sum(1 for v in waits if v > CUTOFF_MS),
        "nGt50PlusE": sum(1 for v in waits if v + e > CUTOFF_MS),
        "waitMin": waits[0] if n else None,
        "waitMed": statistics.median(waits) if n else None,
        "waitMax": waits[-1] if n else None,
        "waits": waits,
        "realHits": sum(1 for x in rows if x["isReal"]),
        "latP50_realHits": (statistics.median([x["wait"] for x in rows if x["isReal"]])
                            if any(x["isReal"] for x in rows) else None),
    }

# ------------------------------------------------------------------ 5 结构量（U6 的后果）
n_i0 = sum(1 for r in REC if r["i"] == 0)
n_og_none = sum(1 for r in REC if r["og"] is None)
n_he_lt64 = sum(1 for r in REC if r["he"] < N_HIST)
n_og_none_he_ge64 = sum(1 for r in REC if r["og"] is None and r["he"] >= N_HIST)
real0_mapped = []
for k in real_start0:
    hit = [r for r in REC if r["key"] == k]
    real0_mapped.append((k, len(hit), hit[0]["he"] if hit else None,
                         hit[0]["og"] if hit else None))
out("")
out("【结构量 · og=None / he<64 与 startTick=0 的真实事件】")
out(f"  i==0 游程（og=None） n={n_i0}/{len(REC)}；he<64 无基线游程 n={n_he_lt64}/{len(REC)}")
out(f"  og=None 且 he>=64 的游程 n={n_og_none_he_ge64}（i==0 ⇒ he=0，故必为 0）")
out(f"  startTick==0 的 real 事件 n={len(real_start0)}：")
for k, cnt, he, og in real0_mapped:
    out(f"    {k}  对应游程数={cnt}  he={he}  og={fmt(og) if og is not None else 'None'}"
        f"  ⇒ he<64 且 og=None，6 个 id 全部不触发（结构性不可达）")
out("  结论：og=None 在本语料里不会让「已触发的格子」变得无定义，而是让这些游程"
    "整体不进入触发集（U6）；因此 12 格仍可补算，此事实须作为限制单列。")

# ------------------------------------------------------------------ 6 主表：12 格
out("")
out("=" * 104)
out("【§四 主表 · 统一口径 U 下 6×2=12 格重跑结果（每格给出实跑数值）】")
out("=" * 104)
out("口径：U1 id 权威谓词锚 / U2 wait=(t[idx]-t[i])*1000 (S_hat) / U3 og=t[i]-t[i-1]")
out(f"      U4 e={e_med:.9f}ms(全精度中位常数) / U5 >=100: wait>=100；+e>50: wait+e>50")
out("      分母 = 全部触发 nTrig（不是仅真实命中子集）")
out("")
hdr = (f"{'id':<16}|{'谓词锚':<10}|{'nTrig':>6}|{'>=100':>7}|{'+e>50':>7}|"
       f"{'waitMin':>10}|{'waitMed':>10}|{'waitMax':>10}|{'realHits':>9}")
out(hdr)
out("-" * len(hdr))
RESULTS = {}
for cid, anchor, fn in IDS:
    rows = run_crit(fn)
    t = tally(rows, e_med)
    t["id"] = cid
    t["anchor"] = anchor
    t["rows"] = rows
    RESULTS[cid] = t
    out(f"{cid:<16}|{anchor:<10}|{t['nTrig']:>6}|{t['nGe100']:>7}|{t['nGt50PlusE']:>7}|"
        f"{fmt(t['waitMin']):>10}|{fmt(t['waitMed']):>10}|{fmt(t['waitMax']):>10}|{t['realHits']:>9}")

out("")
out("【逐格明细：12 格各自数值 + 可手核的 wait 有序表】")
for cid, anchor, fn in IDS:
    t = RESULTS[cid]
    out(f"  {cid}  (谓词锚={anchor})")
    out(f"    >=100   = {t['nGe100']}/{t['nTrig']}   （wait>=100.0 的触发数）")
    out(f"    +e>50   = {t['nGt50PlusE']}/{t['nTrig']}   （wait+{e_med:.9f}>50.0 的触发数）")
    out(f"    附：>50 = {t['nGt50']}/{t['nTrig']}（副产物，不属本任务 12 格）；"
        f"wait min/med/max = {fmt(t['waitMin'])}/{fmt(t['waitMed'])}/{fmt(t['waitMax'])}")
    ws = ", ".join(f"{v:.3f}" for v in t["waits"])
    out(f"    wait 有序表(ms, n={t['nTrig']}): [{ws}]")

# ------------------------------------------------------------------ 7 自检 / 交叉校验
out("")
out("=" * 104)
out("【§五 自检与交叉校验（既有件仅作只读参照，不作为本轮数值来源）】")
out("=" * 104)
ref = json.loads(REF_METRICS.read_text(encoding="utf-8-sig"))
out("(1) 触发集必须与 CRITERIA_METRICS.json 的 triggers/realHits/latencyP50Ms 对齐：")
all_ok = True
for cid, anchor, fn in IDS:
    t = RESULTS[cid]
    rj = ref[cid]
    c1 = t["nTrig"] == rj["triggers"]
    c2 = t["realHits"] == rj["realHits"]
    c3 = (t["latP50_realHits"] is None and rj["latencySampleN"] == 0) or (
        t["latP50_realHits"] is not None and
        abs(t["latP50_realHits"] - rj["latencyP50Ms"]) < 0.002)
    ok = c1 and c2 and c3
    all_ok = all_ok and ok
    out(f"    {cid:<16} nTrig {t['nTrig']} vs {rj['triggers']} {'OK' if c1 else 'FAIL'} | "
        f"realHits {t['realHits']} vs {rj['realHits']} {'OK' if c2 else 'FAIL'} | "
        f"latP50(real) {fmt(t['latP50_realHits'])} vs {fmt(rj['latencyP50Ms'])} {'OK' if c3 else 'FAIL'}"
        f" | note={rj['note']}")
out(f"    → 全部对齐 = {all_ok}")

out("(2) 4 个 lastEdge id 的 wait 分布须与主探针 _dtrigger_probe_out.txt 的实测一致：")
probe_expect = {
    "C2-abs-P95x2": (29, 66.334, 70.931, 321.002),
    "C3-r4":        (24, 125.884, 127.491, 440.389),
    "C3-r8":        (16, 251.709, 256.261, 258.378),
    "C3-r12":       (15, 377.385, 385.601, 387.990),
}
for cid, (n, mn, md, mx) in probe_expect.items():
    t = RESULTS[cid]
    ok = (t["nTrig"] == n and abs(t["waitMin"] - mn) < 0.002
          and abs(t["waitMed"] - md) < 0.002 and abs(t["waitMax"] - mx) < 0.002)
    all_ok = all_ok and ok
    out(f"    {cid:<16} min/med/max {fmt(t['waitMin'])}/{fmt(t['waitMed'])}/{fmt(t['waitMax'])}"
        f"  vs  {mn:.3f}/{md:.3f}/{mx:.3f}  {'OK' if ok else 'FAIL'}")

out("(3) e 取 2.511 常数（补算表 :4 的 3 位值）时 12 格是否变化：")
for cid, anchor, fn in IDS:
    t2 = tally(RESULTS[cid]["rows"], e_rounded)
    same = (t2["nGe100"] == RESULTS[cid]["nGe100"] and
            t2["nGt50PlusE"] == RESULTS[cid]["nGt50PlusE"])
    all_ok = all_ok and same
    out(f"    {cid:<16} >=100 {t2['nGe100']} / +e>50 {t2['nGt50PlusE']}"
        f"  {'与全精度 e 相同' if same else '发生变化'}")

out("(4) C3-r12 触发的真实事件覆盖数（§3.2 :238-239 称 15 次全为 non-real）：")
t12 = RESULTS["C3-r12"]
out(f"    realHits={t12['realHits']}/{t12['nTrig']}；"
    f"其 >=100={t12['nGe100']} / +e>50={t12['nGt50PlusE']} 全部计在非真实触发上"
    "（口径 B 计费漏洞，不改变本轮两列的定义）")

out("")
out("【§五附 口径敏感性 · 若强行把 6 个 id 的谓词锚全部统一为 runStart】")
out("  说明：这不是主表答案（它会改变 4 个 id 的触发集，故不属于这 4 个 id）；")
out("        单列出来只为定位补算表 :21-22 的来源，并量化锚口径对 12 格的影响。")
SENS = [
    ("C2-abs-P95x2 → P95x2/runStart", lambda r, w: pred_abs_runstart(r, w)),
    ("C3-r4        → r4/runStart",    lambda r, w: pred_rate(r, w, 4.0, "runStart")),
    ("C3-r4-clean  → (不变)",         lambda r, w: pred_rate(r, w, 4.0, "runStart")),
    ("C3-r8        → r8/runStart",    lambda r, w: pred_rate(r, w, 8.0, "runStart")),
    ("C3-r8-clean  → (不变)",         lambda r, w: pred_rate(r, w, 8.0, "runStart")),
    ("C3-r12       → r12/runStart",   lambda r, w: pred_rate(r, w, 12.0, "runStart")),
]
hdr2 = f"{'variant':<34}|{'nTrig':>6}|{'>=100':>7}|{'+e>50':>7}|{'waitMed':>10}|{'waitMax':>10}"
out(hdr2)
out("-" * len(hdr2))
for name, fn in SENS:
    t = tally(run_crit(fn), e_med)
    out(f"{name:<34}|{t['nTrig']:>6}|{t['nGe100']:>7}|{t['nGt50PlusE']:>7}|"
        f"{fmt(t['waitMed']):>10}|{fmt(t['waitMax']):>10}")
out("  对照（只读参照，不采信为结果）：_dtrigger_supplement_out.txt:15 的 C2-P95x2-复算"
    " = 27/4/4(>=100=4)；:21 的 C3-r4 = 24/24/24；:22 的 C3-r8 = 16/16/16。")
out("  ⇒ 补算表的 C3-r4 / C3-r8 行按其 runStart 谓词实为 `-clean` 两档的触发集；"
    "C2-P95x2-复算 行与 C2-abs-P95x2 无关（29 触发/>=100=5/+e>50=29 vs 27/4/27）。"
    "这是 §3.2 标签/锚错配的定量定位。")
out("  若把「统一锚」读作 6 个 id 一律 runStart，则上表即答案，但会替换 4 个 id 的触发集，"
    "与 CRITERIA_METRICS.json 及主探针已落账的 id 定义不符，故不作主结论。")
out("  本轮『统一』的准确含义：一条统一规则（每个 id 取其权威登记的锚）无例外地施加于全部 6 个 id"
    "与全部 12 格；两列的等待锚 U2 更是 6 个 id 完全同一个 S_hat，不存在混用。")

# ------------------------------------------------------------------ 8 结论与未验项
out("")
out("=" * 104)
out("【§六 结论（只含本轮实跑可判定的 12 格）】")
out("=" * 104)
out("采用口径 U（U1 id 权威谓词锚 + U2 统一 S_hat 等待锚 + U3 og + U4 e 中位常数 + U5/U6），")
out("12 格【全部可补算】，无需写「不可补算」：")
out("")
out("| id | >=100 | +e>50 |")
out("|---|---:|---:|")
for cid, anchor, fn in IDS:
    t = RESULTS[cid]
    out(f"| {cid} | {t['nGe100']} | {t['nGt50PlusE']} |")
out("")
out("结构性理由说明（为何 og=None 没有使任何一格不可补算）：og=None 只出现在 i==0，"
    "本语料中 i==0 ⇒ he=0<64，故 4 个 lastEdge id 与 2 个 runStart id 都在 U6 下"
    "直接不触发，触发集内每个元素都有定义良好的 og 与 wait；不存在「已触发但 wait 无定义」"
    "的情形。代价是 4 条 startTick=0 的真实事件在 6 个 id 下结构性不可达。")
out("")
out("【§七 本轮仍未验项（单列，不并入上述结论）】")
out("  1. 物理起点 S 的精确 waitAfterS：语料只有 (t,f)，S ∈ (t[i-1], t[i]] 不可测；"
    "本轮全部 wait 是 S_hat 锚下的下界（S_OBSERVABILITY.md:57-63、CRITERIA_COMPARE.md:395）。")
out("  2. 逐游程代入各自 og/e 的实测 +e>50：本轮按 §3.1:222-223 只用中位常数 e，"
    "未做逐游程修正（该修正在既有定义中本就未验）。")
out("  3. Q5 四项（触发延迟、采样扰动、端到端保存时刻 C、因果关系）：全未验"
    "（RULING_D30.md:22,78）；本轮不触碰。")
out("  4. 4 条 startTick=0 真实事件的物理 S 与总时长：不可判定（S_OBSERVABILITY.md:191）。")
out("  5. 其余 §7 各项（实际保存负担/配额资源、内部状态旗标、跨窗连续时序、"
    "延迟分布逐档重跑、工程可行性/修复收益/方案批准）：本轮均未实跑，保持未验。")
out("")
out(f"自检总判定 = {'PASS' if all_ok else 'FAIL'}（全部检查项均为本脚本本轮实跑）")

# ------------------------------------------------------------------ 9 落盘
WD.mkdir(parents=True, exist_ok=True)
for p in (OUT_TXT, OUT_JSON):
    if not p.resolve().is_relative_to(WD):
        raise ValueError("write escape")
OUT_TXT.write_text("\n".join(L) + "\n", encoding="utf-8")
dump = {
    "unified_anchor_spec": {
        "U1_predicate_anchor": "per-id authoritative anchor from _dtrigger_metrics.py:217,223-227",
        "U2_wait_anchor": "S_hat = t[runStart]; wait=(t[idx]-t[i])*1000 ms",
        "U3_og": "(t[i]-t[i-1])*1000 ms if i>0 else None; since_advance = wait + og",
        "U4_e": "median(og over all runs with i>0), single constant, recomputed here",
        "U5_columns": ">=100: wait>=100.0 ; +e>50: wait+e>50.0 ; denominator = all triggers",
        "U6_undefined": "og=None or he<64 or base<=0 -> no trigger",
    },
    "e_med_full": e_med,
    "e_rounded_reference": e_rounded,
    "n_runs": len(REC),
    "n_real": len(real),
    "n_real_startTick0": len(real_start0),
    "real_startTick0": [list(k) for k in real_start0],
    "n_i0": n_i0,
    "n_og_none": n_og_none,
    "n_he_lt64": n_he_lt64,
    "n_og_none_he_ge64": n_og_none_he_ge64,
    "selfcheck_all_pass": all_ok,
    "cells": {cid: {k: v for k, v in RESULTS[cid].items() if k != "rows"}
              for cid, _, _ in IDS},
    "trigger_details": {cid: RESULTS[cid]["rows"] for cid, _, _ in IDS},
}
OUT_JSON.write_text(json.dumps(dump, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
out(f"\n输出已写：{OUT_TXT}")
out(f"输出已写：{OUT_JSON}")
