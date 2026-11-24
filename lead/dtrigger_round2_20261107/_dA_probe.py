# -*- coding: utf-8 -*-
"""
_dA_probe.py — 结构探针：只读语料，核算 (t,f) 前缀的可分辨性上界、存活集基准率、
逐游程 e / 前一游程摘要的可得性。零真机、零采样代码、只读语料。

所有实跑：python -I -X utf8 <绝对路径>/_dA_probe.py
输出：     <同目录>/_dA_probe_out.txt（唯一写域 lead/dtrigger_round2_20261107/，前缀 _dA_）

口径复刻自 lead/dtrigger_compare_20261107/_cost_quota.py:82-168（不 import、不复用其结果数字）：
  - 语料 = out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/**/measure_w*.json
  - moving64 推进窗 = _stall_vs_gap_out.txt 的 97 行中、窗内 samples.f 有帧号变化者（=64）
  - 游程 = 每窗内连续相同帧号的最大段 (i..j)，共 28381 条
  - 真实事件 = STALL_EVENTS.json 中 isRealMatch==True 的 1681 条，(startTick,endTick) 与游程对齐
  - dfin = (t[j]-t[i])*1000 ms；误触发(事后计费) = dfin<100ms
本探针不产生任何触发判据，只核算「前缀能观测到什么 / 不能观测到什么」。
"""
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
WD = (ROOT / "lead/dtrigger_round2_20261107").resolve()
OUT = WD / "_dA_probe_out.txt"

if not OUT.resolve().is_relative_to(WD):
    raise ValueError("output escapes write domain")

lines = []
def out(s=""):
    lines.append(str(s)); print(s)

# ---------------------------------------------------------------- 0 指纹
out("=" * 104)
out("【_dA_probe.py · (t,f) 前缀结构探针 · 零真机 / 零采样代码 / 只读语料】")
out("=" * 104)
for rel in ("lead/stall_event_def_20261106/STALL_EVENTS.json",
            "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt",
            "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md",
            "lead/dtrigger_compare_20261107/_cost_quota_data.json",
            "lead/dstart_observable_20261107/S_OBSERVABILITY.md"):
    b = (ROOT / rel).read_bytes()
    out(f"sha256 {rel} = {hashlib.sha256(b).hexdigest()} bytes={len(b)}")

# ---------------------------------------------------------------- 1 语料与游程
cache = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr = p.resolve()
    if not pr.is_relative_to(BASE):
        raise ValueError("corpus escapes base")
    parts = pr.relative_to(BASE).parts
    key = (parts[0] if len(parts) > 1 else "(root)", pr.stem[len("measure_"):])
    d = json.loads(pr.read_text(encoding="utf-8-sig"))
    assert len(d["samples"]["t"]) == len(d["samples"]["f"])
    cache[key] = d
n_samples = sum(len(v["samples"]["t"]) for v in cache.values())
out(f"\n语料文件 n={len(cache)}，采样点 n={n_samples}，hz={sorted({v.get('hz') for v in cache.values()})}")

manifest_keys = set()
for ln in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_()]+)\s+(w\d)\s+([0-9.]+)", ln.strip())
    if m and (m[1], m[2]) in cache:
        s = cache[(m[1], m[2])]["samples"]
        if len(s["t"]) >= 2 and any(a != b for a, b in zip(s["f"], s["f"][1:])):
            manifest_keys.add((m[1], m[2]))
manifest_keys = sorted(manifest_keys)
out(f"moving64 推进窗 n={len(manifest_keys)}，覆盖 trip n={len(set(k[0] for k in manifest_keys))}")

events_all = json.loads(EVENTS.read_text(encoding="utf-8-sig"))
real = [e for e in events_all if e.get("isRealMatch") is True]
real_keys = {(e["trip"], e["window"], e["startTick"], e["endTick"]) for e in real}
dur_of = {(e["trip"], e["window"], e["startTick"], e["endTick"]): e["durationMs"] for e in real}
out(f"STALL_EVENTS 全量 n={len(events_all)}，isRealMatch==true n={len(real)}，去重 real_keys n={len(real_keys)}")

REC = []
for trip, win in manifest_keys:
    s = cache[(trip, win)]["samples"]
    T, F = s["t"], s["f"]
    n = len(F)
    # 与 _cost_quota.py:137-142 / _dA_run.py 同口径：hist = 帧沿到帧沿的已完成帧周期，
    # hlen[a] = 采样点 a 处已完成的帧周期数；runStart 处只取 hlen[i-1] 及更早（不含当前停滞）
    hist, hlen, le = [], [0] * n, 0
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
        dfin = (T[j] - T[i]) * 1000.0
        e = (T[i] - T[i - 1]) * 1000.0 if i > 0 else None      # 观测起点滞后上界代理
        he = hlen[i - 1] if i > 0 else 0
        D = hist[he - 1] if he >= 1 else None                    # 前一已完成帧周期(同 corpus 约定)
        # 前一「已完成」游程摘要：仅用 t[..i-1] 与帧号，全为已完成历史
        prev_i = None
        if i > 0:
            q = i - 1
            fq = F[q]
            while q > 0 and F[q - 1] == fq:
                q -= 1
            prev_i = q
        P = i - prev_i if prev_i is not None else None           # 前一周期采样点数
        prev_gaps = [(T[k] - T[k - 1]) * 1000.0 for k in range(prev_i + 1, i + 1)] if prev_i is not None else []
        REC.append({
            "trip": trip, "win": win, "i": i, "j": j, "npts": j - i + 1,
            "T": T, "F": F, "dfin": dfin, "e": e,
            "key": (trip, win, i, j), "is_real": (trip, win, i, j) in real_keys,
            "D": D, "P": P, "prev_min_gap": min(prev_gaps) if prev_gaps else None,
        })
        i = j + 1
out(f"推进窗内帧号游程 n={len(REC)}；真实事件与游程 (i,j) 对齐 n={sum(1 for r in REC if r['is_real'])}/{len(real_keys)}")

# dfin 与 STALL_EVENTS.durationMs 是否一致（口径核对，不参与触发）
diffs = []
for r in REC:
    if r["is_real"]:
        diffs.append(abs(r["dfin"] - dur_of[r["key"]]))
out(f"真实事件 |dfin - durationMs| : max={max(diffs):.6f} ms, mean={sum(diffs)/len(diffs):.6f} ms, n>0.01ms={sum(1 for x in diffs if x>0.01)}")

# ---------------------------------------------------------------- 2 e 分布（:177 的 e 修正输入）
es = sorted(r["e"] for r in REC if r["e"] is not None)
def pctl(a, p):
    return a[int(p * (len(a) - 1))] if a else None
out(f"\n【逐游程 e = t[runStart]-t[runStart-1]（观测滞后上界代理）】")
out(f"  有效 n={len(es)}（首拍游程 {len(REC)-len(es)} 条无前序 -> e 未验）")
out(f"  min={es[0]:.3f} med={pctl(es,.5):.3f} P95={pctl(es,.95):.3f} P99={pctl(es,.99):.3f} max={es[-1]:.3f} ms")
out(f"  :177 严格口径：真实等待 = waitAfterS_hat + (S_hat-S)，(S_hat-S)∈[0,e]，故 S_hat 锚等待仅为下界；")
out(f"  合规须 waitAfterS_hat + e <= 50ms（逐游程 e，非中位常数）。")

# ---------------------------------------------------------------- 3 存活集与基准率（可判定计数上界）
# A(τ) = {游程: dfin > τ}（帧在 elapsed=τ 时仍冻结）。
# 任何「帧未推进持续 >= τ」型在线因果谓词，在 τ 处只能对 A(τ) 中的游程触发；
# dfin<=τ 的游程在 τ 之前帧已推进，其前缀在 τ 处已终止，不可能被 τ 处触发。
# 因此该谓词在 τ 处的查准率上界 = |A_real(τ)| / |A(τ)|（基准率），可逐 τ 计数。
out("\n" + "=" * 104)
out("【存活集基准率 base_rate(τ) = A_real(τ)/A(τ)：:177 及时性 -> 区分度的计数上界】")
out("  A_real = isRealMatch==True 且 dfin>τ；A_falseB = dfin<100 且 dfin>τ；A_other = dfin>=100 但非 real(23条口径B伪影)")
out("  τ(ms) |   A(τ) | A_real | A_falseB | A_other | base_rate=A_real/A | 需等>=τ才能排除的假触发数")
out("  " + "-" * 100)
TAUS = (10, 18, 25, 30, 40, 45, 50, 55, 60, 70, 80, 90, 99)
bound_rows = []
for tau in TAUS:
    A = [r for r in REC if r["dfin"] > tau]
    a_real = sum(1 for r in A if r["is_real"])
    a_fb = sum(1 for r in A if r["dfin"] < 100 and not r["is_real"])
    a_other = len(A) - a_real - a_fb
    br = a_real / len(A) if A else float("nan")
    bound_rows.append((tau, len(A), a_real, a_fb, a_other, br))
    out(f"  {tau:>5} | {len(A):>7} | {a_real:>6} | {a_fb:>9} | {a_other:>7} | {br*100:>9.4f}% | {a_fb:>7}")
out("  读法：τ=50ms 时 A_falseB 条游程与真实事件同处于「帧仍冻结」状态，二者在 τ 处的")
out("  「帧号+已流逝时长」前缀状态相同；要排除它们只能把 τ 推到 100ms，而 :177 只允许 <=50ms（含 e 更严）。")

# ---------------------------------------------------------------- 4 逐游程「前缀签名」碰撞计数（充分条件，下界）
# 精确签名 = (前 τ 内相邻采样间隔 1µs 量化序列, 前一帧周期 D 的 1µs 量化, 前一周期采样点数 P)
# t 的存储精度为 1e-6 s = 1µs，故量化到 1µs 对语料无损；签名相同 => 前缀 (t,f) 数组逐位相同
# => 对任何「前缀+已完成历史」函数型在线因果谓词都不可分辨（充分条件）。
# 粗签名 = 间隔落入 {S:<0.05, M:0.05-0.5, L:0.5-2, X:2-5, G:>5} ms 的形状字 + D 的同类桶 + P 桶
# => 对任何「形状/序数」型谓词（本轮新判据族所属类）不可分辨。
def sig_prefix(r, tau, coarse):
    T, i = r["T"], r["i"]
    gaps = []
    x = i + 1
    while x <= r["j"] and (T[x] - T[i]) * 1000.0 <= tau:
        gaps.append((T[x] - T[x - 1]) * 1000.0)
        x += 1
    if coarse:
        def b(g):
            return "S" if g < 0.05 else ("M" if g < 0.5 else ("L" if g < 2 else ("X" if g < 5 else "G")))
        gsig = "".join(b(g) for g in gaps)
        dsig = b(r["D"]) if r["D"] is not None else "NONE"
        psig = "P0" if r["P"] is None else ("P1" if r["P"] <= 3 else ("P2" if r["P"] <= 8 else "P3"))
        return (len(gaps), gsig, dsig, psig)
    return (len(gaps), tuple(round(g, 3) for g in gaps),
            None if r["D"] is None else round(r["D"], 3), r["P"])

out("\n" + "=" * 104)
out("【前缀签名碰撞：real 与 dfin<100 的假游程共享同一前缀签名的类数 / 条数（下界）】")
for tau in (10, 18, 30, 40, 50):
    for coarse in (False, True):
        cls = defaultdict(lambda: [0, 0])   # sig -> [n_real, n_false]
        for r in REC:
            if r["dfin"] <= tau:
                continue
            s = sig_prefix(r, tau, coarse)
            if r["is_real"]:
                cls[s][0] += 1
            elif r["dfin"] < 100:
                cls[s][1] += 1
        mixed = [(s, v) for s, v in cls.items() if v[0] > 0 and v[1] > 0]
        real_in_mixed = sum(v[0] for _, v in mixed)
        false_in_mixed = sum(v[1] for _, v in mixed)
        tag = "粗(形状)" if coarse else "精确(1µs)"
        out(f"  τ={tau:>2}ms {tag:<10} 混合类数={len(mixed):>6}  混合类中 real={real_in_mixed:>5}  false={false_in_mixed:>6}"
            f"  -> 触发全部 real 至少连带 {len(mixed):>6} 个不可分辨类、{false_in_mixed:>6} 次强制误触发")
out("  说明：精确签名的碰撞是「充分条件」，故上述数字是强制共享判定数的下界；")
out("  通用命中集下界 LB1 见下一节与 _dA_out.txt §6 证据③。")

# ---------------------------------------------------------------- 5 前一游程摘要可得性（新判据族前置条件）
out("\n" + "=" * 104)
out("【新判据族所需「相邻游程 / 间隔形状」信息的可得性】")
have_D = sum(1 for r in REC if r["D"] is not None)
have_g3 = sum(1 for r in REC if r["npts"] >= 4)
have_prevmin = sum(1 for r in REC if r["prev_min_gap"] is not None)
out(f"  有前一帧周期 D 的游程 n={have_D}/{len(REC)}；首拍游程无前序 n={len(REC)-have_D}（e 与 D 均未验）")
out(f"  有 >=4 拍可构成 3 项间隔形状字的游程 n={have_g3}/{len(REC)}")
out(f"  有前一周期最短间隔 prev_min_gap 的游程 n={have_prevmin}/{len(REC)}")
Ds = sorted(r["D"] for r in REC if r["D"] is not None)
out(f"  D 分布(ms)：n={len(Ds)} min={Ds[0]:.3f} med={pctl(Ds,.5):.3f} P95={pctl(Ds,.95):.3f} max={Ds[-1]:.3f}")

# ---------------------------------------------------------------- 6 前缀签名命中集（限定特征类）
# 形式化（设 φ 为任一「平移不变前缀特征签名 σ」的确定性函数型在线因果判据）：
#   触发(R,a) ⇔ φ(σ(R,a))=1；每条 real 的可选前缀集 S_R={σ(R,a): a<=τ}。
#   若 φ 覆盖全部有前缀 real，其接受集 W 必须命中每条 S_R（命中集问题）。
#   forced_FP(W) = #{F∈FalseB : S_F ∩ W ≠ ∅}（去重；每个 F 每游程最多触发一次）。
#   下界 LB1 = max_R min_{s∈S_R} c(s)，c(s)=#{F: s∈S_F}：覆盖最贵那条 R 的 s 单独强制
#   >= min_{S_R} c 个不同 F 触发。UB_naive = #{F: S_F ∩ U_R ≠ ∅}（朴素 φ=接受 U_R 的
#   单次实跑，仅上界参考，不是所有 φ 的公共下界）。
# 粗签名对应「形状/序数/相邻游程」特征类；精确签名对应 1µs 量化全精度差值前缀。
# 精确签名下 UB_naive 很小（本语料 2 条），故对「任意实值函数型谓词」不作不可能断言（见 U5）。
def all_sigs(r, tau, coarse):
    T, i, j = r["T"], r["i"], r["j"]
    dsig = (("S" if r["D"] < 0.05 else "M" if r["D"] < 0.5 else "L" if r["D"] < 2
             else "X" if r["D"] < 5 else "G") if coarse else round(r["D"], 3)) if r["D"] is not None else None
    psig = ("P0" if r["P"] is None else "P1" if r["P"] <= 3 else "P2" if r["P"] <= 8 else "P3") if coarse else r["P"]
    def bkt(g):
        return "S" if g < 0.05 else ("M" if g < 0.5 else ("L" if g < 2 else ("X" if g < 5 else "G")))
    word_c, word_e = "", []
    S = set()
    x = i + 1
    while x <= j and (T[x] - T[i]) * 1000.0 <= tau:
        g = (T[x] - T[x - 1]) * 1000.0
        if coarse:
            word_c += bkt(g)
            S.add((x - i, word_c, dsig, psig))
        else:
            word_e.append(round(g, 3))
            S.add((x - i, tuple(word_e), dsig, psig))
        x += 1
    return S

out("\n" + "=" * 104)
out("【前缀签名命中集：限定特征类下的强制误触发计数下界（可判定的形式化证据）】")
out("  LB1 = max_R min_{s∈S_R} c(s)（c(s)=#{falseB F: s∈S_F}）；任意覆盖全部有前缀 real 的 φ")
out("  满足 forced_FP >= LB1，precision <= n_cov/(n_cov+LB1)。")
out("  UB_naive = #{F: S_F ∩ U_R ≠ ∅}（朴素 φ=接受 U_R 的一次实跑，仅参考，不是公共下界）。")
out("  " + "-" * 100)
for tau, coarse in ((18, True), (30, True), (40, True), (50, True), (18, False), (50, False)):
    U = set()
    real_sets, false_sets = [], []
    cnt = defaultdict(int)
    n_cov = 0
    for r in REC:
        # 口径 B：误触发 = dfin<100；dfin>=100 但 isRealMatch=False 的 23 条口径B伪影不计费
        if not r["is_real"] and r["dfin"] >= 100:
            continue
        S = all_sigs(r, tau, coarse)
        if r["is_real"]:
            if S:
                real_sets.append(S); U |= S; n_cov += 1
        else:
            false_sets.append(S)
            for s in S:
                cnt[s] += 1
    lb1 = max(min(cnt[s] for s in S) for S in real_sets) if real_sets else 0
    ub_naive = sum(1 for S in false_sets if (S & U))
    prec = n_cov / (n_cov + lb1) if (n_cov + lb1) else float("nan")
    tag = "粗(形状/序数)" if coarse else "精确(1µs 差值)"
    out(f"  τ={tau:>2}ms {tag:<16} |U_R|={len(U):>7}  n_cov={n_cov:>5}  "
        f"LB1={lb1:>6}  precision<={prec*100:>7.4f}%  UB_naive(朴素φ)={ub_naive:>6}")
out("  注：粗签名（形状/序数/相邻游程类，本题限定特征类）下 LB1>0、precision 上界可判定；")
out("  精确签名下 LB1 可能很小，故对「任意实值函数型谓词」不作信息论级不可能断言（见 U5）。")
out("  但配额硬上界与存活集基准率上界对任意谓词无条件成立（见 _dA_out.txt §6 证据①②）。")

out("\n【执行者结束 · 零真机 / 零采样代码 / 只读语料 / 无 commit push】")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"\n[written] {OUT} bytes={len(OUT.read_bytes())}")
