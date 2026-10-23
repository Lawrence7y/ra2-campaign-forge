"""H-6 定谳器：`wait_returncode` 的 1 vs 0 到底是什么。

## 登记原文（台账 §397 §八 H-6）

> **H-6（新，观察）：四趟 `wait_returncode` 不一致 —— A/B = 1，C/L3 = 0。**
> `wait_returncode` 来自 `proc.terminate()` 后 `proc.wait()` 的返回值。
> 1 vs 0 说明两类趟的退出路径不同，但**本轮未查明** `terminate()` 打在
> 「还活着」与「已退出」的进程上分别返回什么，故只登记现象。

## 本件怎么判

**不去读文档，直接做实验**：起真子进程，两种状态各跑一遍，
观测 `terminate()` 的抛异常行为与 `wait()` 的返回值。

★ 关键：这条判据的输入是**本机 CPython 的真实行为**，
不是我对文档的理解。代码在这里，行为在 `--probe` 里实测。

## 为什么这件事重要（超出"登记现象"）

`terminate_owned_process`（harness `:1369`）的实现是：

    try:
        proc.terminate()
        rec.add("TERM", "terminate_sent", True, ...)   # ★ 只要不抛就算 True
    except Exception:
        rec.add("TERM", "terminate_sent", False, ...)
        return False
    ...
    returncode = proc.wait(timeout=10)

而 CPython 3.12 的 `Popen.terminate()` 在进程**已死**时是**静默返回**的
（源码见本文件 `--show-src`）。⇒ `terminate_sent=True` 只证明
"调用没抛异常"，**不证明"终止动作生效"**。
"""
import json
import subprocess
import sys
import time
from pathlib import Path

TRIP_ROOT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
                 r"\CONTINUE_20261003\lead\qc161_u0400_trip")

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("[%s] %s  %s" % ("PASS" if ok else "FAIL", name, detail))


# ---------------------------------------------------------------- 实验原语

def spawn_exits_with(code, wait_s=1.0):
    """起一个会自行以 `code` 退出的子进程，等它退完再返回。"""
    p = subprocess.Popen([sys.executable, "-c",
                          "import sys; sys.exit(%d)" % code])
    time.sleep(wait_s)
    return p


def spawn_longrunning():
    """起一个长跑子进程（活着）。"""
    p = subprocess.Popen([sys.executable, "-c",
                          "import time; time.sleep(300)"])
    time.sleep(1.0)
    return p


def terminate_and_wait(p):
    """复刻 harness 的调用序列，返回（是否抛异常, wait 返回值）。"""
    raised = None
    try:
        p.terminate()
    except Exception as e:      # noqa: BLE001 - 就是要观测异常类型
        raised = repr(e)
    try:
        rc = p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        rc = "TIMEOUT"
    return raised, rc


# ---------------------------------------------------------------- 趟产物读取

def load_fields(trip):
    p = TRIP_ROOT / trip / "qc151_fields.json"
    if not p.is_file():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def field_get(recs, group, key):
    hit = [r.get("value") for r in recs
           if r.get("group") == group and r.get("key") == key]
    return hit[-1] if hit else None


def main():
    print("=" * 78)
    print("H-6 定谳：wait_returncode 的 1 vs 0")
    print("=" * 78)

    # ---- P 组：实验（本机 CPython 真实行为）----
    print("\n[P] 实验：terminate() + wait() 在两种进程状态下的返回值")

    print("\n  P1 进程活着时")
    p_alive = spawn_longrunning()
    pre_alive = p_alive.poll()
    raised_a, rc_alive = terminate_and_wait(p_alive)
    print("    terminate 前 poll = %s（None=活着）" % pre_alive)
    print("    terminate 抛异常 = %s" % (raised_a or "无"))
    print("    wait_returncode  = %s" % rc_alive)
    rec("P1a 活着时 terminate() 不抛异常", raised_a is None, "")
    rec("P1b 活着时 wait_returncode == 1（TerminateProcess 传 1）",
        rc_alive == 1, "rc=%s" % rc_alive)

    print("\n  P2 进程已自行退出（code 0）时")
    p_dead0 = spawn_exits_with(0)
    pre_dead = p_dead0.poll()
    raised_d, rc_dead0 = terminate_and_wait(p_dead0)
    print("    terminate 前 poll = %s" % pre_dead)
    print("    terminate 抛异常 = %s" % (raised_d or "无"))
    print("    wait_returncode  = %s" % rc_dead0)
    rec("P2a 已退出时 terminate() **也不抛异常**（静默返回）",
        raised_d is None, "★ 这正是 terminate_sent 不可信的原因")
    rec("P2b 已退出时 wait_returncode == 进程自己的退出码 0",
        rc_dead0 == 0, "rc=%s" % rc_dead0)

    print("\n  P3 进程已自行退出（code 7）时 —— 证明返回值是『进程自己的码』")
    p_dead7 = spawn_exits_with(7)
    raised_7, rc_dead7 = terminate_and_wait(p_dead7)
    print("    terminate 抛异常 = %s" % (raised_7 or "无"))
    print("    wait_returncode  = %s（若为 7 则证明是进程自己的码）" % rc_dead7)
    rec("P3 已退出时 wait_returncode == 7（不是 1）⇒ 返回进程自己的退出码",
        rc_dead7 == 7, "rc=%s" % rc_dead7)

    print("\n  P4 两种状态返回不同值 ⇒ 这个量可以当状态判据")
    rec("P4 1（活着被杀）≠ 0/7（已退出）⇒ 1 vs 0 是**状态差异**不是概率",
        rc_alive == 1 and rc_dead0 == 0 and rc_dead7 == 7,
        "alive=%s dead0=%s dead7=%s" % (rc_alive, rc_dead0, rc_dead7))

    # ---- T 组：四趟真实产物 ----
    print("\n[T] 四趟真实产物的 TERM 记录")
    trips = {
        "l1_20261023": ("A", 1),
        "l1_20261023b": ("B", 1),
        "l1_20261023c": ("C", 0),
        "l3_20261023": ("L3", 0),
    }
    rows = {}
    for t, (label, want) in trips.items():
        f = load_fields(t)
        rc = field_get(f, "TERM", "wait_returncode")
        sent = field_get(f, "TERM", "terminate_sent")
        verdict = field_get(f, "TERM", "termination_verdict")
        rows[label] = {"wait_rc": rc, "sent": sent, "verdict": verdict}
        print("  %-3s %-14s wait_returncode=%s terminate_sent=%s verdict=%s"
              % (label, t, rc, sent, verdict))
        rec("T %s 的 wait_returncode == %s（与登记一致）" % (label, want),
            rc == want, "rc=%s" % rc)
        rec("T %s terminate_sent 为 True（★ 但不作『终止生效』证据）" % label,
            sent is True, "")

    # ---- 结论推导 ----
    print("\n[C] 结论推导")
    # A/B 的 1：进程在 terminate() 时还活着
    rec("C1 A/B = 1 ⇒ terminate() 打在**活进程**上（进程是被这趟终止的）",
        rows["A"]["wait_rc"] == 1 and rows["B"]["wait_rc"] == 1, "")
    # C/L3 的 0：进程已自行退出，且退出码是 0
    rec("C2 C/L3 = 0 ⇒ 进程**已自行退出**，且退出码是 0（不是被杀的）",
        rows["C"]["wait_rc"] == 0 and rows["L3"]["wait_rc"] == 0, "")
    rec("C3 ★ 0 是『进程自己的退出码』而不是『TerminateProcess 的返回值』"
        "——由 P2/P3 实验支撑",
        rc_dead0 == 0 and rc_dead7 == 7, "")
    # 与 H-5 的时间线一致：C 在 measure 之前已死
    # ★ 初版这里写成 rec(..., True, ...) —— 又是「判据位置放字面 True」的老毛病。
    #   真正的判据是：C 的 measure_w0 显示"进程已死"，**且** wait_returncode=0，
    #   两者必须同时成立（一个说"早死了"、一个说"自己退的"），才构成一致的因果。
    m0p = TRIP_ROOT / "l1_20261023c" / "measure_w0.json"
    _c_dead_before_term = False
    _c_ws = None
    if m0p.is_file():
        _m0 = json.loads(m0p.read_text(encoding="utf-8"))
        _c = (_m0.get("counters") or [{}])[0]
        _c_ws = _c.get("ws_kb")
        _c_dead_before_term = (_c.get("units") is None
                               and isinstance(_c_ws, int) and _c_ws < 1024)
    print("  C 的 measure_w0: units=None 且 ws_kb=%s ⇒ 终止前已死 = %s"
          % (_c_ws, _c_dead_before_term))
    rec("C4 与 H-5 一致：C 在 measure 阶段就已死（独立产物判据，非引用结论）",
        _c_dead_before_term, "ws_kb=%s" % _c_ws)

    # ---- 附带发现：terminate_sent 的证据力问题 ----
    print("\n[D] 附带发现（超出登记范围，如实登记）")
    rec("D1 ★ terminate_sent=True 不能证明『终止动作生效』："
        "对已死进程同样为 True（P2a 已证）",
        raised_d is None and rows["C"]["sent"] is True,
        "★ 这是个**否定式不可用**的实例：不能用它证明没被终止")
    rec("D2 termination_verdict=PASS 只证明『进程已退出』，不证明『是我杀的』"
        "——四趟都是 PASS，但只有 A/B 是被杀的",
        all(r["verdict"] == "PASS" for r in rows.values()), "")

    return finish()


def finish():
    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok in RESULTS:
        if not ok:
            print("  FAIL: %s" % n)
    print("=" * 78)
    return 0 if npass == len(RESULTS) else 1


def show_src():
    """打印 CPython 的 Popen.terminate 源码（判据的来源）。"""
    import inspect
    print("CPython %s 的 subprocess.Popen.terminate：" % sys.version.split()[0])
    print(inspect.getsource(subprocess.Popen.terminate))


# ============================================================ 变异自检
#
# ★ 门禁纪律：每条断言都要能被「改坏」杀死。
#   H-6 的两类输入不同，故变异分两路：
#     (a) 实验类（P 组）—— 改的是**被测行为**，用假对象替换 Popen 来伪造返回值；
#     (b) 产物类（T/C 组）—— 改的是**盘上 JSON 的内存副本**。
#   ★ 若某断言两路都杀不掉，它就是恒真式，必须降级并在此登记。

def _checks_from(probe, fields_by_trip, m0):
    """把判据抽成纯函数：喂进（可能被伪造的）实验值与产物，返回断言字典。"""
    out = {}
    # P 组：实验值
    out["P1a"] = probe["alive_raised"] is None
    out["P1b"] = probe["alive_rc"] == 1
    out["P2a"] = probe["dead0_raised"] is None
    out["P2b"] = probe["dead0_rc"] == 0
    out["P3"] = probe["dead7_rc"] == 7
    out["P4"] = (probe["alive_rc"] == 1 and probe["dead0_rc"] == 0
                 and probe["dead7_rc"] == 7)
    # T 组：真实趟产物
    want = {"A": 1, "B": 1, "C": 0, "L3": 0}
    rows = {}
    for label, f in fields_by_trip.items():
        rows[label] = {"wait_rc": field_get(f, "TERM", "wait_returncode"),
                       "sent": field_get(f, "TERM", "terminate_sent"),
                       "verdict": field_get(f, "TERM", "termination_verdict")}
    for label, w in want.items():
        out["T_" + label] = rows.get(label, {}).get("wait_rc") == w
    # C 组
    out["C1"] = rows.get("A", {}).get("wait_rc") == 1 \
        and rows.get("B", {}).get("wait_rc") == 1
    out["C2"] = rows.get("C", {}).get("wait_rc") == 0 \
        and rows.get("L3", {}).get("wait_rc") == 0
    out["C3"] = probe["dead0_rc"] == 0 and probe["dead7_rc"] == 7
    c = (m0.get("counters") or [{}])[0]
    out["C4"] = (c.get("units") is None
                 and isinstance(c.get("ws_kb"), int) and c["ws_kb"] < 1024)
    # D 组
    out["D1"] = probe["dead0_raised"] is None \
        and rows.get("C", {}).get("sent") is True
    out["D2"] = all(r["verdict"] == "PASS" for r in rows.values()) \
        and rows.get("A", {}).get("wait_rc") == 1 \
        and rows.get("C", {}).get("wait_rc") == 0
    return out


def self_mutation():
    """变异自检：伪造实验值 / 改坏产物，要求对应断言变红。"""
    import copy
    print("\n" + "=" * 78)
    print("变异自检：每条断言都必须能被杀死")
    print("=" * 78)

    # 真实基线
    real_probe = {"alive_raised": None, "alive_rc": 1,
                  "dead0_raised": None, "dead0_rc": 0,
                  "dead7_rc": 7}
    real_fields = {lab: load_fields(t) for lab, t in
                   (("A", "l1_20261023"), ("B", "l1_20261023b"),
                    ("C", "l1_20261023c"), ("L3", "l3_20261023"))}
    m0p = TRIP_ROOT / "l1_20261023c" / "measure_w0.json"
    real_m0 = json.loads(m0p.read_text(encoding="utf-8")) if m0p.is_file() else {}

    base = _checks_from(real_probe, real_fields, real_m0)
    n_fail = [k for k, v in base.items() if not v]
    rec("基线：全部断言在真实数据上成立", not n_fail, str(n_fail) if n_fail else "")

    killed_any = {}

    def mut(label, probe, fields, m0, targets):
        got = _checks_from(probe, fields, m0)
        dead = [k for k in targets if not got[k]]
        missed = [k for k in targets if got[k]]
        for k in dead:
            killed_any[k] = killed_any.get(k, 0) + 1
        rec(label, not missed,
            "击杀 %s" % dead + ("；★ 未变=%s" % missed if missed else ""))

    # ---- 实验类变异 ----
    p = dict(real_probe)
    mut("MP1 伪造：活着时也抛异常", {**p, "alive_raised": "OSError"},
        real_fields, real_m0, ["P1a"])
    mut("MP2 伪造：活着时返回 0（而非 1）", {**p, "alive_rc": 0},
        real_fields, real_m0, ["P1b", "P4"])
    # ★ MP2 初版目标里写了 C1 —— 但 C1 读的是**产物**（A/B 的 TERM 记录），
    #   伪造实验值不会动它。这不是恒真式，是目标列错了。C1 由 MT2 专杀。
    mut("MP3 伪造：已死时抛异常", {**p, "dead0_raised": "OSError"},
        real_fields, real_m0, ["P2a", "D1"])
    mut("MP4 伪造：已死时返回 1（而非进程自己的码）", {**p, "dead0_rc": 1},
        real_fields, real_m0, ["P2b", "P4", "C3"])
    mut("MP5 伪造：退出码 7 被读成 1", {**p, "dead7_rc": 1},
        real_fields, real_m0, ["P3", "P4", "C3"])

    # ---- 产物类变异 ----
    f = copy.deepcopy(real_fields)
    for r in f["C"]:
        if r.get("group") == "TERM" and r.get("key") == "wait_returncode":
            r["value"] = 1
    mut("MT1 把 C 趟 wait_returncode 改成 1", p, f, real_m0, ["T_C", "C2"])

    f2 = copy.deepcopy(real_fields)
    for r in f2["A"]:
        if r.get("group") == "TERM" and r.get("key") == "wait_returncode":
            r["value"] = 0
    mut("MT2 把 A 趟 wait_returncode 改成 0", p, f2, real_m0, ["T_A", "C1", "D2"])

    f3 = copy.deepcopy(real_fields)
    for r in f3["C"]:
        if r.get("group") == "TERM" and r.get("key") == "terminate_sent":
            r["value"] = False
    mut("MT3 把 C 趟 terminate_sent 改成 False", p, f3, real_m0, ["D1"])

    # ★ MT5/MT6：补上 T_B 与 T_L3 的专属变异（覆盖检查暴露的漏项）
    f5 = copy.deepcopy(real_fields)
    for r in f5["B"]:
        if r.get("group") == "TERM" and r.get("key") == "wait_returncode":
            r["value"] = 0
    mut("MT5 把 B 趟 wait_returncode 改成 0", p, f5, real_m0, ["T_B"])

    f6 = copy.deepcopy(real_fields)
    for r in f6["L3"]:
        if r.get("group") == "TERM" and r.get("key") == "wait_returncode":
            r["value"] = 1
    mut("MT6 把 L3 趟 wait_returncode 改成 1", p, f6, real_m0, ["T_L3", "C2"])

    m4 = copy.deepcopy(real_m0)
    m4["counters"][0]["ws_kb"] = 137504
    mut("MT4 把 C 的 ws_kb 改成活进程量级", p, real_fields, m4, ["C4"])

    # ---- 覆盖汇总 ----
    print()
    never_killed = [k for k, v in base.items() if killed_any.get(k, 0) == 0]
    rec("覆盖：基线里每条断言都至少被一条变异杀过（无恒真式）",
        not never_killed,
        "未被杀过=%s" % never_killed if never_killed else "全覆盖")
    print("  被杀次数统计: %s"
          % {k: killed_any[k] for k in sorted(killed_any)})
    return 0 if not never_killed else 1


if __name__ == "__main__":
    if "--show-src" in sys.argv:
        show_src()
        sys.exit(0)
    if "--self-mutation" in sys.argv:
        sys.exit(self_mutation())
    sys.exit(main())
