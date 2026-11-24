# -*- coding: utf-8 -*-
"""独立复核员 hy4 · 缩减形式补证回件（_ar_check.py / _ar_out.txt）独立重算。
不从被核脚本 import 任何函数：从原始 (t,f) 语料重建游程、real 键、e、签名、配额模拟。
只读既有件；写域 = lead/a_dim_reduced_20261108/，输出仅本文件 + _verify_hy4_out.txt。
python -I -X utf8 + 绝对路径；指纹 hashlib；零真机/零采样代码。
"""
import hashlib
import json
import os
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
EVENTS = ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json"
MANIFEST = ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt"
QUOTA_JSON = ROOT / "lead/dtrigger_compare_20261107/_cost_quota_data.json"
DA_OUT = ROOT / "lead/dtrigger_round2_20261107/_dA_out.txt"
VA_OUT = ROOT / "lead/dtrigger_round2_20261107/_verify_A_out.txt"
WD = ROOT / "lead/a_dim_reduced_20261108"
OUT = WD / "_verify_hy4_out.txt"

L = []
def say(s=""):
    print(s); L.append(s)

def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

# ---- F0 指纹（复核回件必须含被核对象 SHA256 + 字节数）----
say("=== F0 被核对象指纹（本会话 hashlib 实算）===")
SUBJECTS = [
    "lead/dtrigger_round2_20261107/_dA_out.txt",
    "lead/dtrigger_round2_20261107/_dA_design.md",
    "lead/dtrigger_round2_20261107/_verify_A_out.txt",
    "lead/dtrigger_round2_20261107/_verify_A_recompute.py",
    "lead/r2_final_grade_20261108/R2_FINAL_GRADE.md",
    "lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md",
    "lead/a_dim_reduced_20261108/_ar_check.py",
    "lead/a_dim_reduced_20261108/_ar_out.txt",
]
EXPECT = {
    "lead/dtrigger_round2_20261107/_dA_out.txt": "8825e115f92bdf407cf20dde724e5633adc4e08e3f97bcee58299b95a8cb6d43/29813",
    "lead/dtrigger_round2_20261107/_dA_design.md": "d5d487a7792da6ce89e143faa05727a4fe484cb66b400622c02511230770e0df/20819",
    "lead/dtrigger_round2_20261107/_verify_A_out.txt": "145d4fa12e0e618f859c8f98305034d0ddb2952ae47b668e7a6a4c37290ca3b7/11204",
    "lead/dtrigger_round2_20261107/_verify_A_recompute.py": "5d906aa00069a4b9d484221db37368efe9cb83930cfeee85a4b0c5c53124fd4e/36794",
    "lead/r2_final_grade_20261108/R2_FINAL_GRADE.md": "7ce09812f7bd905a95114a2cc2cea56b3dc3dbaef3d8e0d14c58685762ecab24/30140",
    "lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md": "bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde/22351",
}
fp_all_ok = True
for rel in SUBJECTS:
    h, n = fp(ROOT / rel)
    say(f"被核对象 SHA256 = {h}，字节数 = {n}    [{rel}]")
    if rel in EXPECT:
        eh, en = EXPECT[rel].split("/")
        ok = (h == eh and n == int(en))
        fp_all_ok &= ok
        say(f"  对照编排方指纹: {'MATCH' if ok else 'MISMATCH'}")
say(f"F0 六件编排方指纹全 MATCH = {fp_all_ok}")
say()

# ---- F1 从原始语料重建：(t,f) -> 游程 -> real 键 ----
say("=== F1 独立重建语料（不 import 被核脚本）===")
raw = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr = p.resolve()
    parts = pr.relative_to(BASE).parts
    trip = parts[0] if len(parts) > 1 else "(root)"
    win = pr.stem[len("measure_"):]
    raw[(trip, win)] = json.loads(pr.read_text(encoding="utf-8-sig"))
n_samples = sum(len(v["samples"]["t"]) for v in raw.values())
hzs = sorted({v.get("hz") for v in raw.values()})
say(f"files={len(raw)} samples={n_samples} hz={hzs}")

# manifest 中「有帧号变化」的窗 = moving window
mkeys = set()
for ln in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if m and (m[1], m[2]) in raw:
        s = raw[(m[1], m[2])]["samples"]
        if len(s["t"]) >= 2 and any(a != b for a, b in zip(s["f"], s["f"][1:])):
            mkeys.add((m[1], m[2]))
mkeys = sorted(mkeys)
say(f"moving windows={len(mkeys)} trips={len({k[0] for k in mkeys})}")

ev = json.loads(EVENTS.read_text(encoding="utf-8-sig"))
real_keys = {(e["trip"], e["window"], e["startTick"], e["endTick"])
             for e in ev if e.get("isRealMatch") is True}
say(f"events all={len(ev)} isRealMatch={len(real_keys)}")

# 独立游程切分：连续相同帧号 = 一条游程
recs = []
for trip, win in mkeys:
    T = raw[(trip, win)]["samples"]["t"]
    F = raw[(trip, win)]["samples"]["f"]
    n = len(F)
    # hist：帧沿到帧沿的帧周期；he = 游程起点前已完成的帧周期数
    hist = []
    le = 0
    hlen = [0] * n
    for a in range(1, n):
        if F[a] != F[a - 1]:
            hist.append((T[a] - T[le]) * 1000.0)
            le = a
        hlen[a] = len(hist)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and F[j + 1] == F[i]:
            j += 1
        he = hlen[i - 1] if i > 0 else 0
        e_ms = (T[i] - T[i - 1]) * 1000.0 if i > 0 else None
        q = i - 1
        if i > 0:
            fq = F[q]
            while q > 0 and F[q - 1] == fq:
                q -= 1
            prev_len = i - q
        else:
            prev_len = None
        recs.append({
            "trip": trip, "win": win, "i": i, "j": j, "T": T, "F": F,
            "key": (trip, win, i, j),
            "is_real": (trip, win, i, j) in real_keys,
            "dfin": (T[j] - T[i]) * 1000.0,
            "e": e_ms,
            "D": hist[he - 1] if he >= 1 else None,
            "prev_len": prev_len,
        })
        i = j + 1
say(f"runs={len(recs)} real_aligned={sum(1 for r in recs if r['is_real'])} "
    f"e_valid={sum(1 for r in recs if r['e'] is not None)} "
    f"e_none={sum(1 for r in recs if r['e'] is None)}")
say()

# ---- F2 配额理想值 + 紧性（独立实算）----
say("=== F2 配额上界 ideal W/T 独立实算 ===")
wc = Counter(k[:2] for k in real_keys)
tc = Counter(k[0] for k in real_keys)
ideal_w = {N: sum(min(N, c) for c in wc.values()) for N in (1, 3, 5)}
ideal_t = {N: sum(min(N, c) for c in tc.values()) for N in (1, 3, 5)}
say(f"ideal_w={ideal_w} nonempty_windows={len(wc)}")
say(f"ideal_t={ideal_t} nonempty_trips={len(tc)}")
cw = sorted(wc.values())
say(f"c_w: min={cw[0]} med={statistics.median(cw)} max={cw[-1]} "
    f"c_w>=5={sum(1 for c in cw if c >= 5)}")
say(f"F2 PASS ideal_w=={{1:26,3:73,5:117}} :: {ideal_w == {1:26,3:73,5:117}}")
say(f"F2 PASS ideal_t=={{1:12,3:31,5:47}} :: {ideal_t == {1:12,3:31,5:47}}")

# 上界等式本身：Σ min(N,c_w) 逐窗封顶；检查它确实是「任何谓词」的上界：
# 对每条游程最多 1 次触发，每组前 N 次触发 <= 该组 real 数（c_w），且 <= N。
# 直接验证：对 41 档既有判据的 W5 全部 <= 117
da_lines = DA_OUT.read_text(encoding="utf-8-sig").splitlines()
da_w5 = []
for ln in da_lines[48:65]:
    parts = [x.strip() for x in ln.split("|")]
    if len(parts) >= 11 and re.match(r"^(CAL|D\d)", parts[0]):
        vals = [int(x) for x in parts[8].split()]
        da_w5.append((parts[0], vals[2]))
qj = json.loads(QUOTA_JSON.read_text(encoding="utf-8-sig"))
qj_w5 = [(cid, res["window5"]["captured"]) for cid, res in qj["results"].items()]
say(f"_dA_out.txt 15 档 W5 max={max(v for _,v in da_w5)} "
    f"(_cost_quota_data.json 26 档 W5 max={max(v for _,v in qj_w5)})")
say(f"F2 PASS 41 档无一达 117 :: "
    f"{all(v < 117 for _,v in da_w5) and all(v < 117 for _,v in qj_w5)}")
say()

# ---- F3 EXACT_LOOKUP 独立复现（1µs 精确签名查表，train=test）----
say("=== F3 EXACT_LOOKUP 独立复现（上界紧性见证）===")
def gap_ms(T, x):
    return (T[x] - T[x - 1]) * 1000.0
def elapsed_ms(T, i, x):
    return (T[x] - T[i]) * 1000.0
def sig_pairs(r, tau, coarse):
    T, i, j = r["T"], r["i"], r["j"]
    D, P = r["D"], r["prev_len"]
    if coarse:
        dsig = ("S" if D < 0.05 else "M" if D < 0.5 else "L" if D < 2 else "X" if D < 5 else "G") if D is not None else "NONE"
        psig = "P0" if P is None else "P1" if P <= 3 else "P2" if P <= 8 else "P3"
        word, out, we = "", [], None
    else:
        dsig = round(D, 3) if D is not None else None
        psig = P
        word, out, we = "", [], []
    x = i + 1
    while x <= j and elapsed_ms(T, i, x) <= tau:
        g = gap_ms(T, x)
        if coarse:
            word += ("S" if g < 0.05 else "M" if g < 0.5 else "L" if g < 2 else "X" if g < 5 else "G")
            out.append((x, (x - i, word, dsig, psig)))
        else:
            we.append(round(g, 3))
            out.append((x, (x - i, tuple(we), dsig, psig)))
        x += 1
    return out

TAU = 50.0
real_sigs = set()
for r in recs:
    if r["is_real"]:
        for _, s in sig_pairs(r, TAU, False):
            real_sigs.add(s)
say(f"|real_exact_sigs| = {len(real_sigs)}")

trig = []
for r in recs:
    t_idx = None
    for idx, s in sig_pairs(r, TAU, False):
        if s in real_sigs:
            t_idx = idx
            break
    if t_idx is None:
        continue
    w = elapsed_ms(r["T"], r["i"], t_idx)
    e = r["e"]
    trig.append({
        "t": r["T"][t_idx], "win": r["win"], "trip": r["trip"], "key": r["key"],
        "is_real": r["is_real"], "dfin": r["dfin"], "w": w, "e": e,
        "strict": (e is not None and w + e <= 50.0),
    })
n_real = sum(1 for t in trig if t["is_real"])
n_falseB = sum(1 for t in trig if t["dfin"] < 100 and not t["is_real"])
prec = n_real / (n_real + n_falseB) if (n_real + n_falseB) else None
strict_real = len({t["key"] for t in trig if t["is_real"] and t["strict"]})
say(f"EXACT_LOOKUP trig={len(trig)} real={n_real} falseB={n_falseB} "
    f"precision={prec:.6f} in50_strict={strict_real}/1681")

def quota(trig, scope, N):
    g = defaultdict(list)
    for t in trig:
        g[(t["trip"], t["win"]) if scope == "window" else t["trip"]].append(t)
    cap = set()
    for arr in g.values():
        arr.sort(key=lambda x: (x["t"], x["win"], x["key"][2], x["key"][3]))
        for t in arr[:N]:
            if t["is_real"]:
                cap.add(t["key"])
    return len(cap)

W = {N: quota(trig, "window", N) for N in (1, 3, 5)}
T = {N: quota(trig, "trip", N) for N in (1, 3, 5)}
say(f"EXACT_LOOKUP W={W} T={T}")
say(f"F3 PASS W 达理想上界 :: {W == ideal_w}   T 达理想上界 :: {T == ideal_t}")
va_lines = VA_OUT.read_text(encoding="utf-8-sig").splitlines()
say(f"F3 对照 _verify_A_out.txt:119-120 数值一致 :: "
    f"{(len(trig), n_real, n_falseB, round(prec,6), strict_real) == (1679,1678,1,0.999404,1619)}")
say("注：紧性见证谓词的查表内容由同语料 is_real 标签构成（train=test）——本复核据实登记。")
say()

# ---- F4 1621/1681 独立实算 ----
say("=== F4 1621/1681 独立实算（离线可证计数来源）===")
rr = [r for r in recs if r["is_real"]]
gt50 = [r for r in rr if r["e"] is not None and r["e"] > 50]
enone = [r for r in rr if r["e"] is None]
le50 = [r for r in rr if r["e"] is not None and r["e"] <= 50]
say(f"real n={len(rr)}  e>50ms n={len(gt50)}  e未验 n={len(enone)}  e<=50ms n={len(le50)}")
say(f"F4 PASS (56,4,1621) :: {(len(gt50), len(enone), len(le50)) == (56,4,1621)}")
say(f"1621/1681 = {len(le50)/1681*100:.6f}%")
es = sorted(r["e"] for r in gt50)
say(f"e>50: min={es[0]:.3f} med={statistics.median(es):.3f} "
    f"P90={es[int(0.9*55)]:.3f} max={es[-1]:.3f} ms")
say(f"F4 PASS EXACT_LOOKUP in50_strict {strict_real} <= 1621 :: {strict_real <= 1621}")
say("e = t[runStart]-t[runStart-1] 是外部采样器相邻采样间隔（观测装置产物）；"
    "离线 S_hat-S∈[0,e] 夹逼，w+e<=50 才可证 -> 60 条不可判定 -> 1621。")
say()

# ---- F5 LB1 独立重算 ----
say("=== F5 LB1 粗签名（限定特征类）独立重算 ===")
for tau in (18.0, 50.0):
    counts = Counter()
    rsets = []
    U = set()
    empty_real = 0
    n_fb = 0
    for r in recs:
        S = {s for _, s in sig_pairs(r, tau, True)}
        if r["is_real"]:
            if S:
                rsets.append(S); U |= S
            else:
                empty_real += 1
        elif r["dfin"] < 100:
            n_fb += 1
            counts.update(S)
    lb1 = max(min(counts[s] for s in S) for S in rsets) if rsets else 0
    ub = sum(1 for r in recs if not r["is_real"] and r["dfin"] < 100
             and ({s for _, s in sig_pairs(r, tau, True)} & U))
    n_cov = len(rsets)
    p = n_cov / (n_cov + lb1) if (n_cov + lb1) else None
    say(f"tau={tau:.0f}: n_cov={n_cov} empty_real={empty_real} LB1={lb1} "
        f"UB_naive={ub} precision<={p*100:.4f}% falseB母体={n_fb}")
    if tau == 18.0:
        lb18, p18 = lb1, p
    else:
        lb50, p50 = lb1, p
say(f"F5 PASS tau18 LB1=4056 & tau50 LB1=1638 :: {lb18==4056 and lb50==1638}")
say(f"F5 PASS tau50 precision<=50.6031% :: {abs(p50*100-50.6031)<5e-5}")
say()

# ---- F6 oracle 脱钩：O1a / O1b / O2 / O3 独立复算 ----
say("=== F6 oracle 脱钩检验独立复算 ===")
# base_rate
for tau in (10.0, 30.0, 40.0, 50.0):
    alive = [r for r in recs if r["dfin"] > tau]
    ar = sum(1 for r in alive if r["is_real"])
    say(f"base_rate tau={tau:.0f}: A={len(alive)} real={ar} "
        f"falseB={sum(1 for r in alive if r['dfin']<100 and not r['is_real'])} "
        f"br={ar/len(alive)*100:.4f}%")
say(f"差分算术 1681/(1681+3355*0.01) = {1681/(1681+3355*0.01):.6f}")

# O1a leave-own-run-out
owners = defaultdict(set)
for r in rr:
    for _, s in sig_pairs(r, TAU, False):
        owners[s].add(r["key"])
cross = 0
for r in rr:
    own = {s for _, s in sig_pairs(r, TAU, False)}
    if any(owners[s] - {r["key"]} for s in own):
        cross += 1
false_all = sum(1 for r in recs if not r["is_real"] and r["dfin"] < 100
                and any(s in owners for s in {s for _, s in sig_pairs(r, TAU, False)}))
say(f"O1a(仍用 oracle 标签建表): 去自身签名后 real 触发={cross}/1681, falseB 触发={false_all}")

# O1b/O2 trip holdout
trips = sorted({r["trip"] for r in recs})
train_t = {t for i, t in enumerate(trips) if i % 2 == 0}
test_t = {t for i, t in enumerate(trips) if i % 2 == 1}
tr_real = [r for r in rr if r["trip"] in train_t]
te_real = [r for r in rr if r["trip"] in test_t]
say(f"holdout trips={len(trips)} train={len(train_t)} test={len(test_t)} "
    f"train_real={len(tr_real)} test_real={len(te_real)}")
for tag, coarse in (("O1b 精确", False), ("O2 粗", True)):
    ts = set()
    for r in tr_real:
        for _, s in sig_pairs(r, TAU, coarse):
            ts.add(s)
    fr = ff = fa = 0
    for r in recs:
        if r["trip"] not in test_t:
            continue
        if not any(s in ts for s in (s for _, s in sig_pairs(r, TAU, coarse))):
            continue
        if r["is_real"]:
            fr += 1
        elif r["dfin"] < 100:
            ff += 1
        else:
            fa += 1
    pr = fr / (fr + ff) if (fr + ff) else None
    say(f"{tag}(train 表仍由 oracle 标签构成): test 触发={fr+ff+fa} "
        f"real={fr} falseB={ff} precision={pr*100 if pr is not None else -1:.4f}% "
        f"test-real recall={fr/len(te_real)*100:.2f}%")

# O3 无标签判据：构造只读 (t,f)，不触碰 is_real；事后计费才用 is_real
def cal_abs(r, theta):
    T, i, j = r["T"], r["i"], r["j"]
    if j - i + 1 < 3:
        return None
    for x in range(i + 2, j + 1):
        if elapsed_ms(T, i, x) > theta:
            return x
    return None
def d4_burst(r):
    T, i, j = r["T"], r["i"], r["j"]
    prev = None
    for x in range(i + 1, j + 1):
        g = gap_ms(T, x)
        if prev is not None and prev < 0.5 and g >= 2.0:
            return x
        prev = g
    return None
def word_mmm(r):
    T, i, j = r["T"], r["i"], r["j"]
    w = ""
    for x in range(i + 1, j + 1):
        g = gap_ms(T, x)
        w += ("S" if g < 0.05 else "M" if g < 0.5 else "L" if g < 2 else "X" if g < 5 else "G")
        if len(w) >= 3 and w.endswith("MMM"):
            return x
    return None
for cid, fn in (("C4-t40", lambda r: cal_abs(r, 40.0)),
                ("D4-burst", d4_burst), ("D1-word-MMM", word_mmm)):
    nr = nf = 0
    for r in recs:
        if fn(r) is None:
            continue
        if r["is_real"]:
            nr += 1
        elif r["dfin"] < 100:
            nf += 1
    pr = nr / (nr + nf) if (nr + nf) else None
    say(f"O3 无标签 {cid}: trig_real={nr} falseB={nf} "
        f"precision={pr*100 if pr is not None else -1:.4f}% recall={nr/1681*100:.2f}%")

# O3 构造是否读 is_real：用 inspect 检查函数源码（不执行注入）
import inspect
for fn in (cal_abs, d4_burst, word_mmm):
    src = inspect.getsource(fn)
    say(f"O3 构造源码含 'is_real'? {cid if False else fn.__name__}: {'is_real' in src}")
say()

# ---- F7 逐字抄录核对（S1 与被核原文逐行比对）----
say("=== F7 逐字抄录核对：_ar_out.txt S1 段 vs 被核原文 ===")
ar = (WD / "_ar_out.txt").read_text(encoding="utf-8-sig").splitlines()
da = DA_OUT.read_text(encoding="utf-8-sig").splitlines()
# 抽出 S1 段中 _dA_out.txt 的引用行（形如 "<num>\t<text>"）
bad = []
checked = 0
for ln in ar:
    if "\t" not in ln:
        continue
    num, _, txt = ln.partition("\t")
    if not num.isdigit():
        continue
    k = int(num)
    if 1 <= k <= len(da):
        # 只在 _dA_out.txt 区段（S1 前半）检查：行号 <= 283
        if k <= 283 and da[k-1] != txt:
            bad.append((k, da[k-1][:80], txt[:80]))
        checked += 1
say(f"S1 中带行号的引用行检查数={checked}  与 _dA_out.txt 原文不一致数={len(bad)}")
for b in bad[:10]:
    say(f"  MISMATCH line {b[0]}: orig={b[1]!r} quoted={b[2]!r}")
say("（注：S1 同时含 _dA_design.md / R2_FINAL_GRADE.md / R2_BREAKPOINTS_CLOSURE.md 引文，"
    "其行号不属 _dA_out.txt，上面的比对仅对 <=283 行生效，可能对 design 段行号误比对；"
    "下方另做分文件精确核对。）")

# 分文件精确核对 S1 每个 ---- file ---- 块
blocks = {}
cur = None
for ln in ar:
    if ln.startswith("---- ") and ln.endswith(" ----"):
        cur = ln[5:-5]
        blocks[cur] = []
    elif cur is not None and ln.startswith("=== "):
        cur = None
    elif cur is not None and "\t" in ln and ln.partition("\t")[0].isdigit():
        blocks[cur].append((int(ln.partition("\t")[0]), ln.partition("\t")[2]))
SRC = {
    "lead\\dtrigger_round2_20261107\\_dA_out.txt": DA_OUT,
    "lead\\dtrigger_round2_20261107\\_dA_design.md": ROOT / "lead/dtrigger_round2_20261107/_dA_design.md",
    "lead\\r2_final_grade_20261108\\R2_FINAL_GRADE.md": ROOT / "lead/r2_final_grade_20261108/R2_FINAL_GRADE.md",
    "lead\\criteria_r3_verify_20261108\\R2_BREAKPOINTS_CLOSURE.md": ROOT / "lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md",
}
for blk, rows in blocks.items():
    if blk not in SRC:
        say(f"  块 {blk} 未映射源，跳过")
        continue
    src_lines = SRC[blk].read_text(encoding="utf-8-sig").splitlines()
    mism = []
    for k, txt in rows:
        if k < 1 or k > len(src_lines) or src_lines[k-1] != txt:
            mism.append((k, src_lines[k-1][:70] if 1 <= k <= len(src_lines) else "<OOR>", txt[:70]))
    say(f"  块 {blk}: 引用行={len(rows)} 不一致={len(mism)}")
    for m in mism[:6]:
        say(f"    MISMATCH {m[0]}: {m[1]!r} vs {m[2]!r}")
say()

# ---- F8 S1 之外的「是否代裁 / 是否拔高」文本扫描 ----
say("=== F8 文本扫描（不代裁 / 不拔高）===")
ar_text = "\n".join(ar)
for kw in ("立为新结论", "不作裁定", "不代裁", "necessaryCount", "oracleDecouplable", "未验"):
    say(f"_ar_out.txt 含 '{kw}': {kw in ar_text}")
say("回件（题给补证文本）任务5 原文含『不作裁定』：见题面【任务5·不代裁】。")
say()

OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"[written] {OUT} bytes={OUT.stat().st_size}")
