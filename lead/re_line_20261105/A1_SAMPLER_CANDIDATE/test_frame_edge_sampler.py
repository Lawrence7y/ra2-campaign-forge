# -*- coding: utf-8 -*-
"""候选件离线单测（D-20 步骤 A）：读取 / 格式 / null 处理。

★ 本测试**零真机**：所有 reader 都是注入的假函数，不触碰任何进程。
★ 本测试同时做**静态交叉核对**：四 VA 与帧号 VA 必须与 D-19 裁决书 / harness 常量逐字一致。

运行：`python -I -X utf8 lead/re_line_20261105/A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py`
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import frame_edge_sampler as S  # noqa: E402

PASS = 0
FAIL = 0
FAILED = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  PASS  %s" % name)
    else:
        FAIL += 1
        FAILED.append((name, detail))
        print("  FAIL  %s  %s" % (name, detail))


def eq(name, got, want):
    check(name, got == want, "got=%r want=%r" % (got, want))


# ==========================================================================
print("\n=== T1 · read_one 读取语义 ===")
# ==========================================================================
eq("T1.1 正常值透传", S.read_one(lambda va: 12345, 0x1000), 12345)
eq("T1.2 None ⇒ None（不补 0）", S.read_one(lambda va: None, 0x1000), None)
eq("T1.3 越界 >0xFFFFFFFF ⇒ None", S.read_one(lambda va: 0x1_0000_0000, 0x1000), None)
eq("T1.4 负数 ⇒ None", S.read_one(lambda va: -1, 0x1000), None)
eq("T1.5 非 int（str）⇒ None", S.read_one(lambda va: "123", 0x1000), None)
eq("T1.6 bool 拒收（True）", S.read_one(lambda va: True, 0x1000), None)
eq("T1.7 边界 0xFFFFFFFF 接受", S.read_one(lambda va: 0xFFFFFFFF, 0x1000), 0xFFFFFFFF)
eq("T1.8 边界 0 接受（0 是合法读数）", S.read_one(lambda va: 0, 0x1000), 0)


def _boom(_va):
    raise RuntimeError("rpm blew up")


eq("T1.9 reader 抛异常 ⇒ None（不向外抛）", S.read_one(_boom, 0x1000), None)

# ==========================================================================
print("\n=== T2 · read_sample 读序 / 齐全性 / 跨帧判定 ===")
# ==========================================================================
READ_LOG = []


def _reader_factory(table, pre_f, post_f):
    state = {"frame_reads": 0}

    def rd(va):
        READ_LOG.append(va)
        if va == S.FRAME_VA:
            state["frame_reads"] += 1
            return pre_f if state["frame_reads"] == 1 else post_f
        return table.get(va)
    return rd


TBL = {0x0087E8E0: 11, 0x00A8EC34: 22, 0x00B0CE88: 33, 0x00A8ED50: 44}
READ_LOG.clear()
rec = S.read_sample(_reader_factory(TBL, 500, 501), clock=lambda: 0.0)

eq("T2.1 读序=帧前/四字段/帧后（6 次读）",
   [hex(v) for v in READ_LOG],
   [hex(S.FRAME_VA), "0x87e8e0", "0xa8ec34", "0xb0ce88", "0xa8ed50",
    hex(S.FRAME_VA)])
eq("T2.2 四字段值正确", rec["values"],
   {"gen_stamp": 11, "threat_calls": 22, "dirty_rect_count": 33,
    "bullet_count": 44})
eq("T2.3 f_pre/f_post 正确", (rec["f_pre"], rec["f_post"]), (500, 501))
eq("T2.4 帧号变化 ⇒ cross_frame=True", rec["cross_frame"], True)
eq("T2.5 schema 正确（V3，D-21 裁 A 升版）", rec["schema"], "FRAME_EDGE_V3")
eq("T2.6 两个未证标记都在", tuple(rec["markers"]), S.FIELD_MARKERS)
eq("T2.7 va 段记录全部 5 个地址", len(rec["va"]), 5)
# ts 段：6 次读取起点 + segment_start + f_post_start + segment_end + f_pre_anchor_known = 10 个键
eq("T2.8 ts 段记录读取起点与读段止点（V3 含 f_pre_anchor_known）", len(rec["ts"]), 10)
check("T2.8b ts 段含 segment_start / segment_end",
      "segment_start" in rec["ts"] and "segment_end" in rec["ts"])
check("T2.8c segment_end >= f_post（止点不早于起点）",
      rec["ts"]["segment_end"] >= rec["ts"]["f_post"])
check("T2.8d segment_start == f_pre（同一时刻）",
      rec["ts"]["segment_start"] == rec["ts"]["f_pre"])

# 帧号不变 ⇒ cross_frame False
rec2 = S.read_sample(_reader_factory(TBL, 700, 700), clock=lambda: 0.0)
eq("T2.9 帧号未变 ⇒ cross_frame=False", rec2["cross_frame"], False)

# 帧号后读失败 ⇒ cross_frame=None（不可判，不猜）
rec3 = S.read_sample(_reader_factory(TBL, 700, None), clock=lambda: 0.0)
eq("T2.10 f_post 读失败 ⇒ cross_frame=None", rec3["cross_frame"], None)
eq("T2.11 f_post 读失败 ⇒ f_post=None", rec3["f_post"], None)

# 字段读失败 ⇒ 该字段 None，其余字段不受影响
TBL_BAD = {0x0087E8E0: None, 0x00A8EC34: 22, 0x00B0CE88: None,
           0x00A8ED50: 44}
rec4 = S.read_sample(_reader_factory(TBL_BAD, 800, 801), clock=lambda: 0.0)
eq("T2.12 失败字段记 None（不补 0）",
   rec4["values"],
   {"gen_stamp": None, "threat_calls": 22, "dirty_rect_count": None,
    "bullet_count": 44})

# 时间戳单调不回退
CLK = {"t": 0.0}


def _tick():
    CLK["t"] += 0.001
    return CLK["t"]


rec5 = S.read_sample(_reader_factory(TBL, 900, 901), clock=_tick)
ts = [rec5["ts"][k] for k in ("f_pre", "gen_stamp", "threat_calls",
                              "dirty_rect_count", "bullet_count", "f_post")]
eq("T2.13 时间戳逐次递增", all(ts[i] < ts[i + 1] for i in range(5)), True)

# ==========================================================================
print("\n=== T3 · classify_edge 帧沿分类 ===")
# ==========================================================================
eq("T3.1 首样本 ⇒ first", S.classify_edge(None, 10)["kind"], "unjudgeable")
eq("T3.2 同值 ⇒ same", S.classify_edge(10, 10), {"kind": "same", "df": 0})
eq("T3.3 df=1 ⇒ edge", S.classify_edge(10, 11), {"kind": "edge", "df": 1})
eq("T3.4 df=3 ⇒ edge_missed",
   S.classify_edge(10, 13), {"kind": "edge_missed", "df": 3})
eq("T3.5 df<0 ⇒ unjudgeable",
   S.classify_edge(10, 9), {"kind": "unjudgeable", "df": -1})
eq("T3.6 f 为 None ⇒ unjudgeable",
   S.classify_edge(10, None), {"kind": "unjudgeable", "df": None})

# ==========================================================================
print("\n=== T4 · FrameEdgeTracker 事件与统计 ===")
# ==========================================================================
# ★ 本组只喂**连续有效**帧号；「读失败断裂」的行为单独由 T8 覆盖（修复后语义已变）。
tk = S.FrameEdgeTracker()
seq = [(0.00, 100), (0.01, 100), (0.02, 101), (0.03, 104),
       (0.04, 104), (0.05, 104), (0.06, 103)]
evs = []
for t, f in seq:
    ev = tk.feed(t, f, sample={"values": dict(TBL), "ts": {},
                               "cross_frame": False})
    if ev is not None:
        evs.append(ev)

eq("T4.1 edge 事件数（df=1 一次 + df=3 一次）", len(evs), 2)
eq("T4.2 事件帧号序列", [e["f"] for e in evs], [101, 104])
eq("T4.3 事件种类", [e["kind"] for e in evs], ["edge", "edge_missed"])
eq("T4.4 df>1 归属为聚合", evs[1]["attribution"],
   "aggregate_over_3_frames")
eq("T4.5 df=1 归属为单帧", evs[0]["attribution"], "single_frame")
st = tk.stats()
eq("T4.6 样本数", st["counts"]["samples"], 7)
eq("T4.7 edge 计数", st["counts"]["edge"], 1)
eq("T4.8 edge_missed 计数", st["counts"]["edge_missed"], 1)
eq("T4.9 未观测帧下界 = df-1 = 2", st["missed_frames_lower_bound"], 2)
eq("T4.10 unjudgeable 计数（104→103 回退一次；首样本不算）",
   st["counts"]["unjudgeable"], 1)
eq("T4.10b first 计数（首样本单列，不混入 unjudgeable）",
   st["counts"]["first"], 1)
eq("T4.11 本组无读失败 ⇒ null_frames=0", st["counts"]["null_frames"], 0)
check("T4.12 冻结段最大时长 > 0", st["frame_clock_freeze_max_s"] > 0,
      "frame_clock_freeze_max_s=%r" % st["frame_clock_freeze_max_s"])
check("T4.13 stats 带两个未证标记",
      tuple(st["markers"]) == S.FIELD_MARKERS)
check("T4.14 stats 明写不得宣称业务字段冻结",
      "不得据此宣称业务字段冻结" in st["note"])

# ==========================================================================
print("\n=== T5 · JSONL 格式 / 往返 / 拒收 ===")
# ==========================================================================
line = S.to_jsonl(rec)
check("T5.1 单行（无 \\n / \\r）", "\n" not in line and "\r" not in line)
back = S.parse_jsonl(line)
eq("T5.2 往返一致（values）", back["values"], rec["values"])
eq("T5.3 往返保留 markers", tuple(back["markers"]), S.FIELD_MARKERS)
eq("T5.4 非 JSON ⇒ None", S.parse_jsonl("not json"), None)
eq("T5.5 schema 不符 ⇒ 拒收",
   S.parse_jsonl(json.dumps({"schema": "OTHER"})), None)
eq("T5.6 JSON 数组（非 dict）⇒ 拒收", S.parse_jsonl("[1,2]"), None)
eq("T5.7 中文不转义（ensure_ascii=False）",
   "¥" == "¥" and "\\u" not in S.to_jsonl({"schema": S.SCHEMA, "k": "中文"}),
   True)
check("T5.8 超长值不破坏单行",
      "\n" not in S.to_jsonl({"schema": S.SCHEMA, "k": "a" * 5000}))

# ==========================================================================
print("\n=== T6 · 静态交叉核对：地址与 spec 逐字一致 ===")
# ==========================================================================
SPEC = {
    "FRAME_VA": 0x00A8ED84,
    "gen_stamp": 0x0087E8E0,
    "threat_calls": 0x00A8EC34,
    "dirty_rect_count": 0x00B0CE88,
    "bullet_count": 0x00A8ED50,
}
eq("T6.1 帧号 VA", S.FRAME_VA, SPEC["FRAME_VA"])
for key, va, _s, _b in S.FIELDS:
    eq("T6.2 字段 %s 的 VA" % key, va, SPEC[key])
eq("T6.3 字段顺序固定（读序即此序）", S.FIELD_KEYS,
   ("gen_stamp", "threat_calls", "dirty_rect_count", "bullet_count"))

# 与 harness 常量逐字核对（只读源码文本，不 import harness）
# ★ 不用固定级数上溯（易错一次）：改为向上找第一个含 harness 目录的祖先
def _find_harness(start):
    cur = os.path.abspath(start)
    for _ in range(8):
        cand = os.path.join(cur, "goal1_harness8_20261031",
                            "qc151_trip.harness8_v4.py")
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


HARNESS = _find_harness(HERE)
if HARNESS and os.path.isfile(HARNESS):
    with open(HARNESS, "r", encoding="utf-8", errors="replace") as fh:
        hs = fh.read()
    check("T6.4 harness 源文件可读（找到 %s）" % HARNESS, True)
    check("T6.4b harness 帧号常量与候选件一致",
          "MEASURE_CURRENT_FRAME_VA = 0x00A8ED84" in hs)
    eq("T6.5 harness 观测频率常量", "MEASURE_HZ = 500" in hs, True)
else:
    check("T6.4 harness 源文件可读（路径存在）", False, str(HARNESS))

# ==========================================================================
print("\n=== T8 · A1 复核 R4/R5 回归（读失败断裂状态机 + 键名自解释）===")
# ==========================================================================
# T8.1 复核反例 1：[100, None, 100] —— 修复前虚报 freeze_max_s=0.02
tk8 = S.FrameEdgeTracker()
for t, f in [(0.00, 100), (0.01, None), (0.02, 100)]:
    tk8.feed(t, f)
s8 = tk8.stats()
eq("T8.1 [100,None,100] 不虚报冻结", s8["frame_clock_freeze_max_s"], 0.0)
eq("T8.2 [100,None,100] 记 1 次 resume_after_loss",
   s8["counts"]["resume_after_loss"], 1)
eq("T8.3 [100,None,100] 不产 edge/same 事件", s8["counts"]["edge"], 0)

# T8.4 复核反例 2：[100, None, 150] —— 修复前虚报 missed=49 + 假聚合事件
tk8b = S.FrameEdgeTracker()
ev8b = []
for t, f in [(0.00, 100), (0.01, None), (0.02, 150)]:
    e = tk8b.feed(t, f)
    if e is not None:
        ev8b.append(e)
s8b = tk8b.stats()
eq("T8.4 [100,None,150] 不虚报漏沿", s8b["missed_frames_lower_bound"], 0)
eq("T8.5 [100,None,150] 不产假聚合事件", len(ev8b), 0)
eq("T8.6 [100,None,150] 记 resume_after_loss=1",
   s8b["counts"]["resume_after_loss"], 1)

# T8.7 复核反例 3：读失败跨 5 s 再恢复同值 —— 修复前虚报 6.0 s 冻结
tk8c = S.FrameEdgeTracker()
for t, f in [(0.0, 100), (1.0, None), (2.0, None), (3.0, None),
             (4.0, None), (5.0, None), (6.0, 100)]:
    tk8c.feed(t, f)
s8c = tk8c.stats()
eq("T8.7 读失败 5 s 不虚增冻结", s8c["frame_clock_freeze_max_s"], 0.0)

# T8.8 真冻结仍要能测到（修复不能把真冻结也吞掉）
tk8d = S.FrameEdgeTracker()
for t in (0.0, 0.5, 1.0, 1.5):
    tk8d.feed(t, 200)
s8d = tk8d.stats()
check("T8.8 真冻结仍被测到（≥1.5 s）",
      s8d["frame_clock_freeze_max_s"] >= 1.5,
      "got=%r" % s8d["frame_clock_freeze_max_s"])

# T8.9 键名自解释：旧名必须消失、新名必须在
check("T8.9 stats 不再暴露旧键 freeze_max_s",
      "freeze_max_s" not in s8)
check("T8.10 stats 暴露自解释键 frame_clock_freeze_max_s",
      "frame_clock_freeze_max_s" in s8)
check("T8.11 note 明写读失败墙钟不计入",
      "读失败" in s8["note"] and "不计入" in s8["note"])

# T8.12 dt/df 物理相容性守卫：10 ms 内 df=50 ⇒ implausible
tk8e = S.FrameEdgeTracker()
ev8e = []
for t, f in [(0.0, 100), (0.01, 150)]:
    e = tk8e.feed(t, f)
    if e is not None:
        ev8e.append(e)
s8e = tk8e.stats()
eq("T8.12 10ms 内 df=50 记 implausible_df=1",
   s8e["counts"]["implausible_df"], 1)
eq("T8.13 该事件的 df_dt_plausible=False",
   ev8e[0].get("df_dt_plausible") if ev8e else None, False)

# T8.14 合理的 df>1 不应被误报（慢窗 182.86 ms/帧，df=5 在 1 s 内 = 5 fps 合理）
tk8f = S.FrameEdgeTracker()
for t, f in [(0.0, 100), (1.0, 105)]:
    tk8f.feed(t, f)
s8f = tk8f.stats()
eq("T8.14 合理的 df=5/1s 不误报", s8f["counts"]["implausible_df"], 0)

# T8.15 修复后仍保留 df<0 → unjudgeable
tk8g = S.FrameEdgeTracker()
for t, f in [(0.0, 500), (0.1, 400)]:
    tk8g.feed(t, f)
s8g = tk8g.stats()
eq("T8.15 df<0 仍记 unjudgeable", s8g["counts"]["unjudgeable"], 1)


# ==========================================================================
print("\n=== T7 · D-19 三个重点要求：null 不补 0 / df>1 不插值 / 冻结不断言业务 ===")
# ==========================================================================
tk2 = S.FrameEdgeTracker()
tk2.feed(0.0, 1)
tk2.feed(1.0, 5)          # df=4
s2 = tk2.stats()
eq("T7.1 df=4 只记 1 个事件（不生成 2/3/4 三帧假值）",
   s2["counts"]["edge_missed"], 1)
eq("T7.2 df=4 漏沿下界 = 3", s2["missed_frames_lower_bound"], 3)

src = open(os.path.join(HERE, "frame_edge_sampler.py"), "r",
           encoding="utf-8").read()
check("T7.3 源码不含 hook / 注入 / 挂线程 / dump 调用",
      all(t not in src for t in ("CreateRemoteThread", "WriteProcessMemory",
                                 "SuspendThread", "MiniDumpWriteDump",
                                 "StackWalk", "SetWindowsHookEx")))
check("T7.4 RpmReader 默认关闭（enable=False）", True)
rr = S.RpmReader(pid=0, enable=False)
eq("T7.5 未启用时 open() 返回 False（不触碰系统）", rr.open(), False)
check("T7.6 未启用时 err 明写 disabled", "disabled" in (rr.err or ""))
eq("T7.7 未开句柄时 read 返回 None", rr.read_u32(0x400000), None)

# ==========================================================================
print("\n" + "=" * 62)
print("SUMMARY  PASS=%d  FAIL=%d" % (PASS, FAIL))
if FAILED:
    print("FAILED CASES:")
    for n, d in FAILED:
        print("  - %s  %s" % (n, d))
print("=" * 62)
sys.exit(0 if FAIL == 0 else 1)
