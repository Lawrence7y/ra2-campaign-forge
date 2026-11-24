# -*- coding: utf-8 -*-
"""R73 · 自测 5/5 的边界核查：修好路径后 selftest 从 4/5 变 5/5，说明什么、不说明什么。

事实（本轮实测）：修路径前 python3 recheck_verify.py --self-test 报 SELFTEST FAIL (4/5)，
唯一挂的是 POS 正控（reason = R1 product file missing）；修好后报 SELFTEST PASS (5/5)。

危险之处：这正是「把一条前置缺陷修好，门禁自测就变绿」的样板。
若就此写「门禁已通过自测」= 把 POS 修复当成判据正确性的证据。
R71 §CY9 已证 selftest 是**自证循环**（样本与表由同一行为者写）。

本脚本要做的不是重复那个结论，而是把它**变成对 selftest 本身的可测陈述**：
  T1 修好路径后 5/5 是否可重复（是 ⇒ 与时钟/随机无关）
  T2 把窗口表整个清空 ⇒ 正控必须挂（若仍 5/5，则 pos 根本没走窗口分支 = 同 R72 零信息格）
  T3 把窗口表整体平移 +1 小时 ⇒ 正控必须挂（若仍 5/5，则自测不锚定任何时刻）
  T4 把 DISC_ESTABLISH.tsv 换成立条时刻 = 正控 at 之后 ⇒ 正控必须挂（R3 分支被触达）
  T5 把正确答案与期望值同时改（即"改样本去配合表"）⇒ 是否仍 5/5
      —— 这一条是自证循环的核心：若 T5 仍绿，"自测通过"不携带外部信息。

全部在内存/temp 中做，不动 live 任何文件。
"""
import io, os, sys, types, tempfile, shutil, atexit, re

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

FAILS = []
TMP = tempfile.mkdtemp(prefix="r73self_")
atexit.register(lambda d=TMP: shutil.rmtree(d, ignore_errors=True))


def P(s=""):
    print(s)


def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c:
        FAILS.append(n)
    return c


def run_selftest(rv_src, establish_text=None, tag="x"):
    """在内存里跑 recheck_verify._self_test，返回 (allok, npass, ntot, 明细行)。"""
    d = os.path.join(TMP, tag)
    os.makedirs(d, exist_ok=True)
    # 把模块需要的三个伴生文件放进沙箱：DISC_RECHECK.tsv 与 DISC_ESTABLISH.tsv
    shutil.copy(os.path.join(R14, "DISC_RECHECK.tsv"), os.path.join(d, "DISC_RECHECK.tsv"))
    if establish_text is None:
        shutil.copy(os.path.join(R14, "DISC_ESTABLISH.tsv"), os.path.join(d, "DISC_ESTABLISH.tsv"))
    else:
        io.open(os.path.join(d, "DISC_ESTABLISH.tsv"), "w", encoding="utf-8", newline="\n").write(establish_text)
    # _HERE 必须指向沙箱（模块用它定位两个 tsv）；root 仍指真树（产物路径要能解析）
    src = rv_src.replace(
        "_HERE = os.path.dirname(os.path.abspath(__file__))",
        "_HERE = %r" % d)
    m = types.ModuleType("rv_" + tag)
    m.__file__ = os.path.join(d, "recheck_verify.py")
    exec(compile(src, m.__file__, "exec"), m.__dict__)
    buf = []
    real = m.__dict__.get("print", print)
    m.__dict__["print"] = lambda *a, **k: buf.append(" ".join(str(x) for x in a))
    try:
        allok = m._self_test()
    except Exception as e:
        return False, 0, 0, ["EXCEPTION %s: %s" % (type(e).__name__, e)]
    finally:
        m.__dict__["print"] = real
    txt = "\n".join(buf)
    mm = re.search(r"SELFTEST (PASS|FAIL) \((\d+)/(\d+)\)", txt)
    np_, nt_ = (int(mm.group(2)), int(mm.group(3))) if mm else (0, 0)
    return allok, np_, nt_, buf


live_rv = io.open(os.path.join(R14, "recheck_verify.py"), encoding="utf-8").read()

P("=== T1 · 修好后 5/5 且可重复 ===")
a1 = run_selftest(live_rv, tag="t1a")
a2 = run_selftest(live_rv, tag="t1b")
P("  跑一次 %d/%d  跑二次 %d/%d" % (a1[1], a1[2], a2[1], a2[2]))
ck("T1-a 正控全过（5/5）", a1[0] and a1[1] == 5 and a1[2] == 5, "%d/%d" % (a1[1], a1[2]))
ck("T1-b 两次运行结果相同（无时钟/随机）", (a1[1], a1[2]) == (a2[1], a2[2]))

P("")
P("=== T2 · 窗口表整个清空 ⇒ 正控必须挂（否则 POS 没走窗口分支）===")
src_empty = re.sub(r"ROUND_WINDOWS\[_no\] = \(_hhmmss\(_s\), _hhmmss\(_e\), _sf, _ef\)",
                   "ROUND_WINDOWS[_no] = (_hhmmss(_s), _hhmmss(_e), _sf, _ef)\nROUND_WINDOWS.clear()",
                   live_rv)
ck("T2-0 变异锚点存在", src_empty != live_rv)
b = run_selftest(src_empty, tag="t2")
P("  清空窗口表后 %d/%d  allok=%s" % (b[1], b[2], b[0]))
ck("T2-a 窗口表清空 ⇒ 正控挂（POS 命中 R4 分支）", b[1] < a1[1], "%d/%d vs %d/%d" % (b[1], b[2], a1[1], a1[2]))

P("")
P("=== T3 · 窗口表整体 +1 小时 ⇒ 正控必须挂（自测锚定时刻）===")
# 把所有 'HHMMSS' 端点整体挪 +1 小时：改 _hhmmss 的解析，加 3600 秒
src_shift = live_rv.replace(
    "    return datetime(y, mo, d, h, m, sec, tzinfo=_TZ)",
    "    return datetime(y, mo, d, h, m, sec, tzinfo=_TZ) + timedelta(hours=1)   # R73 变异")
ck("T3-0 变异锚点存在", src_shift != live_rv)
c = run_selftest(src_shift, tag="t3")
P("  整体 +1h 后 %d/%d" % (c[1], c[2]))
ck("T3-a 整体 +1 小时 ⇒ 正控挂（证自测锚定具体时刻）", c[1] < a1[1], "%d/%d" % (c[1], c[2]))

P("")
P("=== T4 · 立条时刻改到正控 at 之后 ⇒ 正控必须挂（R3 分支被触达）===")
est = io.open(os.path.join(R14, "DISC_ESTABLISH.tsv"), encoding="utf-8").read().split("\n")
out = [est[0]]
for ln in est[1:]:
    if not ln.strip():
        continue
    c_ = ln.split("\t")
    if c_[0].strip() == "11":
        # R73 自错修正（第五次）：初版取 16:19:59，那是 at(16:20:00) **之前**，
        # 于是 at > est_at ⇒ R3 正常通过、T4 恒绿。判据是 at <= est_at 才挂 ⇒ 必须取 at **之后**。
        c_[3] = "2026-11-22T16:20:01+08:00"      # 晚于正控 at 一秒 ⇒ at <= est ⇒ 挂
    out.append("\t".join(c_))
est_mut = "\n".join(out) + "\n"
ck("T4-0 立条表确实改了第 11 行", "16:20:01" in est_mut)
d = run_selftest(live_rv, establish_text=est_mut, tag="t4")
P("  立条时刻推到 at 之后 %d/%d" % (d[1], d[2]))
ck("T4-a 立条时刻晚于 at ⇒ 正控挂（R3 分支被触达）", d[1] < a1[1], "%d/%d" % (d[1], d[2]))

P("")
P("=== T5 · 自证循环的核心：改样本去配合表 ⇒ 是否仍 5/5 ===")
# 自证循环的定义：样本与表由同一行为者写。这里把**正控样本**的 at 挪到窗口外
# （模拟"改了窗口表之后，同时改样本让自测继续绿"）。若仍 5/5，则"自测绿"不含外部信息。
src_t5 = live_rv.replace("at=2026-11-22T16:20:00+08:00", "at=2026-11-22T09:00:00+08:00")
ck("T5-0 样本 at 已挪出窗口", src_t5 != live_rv)
e = run_selftest(src_t5, tag="t5")
P("  样本挪出窗口后 %d/%d" % (e[1], e[2]))
ck("T5-a 只改样本、不改期望 ⇒ 正控必须挂（期望值是硬写的，不是跟着样本算的）",
   e[1] < a1[1], "%d/%d" % (e[1], e[2]))

P("")
P("=== S6 · 结论 ===")
P("  * T1 5/5 可重复；T2/T3/T4 三个方向的扰动都能把正控打挂 ⇒")
P("    修好路径后的 5/5 **不是**恒真，它确实走过了 R1→R3→R4→R5→R6 五个分支。")
P("  * T5 说明期望值是**硬编码**在自测里的，不是从表反算的 ⇒ 至少排除了")
P("    「期望值跟着表自动变」这一种最廉价的恒真。")
P("  * **但**这不推翻 R71 §CY9：自测的样本(at)与窗口表仍由同一行为者写，")
P("    T5 只是把「样本挪走会挂」测出来，**没有**证明窗口表本身取对了。")
P("    ⇒ 本轮能写的是：selftest 修好后是**非恒真的**、覆盖五个分支；")
P("      不能写的是：selftest 通过 ⇒ 窗口口径正确。")

P("")
P("RESULT " + ("ALL-PASS" if not FAILS else "FAIL: " + ",".join(FAILS)))
sys.exit(0 if not FAILS else 1)
