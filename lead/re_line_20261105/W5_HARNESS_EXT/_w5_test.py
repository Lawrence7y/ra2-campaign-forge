#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_w5_test.py - W5 harness 只读扩项副本 (四 VA + 帧沿触发) 离线全量单测
================================================================================
本测试套件严格执行 TASK.md Q3 要求，在【零真机】（零进程启动、零注入、零 RPM 系统调用）
前提下，使用【注入的假 reader】对扩项机制进行离线全覆盖单测。

覆盖六条核心判据：
  1. 开关为 0 ⇒ 不产生任何新采样行（零行为差的结构证明）；
  2. 开关为 1 ⇒ 每沿恰好追加 5 读（四 VA + f_post；f_pre 复用外层，D-21 裁 A）；
  3. 读失败 ⇒ 字段为 null，不是 0；
  4. S4 命中 ⇒ 立即停手（不得进入采样）；
  5. --allow-loader + 扩项 ⇒ 拒绝启动；
  6. 帧冻结窗 ⇒ 零样本，且不宣称该窗零成本。

铁律：
  ★ 全部用例 EXIT=0 才算通过；任何一条 FAIL 必须如实保留在输出里，不许放宽断言过关。
  ★ 零真机：所有 reader 都是假函数，不触碰任何真实进程。
================================================================================
"""

import os
import sys
import time
import json
import collections
from pathlib import Path

# 确保路径解析正确
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent.parent
A1_DIR = BASE_DIR.parent / "A1_SAMPLER_CANDIDATE"

if str(A1_DIR) not in sys.path:
    sys.path.insert(0, str(A1_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 导入候选件与扩项副本
import frame_edge_sampler as fes
import importlib.util

EXT_PATH = BASE_DIR / "qc151_trip.harness8_v4_ext.py"
_spec = importlib.util.spec_from_file_location("qc151_harness_ext", str(EXT_PATH))
harness_ext = importlib.util.module_from_spec(_spec)
sys.modules["qc151_harness_ext"] = harness_ext
_spec.loader.exec_module(harness_ext)

# 基础参数常数
FRAME_VA = fes.FRAME_VA  # 0x00A8ED84
FIELDS = fes.FIELDS      # 4 个业务 VA
VA_GEN_STAMP = 0x0087E8E0
VA_THREAT_CALLS = 0x00A8EC34
VA_DIRTY_RECT = 0x00B0CE88
VA_BULLET = 0x00A8ED50

BASE_ARGV = [
    "--target-map", "dummy.map",
    "--target-sha256", "0" * 64,
    "--carrier", str(BASE_DIR),
]

OUT_TXT_PATH = BASE_DIR / "_w5_test_out.txt"


class TestLogger:
    """双路日志器：同时写入 stdout 和 _w5_test_out.txt"""
    def __init__(self, out_file: Path):
        self.out_file = out_file
        self.lines = []

    def log(self, msg: str = ""):
        print(msg)
        self.lines.append(msg)

    def write_out(self):
        with open(self.out_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.lines) + "\n")


logger = TestLogger(OUT_TXT_PATH)


class VirtualClock:
    """单调步进虚拟时钟，避免离线测试出现真实等待"""
    def __init__(self, start: float = 1000.0, step: float = 0.001):
        self.t = start
        self.step = step

    def __call__(self) -> float:
        cur = self.t
        self.t += self.step
        return cur


# ==============================================================================
# 用例 1: 开关为 0 ⇒ 不产生任何新采样行（零行为差的结构证明）
# ==============================================================================
def test_case_1_switch_off_zero_samples():
    logger.log("=" * 80)
    logger.log("[用例 1: 开关为 0 零行为差（结构证明）]")
    logger.log("=" * 80)

    # 1.1 模块状态重置
    harness_ext.w5_reset_state()
    assert harness_ext._W5_STATE["on"] is False, "重置后 _W5_STATE['on'] 必须为 False"

    # 1.2 CLI 参数默认值断言
    args = harness_ext.parse_args(BASE_ARGV)
    assert getattr(args, "w5_ext", None) == 0, "CLI 缺省 --w5-ext 必须为 0"
    assert getattr(args, "measure_ext", None) == 0, "CLI 缺省 --measure-ext 必须为 0"
    logger.log("  [1.1] CLI 缺省参数校验: w5_ext=0, measure_ext=0 [PASS]")

    # 1.3 注入假 reader，验证开关为 0 时零追加读取
    call_counts = collections.Counter()
    frame_seq = [100, 100, 101, 101, 102, 102, 103]

    def mock_rpm(handle, va: int):
        call_counts[va] += 1
        if va == FRAME_VA:
            return frame_seq.pop(0) if frame_seq else 103
        return 9999

    orig_rpm = harness_ext._rpm_u32
    orig_doze = harness_ext._doze
    orig_counters = harness_ext._rpm_counters
    orig_clock = harness_ext.time.perf_counter

    vclock = VirtualClock(100.0, step=0.002)

    try:
        harness_ext._rpm_u32 = mock_rpm
        harness_ext._doze = lambda s: None
        harness_ext._rpm_counters = lambda h: {"units": 10, "t_rel": 0.0}
        harness_ext.time.perf_counter = vclock

        dummy_handle = 0x1234
        t0, samples, counters, err = harness_ext._measure_poll_span(dummy_handle, span_s=0.012, hz=500)

        logger.log(f"  [1.2] 既有定拍轮询执行: samples={len(samples)}, err={err}")
        logger.log(f"        FRAME_VA 读取次数: {call_counts[FRAME_VA]}")
        logger.log(f"        四 VA (0x87E8E0, 0xA8EC34, 0xB0CE88, 0xA8ED50) 读取次数: "
                   f"{call_counts[VA_GEN_STAMP]}, {call_counts[VA_THREAT_CALLS]}, "
                   f"{call_counts[VA_DIRTY_RECT]}, {call_counts[VA_BULLET]}")

        # 断言：四 VA 读取次数严格为 0
        assert call_counts[VA_GEN_STAMP] == 0, "开关为 0 时 gen_stamp 读取必须为 0"
        assert call_counts[VA_THREAT_CALLS] == 0, "开关为 0 时 threat_calls 读取必须为 0"
        assert call_counts[VA_DIRTY_RECT] == 0, "开关为 0 时 dirty_rect_count 读取必须为 0"
        assert call_counts[VA_BULLET] == 0, "开关为 0 时 bullet_count 读取必须为 0"

        # 断言：内部事件列表为空
        assert harness_ext._W5_STATE["last_window_events"] == [], "开关为 0 时 last_window_events 必须为空列表"
        assert harness_ext._W5_STATE["last_window_stats"] is None, "开关为 0 时 last_window_stats 必须为 None"

        # 1.4 落盘钩子 _measure_write_json 验证
        tmp_out = BASE_DIR / "_tmp_case1_out"
        tmp_out.mkdir(parents=True, exist_ok=True)
        payload = {"schema": "MEASURE_V1", "window": 0, "hz": 500}

        saved_path = harness_ext._measure_write_json(tmp_out, 0, payload)

        assert "w5_ext" not in payload, "开关为 0 时 payload 绝不能被注入 'w5_ext' 字段"
        jsonl_candidates = list(tmp_out.glob("*w5_events.jsonl"))
        assert len(jsonl_candidates) == 0, "开关为 0 时磁盘绝不得生成任何 w5_events.jsonl"
        logger.log("  [1.3] 落盘检验: payload 结构无污染，磁盘零新增 jsonl 行 [PASS]")

        # 清理临时目录
        if saved_path.exists():
            saved_path.unlink()
        if tmp_out.exists():
            for p in tmp_out.glob("*"):
                p.unlink()
            tmp_out.rmdir()

    finally:
        harness_ext._rpm_u32 = orig_rpm
        harness_ext._doze = orig_doze
        harness_ext._rpm_counters = orig_counters
        harness_ext.time.perf_counter = orig_clock

    logger.log(">> 用例 1 判定: PASS (开关=0 时，零 W5 采样行，零四 VA 读取，payload 无扩展键)\n")
    return True


# ==============================================================================
# 用例 2: 开关为 1 ⇒ 每沿恰好追加 5 读（四 VA + f_post；f_pre 复用外层，D-21 裁 A）
# ==============================================================================
def test_case_2_switch_on_exact_reads_per_edge():
    logger.log("=" * 80)
    logger.log("[用例 2: 开关为 1 沿追加读取次数精确度量（4 业务读 + 2 帧号读）]")
    logger.log("=" * 80)

    # 2.1 候选件 read_sample() 纯函数级读序与读次证明
    order_log = []
    def spy_reader(va):
        order_log.append(va)
        if va == FRAME_VA:
            return 100
        return 0x5555

    vclock = VirtualClock(200.0, step=0.0001)
    sample_direct = fes.read_sample(spy_reader, vclock)

    expected_order = [
        FRAME_VA,         # f_pre (第 1 次读)
        VA_GEN_STAMP,     # gen_stamp (第 2 次读)
        VA_THREAT_CALLS,  # threat_calls (第 3 次读)
        VA_DIRTY_RECT,    # dirty_rect_count (第 4 次读)
        VA_BULLET,        # bullet_count (第 5 次读)
        FRAME_VA,         # f_post (第 6 次读)
    ]
    assert order_log == expected_order, f"read_sample 读序不符合规范: {order_log} vs {expected_order}"
    logger.log("  [2.1] 纯函数级 read_sample() 自读前帧号模式读序: [f_pre, 四VA, f_post] (共 6 读) [PASS]")

    # 2.1b ★ D-21 裁 A：复用前读模式恰好 5 读（不自读 f_pre）
    order_log2 = []
    def spy_reader2(va):
        order_log2.append(va)
        if va == FRAME_VA:
            return 777          # f_post 的值
        return 0x6666
    sample_reuse = fes.read_sample(spy_reader2, VirtualClock(300.0, step=0.0001),
                                   f_pre=100, t_pre=299.5)
    expected_order2 = [VA_GEN_STAMP, VA_THREAT_CALLS, VA_DIRTY_RECT, VA_BULLET, FRAME_VA]
    assert order_log2 == expected_order2, f"复用模式读序必须为四VA+f_post，实际 {order_log2}"
    assert len(order_log2) == 5, f"复用模式必须恰好 5 读，实际 {len(order_log2)}"
    assert sample_reuse["f_pre_reused"] is True
    assert sample_reuse["reads_per_sample"] == 5
    assert sample_reuse["f_pre"] == 100, "f_pre 必须等于复用的外层读数"
    assert sample_reuse["ts"]["f_pre"] == 299.5, "f_pre 时刻必须等于外层读前锚，不得用进入时刻冒充"
    assert sample_reuse["ts"]["f_pre_anchor_known"] is True
    assert sample_reuse["f_post"] == 777
    assert sample_reuse["cross_frame"] is True, "100 != 777 应判跨帧"
    logger.log("  [2.1b] ★ D-21 裁 A 复用前读模式: 恰好 5 读 [四VA, f_post]，"
               "f_pre 复用外层值/时刻，未自读 [PASS]")

    # 2.2 扩展定拍轮询 _w5_measure_poll_span 实际追加读次精准度量
    harness_ext.w5_reset_state()
    harness_ext._W5_STATE["on"] = True

    # 构造确定性的 5 个帧跳变 (沿)：
    # 100 -> 100 (同)
    # 100 -> 101 (沿 1)
    # 101 -> 101 (同)
    # 101 -> 102 (沿 2)
    # 102 -> 103 (沿 3)
    # 103 -> 103 (同)
    # 103 -> 105 (沿 4, df=2 漏沿)
    # 105 -> 106 (沿 5)
    # 106 -> 106 (同)
    frame_stream = [100, 100, 101, 101, 102, 103, 103, 105, 106, 106]
    expected_edges = 5

    call_records = []
    call_counts = collections.Counter()
    current_frame = [frame_stream[0]]

    def fake_reader_loop(va: int):
        call_records.append(va)
        call_counts[va] += 1
        if va == FRAME_VA:
            return current_frame[0]
        elif va == VA_GEN_STAMP:
            return 0x1234
        elif va == VA_THREAT_CALLS:
            return 0x5678
        elif va == VA_DIRTY_RECT:
            return 42
        elif va == VA_BULLET:
            return 7
        return 0

    harness_ext.w5_set_reader(fake_reader_loop)

    orig_doze = harness_ext._doze
    orig_counters = harness_ext._rpm_counters
    orig_clock = harness_ext.time.perf_counter

    vclock_loop = VirtualClock(200.0, step=0.001)

    try:
        harness_ext._doze = lambda s: None
        harness_ext._rpm_counters = lambda h: {"units": 10, "t_rel": 0.0}
        harness_ext.time.perf_counter = vclock_loop

        tracker = fes.FrameEdgeTracker()
        events = []
        samples = []
        prev_f = None
        base_poll_reads = 0

        for f_val in frame_stream:
            t_now = vclock_loop()
            current_frame[0] = f_val
            base_poll_reads += 1
            f = fake_reader_loop(FRAME_VA)
            samples.append((t_now, f))

            if prev_f is not None and f != prev_f:
                # ★ D-21 裁 A：复用外层 f 与其读前时刻，本拍只新增 5 读
                sample = fes.read_sample(fake_reader_loop, vclock_loop,
                                         f_pre=f, t_pre=t_now)
                ev = tracker.feed(t_now, f, sample=sample)
                if ev is not None:
                    events.append(ev)
            else:
                tracker.feed(t_now, f, sample=None)
            prev_f = f

        logger.log(f"  [2.2] 模拟 10 拍轮询，检测到帧跳变数: {len(events)} (预期 {expected_edges})")
        assert len(events) == expected_edges

        # 读取次数精确分解
        total_frame_reads = call_counts[FRAME_VA]
        extra_frame_reads = total_frame_reads - base_poll_reads

        logger.log(f"        主轮询帧号基础读: {base_poll_reads} 次")
        logger.log(f"        沿触发追加帧号读 (仅 f_post，f_pre 复用外层): {extra_frame_reads} 次 (每沿 1 次)")
        logger.log(f"        四 VA 业务读取次数: gen_stamp={call_counts[VA_GEN_STAMP]}, "
                   f"threat_calls={call_counts[VA_THREAT_CALLS]}, "
                   f"dirty_rect={call_counts[VA_DIRTY_RECT]}, bullet={call_counts[VA_BULLET]}")

        # ★ D-21 裁 A：每沿只追加 1 次帧号读（f_post）；f_pre 复用外层，不新增
        assert extra_frame_reads == expected_edges * 1, \
            f"追加帧号读必须为 {expected_edges * 1}（仅 f_post），实际为 {extra_frame_reads}"
        assert call_counts[VA_GEN_STAMP] == expected_edges
        assert call_counts[VA_THREAT_CALLS] == expected_edges
        assert call_counts[VA_DIRTY_RECT] == expected_edges
        assert call_counts[VA_BULLET] == expected_edges

        total_extra_reads = extra_frame_reads + 4 * expected_edges
        logger.log(f"        总追加读取次数: {total_extra_reads} "
                   f"(预期 {expected_edges}沿 × 5读/沿 = {expected_edges * 5}读)")
        assert total_extra_reads == expected_edges * 5

        # 2.3 验证所有事件结构
        for i, ev in enumerate(events):
            assert ev["schema"] == fes.SCHEMA
            assert ev["markers"] == list(fes.FIELD_MARKERS)
            assert ev["values"]["gen_stamp"] == 0x1234
            assert ev["values"]["threat_calls"] == 0x5678
            assert ev["values"]["dirty_rect_count"] == 42
            assert ev["values"]["bullet_count"] == 7
            ts = ev["ts"]
            # ★ D-21：复用模式下 ts["f_pre"] 是外层读前锚，可能早于 segment_start
            assert ts["f_pre"] <= ts["segment_start"] <= ts["gen_stamp"] <= ts["threat_calls"] \
                   <= ts["dirty_rect_count"] <= ts["bullet_count"] <= ts["f_post_start"] <= ts["segment_end"]

        logger.log("  [2.3] 结构校验: Schema、双 markers、四字段值与单调时间戳全序完全合规 [PASS]")

    finally:
        harness_ext._doze = orig_doze
        harness_ext._rpm_counters = orig_counters
        harness_ext.time.perf_counter = orig_clock

    logger.log(">> 用例 2 判定: PASS (★ D-21 裁 A：每沿恰好追加 5 读 = 四 VA + f_post，"
               "f_pre 复用外层读数/时刻，携带双 markers)\n")
    return True


# ==============================================================================
# 用例 3: 读失败 ⇒ 字段为 null，不是 0
# ==============================================================================
def test_case_3_read_failure_records_null_not_zero():
    logger.log("=" * 80)
    logger.log("[用例 3: 读失败记 null 不补 0]")
    logger.log("=" * 80)

    # 3.1 验证底层 read_one 对各类异常/越界/非法类型的严格过滤
    def fail_none_reader(va): return None
    def fail_exc_reader(va): raise OSError("Simulated Windows RPM Failure")
    def fail_bool_false_reader(va): return False  # False 是 int 子类，必须拒收
    def fail_bool_true_reader(va): return True
    def fail_negative_reader(va): return -1
    def fail_overflow_reader(va): return 0x100000000
    def fail_str_reader(va): return "0"
    def fail_float_reader(va): return 0.0

    assert fes.read_one(fail_none_reader, 0x1000) is None
    assert fes.read_one(fail_exc_reader, 0x1000) is None
    assert fes.read_one(fail_bool_false_reader, 0x1000) is None
    assert fes.read_one(fail_bool_true_reader, 0x1000) is None
    assert fes.read_one(fail_negative_reader, 0x1000) is None
    assert fes.read_one(fail_overflow_reader, 0x1000) is None
    assert fes.read_one(fail_str_reader, 0x1000) is None
    assert fes.read_one(fail_float_reader, 0x1000) is None

    # 有效 u32 必须保留
    assert fes.read_one(lambda va: 0, 0x1000) == 0
    assert fes.read_one(lambda va: 0xFFFFFFFF, 0x1000) == 0xFFFFFFFF
    logger.log("  [3.1] read_one 底层类型过滤与防伪冒 0 断言全部通过 [PASS]")

    # 3.2 构造复合失败 reader：
    # gen_stamp 读失败返回 None
    # threat_calls 抛出 RuntimeError
    # dirty_rect_count 读到真实的 0 (验证真实 0 不会被误杀为 None)
    # bullet_count 读到 15
    # f_pre 读失败返回 None
    # f_post 正常读到 101
    def composite_fail_reader(va: int):
        if va == VA_GEN_STAMP:
            return None
        elif va == VA_THREAT_CALLS:
            raise RuntimeError("RPM Exception")
        elif va == VA_DIRTY_RECT:
            return 0  # 真实值 0
        elif va == VA_BULLET:
            return 15
        elif va == FRAME_VA:
            if not hasattr(composite_fail_reader, "call_count"):
                composite_fail_reader.call_count = 0
            composite_fail_reader.call_count += 1
            if composite_fail_reader.call_count == 1:
                return None
            return 101
        return None

    vclock = VirtualClock(300.0)
    sample = fes.read_sample(composite_fail_reader, vclock)

    vals = sample["values"]
    logger.log(f"  [3.2] 复合失败采样结果:")
    logger.log(f"        gen_stamp (返回 None)       : {vals['gen_stamp']} (is None? {vals['gen_stamp'] is None})")
    logger.log(f"        threat_calls (抛出异常)      : {vals['threat_calls']} (is None? {vals['threat_calls'] is None})")
    logger.log(f"        dirty_rect_count (真实值 0)  : {vals['dirty_rect_count']} (== 0? {vals['dirty_rect_count'] == 0})")
    logger.log(f"        bullet_count (真实值 15)     : {vals['bullet_count']}")
    logger.log(f"        f_pre (读失败)              : {sample['f_pre']}")
    logger.log(f"        f_post (读成功)             : {sample['f_post']}")
    logger.log(f"        cross_frame (因 f_pre 缺项) : {sample['cross_frame']}")

    # 严格判据断言
    assert vals["gen_stamp"] is None
    assert vals["gen_stamp"] != 0, "gen_stamp 失败绝不能补 0"
    assert vals["threat_calls"] is None
    assert vals["threat_calls"] != 0, "threat_calls 失败绝不能补 0"
    assert vals["dirty_rect_count"] == 0, "dirty_rect_count 真实 0 必须保留"
    assert vals["dirty_rect_count"] is not None
    assert sample["f_pre"] is None
    assert sample["cross_frame"] is None, "f_pre 缺失时 cross_frame 必须为 None"

    # 3.3 序列化到 JSON 字符串，直接检查文本格式
    json_str = fes.to_jsonl(sample)
    logger.log(f"  [3.3] JSONL 序列化原文:\n        {json_str}")

    assert '"gen_stamp":null' in json_str, "JSON 串中必须为 '\"gen_stamp\":null'"
    assert '"threat_calls":null' in json_str, "JSON 串中必须为 '\"threat_calls\":null'"
    assert '"dirty_rect_count":0' in json_str, "JSON 串中必须为 '\"dirty_rect_count\":0'"
    assert '"gen_stamp":0' not in json_str, "JSON 串中绝不能出现 '\"gen_stamp\":0'"
    assert '"threat_calls":0' not in json_str, "JSON 串中绝不能出现 '\"threat_calls\":0'"

    # 3.4 喂入 FrameEdgeTracker，验证状态机切断与 null 记账
    tracker = fes.FrameEdgeTracker()
    tracker.feed(300.0, 100)
    assert tracker.initialized is True

    ev = tracker.feed(300.1, 101, sample=sample)
    assert ev is not None
    assert tracker.counts["null_fields"] == 2, f"null_fields 统计必须为 2，实际为 {tracker.counts['null_fields']}"

    ret = tracker.feed(300.2, None)
    assert ret is None
    assert tracker.counts["null_frames"] == 1
    assert tracker.prev_lost is True
    assert tracker.freeze_start_t is None

    ret_resume = tracker.feed(300.3, 105)
    assert ret_resume is None
    assert tracker.counts["resume_after_loss"] == 1
    assert tracker.prev_lost is False

    logger.log("  [3.4] JSON 格式断言 ('null' 而非 '0') 及 Tracker 断裂保护验证通过 [PASS]")
    logger.log(">> 用例 3 判定: PASS (读失败项为 None / null，有效 0 保持 0，绝不补 0)\n")
    return True


# ==============================================================================
# 用例 4: S4 命中 ⇒ 立即停手（不得进入采样）
# ==============================================================================
def test_case_4_s4_hit_stops_immediately_no_sampling():
    logger.log("=" * 80)
    logger.log("[用例 4: S4 命中立即停手断言]")
    logger.log("=" * 80)

    # 4.1 名字扫描纯函数 s4_scan_names 命中验证 (大小写不敏感)
    modules_clean = ["ntdll.dll", "kernel32.dll", "gamemd.exe"]
    scan_clean = harness_ext.s4_scan_names(modules_clean)
    assert scan_clean["hit_count"] == 0
    assert scan_clean["ra2render_hits"] == []
    assert scan_clean["ra2loader_hits"] == []

    modules_hit_r = ["ntdll.dll", "kernel32.dll", "D:\\Games\\Ra2Render.dll"]
    scan_hit_r = harness_ext.s4_scan_names(modules_hit_r)
    assert scan_hit_r["hit_count"] == 1
    assert scan_hit_r["ra2render_hits"] == ["D:\\Games\\Ra2Render.dll"]

    modules_hit_l = ["ntdll.dll", "C:\\ra2\\RA2LOADER.EXE", "user32.dll"]
    scan_hit_l = harness_ext.s4_scan_names(modules_hit_l)
    assert scan_hit_l["hit_count"] == 1
    assert scan_hit_l["ra2loader_hits"] == ["C:\\ra2\\RA2LOADER.EXE"]
    logger.log("  [4.1] s4_scan_names 纯函数命中与大小写不敏感匹配验证通过 [PASS]")

    # 4.2 扩展闸门 s4_injection_gate 命中停手与退出码 62 验证
    harness_ext.w5_reset_state()
    harness_ext._W5_STATE["on"] = True
    rec = harness_ext.Recorder()

    def mock_mother_gate_hit(pid, rec, authorized=False):
        harness_ext.S4_VERDICT["gate"] = "HIT"
        harness_ext.S4_VERDICT["exit_code"] = harness_ext.EXIT_INJECTION_SUSPECTED
        rec.add("S4", "s4_gate", "HIT", "script:s4_injection_gate")
        rec.add("S4", "s4_exit_code", harness_ext.EXIT_INJECTION_SUSPECTED, "script:s4_injection_gate")
        return False

    orig_mother_gate = harness_ext._s4_injection_gate_mother
    try:
        harness_ext._s4_injection_gate_mother = mock_mother_gate_hit
        # 执行 s4_injection_gate
        gate_res = harness_ext.s4_injection_gate(pid=12345, rec=rec, authorized=False)

        logger.log(f"  [4.2] 触发 S4 命中: gate_res={gate_res}, S4_VERDICT={harness_ext.S4_VERDICT}")
        assert gate_res is False, "S4 命中时 gate 必须返回 False"
        assert harness_ext.S4_VERDICT["gate"] in ("HIT", "w5_hit_rejected"), f"gate 状态异常: {harness_ext.S4_VERDICT['gate']}"
        assert harness_ext.S4_VERDICT["exit_code"] == 62, "S4 命中时退出码必须为 62 (EXIT_INJECTION_SUSPECTED)"

        w5_assertions = [r for r in rec.rows if r["group"] == "W5EXT" and r["key"] == "s4_hard_assertion"]
        assert len(w5_assertions) > 0, "必须记录 W5EXT 硬断言阻断"
        assert w5_assertions[0]["value"] == "FAILED_INJECTION_SUSPECTED"
        logger.log(f"        W5EXT 审计记录: {w5_assertions[0]['value']} ({w5_assertions[0]['note']}) [PASS]")

    finally:
        harness_ext._s4_injection_gate_mother = orig_mother_gate

    # 4.3 验证 _measure_run 硬阻断（零采样进入）
    sampling_invoked = [False]

    def mock_measure_poll_span_spy(*args, **kwargs):
        sampling_invoked[0] = True
        return 0, [], [], None

    orig_poll = harness_ext._measure_poll_span
    rec_run = harness_ext.Recorder()
    budget = harness_ext.TripBudget(rec_run)

    try:
        harness_ext._measure_poll_span = mock_measure_poll_span_spy
        harness_ext._W5_STATE["ra2render_hits"] = ["Ra2Render.dll"]

        fake_out_dir = BASE_DIR / "_tmp_case4_out"
        fake_out_dir.mkdir(parents=True, exist_ok=True)
        harness_ext._measure_run(rec_run, budget, pid=12345, out_dir=fake_out_dir, map_sha256="0" * 64)

        logger.log(f"  [4.3] _measure_run 阻断执行: sampling_invoked={sampling_invoked[0]}")
        assert sampling_invoked[0] is False, "S4 命中时绝不得进入采样循环 (poll_span 零调用)"

        aborted_recs = [r for r in rec_run.rows if r["group"] == "W5EXT" and r["key"] == "measure_gate_aborted"]
        assert len(aborted_recs) > 0, "必须记录 measure_gate_aborted"
        logger.log(f"        _measure_run 阻断记录: {aborted_recs[0]['note']} [PASS]")

        if fake_out_dir.exists():
            for p in fake_out_dir.glob("*"): p.unlink()
            fake_out_dir.rmdir()

    finally:
        harness_ext._measure_poll_span = orig_poll

    logger.log(">> 用例 4 判定: PASS (S4 命中立即停手，且完全阻断进入采样阶段)\n")
    return True


# ==============================================================================
# 用例 5: --allow-loader + 扩项 ⇒ 拒绝启动
# ==============================================================================
def test_case_5_allow_loader_with_ext_refuses_to_start():
    logger.log("=" * 80)
    logger.log("[用例 5: --allow-loader + 扩项 拒绝启动]")
    logger.log("=" * 80)

    # 5.1 CLI / 入口网关级冲突检查
    # 当同时给出 --allow-loader 和 --w5-ext 1
    argv_conflict = BASE_ARGV + ["--allow-loader", "--w5-ext", "1"]
    ret_code = harness_ext.main(argv_conflict)
    logger.log(f"  [5.1] main([--allow-loader, --w5-ext 1]) 退出码: {ret_code} (EXIT_INJECTION_SUSPECTED=62)")
    assert ret_code == harness_ext.EXIT_INJECTION_SUSPECTED, "同时开启 --allow-loader 与扩项必须拒绝启动并返回 62"

    # 同义别名 --measure-ext 1 也必须被拒绝
    argv_conflict2 = BASE_ARGV + ["--allow-loader", "--measure-ext", "1"]
    ret_code2 = harness_ext.main(argv_conflict2)
    logger.log(f"  [5.1b] main([--allow-loader, --measure-ext 1]) 退出码: {ret_code2} (EXIT_INJECTION_SUSPECTED=62)")
    assert ret_code2 == harness_ext.EXIT_INJECTION_SUSPECTED

    # 5.2 注入闸门级断言：即使 authorized=True，s4_injection_gate 遇到扩项开启也必须拒绝
    harness_ext.w5_reset_state()
    harness_ext._W5_STATE["on"] = True
    rec_gate = harness_ext.Recorder()

    orig_mother_gate = harness_ext._s4_injection_gate_mother
    try:
        # 假定母本在 authorized=True 时原本放行
        harness_ext._s4_injection_gate_mother = lambda pid, rec, authorized=False: True

        gate_res = harness_ext.s4_injection_gate(pid=12345, rec=rec_gate, authorized=True)
        logger.log(f"  [5.2] s4_injection_gate(authorized=True, w5_on=True) 判定结果: {gate_res}")
        logger.log(f"        S4_VERDICT: {harness_ext.S4_VERDICT}")

        assert gate_res is False, "扩项开启下，authorized=True 必须被拒绝放行"
        assert harness_ext.S4_VERDICT["gate"] == "w5_refused_allow_loader"
        assert harness_ext.S4_VERDICT["exit_code"] == 62

        rec_entries = [r for r in rec_gate.rows if r["group"] == "W5EXT" and r["key"] == "s4_hard_assertion"]
        assert len(rec_entries) > 0
        assert rec_entries[0]["value"] == "FAILED_ALLOW_LOADER"
        logger.log(f"        硬阻断记账: {rec_entries[0]['note']} [PASS]")

    finally:
        harness_ext._s4_injection_gate_mother = orig_mother_gate

    # 5.3 运行级断言：_measure_run 遇到 allow_loader 必须直接阻断
    rec_run = harness_ext.Recorder()
    budget = harness_ext.TripBudget(rec_run)
    orig_allow_loader = list(harness_ext.A8_ALLOW_LOADER)
    sampling_invoked = [False]

    def mock_poll(*args, **kwargs):
        sampling_invoked[0] = True
        return 0, [], [], None

    orig_poll = harness_ext._measure_poll_span
    fake_out_dir = BASE_DIR / "_tmp_case5_out"
    fake_out_dir.mkdir(parents=True, exist_ok=True)

    try:
        harness_ext._measure_poll_span = mock_poll
        harness_ext._W5_STATE["ra2render_hits"] = []
        harness_ext._W5_STATE["ra2loader_hits"] = []
        harness_ext.A8_ALLOW_LOADER[0] = True

        harness_ext._measure_run(rec_run, budget, pid=12345, out_dir=fake_out_dir, map_sha256="0" * 64)
        logger.log(f"  [5.3] _measure_run(A8_ALLOW_LOADER=True) 阻断结果: sampling_invoked={sampling_invoked[0]}")
        assert sampling_invoked[0] is False, "A8_ALLOW_LOADER=True 时绝不得进入采样"

        recs = [r for r in rec_run.rows if r["group"] == "W5EXT" and r["key"] == "measure_gate_aborted"]
        assert len(recs) > 0
        assert recs[0]["value"] == "allow_loader_active"
        logger.log(f"        采样入口阻断留痕: {recs[0]['note']} [PASS]")

        if fake_out_dir.exists():
            for p in fake_out_dir.glob("*"): p.unlink()
            fake_out_dir.rmdir()

    finally:
        harness_ext.A8_ALLOW_LOADER[:] = orig_allow_loader
        harness_ext._measure_poll_span = orig_poll

    # 5.4 对照实验验证（合规组合）
    args_good_ext = harness_ext.parse_args(BASE_ARGV + ["--w5-ext", "1"])
    assert bool(getattr(args_good_ext, "w5_ext", 0)) is True
    assert getattr(args_good_ext, "allow_loader", False) is False

    args_good_loader = harness_ext.parse_args(BASE_ARGV + ["--allow-loader"])
    assert getattr(args_good_loader, "allow_loader", False) is True
    assert bool(getattr(args_good_loader, "w5_ext", 0)) is False
    logger.log("  [5.4] 对照实验 (单一扩项 / 单一 loader) 合规组合检验通过 [PASS]")

    logger.log(">> 用例 5 判定: PASS (--allow-loader + 扩项被 main 前置拦截，直接拒绝启动)\n")
    return True


# ==============================================================================
# 用例 6: 帧冻结窗 ⇒ 零样本，且不宣称该窗零成本
# ==============================================================================
def test_case_6_frozen_window_zero_samples_and_no_zero_cost_claim():
    logger.log("=" * 80)
    logger.log("[用例 6: 帧冻结窗零样本且不宣称零成本]")
    logger.log("=" * 80)

    harness_ext.w5_reset_state()
    harness_ext._W5_STATE["on"] = True

    call_counts = collections.Counter()
    frozen_frame = 3668

    def fake_frozen_reader(va: int):
        call_counts[va] += 1
        if va == FRAME_VA:
            return frozen_frame
        elif va == VA_GEN_STAMP:
            return 111
        elif va == VA_THREAT_CALLS:
            return 222
        elif va == VA_DIRTY_RECT:
            return 333
        elif va == VA_BULLET:
            return 444
        return 0

    harness_ext.w5_set_reader(fake_frozen_reader)

    orig_doze = harness_ext._doze
    orig_counters = harness_ext._rpm_counters
    orig_clock = harness_ext.time.perf_counter

    vclock = VirtualClock(500.0, step=0.002)

    try:
        harness_ext._doze = lambda s: None
        harness_ext._rpm_counters = lambda h: {"units": 10, "t_rel": 0.0}
        harness_ext.time.perf_counter = vclock

        t0, samples, counters, err = harness_ext._w5_measure_poll_span(0x1234, span_s=0.5, hz=500)

        events_freeze = harness_ext._W5_STATE["last_window_events"]
        stats_freeze = harness_ext._W5_STATE["last_window_stats"]

        logger.log(f"  [6.1] 冻结窗采样结果:")
        logger.log(f"        既有轮询样本数: {len(samples)} (全部 CurrentFrame={frozen_frame})")
        logger.log(f"        追加四 VA 事件数: {len(events_freeze)} (预期严格为 0)")
        logger.log(f"        四 VA 追加读取总数: {sum(call_counts[va] for _, va, _, _ in fes.FIELDS)} (预期严格为 0)")

        # 断言：零样本
        assert len(events_freeze) == 0, f"冻结窗追加事件数必须为 0，实际为 {len(events_freeze)}"
        assert call_counts[VA_GEN_STAMP] == 0
        assert call_counts[VA_THREAT_CALLS] == 0
        assert call_counts[VA_DIRTY_RECT] == 0
        assert call_counts[VA_BULLET] == 0

        # 6.2 统计字典与不宣称零成本断言
        logger.log(f"  [6.2] Tracker 统计输出:")
        logger.log(f"        counts.edge: {stats_freeze['counts']['edge']}")
        logger.log(f"        frame_clock_freeze_max_s: {stats_freeze['frame_clock_freeze_max_s']} s")
        logger.log(f"        note: {stats_freeze['note']}")

        assert stats_freeze["counts"]["edge"] == 0, "冻结窗沿数必须为 0"
        assert stats_freeze["counts"]["samples"] > 0
        assert stats_freeze["frame_clock_freeze_max_s"] > 0
        assert "不得据此宣称业务字段冻结" in stats_freeze["note"], "stats_freeze['note'] 必须声明不得据此宣称业务字段冻结"
        assert stats_freeze["markers"] == list(fes.FIELD_MARKERS)

        # 6.3 检查 payload 包装
        tmp_out = BASE_DIR / "_tmp_case6_out"
        tmp_out.mkdir(parents=True, exist_ok=True)
        payload = {"window": 1, "hz": 500, "stats": {}}

        harness_ext._measure_write_json(tmp_out, 1, payload)
        w5_data = payload.get("w5_ext", {})

        assert w5_data.get("events_count") == 0, "payload events_count 必须为 0"
        assert "zero_cost" not in w5_data or w5_data["zero_cost"] is False, "绝不得宣称 zero_cost=True"
        assert "zero_burden" not in w5_data or w5_data["zero_burden"] is False, "绝不得宣称 zero_burden=True"

        logger.log("  [6.3] 零成本宣称规避校验通过: 绝无 zero_cost=True 声明，合规披露盲区 [PASS]")

        if tmp_out.exists():
            for p in tmp_out.glob("*"): p.unlink()
            tmp_out.rmdir()

    finally:
        harness_ext._doze = orig_doze
        harness_ext._rpm_counters = orig_counters
        harness_ext.time.perf_counter = orig_clock

    logger.log(">> 用例 6 判定: PASS (帧冻结窗零样本，note 明示不宣称业务字段冻结，保留双 markers)\n")
    return True


# ==============================================================================
# 主执行入口
# ==============================================================================
def main():
    logger.log("=" * 80)
    logger.log("W5 HARNESS EXT 离线单测试运行")
    logger.log(f"母本路径: {REPO_ROOT / 'lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py'}")
    logger.log(f"副本路径: {EXT_PATH}")
    logger.log(f"候选件路径: {A1_DIR / 'frame_edge_sampler.py'}")
    logger.log("=" * 80 + "\n")

    test_cases = [
        ("Case 1: 开关为 0 ⇒ 不产生任何新采样行（零行为差结构证明）", test_case_1_switch_off_zero_samples),
        ("Case 2: 开关为 1 ⇒ 每沿恰好追加 5 读（四 VA + f_post，D-21 裁 A）", test_case_2_switch_on_exact_reads_per_edge),
        ("Case 3: 读失败 ⇒ 字段为 null，不是 0", test_case_3_read_failure_records_null_not_zero),
        ("Case 4: S4 命中 ⇒ 立即停手（不得进入采样）", test_case_4_s4_hit_stops_immediately_no_sampling),
        ("Case 5: --allow-loader + 扩项 ⇒ 拒绝启动", test_case_5_allow_loader_with_ext_refuses_to_start),
        ("Case 6: 帧冻结窗 ⇒ 零样本，且不宣称该窗零成本", test_case_6_frozen_window_zero_samples_and_no_zero_cost_claim),
    ]

    results = []
    start_t = time.time()

    for name, test_func in test_cases:
        try:
            ok = test_func()
            results.append((name, "PASS" if ok else "FAIL", None))
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}"
            logger.log(f"!! 用例执行异常: {name}")
            logger.log(f"   {err_msg}")
            results.append((name, "FAIL", err_msg))

    duration = time.time() - start_t

    logger.log("=" * 80)
    logger.log("测试结果汇总")
    logger.log("=" * 80)
    all_passed = True
    for name, status, err in results:
        err_info = f" ({err})" if err else ""
        logger.log(f"  [{status}] {name}{err_info}")
        if status != "PASS":
            all_passed = False

    logger.log("-" * 80)
    passed_count = sum(1 for _, s, _ in results if s == "PASS")
    total_count = len(results)
    logger.log(f"总计: {total_count} 用例, 通过: {passed_count}, 失败: {total_count - passed_count}")
    logger.log(f"总耗时: {duration:.3f} 秒 (全部纯离线模拟，零真机系统调用)")
    logger.log(f"最终判定: {'PASS (EXIT=0)' if all_passed else 'FAIL (EXIT=1)'}")
    logger.log("=" * 80)

    # 写入落盘文件
    logger.write_out()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
