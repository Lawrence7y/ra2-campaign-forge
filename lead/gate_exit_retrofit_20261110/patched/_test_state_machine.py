# -*- coding: utf-8 -*-
"""D-13b 纯逻辑状态机离线单测（合成时序 / 零真机 / 零采样实现 / 零系统接口）。

授权：RULING_D27.md:8、:32（D-13b 上限 = 离线设计 + 纯模型/合成数据单测）。
写域：lead/d13b_design_20261106/（TASK.md:7）。
运行：python -I -X utf8 <绝对路径>/_test_state_machine.py > <绝对路径>/_test_out.txt

纪律：
- 本文件只用标准库 importlib.util（按绝对路径加载同目录状态机模块，非系统接口、
  非采样 API），不含 §7 专项 A 的任何关键词（由门禁 check_d13b.py 与本次外部
  grep 实跑核验，见交付说明）。-I 隔离模式下脚本目录不在 sys.path，故用
  spec_from_file_location 显式加载，不依赖 cwd。
- 状态机源码仅以 open(...).read() 作只读文本用于内省检查；本文件不把任何外部
  数据当作代码执行（无 exec / eval / compile）。
- 时钟 t_ms 是合成逻辑时钟，不是真实系统时间；系统调度时延、扰动、资源释放、
  真实栈可解析性一律 [未验]（RULING_D27.md:42、:67；STALL_EVENT_DEFINITION.md:216、:218）。
- <50ms / <=20ms / <10ms / 最多 3 次 / >=3.0s 冷却 / 100ms 清理 / rc=0 全为
  [待论证指标]，模型通过不验证真实运行上界、不保证 rc=0（RULING_D27.md:44、:67）。
- ★ 不写「长停不存在」；正确表述：当前 97 窗按现规则保留的事件中未识别到 >=1s 平台，
  语义漏检及跨场景代表性未闭合（RULING_D27.md:52）。
- ★ >1s 只作 [保守停止预算]，不作结束态语义真值（RULING_D27.md:44、TASK.md:53、:66）。
- ★ n=1681（保留标签数）与 n=1737（full97 全部候选，含 56 个 false）不是同口径，
  不得直接对照（RULING_D27.md:48）；本单测不消费这两个数。
"""

import importlib.util

# ---- 按绝对路径显式加载状态机（-I 隔离模式下不依赖 sys.path / cwd）----------
_DIR = __file__.replace("\\", "/").rsplit("/", 1)[0]
_SM_PATH = _DIR + "/_state_machine.py"
_SPEC = importlib.util.spec_from_file_location("_state_machine_under_test", _SM_PATH)
_SM = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_SM)

# 只读文本，仅用于 §0 的内省检查（不执行、不注入）
_SM_SRC = open(_SM_PATH, encoding="utf-8").read()

SM = _SM.CaptureStateMachine
ST_ARMED = _SM.ST_ARMED
ST_COOLDOWN = _SM.ST_COOLDOWN
ST_DISARMED_BUDGET = _SM.ST_DISARMED_BUDGET
ST_EXITED = _SM.ST_EXITED
SEM_UNKNOWN = _SM.SEM_UNKNOWN
SEM_RECOVERED = _SM.SEM_RECOVERED
SEM_ANOMALY_REWIND = _SM.SEM_ANOMALY_REWIND
SEM_BUDGET_ONLY = _SM.SEM_BUDGET_ONLY
SEMANTIC_VALUES = _SM.SEMANTIC_VALUES
KIND_STALL = _SM.KIND_STALL
KIND_RECOVERED = _SM.KIND_RECOVERED
KIND_WINDOW_END = _SM.KIND_WINDOW_END
KIND_WINDOW_GAP = _SM.KIND_WINDOW_GAP
KIND_REWIND = _SM.KIND_REWIND
KIND_UNKNOWN = _SM.KIND_UNKNOWN
KIND_TERMINATE = _SM.KIND_TERMINATE
UNVERIFIED = _SM.UNVERIFIED
PARAM_BASIS = _SM.PARAM_BASIS

_PASS = 0
_FAIL = 0


def check(cond, label, detail=""):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  [PASS] " + label + ((" | " + str(detail)) if detail else ""))
    else:
        _FAIL += 1
        print("  [FAIL] " + label + ((" | " + str(detail)) if detail else ""))


def section(title):
    print("")
    print("==== " + title + " ====")


def obs(t, win, sid, dur, kind=KIND_STALL, frame=10):
    return {"t_ms": t, "window": win, "stall_id": sid, "frame": frame,
            "duration_ms": dur, "kind": kind}


def reasons(actions):
    return [a["reason"] for a in actions]


print("=" * 78)
print("D-13b 纯逻辑状态机离线单测（合成时序）")
print("命令: python -I -X utf8 " + __file__.replace("\\", "/"))
print("状态机: " + _SM_PATH)
print("口径提醒: n=1681 保留标签数 / n=1737 full97 全部候选(含56 false) 非同口径，不对照")
print("未验提醒: 系统时延/扰动/资源释放/真实栈可解析性 [未验]；指标 [待论证指标]")
print("=" * 78)

# ---------------------------------------------------------------------------
section("0 结构性不变量（纯逻辑 / 反扫描 / 口径诚实）")
check(not any(ln.lstrip().startswith(("import ", "from "))
              for ln in _SM_SRC.splitlines()),
      "状态机源码无任何 import / from 语句（零系统接口）",
      "lines=%d" % len(_SM_SRC.splitlines()))
_bad_sem = ("MATCH_ENDED", "TERMINAL_FREEZE", "ENDED", "LONG_STALL_ABSENT", "长停不存在")
check(all(v not in _bad_sem for v in SEMANTIC_VALUES),
      "语义取值集合不含任何『结束态 / 终局 / 长停不存在』真值",
      "SEMANTIC_VALUES=%s" % (SEMANTIC_VALUES,))
check("[保守停止预算]" in _SM_SRC and "[待论证指标]" in _SM_SRC
      and "[未验]" in _SM_SRC and "[估算]" in _SM_SRC,
      "源码含 [保守停止预算] / [待论证指标] / [未验] / [估算] 四类定位标记")
check("语义漏检及跨场景代表性未闭合" in _SM_SRC and "不得直接对照" in _SM_SRC,
      "源码含 D-27 三条裁决更正的正确表述（不写长停不存在 / 口径不对照）")
check(len(UNVERIFIED) >= 6 and all(k in " ".join(UNVERIFIED)
                                   for k in ("系统", "扰动", "资源", "栈")),
      "未验清单覆盖系统时延 / 扰动 / 资源释放 / 栈可解析性四项",
      "items=%d" % len(UNVERIFIED))
check(all("[待论证指标]" in v for v in
          (PARAM_BASIS["quota_cap"], PARAM_BASIS["cooldown_ms"],
           PARAM_BASIS["budget_stop_ms"], PARAM_BASIS["exit_budget_ms"])),
      "配额/冷却/停止预算/退出预算四项参数均标 [待论证指标]")

# ---------------------------------------------------------------------------
section("1 窗内配额上限（quota_cap=3 [待论证指标]）")
m = SM(quota_cap=3, cooldown_ms=0.0)
res = m.run([obs(100 * i, "w1", "Q%d" % i, 150.0) for i in range(5)])
_caps = sum(1 for a in res if a["decision"] == "CAPTURE")
check(_caps == 3, "单窗 5 个不同停滞 -> 恰好 3 次 CAPTURE", "captures=%d" % _caps)
check(all(a["reason"] == "QUOTA_EXHAUSTED" for a in res[3:]),
      "配额耗尽后 2 次均为 QUOTA_EXHAUSTED", "reasons=%s" % reasons(res[3:]))
check(m.window_capture_count == 3, "窗内捕获计数封顶 3", "count=%d" % m.window_capture_count)
res2 = m.run([obs(1000 + i, "w2", "R%d" % i, 150.0) for i in range(3)])
check(sum(1 for a in res2 if a["decision"] == "CAPTURE") == 3,
      "换窗后窗内配额归零，重新允许 3 次（dedup 注册表不归零）")

# ---------------------------------------------------------------------------
section("2 冷却期与冷却回退（cooldown_ms=3000 [待论证指标], >= 边界）")
m = SM(quota_cap=10, cooldown_ms=3000.0)
a1 = m.process(obs(0, "w1", "C1", 150.0))
check(a1["decision"] == "CAPTURE" and a1["state_after"] == ST_COOLDOWN,
      "首次捕获后进入 COOLDOWN")
a2 = m.process(obs(1000, "w1", "C2", 150.0))
check(a2["decision"] == "SKIP" and a2["reason"] == "COOLDOWN",
      "冷却期内（t=1000ms）抑制捕获")
a3 = m.process(obs(2999, "w1", "C3", 150.0))
check(a3["decision"] == "SKIP" and a3["reason"] == "COOLDOWN",
      "冷却未满 1ms（t=2999ms）仍抑制")
a4 = m.process(obs(3000, "w1", "C4", 150.0))
check(a4["decision"] == "CAPTURE" and a4["state_before"] == ST_ARMED,
      "冷却期满（t=3000ms, >= 边界）回退 COOLDOWN -> ARMED 并放行",
      "state_before=%s" % a4["state_before"])
m2 = SM(quota_cap=10, cooldown_ms=3000.0)
m2.process(obs(0, "w1", "D1", 150.0))
b = m2.process(obs(-50, "w1", "D2", 150.0))
check(b["reason"] == "COOLDOWN",
      "合成时钟回退/乱序（t=-50ms）不误判冷却到点 [回退鲁棒性]")

# ---------------------------------------------------------------------------
section("3 停止与回退转换 + 正常退出路径")
m = SM(quota_cap=3, cooldown_ms=0.0)
a = m.process(obs(0, "w1", "L1", 1050.0))
check(a["decision"] == "SKIP" and a["reason"] == "BUDGET_STOP_CONSERVATIVE",
      ">1s 观察 -> 保守停止预算，SKIP（非结束态语义真值）")
check(a["state_after"] == ST_DISARMED_BUDGET and a["semantic"] == SEM_BUDGET_ONLY,
      "状态 -> DISARMED_BUDGET；语义 -> BUDGET_STOP_ONLY",
      "semantic=%s" % a["semantic"])
check(a["semantic"] not in _bad_sem, "保守停止不写任何结束/终局语义")
b = m.process(obs(1, "w1", "L2", 150.0))
check(b["decision"] == "SKIP" and b["reason"] == "BUDGET_STOP_CONSERVATIVE",
      "保守停止态下普通短停仍少采（不会把长停误判为不存在）")
c = m.process(obs(2, "w2", "L3", 150.0))
check(c["decision"] == "CAPTURE" and c["state_before"] == ST_ARMED,
      "[回退A] 新测量窗按窗界解除保守停止预算 DISARMED_BUDGET -> ARMED")
m2 = SM(quota_cap=3, cooldown_ms=0.0)
m2.process(obs(0, "w1", "L1", 1050.0))
r = m2.process(obs(1, "w1", "L1", 0.0, kind=KIND_RECOVERED))
check(r["semantic"] == SEM_RECOVERED and r["state_after"] == ST_ARMED,
      "[回退B] 正向恢复证据解除保守停止预算；语义写 RECOVERED（非终局）")
c2 = m2.process(obs(2, "w1", "L4", 150.0))
check(c2["decision"] == "CAPTURE", "[回退B] 解除后恢复正常捕获能力")
m3 = SM(quota_cap=3, cooldown_ms=0.0)
m3.process(obs(0, "w1", "E1", 150.0))
x = m3.process(obs(1, "w1", None, 0.0, kind=KIND_TERMINATE))
check(x["decision"] == "EXIT" and x["state_after"] == ST_EXITED,
      "[正常退出路径] 显式请求 -> EXIT / EXITED（不是由未观察到恢复推断）")
check(x["semantic"] == SEM_UNKNOWN, "正常退出不写结束态语义真值")
y = m3.process(obs(2, "w1", "E2", 150.0))
check(y["reason"] == "EXITED_IDEMPOTENT", "EXITED 后幂等，不再捕获")
check(m3.summary()["exit_budget_verified"] is False,
      "100ms 零残留 / rc=0 标为未验，模型不背书 [待论证指标][未验]")

# ---------------------------------------------------------------------------
section("4 事件匹配判定 / 同一停滞多次观察去重")
m = SM(quota_cap=10, cooldown_ms=0.0)
seq = [
    obs(0, "w1", "SAME", 50.0),    # 门槛下
    obs(10, "w1", "SAME", 150.0),  # 首次成功捕获
    obs(20, "w1", "SAME", 180.0),  # 重复
    obs(30, "w2", "SAME", 200.0),  # 跨窗重复
    obs(40, "w2", "SAME", 250.0),  # 再重复
]
res = m.run(seq)
check(res[0]["reason"] == "BELOW_THRESHOLD", "门槛下观察不捕获且不占位")
check(res[1]["decision"] == "CAPTURE", "同一停滞首次达门槛 -> 1 次 CAPTURE")
check(all(a["reason"] == "DUP_ALREADY_CAPTURED" for a in res[2:]),
      "其后 3 次（含跨窗）全部 DUP_ALREADY_CAPTURED", "reasons=%s" % reasons(res[2:]))
rep = m.dedup_report()
check(rep["distinct_stalls"] == 1 and rep["raw_stall_observations"] == 5
      and rep["captures"] == 1,
      "5 次原始观察 -> 1 个物理停滞 / 1 次捕获",
      "report=%s" % {k: rep[k] for k in ("distinct_stalls", "raw_stall_observations", "captures")})
check(rep["per_stall"][0]["windows"] == ["w1", "w2"],
      "跨窗停滞合并为同一身份（避开 _stall_probe.py:169-189 逐窗独立处理）")
z = m.process(obs(50, "w2", "OTHER", 150.0))
check(z["decision"] == "CAPTURE", "去重按物理身份而非全局抑制，另一停滞仍可捕获")

# ---------------------------------------------------------------------------
section("5 六类场景（合成时序）与既有缺陷反向验证")
# (a) 100-200ms 平台
ma = SM(quota_cap=3, cooldown_ms=0.0)
ra = ma.process(obs(0, "w1", "A1", 150.0))
check(ra["decision"] == "CAPTURE",
      "100-200ms 平台：模型逻辑上授予 CAPTURE")
print("       NOTE: 这只是逻辑放行；真实剩余覆盖受端到端预算约束，"
      "系统时延/扰动 [未验]，实测覆盖 [未验]（BUDGET_MODEL.json 合计 152.5ms >= 中位 129.93ms）")

# (b) 窗末截断：开放停滞携带到后续窗，不无条件关闭
mb = SM(quota_cap=3, cooldown_ms=0.0)
mb.process(obs(0, "w1", "B1", 150.0))
e = mb.process(obs(1, "w1", None, 0.0, kind=KIND_WINDOW_END))
check(e["decision"] == "OBSERVE" and e["reason"] == "WINDOW_END_CARRIED",
      "窗末截断 -> 保持开放，不无条件判 false/continue")
check(e["semantic"] == SEM_UNKNOWN and e["open_stalls"] >= 1,
      "窗末截断语义 UNKNOWN，开放停滞数=%d" % e["open_stalls"])
rb = mb.process(obs(2, "w2", "B1", 0.0, kind=KIND_RECOVERED))
check(rb["semantic"] == SEM_RECOVERED and "B1" not in mb.summary()["open_stalls"],
      "后续窗收到正向恢复 -> RECOVERED 并解析（不看后续窗的缺陷已被避开）")

# (c) 全窗后恢复 / 未观察到恢复 != 结束
mc = SM(quota_cap=3, cooldown_ms=0.0)
mc.process(obs(0, "w1", "F1", 150.0))
u = mc.process(obs(1, "w2", None, 0.0, kind=KIND_WINDOW_GAP))
check(u["reason"] == "WINDOW_GAP_UNKNOWN" and u["semantic"] == SEM_UNKNOWN,
      "缺窗/未观察到恢复 -> UNKNOWN，绝不写终局冻结")
check("F1" in mc.summary()["open_stalls"],
      "未观察到恢复时停滞保持开放登记（不判 match_ended_terminal_freeze）")

# (d) 帧号回滚
md = SM(quota_cap=3, cooldown_ms=0.0)
rw = md.process(obs(0, "w1", "G1", 150.0, kind=KIND_REWIND))
check(rw["decision"] == "SKIP" and rw["reason"] == "FRAME_REWIND_ANOMALY"
      and rw["semantic"] == SEM_ANOMALY_REWIND,
      "帧号回滚 -> 标异常并抑制；不宣称已证非真实停滞（RULING_D27.md:48）")

# (e) 未知状态
me = SM(quota_cap=3, cooldown_ms=0.0)
uk = me.process(obs(0, "w1", "H1", 150.0, kind=KIND_UNKNOWN))
check(uk["decision"] == "SKIP" and uk["reason"] == "UNKNOWN_INSUFFICIENT_DATA"
      and uk["semantic"] == SEM_UNKNOWN,
      "数据不足 -> 诚实输出 UNKNOWN，抑制捕获，不改状态")

# (f) >1s 一律不捕获，但也不删除登记（少采而非不存在）
mf = SM(quota_cap=10, cooldown_ms=0.0)
resf = mf.run([obs(i, "w1", "X%d" % i, 1000.0 + i) for i in range(5)])
check(all(a["decision"] != "CAPTURE" for a in resf),
      ">1s 观察 5 次全部不捕获（保守停止预算，只少采）")
check(len(mf.summary()["open_stalls"]) == 5,
      "保守停止不删除停滞登记 -> 不把长停误判为不存在（TASK.md:66）")
check(all(a["semantic"] not in _bad_sem for a in resf),
      ">1s 观察不产出任何结束态 / 长停不存在语义真值")

print("")
print("       NOTE: 真实栈格式与可解析性、系统调度时延、采样扰动、资源释放时序")
print("             均为 [未验]；本单测只验证纯逻辑状态转换，不验证真实运行上界。")

print("")
print("=" * 78)
print("PASS=%d FAIL=%d" % (_PASS, _FAIL))


# ---------- 出口改造（纯追加：以上 1-273 行与原件逐字节一致，未改一字） ----------
# 原型：lead/dtrigger_compare_20261107/_check_dtrigger.py:31-35 + :226-228
# 原件对自身的检查 = :62-69 的 check(cond, label, detail)，全文 43 次调用
#   （:96-265）：cond 真 -> :65 _PASS += 1 打印 "  [PASS] "；cond 假 ->
#   :68 _FAIL += 1 打印 "  [FAIL] "；:273 打印 "PASS=%d FAIL=%d" 汇总。
#   无 assert、无写盘、无退出码（全文止于 :273）。:219-220 / :267-269 的
#   NOTE 是对被测状态机的 [未验] 注记，不是本脚本的检查结果，不纳入聚合。
# 判据：_FAIL == 0 即原件自身的「43 项检查全部通过」，与 :273 摘要同源。
# 下面以 ok 作合取聚合变量，把该判据与 §0 六条结构性自检（逐字复用原件
# 表达式、只引用仍存活的模块级只读全局量）逐项合取；不重跑状态机、不改写
# 任何原有检查/打印/判定式。原有 43 行 [PASS]/[FAIL] 与 :273 摘要一字不动。
# 本件无 if __name__ == "__main__" 块、全库无 Python import 方（rg 实跑），
# 故不是库本体；只新增一个全局名 ok，不覆盖任何调用方同名符号。
ok = True
ok = ok and bool(_FAIL == 0)                 # 权威项：覆盖全部 43 项检查
ok = ok and bool(not any(ln.lstrip().startswith(("import ", "from "))
                         for ln in _SM_SRC.splitlines()))
ok = ok and bool(all(v not in _bad_sem for v in SEMANTIC_VALUES))
ok = ok and bool("[保守停止预算]" in _SM_SRC and "[待论证指标]" in _SM_SRC
                 and "[未验]" in _SM_SRC and "[估算]" in _SM_SRC)
ok = ok and bool("语义漏检及跨场景代表性未闭合" in _SM_SRC
                 and "不得直接对照" in _SM_SRC)
ok = ok and bool(len(UNVERIFIED) >= 6
                 and all(k in " ".join(UNVERIFIED)
                         for k in ("系统", "扰动", "资源", "栈")))
ok = ok and bool(all("[待论证指标]" in v for v in
                     (PARAM_BASIS["quota_cap"], PARAM_BASIS["cooldown_ms"],
                      PARAM_BASIS["budget_stop_ms"], PARAM_BASIS["exit_budget_ms"])))
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
