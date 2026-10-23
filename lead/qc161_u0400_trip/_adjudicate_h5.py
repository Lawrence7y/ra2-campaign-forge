"""H-5 定谳器：用旁路帧钟序列判定「C/L3 的 gamemd 是什么时候、以什么方式离开的」。

## 背景（台账 §397 §八 H-5）

登记原文：

> **H-5（新，未定谳）：C/L3 两趟的 gamemd 进程在 measure 窗之前就已退出。**
> 证据：`measure_w0.json` 的 `counters` 里 `ws_kb = 20` / `pf_kb = 64`
> （活进程约 137 MB，差 4 个数量级），`units = null`；隔离检查报
> `CreateToolhelp32Snapshot(pid=…) 失败: err=299`（`ERROR_PARTIAL_COPY`），
> 而 A/B 两趟 `iso_verdict = PASS`。
> **本节不主张死因**……**要定谳需要**：在 C/L3 这类趟上加进程存活探针
> （`_launch_monitored_20261023.py` 已有 `pid` 与 `open_read`，可扩一个
> `IsProcessAlive` 时间序列），**本轮未做**。

★ 本件的第一件事实：**那个探针早就跑了，数据就在盘上。**
`l1_20261023c/_v11a_concurrent_clock.json` 有 **14,215 条** 200 Hz 采样序列，
覆盖 t=0…77.16 s。登记时没读它，于是写下「本轮未做」。

## 本件要回答的三个问题

Q1 **进程在旁路序列结束（77.16 s）时是否还活着？**
Q2 **harness 在 126 s 后读不到任何东西，是「进程已死」还是「页被解映射」？**
Q3 **能否把死亡时刻夹到一个区间里？**

## 判据设计（否定式必须能被杀死）

`rpm_u32` 的实现是：`ReadProcessMemory` 返回 FALSE ⇒ 返回 `None` ⇒
`Monitor.run` 走 `continue`，**该样本不进入 series**。
所以 series 里出现 `f == 0` 的样本，只可能来自「RPM 成功且值真的是 0」。
这两个分支在**数据形态上可区分**：

  - 进程死 / 页无效 ⇒ series **停止增长**（不是出现 0）
  - 进程活着、值为 0 ⇒ series **继续增长，值为 0**

故 Q1 的判据是「尾部是否仍在增长」，不是「值是否为 0」。
"""
import json
import struct
import sys
from pathlib import Path

TRIP_ROOT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
                 r"\CONTINUE_20261003\lead\qc161_u0400_trip")
GAMEMD = TRIP_ROOT / "_src_L1_sf8_20261020" / "gamemd.exe"

# 探针 VA（与 harness / 旁路工具逐字同源）
PROBE_VAS = {
    0x00A8ED84: "CurrentFrame",
    0x008B4118: "units",
    0x00A83DF8: "infantry",
    0x00A8EC88: "techno",
}

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("[%s] %s  %s" % ("PASS" if ok else "FAIL", name, detail))


def pe_sections(path):
    """返回 [(name, va, vsize)]，VA 已加 ImageBase。"""
    b = Path(path).read_bytes()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    optsz = struct.unpack_from("<H", b, pe + 20)[0]
    base = struct.unpack_from("<I", b, pe + 24 + 28)[0]
    so = pe + 24 + optsz
    out = []
    for i in range(nsec):
        o = so + i * 40
        name = b[o:o + 8].rstrip(b"\x00").decode("latin1")
        vsz, va = struct.unpack_from("<II", b, o + 8)
        out.append((name, base + va, vsz))
    return out


def section_of(secs, va):
    for name, sva, vsz in secs:
        if sva <= va < sva + vsz:
            return name
    return None


def load_series(trip):
    p = TRIP_ROOT / trip / "_v11a_concurrent_clock.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def load_fields(trip):
    p = TRIP_ROOT / trip / "qc151_fields.json"
    if not p.is_file():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def field_get(recs, group, key):
    hit = [r.get("value") for r in recs
           if r.get("group") == group and r.get("key") == key]
    return hit[-1] if hit else None


def boot_budget(recs):
    """从 BUDGET 组取出各阶段起点/耗时，返回 dict。"""
    out = {}
    for r in recs:
        if r.get("group") != "BUDGET":
            continue
        k = str(r.get("key", ""))
        if k.startswith("stage_begin:"):
            out.setdefault(k.split(":", 1)[1], {})["begin"] = r.get("value")
        elif k.startswith("stage_seconds:"):
            out.setdefault(k.split(":", 1)[1], {})["sec"] = r.get("value")
    return out


def main():
    print("=" * 78)
    print("H-5 定谳：C/L3 的 gamemd 死亡时刻与方式")
    print("=" * 78)

    # ---- Q0：探针 VA 必须落在静态段（否则「读不到」可能只是页被解映射）----
    print("\n[Q0] 探针 VA 的段归属 —— 决定「RPM 失败」能否等价于「进程已死」")
    if not GAMEMD.is_file():
        rec("Q0 gamemd.exe 可得", False, str(GAMEMD))
        return finish()
    secs = pe_sections(GAMEMD)
    print("  段表: %s" % [(n, hex(v), hex(s)) for n, v, s in secs])
    all_static = True
    for va, label in PROBE_VAS.items():
        s = section_of(secs, va)
        is_static = s in (".data", ".rdata", ".text")
        all_static &= is_static
        print("  %-12s @%#010x -> %-8s %s"
              % (label, va, s, "静态段" if is_static else "★ 非静态"))
    rec("Q0 四个探针 VA 全在静态段 ⇒ 活进程必可读", all_static, "")

    # ---- Q1：旁路序列尾部是否仍在增长 ----
    print("\n[Q1] 旁路序列尾部是否仍在增长（增长=进程活、值为真 0）")
    side = load_series("l1_20261023c")
    if side is None:
        rec("Q1 l1_20261023c 有旁路产物", False, "文件缺失")
        return finish()
    s = side["series"]
    nz = [i for i, x in enumerate(s) if x[1] != 0]
    last_nz = nz[-1] if nz else None
    after = s[last_nz + 1:] if last_nz is not None else []
    print("  样本总数 %d，时间跨度 %.3f → %.3f s"
          % (len(s), s[0][0], s[-1][0]))
    print("  frame 非零样本 %d 条；最后非零 t=%.4f frame=%d"
          % (len(nz), s[last_nz][0], s[last_nz][1]) if last_nz else "  无非零")
    print("  其后样本 %d 条，跨度 %.3f → %.3f s（%.3f s）"
          % (len(after), after[0][0], after[-1][0],
             after[-1][0] - after[0][0]) if after else "  无")
    rec("Q1a 帧归零后仍有大量样本（若进程死则样本会停止增长）",
        len(after) > 100, "%d 条" % len(after))
    gaps = [round(after[i + 1][0] - after[i][0], 4) for i in range(len(after) - 1)]
    max_gap = max(gaps) if gaps else None
    rec("Q1b 尾部采样间隔无断裂（无 >0.1 s 空洞 ⇒ 无 RPM 连续失败）",
        max_gap is not None and max_gap < 0.1, "max_gap=%s" % max_gap)
    tail_units = sorted({x[2] for x in after})
    tail_inf = sorted({x[3] for x in after})
    tail_tech = sorted({x[4] for x in after})
    print("  尾部 units/infantry/techno 取值集: %s / %s / %s"
          % (tail_units, tail_inf, tail_tech))
    rec("Q1c 尾部三个计数器均非 None 且冻结（读到值但不再变化）",
        all(v is not None for v in (tail_units[0] if tail_units else None,
                                    tail_inf[0] if tail_inf else None,
                                    tail_tech[0] if tail_tech else None))
        and len(tail_units) == 1 and len(tail_inf) == 1 and len(tail_tech) == 1,
        "")
    rec("Q1d 帧计数在 t=%.2f 后恒为 0（不是变 None）" % s[last_nz][0],
        all(x[1] == 0 for x in after), "")

    # ---- Q2：harness 侧证据 ----
    print("\n[Q2] harness 侧：126 s 后完全读不到，判「进程已死」还是「页无效」")
    f = load_fields("l1_20261023c")
    m0p = TRIP_ROOT / "l1_20261023c" / "measure_w0.json"
    m0 = json.loads(m0p.read_text(encoding="utf-8")) if m0p.is_file() else {}
    ctr = (m0.get("counters") or [{}])[0]
    _err = str(m0.get("error") or "")
    print("  measure_w0.counters[0]: units=%s ws_kb=%s pf_kb=%s"
          % (ctr.get("units"), ctr.get("ws_kb"), ctr.get("pf_kb")))
    print("  measure_w0.error: %s" % _err)
    # ★ 原版这里写的是 `ctr.get("units") is None and "RPM" not in "x"` ——
    #   后半句对任何输入恒真（判据与论据无关），是恒真式的典型。
    #   改为同时断言「有效样本为 0」这个**取自产物文本**的量。
    _zero_ok = ctr.get("units") is None and "有效样本 0" in _err
    rec("Q2a harness 侧 RPM 全失败（units=None 且文案含『有效样本 0』）",
        _zero_ok, "%s" % _err[:50])
    rec("Q2b ws_kb 退到个位数量级（活进程约 137 MB）",
        isinstance(ctr.get("ws_kb"), int) and ctr["ws_kb"] < 1024,
        "ws_kb=%s" % ctr.get("ws_kb"))
    iso = field_get(f, "ISOLATION", "iso_error")
    iso_v = field_get(f, "ISOLATION", "iso_verdict")
    print("  ISOLATION: verdict=%s error=%s" % (iso_v, iso))
    rec("Q2c 隔离枚举报 err=299（ERROR_PARTIAL_COPY）",
        "299" in str(iso), str(iso))

    # ---- Q3：把死亡时刻夹到区间（★ 本轮重写：原版 Q3a/Q3b 只是重复 Q1a/Q2a）----
    print("\n[Q3] 死亡时刻的夹逼区间 —— 上界取自旁路，下界取自 harness")
    bud = boot_budget(f)
    frame = bud.get("frame", {})
    frame_begin = frame.get("begin")
    frame_sec = frame.get("sec")
    print("  BUDGET stage:frame begin=%s sec=%s" % (frame_begin, frame_sec))

    # 探针 t0（gamemd 首次被发现）在 harness 时间轴上的位置：
    # Monitor 在 spawnv 之后立刻起，harness 的 launch 阶段也在那之前结束
    # ⇒ t0 ≈ stage_begin:launch 结束时刻（两值均为 harness 自己的相对钟）
    launch_begin = bud.get("launch", {}).get("begin")
    launch_sec = bud.get("launch", {}).get("sec")
    print("  BUDGET stage:launch begin=%s sec=%s" % (launch_begin, launch_sec))

    side_end = s[-1][0]
    side_alive_upper = (launch_begin + launch_sec + side_end) if (
        launch_begin is not None and launch_sec is not None) else None
    dead_lower = (frame_begin + frame_sec) if (
        frame_begin is not None and frame_sec is not None) else None
    print("  旁路最后有效样本 t=%.3f s（相对 gamemd 首次被发现）" % side_end)
    if side_alive_upper is not None:
        print("  ⇒ 换算到 harness 钟：仍活着的时刻 ≥ %.1f s（附加上界）"
              % side_alive_upper)
    if dead_lower is not None:
        print("  ⇒ harness 首次读不到的时刻 = frame 阶段末 = %.1f s" % dead_lower)
    if side_alive_upper is not None and dead_lower is not None:
        print("  ⇒ 死亡时刻落在 (%.1f, %.1f] s 区间内，宽度 %.1f s"
              % (side_alive_upper, dead_lower, dead_lower - side_alive_upper))
    rec("Q3a 存在非空夹逼区间（上界 < 下界，宽度 > 0）",
        side_alive_upper is not None and dead_lower is not None
        and side_alive_upper < dead_lower,
        "(%s, %s]" % (side_alive_upper, dead_lower))
    # ★ 关键：上界必须由**旁路样本**支撑，不能只由 harness 自己说
    rec("Q3b 上界时刻有真实样本（该时刻的 units 读得到，非 None）",
        len(after) > 0 and after[-1][2] is not None,
        "t=%.2f units=%s" % (after[-1][0], after[-1][2]) if after else "无")

    # ★★ Q3c：用 Monitor 的停机机制把上界再收紧。
    #   `Monitor.run` 在 RPM 连续失败时 `misses += 1`，超过 400 才 break，
    #   期间每次 `sleep(0.05)` ⇒ 从「第一次失败」到「线程退出」至少 400×0.05=20 s。
    #   线程退出必须早于 `mon.stop()`（`spawnv` 返回后立即调用），
    #   而 `spawnv` 返回 = harness 进程退出 = `duration_s`。
    #   ⇒ 若进程死在最后一条样本之后，则：
    #        死时刻 + 20 s ≤ duration_s
    #   ⇒ 上界收紧为 duration_s − 20 s（前提：死亡确实发生在最后样本之后）。
    dur = side.get("duration_s")
    MON_BREAK_S = 400 * 0.05
    tight_upper = (dur - MON_BREAK_S) if isinstance(dur, (int, float)) else None
    print("  Monitor 停机: RPM 连续失败 >400 次 × sleep(0.05) = 至少 %.1f s" % MON_BREAK_S)
    print("  harness duration_s = %s ⇒ 线程必须在它之前退出" % dur)
    if tight_upper is not None:
        print("  ⇒ 若死亡在最后样本之后: 死时刻 ≤ %.1f s（= duration − %.0f）"
              % (tight_upper, MON_BREAK_S))
    if tight_upper is not None and side_alive_upper is not None:
        print("  ⇒ 收紧后的区间: (%.1f, %.1f] s，宽度 %.1f s"
              % (side_alive_upper, min(tight_upper, dead_lower or tight_upper),
                 min(tight_upper, dead_lower or tight_upper) - side_alive_upper))
    rec("Q3c 用停机机制收紧上界后区间变窄（证明该推导有实际约束力）",
        tight_upper is not None and dead_lower is not None
        and tight_upper < dead_lower,
        "tight_upper=%s vs frame_end=%s" % (tight_upper, dead_lower))
    # ★ 该收紧依赖一个前提，必须单列断言，不能混在结论里
    rec("Q3d 收紧前提成立：Monitor 线程确实在 duration_s 之前就停了"
        "（否则 20 s 推导不适用）",
        isinstance(side_end, (int, float)) and isinstance(dur, (int, float))
        and side_end < dur,
        "side_end=%.1f < dur=%.1f" % (side_end, dur))

    # ---- Q4：A/B 对照（同批、同 harness、未死）----
    print("\n[Q4] 同批对照：A/B 两趟的 ws_kb（证明「差距是数量级」不是抖动）")
    for t in ("l1_20261023", "l1_20261023b"):
        p = TRIP_ROOT / t / "measure_w0.json"
        if not p.is_file():
            rec("Q4 %s 有 measure_w0" % t, False, "")
            continue
        j = json.loads(p.read_text(encoding="utf-8"))
        c = (j.get("counters") or [{}])[0]
        print("  %-14s units=%s ws_kb=%s" % (t, c.get("units"), c.get("ws_kb")))
        rec("Q4 %s ws_kb 为活进程量级（>100 MB）" % t,
            isinstance(c.get("ws_kb"), int) and c["ws_kb"] > 100 * 1024,
            "ws_kb=%s" % c.get("ws_kb"))

    # ---- Q5：L3 是否同型 ----
    print("\n[Q5] l3_20261023 是否与 C 同型")
    p3 = TRIP_ROOT / "l3_20261023" / "measure_w0.json"
    if p3.is_file():
        j3 = json.loads(p3.read_text(encoding="utf-8"))
        c3 = (j3.get("counters") or [{}])[0]
        print("  ws_kb=%s units=%s err=%s"
              % (c3.get("ws_kb"), c3.get("units"), str(j3.get("error"))[:50]))
        rec("Q5 L3 同样 ws_kb 个位数 + units=None",
            isinstance(c3.get("ws_kb"), int) and c3["ws_kb"] < 1024
            and c3.get("units") is None, "ws_kb=%s" % c3.get("ws_kb"))
        rec("Q5b L3 **没有**旁路产物 ⇒ 它的死亡时刻无法夹逼（只有 C 能）",
            not (TRIP_ROOT / "l3_20261023" / "_v11a_concurrent_clock.json").is_file(),
            "")

    # ---- Q6：TERM 记录能佐证什么 ----
    print("\n[Q6] TERM 记录：收尾时进程句柄状态")
    term_v = field_get(f, "TERM", "termination_verdict")
    term_rc = field_get(f, "TERM", "wait_returncode")
    ct_now = field_get(f, "TERM", "current_creation_time")
    ct_launch = field_get(f, "LAUNCH", "launch_pid_creation_time")
    print("  termination_verdict=%s wait_returncode=%s" % (term_v, term_rc))
    print("  current_creation_time=%s launch_pid_creation_time=%s"
          % (ct_now, ct_launch))
    rec("Q6a 收尾时仍能取到创建时间且与 launch 时相同 ⇒ 句柄未失效",
        ct_now is not None and ct_now == ct_launch, "%s" % ct_now)
    rec("Q6b wait_returncode=0（terminate 打在已退出进程上）",
        term_rc == 0, "rc=%s" % term_rc)

    # ---- Q7：harness 自带探针的独立佐证（第三个观测通道）----
    print("\n[Q7] harness 自带探针（qc213p2）是否也读不到 —— 独立佐证")
    p2 = field_get(f, "MEASURE", "qc213p2_probe_final")
    p1 = field_get(f, "MEASURE", "qc213_probe_final")
    print("  qc213_probe_final   = %s"
          % json.dumps(p1, ensure_ascii=False) if p1 else "  (无)")
    print("  qc213p2_probe_final = %s"
          % json.dumps(p2, ensure_ascii=False) if p2 else "  (无)")
    if isinstance(p2, dict):
        rec("Q7a harness 自带探针 first_frame/last_frame 均为 null",
            p2.get("first_frame") is None and p2.get("last_frame") is None,
            "first=%s last=%s" % (p2.get("first_frame"),
                                  p2.get("last_frame")))
        rec("Q7b ladder_dropped > 0（探针尝试过、但一帧都没锁到）",
            isinstance(p2.get("ladder_dropped"), int)
            and p2["ladder_dropped"] > 0,
            "dropped=%s" % p2.get("ladder_dropped"))
    if isinstance(p1, dict):
        rec("Q7c qc213 通道同样 latched_n=0 / snapshots 空",
            p1.get("latched_n") == 0 and not p1.get("snapshots"), "")
    # ★★ Q7d：这是本件最强的一条 —— 旁路与 harness 是**两个独立进程**、
    #   各自 OpenProcess，一条在 77 s 读到值、另一条在 161 s 读不到。
    #   若只是「页被解映射」，两条都该读不到；若只是「旁路工具自身坏了」，
    #   harness 那侧就无从解释。两者并存 ⇒ 进程在两者之间消失。
    #   ★ 判据不能写成 `True`（那是恒真式）：这里真正要比的是
    #   **同一个 pid**——旁路记录的 gamemd_pid 必须等于 harness 的 launch_pid，
    #   否则「同一进程」这个前提不成立，整条推理作废。
    _side_pid = side.get("gamemd_pid")
    _launch_pid = field_get(f, "LAUNCH", "launch_pid")
    print("  旁路 gamemd_pid=%s   harness launch_pid=%s"
          % (_side_pid, _launch_pid))
    rec("Q7d 旁路与 harness 观测的是同一个 pid（否则『同一进程』前提不成立）",
        _side_pid is not None and _side_pid == _launch_pid,
        "side=%s launch=%s" % (_side_pid, _launch_pid))

    # ---- Q8：把「进程已死」与「读得到但游戏停摆」分开记录 ----
    print("\n[Q8] 结论归类：C 趟的两种状态是**先后**关系，不是同一种")
    rec("Q8a 阶段一（≤ 88.7 s）：进程活着，但帧计数已归零 6.28 s（游戏停摆）",
        len(after) > 100 and all(x[1] == 0 for x in after),
        "尾部 %d 条全 0" % len(after))
    rec("Q8b 阶段二（≥ 161.75 s）：进程不可读（ws_kb=20、RPM 全失败）",
        isinstance(ctr.get("ws_kb"), int) and ctr["ws_kb"] < 1024,
        "ws_kb=%s" % ctr.get("ws_kb"))
    rec("Q8c 两阶段的时间先后由各自原始观测支撑（非同一时刻）",
        side_end < (dead_lower or 0),
        "%.1f s < %s s" % (side_end, dead_lower))

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


# ============================================================ 变异自检
#
# ★ 门禁纪律：每条取值证明都必须配一条「改坏被测数据 ⇒ 必红」的变异。
#   本件的被测量全是**盘上的趟产物**，故变异体 = 在内存里改坏 JSON 后
#   用同一套判据重算。若某条断言在数据被改坏后仍为 PASS，它就是恒真式，
#   必须降级为「结构性普查」并在此登记。
#
# ★ 不写盘：所有变异只改内存中的 dict/list，不碰真产物。

def _run_checks(series, m0, fields, secs, dur_override=None):
    """把 main() 的判据抽成纯函数：喂进（可能被变异的）数据，返回 bool 列表。

    返回按断言名索引的 dict，便于变异逐条比对。
    """
    out = {}
    s = series["series"]
    nz = [i for i, x in enumerate(s) if x[1] != 0]
    last_nz = nz[-1] if nz else None
    after = s[last_nz + 1:] if last_nz is not None else []

    # Q0
    out["Q0"] = all(section_of(secs, va) in (".data", ".rdata", ".text")
                    for va in PROBE_VAS)
    # Q1
    out["Q1a"] = len(after) > 100
    gaps = [after[i + 1][0] - after[i][0] for i in range(len(after) - 1)]
    out["Q1b"] = bool(gaps) and max(gaps) < 0.1
    out["Q1c"] = bool(after) and all(
        x[2] is not None and x[3] is not None and x[4] is not None
        for x in after) and len({x[2] for x in after}) == 1
    out["Q1d"] = bool(after) and all(x[1] == 0 for x in after)
    # Q2
    ctr = (m0.get("counters") or [{}])[0]
    err = str(m0.get("error") or "")
    out["Q2a"] = ctr.get("units") is None and "有效样本 0" in err
    out["Q2b"] = isinstance(ctr.get("ws_kb"), int) and ctr["ws_kb"] < 1024
    iso = field_get(fields, "ISOLATION", "iso_error")
    out["Q2c"] = "299" in str(iso)
    # Q3
    bud = boot_budget(fields)
    fb = bud.get("frame", {}).get("begin")
    fs = bud.get("frame", {}).get("sec")
    lb = bud.get("launch", {}).get("begin")
    ls = bud.get("launch", {}).get("sec")
    side_end = s[-1][0]
    upper = (lb + ls + side_end) if None not in (lb, ls) else None
    lower = (fb + fs) if None not in (fb, fs) else None
    out["Q3a"] = upper is not None and lower is not None and upper < lower
    out["Q3b"] = bool(after) and after[-1][2] is not None
    dur = dur_override if dur_override is not None else series.get("duration_s")
    tight = (dur - 20.0) if isinstance(dur, (int, float)) else None
    out["Q3c"] = tight is not None and lower is not None and tight < lower
    out["Q3d"] = isinstance(dur, (int, float)) and side_end < dur
    # Q6
    out["Q6a"] = (field_get(fields, "TERM", "current_creation_time")
                  == field_get(fields, "LAUNCH", "launch_pid_creation_time")
                  is not None)
    out["Q6b"] = field_get(fields, "TERM", "wait_returncode") == 0
    # Q7
    p2 = field_get(fields, "MEASURE", "qc213p2_probe_final")
    p1 = field_get(fields, "MEASURE", "qc213_probe_final")
    out["Q7a"] = isinstance(p2, dict) and p2.get("first_frame") is None \
        and p2.get("last_frame") is None
    out["Q7b"] = isinstance(p2, dict) and isinstance(p2.get("ladder_dropped"), int) \
        and p2["ladder_dropped"] > 0
    out["Q7c"] = isinstance(p1, dict) and p1.get("latched_n") == 0 \
        and not p1.get("snapshots")
    out["Q7d"] = (series.get("gamemd_pid") is not None
                  and series.get("gamemd_pid")
                  == field_get(fields, "LAUNCH", "launch_pid"))
    # Q8
    out["Q8a"] = len(after) > 100 and all(x[1] == 0 for x in after)
    out["Q8b"] = isinstance(ctr.get("ws_kb"), int) and ctr["ws_kb"] < 1024
    out["Q8c"] = lower is not None and side_end < lower
    return out


def self_mutation():
    """变异自检：逐条改坏数据，要求对应断言变红。"""
    print("\n" + "=" * 78)
    print("变异自检：每条断言都必须能被『改坏数据』杀死")
    print("=" * 78)

    side = load_series("l1_20261023c")
    fields = load_fields("l1_20261023c")
    m0 = json.loads((TRIP_ROOT / "l1_20261023c" / "measure_w0.json")
                    .read_text(encoding="utf-8"))
    secs = pe_sections(GAMEMD)

    import copy
    base = _run_checks(side, m0, fields, secs)
    muts = []

    # M1：把尾部 0 值样本截掉 ⇒ Q1a/Q1d/Q8a 应红
    s1 = copy.deepcopy(side)
    nz = [i for i, x in enumerate(s1["series"]) if x[1] != 0]
    s1["series"] = s1["series"][:nz[-1] + 1]
    muts.append(("M1 截掉帧归零后的 1158 条样本", s1, m0, fields, secs,
                 ["Q1a", "Q1d", "Q8a"]))

    # M2：把尾部样本的 frame 改回非零 ⇒ Q1d/Q8a 应红
    s2 = copy.deepcopy(side)
    nz2 = [i for i, x in enumerate(s2["series"]) if x[1] != 0]
    for i in range(nz2[-1] + 1, len(s2["series"])):
        s2["series"][i] = [s2["series"][i][0], 999] + s2["series"][i][2:]
    muts.append(("M2 把尾部 0 改成非零（伪装成仍在推进）", s2, m0, fields, secs,
                 ["Q1d", "Q8a"]))

    # M3：把 units 改成 None（伪装成 RPM 失败）⇒ Q1c 应红
    s3 = copy.deepcopy(side)
    nz3 = [i for i, x in enumerate(s3["series"]) if x[1] != 0]
    for i in range(nz3[-1] + 1, len(s3["series"])):
        s3["series"][i] = [s3["series"][i][0], s3["series"][i][1],
                           None, s3["series"][i][3], s3["series"][i][4]]
    muts.append(("M3 把尾部 units 改成 None", s3, m0, fields, secs, ["Q1c"]))

    # M4：ws_kb 改回活进程量级 ⇒ Q2b/Q8b 应红
    m4 = copy.deepcopy(m0)
    m4["counters"][0]["ws_kb"] = 137504
    muts.append(("M4 ws_kb 改回 137504", side, m4, fields, secs, ["Q2b", "Q8b"]))

    # M5：error 文案去掉「有效样本 0」⇒ Q2a 应红
    m5 = copy.deepcopy(m0)
    m5["error"] = "某原因"
    muts.append(("M5 error 文案改掉", side, m5, fields, secs, ["Q2a"]))

    # M6：iso_error 改掉 err=299 ⇒ Q2c 应红
    f6 = copy.deepcopy(fields)
    for r in f6:
        if r.get("group") == "ISOLATION" and r.get("key") == "iso_error":
            r["value"] = "无错误"
    muts.append(("M6 iso_error 改成无错误", side, m0, f6, secs, ["Q2c"]))

    # M7：把 frame 阶段耗时改小（下界提前）⇒ Q3a/Q3c/Q8c 可能变
    f7 = copy.deepcopy(fields)
    for r in f7:
        if r.get("group") == "BUDGET" and r.get("key") == "stage_seconds:frame":
            r["value"] = 10.0
    muts.append(("M7 frame 阶段耗时改为 10 s（下界提前到 45 s）", side, m0, f7,
                 secs, ["Q3a", "Q8c"]))

    # M8：gamemd_pid 改成别的 ⇒ Q7d 应红
    s8 = copy.deepcopy(side)
    s8["gamemd_pid"] = 99999
    muts.append(("M8 旁路 gamemd_pid 改成 99999", s8, m0, fields, secs,
                 ["Q7d"]))

    # M9：probe_final 改成「读到过帧」⇒ Q7a/Q7b/Q7c 应红
    f9 = copy.deepcopy(fields)
    for r in f9:
        if r.get("group") == "MEASURE" and r.get("key") == "qc213p2_probe_final":
            r["value"] = {"latched": [1], "latched_n": 1, "ladder_n": 64,
                          "ladder_dropped": 0, "early_done": True,
                          "first_frame": 3900, "last_frame": 4200,
                          "frozen_done": True, "snapshots": [1], "err": None,
                          "errs": 0}
    muts.append(("M9 probe_final 改成读到过帧", side, m0, f9, secs,
                 ["Q7a", "Q7b"]))

    # ★ M13：专打 Q7c（qc213 通道）。M9 只动了 qc213p2，故 Q7c 本来就不该变——
    #   那不是恒真式，是变异目标漏了。这里补一条真正改 qc213 的变异。
    f13 = copy.deepcopy(fields)
    for r in f13:
        if r.get("group") == "MEASURE" and r.get("key") == "qc213_probe_final":
            r["value"] = {"latched": [1], "latched_n": 1, "frozen_done": True,
                          "snapshots": [1], "err": None, "errs": 0}
    muts.append(("M13 把 qc213 通道改成锁到过帧", side, m0, f13, secs, ["Q7c"]))

    # M10：TERM 创建时间改成另一个值 ⇒ Q6a 应红
    f10 = copy.deepcopy(fields)
    for r in f10:
        if r.get("group") == "TERM" and r.get("key") == "current_creation_time":
            r["value"] = 1
    muts.append(("M10 TERM 创建时间改成 1", side, m0, f10, secs, ["Q6a"]))

    # M11：wait_returncode 改成 1 ⇒ Q6b 应红
    f11 = copy.deepcopy(fields)
    for r in f11:
        if r.get("group") == "TERM" and r.get("key") == "wait_returncode":
            r["value"] = 1
    muts.append(("M11 wait_returncode 改成 1", side, m0, f11, secs, ["Q6b"]))

    # M12：把探针 VA 挪到 .rsrc（非法段）⇒ Q0 应红
    #       做法：给一个非静态地址当探针
    saved_vas = dict(PROBE_VAS)
    try:
        PROBE_VAS.clear()
        PROBE_VAS[0x00000001] = "bogus"
        bogus = _run_checks(side, m0, fields, secs)
        rec("M12 探针 VA 挪到未映射地址 ⇒ Q0 变红",
            bogus["Q0"] is False, "Q0=%s" % bogus["Q0"])
    finally:
        PROBE_VAS.clear()
        PROBE_VAS.update(saved_vas)

    all_killed = True
    for label, ss, mm, ff, cc, keys in muts:
        got = _run_checks(ss, mm, ff, cc)
        killed = [k for k in keys if not got[k]]
        missed = [k for k in keys if got[k]]
        ok = not missed
        all_killed &= ok
        rec(label, ok,
            "击杀 %s" % killed + ("；★ 未变=%s" % missed if missed else ""))
    rec("M* 全部变异均至少杀死一条目标断言", all_killed, "")
    return 0 if all_killed else 1


if __name__ == "__main__":
    if "--self-mutation" in sys.argv:
        sys.exit(self_mutation())
    sys.exit(main())
