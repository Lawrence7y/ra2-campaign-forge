# -*- coding: utf-8 -*-
"""R73 · N2-b 引出的必须追测：r55 起点「可以取哪些值」也全绿？

probeequiv_r73 的 N2-b 实测：把 r55 起点 17:41:46 改成 17:39:19 ⇒ C11 由 ok=0/fail=5
翻成 ok=5/fail=0。这意味着 **这 5 条能不能过，完全由 r55 起点这一个数决定**。
那就必须问一个不能省的问题：**能让 5 条全绿的起点值是一个点还是一个区间？**

  若只有唯一的点或极窄区间 ⇒ 该值是「被这 5 条反推出来的」，不是独立证据；
  若区间宽到「几乎所有合理取值都行」⇒ 反过来说明 C11 的 R4 对 r55 这一行**没有鉴别力**，
    它测的不是「轮次对不对」，而是「窗口端点比 at 晚不晚」。

这不是技术性细节：R58 说门禁「变绿」，R72 说「两处都修 5/5」—— 若起点可以随便取，
「绿」就不携带关于轮次归属的信息。本脚本把这句**做成测量**。

方法：单变量扫描。把 r55 起点固定为候选值集合 S 里的每个值，其余一字不动，跑门禁，
记 (起点, ok 数, fail 数)。同时扫 r55 终点做对照（预期：终点对当前 5 条无影响，
因为 at 都早于起点 —— 这正是 probeequiv N2 第一版踩的坑，此处作为**阳性对照**保留）。

反控：
  C1 起点 = 原值 174146 ⇒ 必须 ok=0 fail=5（复现基线）
  C2 起点 = 235959（晚于所有 at）⇒ 必须仍 ok=0 fail=5
  C3 终点扫描里取 174645 与 174644 两值 ⇒ ok 数必须相同（证终点确实无鉴别力）
  C4 扫到 at 恰好等于起点（173919）⇒ 边界必须为**闭区间**（w0 <= at），即 ok=5
"""
import io, os, sys, types, re

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

FAILS = []


def P(s=""):
    print(s)


def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c:
        FAILS.append(n)
    return c


def run_mem(cd_src, rv_src):
    m = types.ModuleType("recheck_verify")
    m.__file__ = os.path.join(R14, "recheck_verify.py")
    exec(compile(rv_src, m.__file__, "exec"), m.__dict__)
    sys.modules["recheck_verify"] = m
    g = {"__name__": "__main__", "__file__": os.path.join(R14, "check_disc.py")}
    buf = []
    g["print"] = lambda *a, **k: buf.append(" ".join(str(x) for x in a))
    code = None
    try:
        exec(compile(cd_src, g["__file__"], "exec"), g)
    except SystemExit as e:
        code = e.code
    finally:
        sys.modules.pop("recheck_verify", None)
    txt = "\n".join(buf) + "\n"
    mm = re.search(r"ok=(\d+) fail=(\d+) frozen-unverifiable=(\d+) claims-none=(\d+)", txt)
    ok, fail = (int(mm.group(1)), int(mm.group(2))) if mm else (-1, -1)
    return ok, fail, txt


live_cd = io.open(os.path.join(R14, "check_disc.py"), encoding="utf-8").read()
live_rv = io.open(os.path.join(R14, "recheck_verify.py"), encoding="utf-8").read()
R55 = "(55, '174146', '174645'"
ck("R55 模板行存在", R55 in live_rv)

base_ok, base_fail, _ = run_mem(live_cd, live_rv)
P("=== S0 · 基线 ===")
P("  live: ok=%d fail=%d" % (base_ok, base_fail))
ck("S0-a 基线复现 ok=0 fail=5", (base_ok, base_fail) == (0, 5), "%d/%d" % (base_ok, base_fail))

# ---- S1 · 起点扫描 ----
# R73 自错修正（第四次）：第一版候选集合里**没有任何早于 173919 的值**，于是「全绿只有 1 个」
# 是采样遗漏的产物，不是发现。判据是 w0 <= at ⇒ 任何 w0 <= 17:39:19 都应全绿。
# 补入更早的值（含 00:00:00、各轮快照之前的时刻）才能测出「绿区"的下界在哪」。
STARTS = [
    ("000000", "= 当日 00:00:00（极端早）"),
    ("112234", "= before_r35 11:22:34（早得很）"),
    ("162803", "= before_r53 16:28:03"),
    ("173400", "= before_r54 17:34:00"),
    ("173918", "= 17:39:18（比最早 at 早一秒）"),
    ("173919", "= 最早那 4 条的 at（17:39:19）"),
    ("173920", "= 17:39:20（比最早 at 晚一秒）"),
    ("174002", "= 第 5 条的 at（17:40:02）"),
    ("174003", "= 17:40:03（晚于全部 at 一秒）"),
    ("174146", "= 原值 before_r55（基线）"),
    ("174408", "= before_r55add 17:44:08"),
    ("174645", "= before_r56 17:46:45"),
    ("174854", "= before_r57 17:48:54"),
    ("235959", "= 当日上界"),
]
P("")
P("=== S1 · r55 起点扫描（终点固定 174645）===")
P("  %-8s %-9s %-9s  %s" % ("起点", "ok", "fail", "说明"))
start_res = {}
for s, note in STARTS:
    mut = live_rv.replace(R55, "(55, '%s', '174645'" % s)
    ck("  变异可构造 %s" % s, mut != live_rv or s == "174146")
    ok, fail, _ = run_mem(live_cd, mut)
    start_res[s] = (ok, fail)
    P("  %-8s ok=%-7d fail=%-7d  %s" % (s, ok, fail, note))

green = [s for s, (o, f) in start_res.items() if (o, f) == (5, 0)]
red = [s for s, (o, f) in start_res.items() if (o, f) == (0, 5)]
P("")
P("  [结果] 全绿起点 %d 个：%s" % (len(green), green))
P("  [结果] 全红起点 %d 个：%s" % (len(red), red))
ck("C1 反控 · 原值 174146 ⇒ ok=0 fail=5", start_res["174146"] == (0, 5), str(start_res["174146"]))
ck("C2 反控 · 235959 ⇒ 仍 ok=0 fail=5", start_res["235959"] == (0, 5), str(start_res["235959"]))
ck("C4 边界 · 起点 == 最早 at（173919）⇒ 闭区间，应 ok=5", start_res["173919"] == (5, 0),
   str(start_res["173919"]))
ck("S1-a 起点扫描确实翻转判据（存在全绿值）", len(green) >= 1, str(green))
ck("S1-b 「全绿」不是唯一值（否则该值可被反推为唯一解）", len(green) >= 2,
   "%d 个全绿起点：%s" % (len(green), green))
ck("S1-c 绿区下界开放（000000 也全绿 ⇒ 无下界约束）", start_res["000000"] == (5, 0),
   str(start_res["000000"]))
ck("S1-d 临界点可分辨（173920 起就不再全绿 ⇒ 上界恰在最早 at）",
   start_res["173920"] != (5, 0), str(start_res["173920"]))

# ---- S2 · 终点扫描（阳性对照：应完全无影响）----
P("")
P("=== S2 · r55 终点扫描（起点固定原值 174146，阳性对照）===")
ENDS = ["174645", "174644", "174600", "235959", "173919"]
end_res = {}
for e in ENDS:
    mut = live_rv.replace(R55, "(55, '174146', '%s'" % e)
    ok, fail, _ = run_mem(live_cd, mut)
    end_res[e] = (ok, fail)
    P("  终点 %-8s ok=%-4d fail=%-4d" % (e, ok, fail))
ck("C3 反控 · 终点 174645 与 174644 结果相同（终点对当前 5 条无鉴别力）",
   end_res["174645"] == end_res["174644"], "%s vs %s" % (end_res["174645"], end_res["174644"]))
ck("S2-a 全部终点取值都 ok=0 fail=5（终点完全不影响这 5 条）",
   all(v == (0, 5) for v in end_res.values()), str(end_res))

# ---- S3 · 结论边界 ----
P("")
P("=== S3 · 结论（必须原样写进四件套）===")
P("  ① 能让 5 条全绿的 r55 起点是一个**开下界的半轴**（实测 %d 个全绿，从 000000 到 173919），" % len(green))
P("     不是唯一的点 ⇒ 「绿」不能反推出 r55 起点该取哪个值。")
P("  ② r55 的**终点**对当前 5 条完全无鉴别力（%d 个取值，结果全同）" % len(ENDS))
P("  ③ 因此本轮能说的只有：C11 的 R4 在 r55 这一行上，等价于"
  "「at 不早于起点」，**不**等价于「轮次归属正确」。")
P("  ④ 不能说的：起点该取哪个值、改表还是改行。这两条仍按 R72 C3 记「不可区分」。")

P("")
P("RESULT " + ("ALL-PASS" if not FAILS else "FAIL: " + ",".join(FAILS)))
sys.exit(0 if not FAILS else 1)
