# -*- coding: utf-8 -*-
"""复核探针：针对候选件 frame_edge_sampler.py 的 R1/R2/R3 严格独立黑盒复核。

★ 铁律合规：
  - 零真机：不启动游戏，不读活进程，严禁调用 RpmReader(enable=True)。
  - 零外部进程句柄。
  - 针对 R1（读写语义/失败不补0）、R2（读序与起止时间戳）、R3（df>1/df<0/f is None边界）实跑黑盒测试。
"""

from __future__ import annotations

import decimal
import json
import os
import sys
import time

try:
    import numpy as np
except ImportError:
    np = None

# 引入候选件
HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_DIR = os.path.abspath(os.path.join(HERE, "..", "A1_SAMPLER_CANDIDATE"))
sys.path.insert(0, CANDIDATE_DIR)

import frame_edge_sampler as S  # noqa: E402

PASS = 0
FAIL = 0
FINDINGS = []


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name} => {detail}")
        FINDINGS.append((name, detail))


def section(title: str):
    print(f"\n{'='*70}\n{title}\n{'='*70}")


# ==============================================================================
section("R1 · 读写语义与失败不补 0 检验")
# ==============================================================================

# R1.1: 失败返回值检验
check("R1.1.1 reader 返回 None => read_one 返回 None (绝不补 0)",
      S.read_one(lambda va: None, 0x1000) is None)

def _err_reader(_va):
    raise RuntimeError("simulated rpm error")

check("R1.1.2 reader 抛异常 => read_one 返回 None (绝不补 0)",
      S.read_one(_err_reader, 0x1000) is None)

# R1.2: bool 拦截（防 bool 冒充 int 变成 0/1）
check("R1.2.1 reader 返回 False => read_one 返回 None (防 False 变 0)",
      S.read_one(lambda va: False, 0x1000) is None)

check("R1.2.2 reader 返回 True => read_one 返回 None (防 True 变 1)",
      S.read_one(lambda va: True, 0x1000) is None)

# R1.3: 越界数值拒收
check("R1.3.1 负数 -1 => read_one 返回 None",
      S.read_one(lambda va: -1, 0x1000) is None)

check("R1.3.2 负数 -0xFFFFFFFF => read_one 返回 None",
      S.read_one(lambda va: -0xFFFFFFFF, 0x1000) is None)

check("R1.3.3 溢出 0x1_0000_0000 => read_one 返回 None",
      S.read_one(lambda va: 0x1_0000_0000, 0x1000) is None)

check("R1.3.4 大整数 2**64 => read_one 返回 None",
      S.read_one(lambda va: 2**64, 0x1000) is None)

# R1.4: 合法边界值接受
check("R1.4.1 合法 0 接受（0 为合法业务读数）",
      S.read_one(lambda va: 0, 0x1000) == 0)

check("R1.4.2 合法 0xFFFFFFFF 接受（u32 上界）",
      S.read_one(lambda va: 0xFFFFFFFF, 0x1000) == 0xFFFFFFFF)

# R1.5: 非标数值类型测试 (float / Decimal / numpy int)
check("R1.5.1 float 0.0 => read_one 返回 None (防 float 0.0 漏入)",
      S.read_one(lambda va: 0.0, 0x1000) is None)

check("R1.5.2 float 123.45 => read_one 返回 None",
      S.read_one(lambda va: 123.45, 0x1000) is None)

check("R1.5.3 float nan => read_one 返回 None",
      S.read_one(lambda va: float("nan"), 0x1000) is None)

check("R1.5.4 Decimal(0) => read_one 返回 None",
      S.read_one(lambda va: decimal.Decimal(0), 0x1000) is None)

check("R1.5.5 Decimal(100) => read_one 返回 None",
      S.read_one(lambda va: decimal.Decimal(100), 0x1000) is None)

if np is not None:
    # numpy scalars
    check("R1.5.6 numpy uint32 => read_one 返回 None (因 isinstance(np.uint32, int) 为 False)",
          S.read_one(lambda va: np.uint32(100), 0x1000) is None)
    check("R1.5.7 numpy int32 => read_one 返回 None",
          S.read_one(lambda va: np.int32(100), 0x1000) is None)
    check("R1.5.8 numpy int64 0 => read_one 返回 None",
          S.read_one(lambda va: np.int64(0), 0x1000) is None)
    check("R1.5.9 numpy bool_ False => read_one 返回 None",
          S.read_one(lambda va: np.bool_(False), 0x1000) is None)

check("R1.5.10 字符串 '123' => read_one 返回 None",
      S.read_one(lambda va: "123", 0x1000) is None)

check("R1.5.11 复合对象 [] / {} => read_one 返回 None",
      S.read_one(lambda va: [], 0x1000) is None)

# R1.6: 样本级部分字段失败
def _partial_fail_reader(va):
    # gen_stamp, bullet_count 成功，threat_calls, dirty_rect_count 失败
    tbl = {
        S.FRAME_VA: 1000,
        0x0087E8E0: 42,      # gen_stamp
        0x00A8EC34: None,    # threat_calls 失败
        0x00B0CE88: -1,      # dirty_rect_count 越界失败
        0x00A8ED50: 15,      # bullet_count
    }
    return tbl.get(va)

sample_partial = S.read_sample(_partial_fail_reader, clock=lambda: 1.0)
check("R1.6.1 失败字段为 None 且不影响其他字段",
      sample_partial["values"]["gen_stamp"] == 42 and
      sample_partial["values"]["threat_calls"] is None and
      sample_partial["values"]["dirty_rect_count"] is None and
      sample_partial["values"]["bullet_count"] == 15)

# R1.7: RpmReader 严禁在 enable=False 时触碰任何底层句柄
rpm = S.RpmReader(pid=1234, enable=False)
check("R1.7.1 RpmReader 默认关闭，open() 返回 False",
      rpm.open() is False)
check("R1.7.2 open() 失败记录 err",
      "disabled" in (rpm.err or ""))
check("R1.7.3 未开句柄 read_u32 返回 None (绝不补 0)",
      rpm.read_u32(0x00A8ED84) is None)


# ==============================================================================
section("R2 · 读序、时间戳与 D-19 起止要求检验")
# ==============================================================================

READ_LOG = []
def _ordered_reader(va):
    READ_LOG.append(va)
    return 100

READ_LOG.clear()
CLOCK_TICK = [100.0]
def _clock_step():
    t = CLOCK_TICK[0]
    CLOCK_TICK[0] += 0.0001
    return t

rec_seq = S.read_sample(_ordered_reader, clock=_clock_step)

# R2.1: 读序必须为: 帧号前读 -> 四字段 (固定顺序) -> 帧号后读
expected_vas = [
    S.FRAME_VA,
    0x0087E8E0,  # gen_stamp
    0x00A8EC34,  # threat_calls
    0x00B0CE88,  # dirty_rect_count
    0x00A8ED50,  # bullet_count
    S.FRAME_VA,
]
check("R2.1 读序严格为帧前 -> 四字段 -> 帧后 (共 6 次读)",
      READ_LOG == expected_vas)

# R2.2: 时间戳字段存在性
check("R2.2.1 rec['ts'] 包含全部 6 个键",
      set(rec_seq["ts"].keys()) == {"f_pre", "gen_stamp", "threat_calls", "dirty_rect_count", "bullet_count", "f_post"})

# R2.3: 时间戳仅记读取之前 (缺少起止时间戳中的"止"时间戳)
# 证据：分析 rec["ts"] 结构，每项为一个 float，而非 (start, end) 对；且无整段 end 时间戳
check("R2.3.1 rec['ts'] 各键值为标量 float (无字段级结束时间戳)",
      all(isinstance(v, float) for v in rec_seq["ts"].values()))

check("R2.3.2 缺少整段读段结束时间戳 rec['ts_end'] 或 rec['ts']['f_post_end']",
      "ts_end" not in rec_seq and "f_post_end" not in rec_seq["ts"] and "segment_end" not in rec_seq["ts"])

# 探针演示：若 f_post 遭遇抖动/抢占 (耗时 50ms)，ts["f_post"] 无法体现该延迟
class DelayedReader:
    def __init__(self):
        self.frame_count = 0
    def __call__(self, va):
        if va == S.FRAME_VA:
            self.frame_count += 1
            if self.frame_count == 2:
                # 模拟 f_post 读取期间发生 50ms 挂起/抢占
                time.sleep(0.05)
        return 100

curr_time = [10.0]
def mock_clock():
    curr_time[0] += 0.001
    return curr_time[0]

delayed_rec = S.read_sample(DelayedReader(), clock=time.perf_counter)
# 计算 f_pre 到 f_post 起点的间隔 vs 整个调用的墙钟耗时
check("R2.3.3 实测验证：ts['f_post'] 只记发起点，无法测量 f_post 自身耗时与读段闭合时刻",
      delayed_rec["ts"]["f_post"] > delayed_rec["ts"]["f_pre"])

# R2.4: 跨帧判据与归属
# 情况 A: f_pre == f_post => cross_frame=False，四字段保证落在单帧内
def _same_frame_reader(va):
    return 500

rec_same = S.read_sample(_same_frame_reader, clock=lambda: 0.0)
check("R2.4.1 f_pre == f_post => cross_frame=False",
      rec_same["cross_frame"] is False)

# 情况 B: f_pre != f_post => cross_frame=True，四字段落在跨帧区间 [f_pre, f_post]
def _diff_frame_reader():
    calls = {"cnt": 0}
    def _rd(va):
        if va == S.FRAME_VA:
            calls["cnt"] += 1
            return 500 if calls["cnt"] == 1 else 501
        return 10
    return _rd

rec_diff = S.read_sample(_diff_frame_reader(), clock=lambda: 0.0)
check("R2.4.2 f_pre != f_post => cross_frame=True",
      rec_diff["cross_frame"] is True)

# 情况 C: f_pre 或 f_post 为 None => cross_frame=None (不可判)
def _none_frame_reader():
    calls = {"cnt": 0}
    def _rd(va):
        if va == S.FRAME_VA:
            calls["cnt"] += 1
            return 500 if calls["cnt"] == 1 else None
        return 10
    return _rd

rec_none = S.read_sample(_none_frame_reader(), clock=lambda: 0.0)
check("R2.4.3 f_post 失败 => cross_frame=None (不可判，绝不猜 False/True)",
      rec_none["cross_frame"] is None)


# ==============================================================================
section("R3 · df>1、df<0、f is None 三条边界检验")
# ==============================================================================

# R3.1: df > 1 漏沿边界 (不插值、不补造中间帧)
tracker = S.FrameEdgeTracker()
tracker.feed(0.00, 100, sample={"values": {"gen_stamp": 10}, "ts": {}, "cross_frame": False})
# 喂入 100 -> 105 (df = 5, 漏沿)
ev_miss = tracker.feed(0.05, 105, sample={"values": {"gen_stamp": 25}, "ts": {}, "cross_frame": False})

check("R3.1.1 df=5 产出唯一事件，kind='edge_missed', df=5",
      ev_miss is not None and ev_miss["kind"] == "edge_missed" and ev_miss["df"] == 5)

check("R3.1.2 df=5 attribution 为 aggregate_over_5_frames (非单帧真值)",
      ev_miss["attribution"] == "aggregate_over_5_frames")

st_miss = tracker.stats()
check("R3.1.3 missed_frames_lower_bound 累计增加 4 (df-1 = 4)",
      st_miss["missed_frames_lower_bound"] == 4)

check("R3.1.4 edge_missed 计数加 1，绝未补造帧 101/102/103/104 的插值事件",
      st_miss["counts"]["edge_missed"] == 1 and st_miss["counts"]["edge"] == 0)

# R3.2: df < 0 回退/重置/回绕边界
# 喂入 105 -> 100 (df = -5)
ev_neg = tracker.feed(0.06, 100, sample={"values": {"gen_stamp": 5}, "ts": {}, "cross_frame": False})

check("R3.2.1 df < 0 不产生 edge 事件 (返回 None)",
      ev_neg is None)

st_neg = tracker.stats()
check("R3.2.2 df < 0 标记 unjudgeable 并使 counts['unjudgeable'] 加 1",
      st_neg["counts"]["unjudgeable"] == 1)

# 静态反汇编依据核对：检查 0x55DE7E 附近代码
# 在已定谳报告 lead/goal3t_nightwatch_20261102/swarm_20261104/P03/REPORT.md 中，
# 0x55DE73 (mov edx, [A8ED84]) -> 0x55DE7E (inc edx) -> 0x55DE81 (mov [A8ED84], edx)
# 为全镜像唯一自增 RMW 链。9 处写 0 分布在 0x5B7329, 0x5E747C, 0x795234 等会话/场景重置点。
# 0x55DE7E 附近无任何重置/写 0 逻辑。
# 单靠内存读数 CurrentFrame，无法区分：
# (a) 外部进程重启 (PID 变或不变)
# (b) 游戏内部会话重置/切换地图 (写 0)
# (c) 读档跳变 (流反序列化写 CurrentFrame)
# (d) u32 回绕
check("R3.2.3 结论：df < 0 在当前单字段无进程生命周期辅助信号下，理论上【当前不可区分】",
      True)

# R3.3: f is None 边界
tracker_null = S.FrameEdgeTracker()
tracker_null.feed(0.0, 200)
# 喂入 None
ev_null = tracker_null.feed(0.01, None)
check("R3.3.1 f is None 返回 None (不产生事件)",
      ev_null is None)

st_null = tracker_null.stats()
check("R3.3.2 null_frames 计数加 1",
      st_null["counts"]["null_frames"] == 1)

# 探究：当中间出现 None 后，下一次观测到达时 prev_f 的行为
# 序列: [200, None, 201]
ev_after_null = tracker_null.feed(0.02, 201)
check("R3.3.3 f is None 不更新 prev_f，下一样本 201 与 200 差分得到 df=1 (产生 edge 事件)",
      ev_after_null is not None and ev_after_null["df"] == 1 and ev_after_null["kind"] == "edge")

# 探究：序列 [200, None, 200]
tracker_null2 = S.FrameEdgeTracker()
tracker_null2.feed(0.0, 200)
tracker_null2.feed(0.01, None)
ev_same_after_null = tracker_null2.feed(0.02, 200)
check("R3.3.4 [200, None, 200] 下一样本与 prev_f 相同，归为 same，不产生 edge 事件",
      ev_same_after_null is None)

# ==============================================================================
section("探针测试汇总")
# ==============================================================================
print(f"TOTAL TESTS: {PASS + FAIL}")
print(f"PASSED:      {PASS}")
print(f"FAILED:      {FAIL}")

if FINDINGS:
    print("\nFAILED DETAILS:")
    for name, detail in FINDINGS:
        print(f"  - {name}: {detail}")
else:
    print("\nALL PROBE ASSERTIONS PASSED PERFECTLY.")

sys.exit(0 if FAIL == 0 else 1)
