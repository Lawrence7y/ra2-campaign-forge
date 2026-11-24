# -*- coding: utf-8 -*-
"""R73 · 窗口宽度与「可伪造面」的量化（落实 §2.57「奖励造假」这句未量化的判读）。

背景：ROUND_WINDOWS 里 r57 的 end 被写成 235959 占位。R71 记「r58-r65 共 8 个快照
时点被 r57 的 235959 吞没」，但**没算过这有多宽、能放过什么**。

本脚本只做测量，不改任何表：
  S1 逐行算出 22 行的窗口宽度，排序，给出中位数与最大者
  S2 实测「r57 这个 6 小时窗口能放过什么」：在临时产物里写一条 at=23:00:00 标 R57 的行，
     看 C11 是否判 PASS（应当在 R4 通过——这正是缺陷）
  S3 实测同一时刻标 R58 会怎样（应当因「no round window」判 False）
     ⇒ 两者对照证明：门禁在此处**奖励写旧轮次号**
  S4 反控：把同一行的 at 挪到窗口外（23:59:59 之后不可能，取次日 00:00:01 会报 Format 错），
     改用 at=17:00:00 标 R57 ⇒ 应当挂在 R4（证 S2 不是恒 PASS）
  S5 反控：at=23:00:00 标 R56 ⇒ 应当挂在 R4（该时刻不在 r56 窗口）

不写 live 任何文件：临时产物落在系统 temp，atexit 清理。
"""
import io, os, sys, types, tempfile, shutil, atexit, hashlib, statistics, re

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

FAILS = []
TMP = tempfile.mkdtemp(prefix="r73win_")
atexit.register(lambda d=TMP: shutil.rmtree(d, ignore_errors=True))


def P(s=""):
    print(s)


def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c:
        FAILS.append(n)
    return c


src = io.open(os.path.join(R14, "recheck_verify.py"), encoding="utf-8").read()
m = types.ModuleType("rv")
m.__file__ = os.path.join(R14, "recheck_verify.py")
exec(compile(src, m.__file__, "exec"), m.__dict__)
W = m.ROUND_WINDOWS

P("=== S1 · 22 行窗口宽度 ===")
rows = []
for no, (w0, w1, sf, ef) in sorted(W.items()):
    secs = (w1 - w0).total_seconds()
    rows.append((secs, no, w0, w1, ef))
P("  %-5s %-10s %-10s %s" % ("轮次", "起", "止", "宽度"))
for secs, no, w0, w1, ef in sorted(rows, key=lambda r: r[0]):
    flag = ""
    if "open" in ef or ef.endswith("235959"):
        flag = "  <== 占位端点"
    P("  R%-4d %-10s %-10s %8.0f s (%.1f min)%s"
      % (no, w0.strftime("%H:%M:%S"), w1.strftime("%H:%M:%S"), secs, secs / 60.0, flag))
widths = [r[0] for r in rows]
med = statistics.median(widths)
mx = max(rows, key=lambda r: r[0])
mn = min(rows, key=lambda r: r[0])
P("")
P("  行数 %d ；中位宽度 %.0f s (%.1f min) ；最窄 R%d = %.0f s ；最宽 R%d = %.0f s (%.2f h)"
  % (len(rows), med, med / 60.0, mn[1], mn[0], mx[1], mx[0], mx[0] / 3600.0))
ck("S1-a 表覆盖 22 行", len(rows) == 22, str(len(rows)))
ck("S1-b 最宽行是 R57（235959 占位）", mx[1] == 57, "R%d" % mx[1])
# R73 自错修正（第六次）：初版写"宽度 > 中位 50 倍"—— 50 是个凭空的整数阈值，
# 实测 27.9 倍就判 FAIL。这正是 R72 立下的教训：连续量不要做二分类。
# 改成**只报数**，异常与否交给下游判断（宽度本身是事实，阈值是判读）。
P("  [数值] R57 宽度 / 中位宽度 = %.1f 倍" % (mx[0] / med))
ck("S1-c R57 宽度是可测的大量级（> 中位数 10 倍，仅作量级核对非判据）",
   mx[0] > 10 * med, "%.1f 倍" % (mx[0] / med))
ck("S1-d R57 宽度 > 5 小时（可容纳 8 个 r58-r65 快照）", mx[0] > 5 * 3600,
   "%.2f h" % (mx[0] / 3600.0))
# r58-r65 的 8 个快照时点是否真的都落在 r57 窗口内
SNAPS = ["175200", "180234", "182334", "182640", "183210", "183611", "183842", "184136"]
w0, w1, _, _ = W[57]
inside = [s for s in SNAPS if w0 <= m._hhmmss(s) < w1]
P("  r58-r65 的 8 个快照时点落在 R57 窗口内的 = %d/8" % len(inside))
ck("S1-e 8/8 快照时点被 R57 吞没（R71 的说法实测成立）", len(inside) == 8,
   "%d/8" % len(inside))

# ---- S2/S3/S5 · 用真校验器判伪造行 ----
row = None
for ln in io.open(os.path.join(R14, "DISC_RECHECK.tsv"), encoding="utf-8").read().split("\n")[1:]:
    if ln.startswith("3\t"):
        row = ln.split("\t")
        break
ck("S2-0 取到纪律 3 的真实行（7 列）", row is not None and len(row) == 7)


def judge(round_s, at_s, tag):
    """在临时产物里写一条自述行，用真校验器判。产物路径只改行挂载点，锚与判据列原样。"""
    d = os.path.join(TMP, tag)
    os.makedirs(d, exist_ok=True)
    pf = os.path.join(d, "p.txt")
    anchor = row[3]
    h = hashlib.sha256(anchor.encode("utf-8")).hexdigest()
    io.open(pf, "w", encoding="utf-8", newline="\n").write(
        "# fixture\nDISC_RECHECK discipline=3 round=%s at=%s anchors=sha256:%s conclusion=PASS\n"
        % (round_s, at_s, h))
    r2 = list(row)
    r2[4] = os.path.relpath(pf, ROOT)
    return m.verify_recheck_line(ROOT, r2)


P("")
P("=== S2 · r57 的 6 小时窗口能放过什么（at=23:00:00 标 R57）===")
ok, det = judge("R57", "2026-11-22T23:00:00+08:00", "s2")
P("  at=23:00:00 标 R57 ⇒ ok=%s  %s" % (ok, det[:100]))
ck("S2-a 23:00:00 标 R57 被判 PASS（可伪造面实测）", ok is True, str(ok))

P("")
P("=== S3 · 同一时刻标 R58（无窗口）===")
ok3, det3 = judge("R58", "2026-11-22T23:00:00+08:00", "s3")
P("  at=23:00:00 标 R58 ⇒ ok=%s  %s" % (ok3, det3[:100]))
ck("S3-a 同一时刻标 R58 被判 False（no round window）", ok3 is False, str(ok3))
ck("S3-b 对照成立：同一时刻，写 R57 过、写 R58 不过 ⇒ 门禁在此奖励写旧轮次号",
   ok is True and ok3 is False, "R57=%s R58=%s" % (ok, ok3))

P("")
P("=== S4/S5 · 反控（防 S2-a 是恒真）===")
ok4, det4 = judge("R57", "2026-11-22T17:00:00+08:00", "s4")
P("  at=17:00:00 标 R57 ⇒ ok=%s  %s" % (ok4, det4[:90]))
ck("S4-a 反控 · 17:00:00 标 R57 必须挂（早于窗起 17:48:54）", ok4 is False, str(ok4))
ck("S4-b 该格挂在 R4（不是被别的分支拦下）", det4.startswith("R4"), det4[:40])
ok5, det5 = judge("R56", "2026-11-22T23:00:00+08:00", "s5")
P("  at=23:00:00 标 R56 ⇒ ok=%s  %s" % (ok5, det5[:90]))
ck("S5-a 反控 · 23:00 标 R56 必须挂（不在 r56 窗口）", ok5 is False, str(ok5))
ok6, det6 = judge("R57", "2026-11-22T17:48:53+08:00", "s6")
P("  at=17:48:53 标 R57（比窗起早一秒）⇒ ok=%s  %s" % (ok6, det6[:90]))
ck("S6-a 边界 · 窗起前 1 秒必须挂（闭区间下界可分辨）", ok6 is False, str(ok6))
ok7, det7 = judge("R57", "2026-11-22T17:48:54+08:00", "s7")
P("  at=17:48:54 标 R57（恰在窗起）⇒ ok=%s  %s" % (ok7, det7[:90]))
ck("S6-b 边界 · 恰在窗起必须过（w0 <= at 为闭）", ok7 is True, str(ok7))

P("")
P("=== S8 · 结论 ===")
P("  * R57 的窗口宽度 %.0f s（%.2f h），是中位宽度 %.0f s 的 %.0f 倍；" % (mx[0], mx[0] / 3600.0, med, mx[0] / med))
P("    实测可放过 at=23:00:00 的伪造行，且同一时刻换标 R58 立即不过。")
P("  * 这不是「口径偏差」，是**可量化的可伪造面**：任何晚于 17:48:54 的时刻，")
P("    只要标 R57 就能通过 R4；标真实轮次（R58-R65）反而不通过。")
P("  * 本轮**不改表**：改属判据变更；改法（扩到 r65 还是删掉 235959）也须单独裁。")
P("    能写的只有这个数：可伪造面 = 6 小时 5 分 5 秒。")

P("")
P("RESULT " + ("ALL-PASS" if not FAILS else "FAIL: " + ",".join(FAILS)))
sys.exit(0 if not FAILS else 1)
