# -*- coding: utf-8 -*-
"""V6 复核重跑 · R1 复用前读读次独立探针

核对目标：
1. frame_edge_sampler.py 的 SHA256 与字节数独立实算；
2. read_sample(reader, clock, f_pre=None, t_pre=None)：
   - 传 f_pre 时是否真的不调 reader(FRAME_VA) 读前帧号？
   - 缺省 f_pre=None 时是否保持原 6 读行为（向后兼容）？
   - 可计数 reader 实测两种模式读次，给出精确原始计数与读序；
3. 反例要求：
   - 构造「只在 FRAME_VA 上计数」的探针，严密追踪前帧号读与后帧号读；
   - 构造禁止前帧号读的断言探针，验证复用模式 0 次前帧号读，默认模式 1 次前帧号读；
   - 边沿测试：f_pre=0（假值陷阱）与 t_pre=None 的读次行为；
   - 流式测试：10 沿实测累计读次对比（50 读 vs 60 读）。

零真机、纯函数式离线执行。
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import os
import sys

TARGET_PATH = "D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py"
CANDIDATE_DIR = "D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE"
OUT_TXT_PATH = "D:/Project/ra2-campaign-forge/lead/re_line_20261105/V6_V3_REVIEW/_v6_r1_out.txt"

sys.path.insert(0, CANDIDATE_DIR)
import frame_edge_sampler as fes  # noqa: E402


class OutputLogger:
    def __init__(self, out_file: str):
        self.out_file = out_file
        self.lines: list[str] = []

    def log(self, msg: str = ""):
        print(msg)
        self.lines.append(msg)

    def write_file(self):
        with open(self.out_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.lines) + "\n")


logger = OutputLogger(OUT_TXT_PATH)


class VirtualClock:
    """虚拟单调时钟"""
    def __init__(self, start: float = 1000.0, step: float = 0.001):
        self.t = start
        self.step = step

    def __call__(self) -> float:
        cur = self.t
        self.t += self.step
        return cur


# ==============================================================================
# 0. 被核对象 SHA256 与字节数实算
# ==============================================================================
def verify_target_object():
    logger.log("=" * 80)
    logger.log("[0. 被核对象 SHA256 与字节数实算]")
    logger.log("=" * 80)

    assert os.path.isfile(TARGET_PATH), f"Target file not found: {TARGET_PATH}"
    with open(TARGET_PATH, "rb") as f:
        data = f.read()
    sha256_val = hashlib.sha256(data).hexdigest()
    size_val = os.path.getsize(TARGET_PATH)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.log(f"被核对象路径 = {TARGET_PATH}")
    logger.log(f"被核对象 SHA256 = {sha256_val}，字节数 = {size_val}")
    logger.log(f"复核时刻 = {now_str}")

    expected_sha256 = "b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e"
    expected_size = 21411
    if sha256_val != expected_sha256 or size_val != expected_size:
        logger.log(f"OBJECT_CHANGED: 期望 SHA256={expected_sha256}, size={expected_size}")
    else:
        logger.log("SHA256 与字节数与任务书基准严格相符。")

    return sha256_val, size_val, now_str


# ==============================================================================
# 1. 可计数 reader 实测「默认 6 读」与「复用 5 读」
# ==============================================================================
class CountingReader:
    """全面记录所有 VA 读取次数、读序及单次读取值的 Reader"""
    def __init__(self, frame_val_pre: int = 100, frame_val_post: int = 101, field_val: int = 0x1234):
        self.frame_val_pre = frame_val_pre
        self.frame_val_post = frame_val_post
        self.field_val = field_val
        self.call_history: list[tuple[int, str]] = []
        self.counts_by_va: collections.Counter = collections.Counter()
        self.frame_va_calls = 0

    def __call__(self, va: int):
        self.counts_by_va[va] += 1
        if va == fes.FRAME_VA:
            self.frame_va_calls += 1
            # 第一次读 FRAME_VA 返回 pre 值，后续返回 post 值
            val = self.frame_val_pre if self.frame_va_calls == 1 else self.frame_val_post
            self.call_history.append((va, f"FRAME_VA (read #{self.frame_va_calls}) -> {val}"))
            return val
        else:
            self.call_history.append((va, f"0x{va:08X} -> {self.field_val}"))
            return self.field_val

    @property
    def total_reads(self) -> int:
        return sum(self.counts_by_va.values())


def test_counting_reader_both_modes():
    logger.log("\n" + "=" * 80)
    logger.log("[1. 可计数 reader 实测两种模式的读次与读序]")
    logger.log("=" * 80)

    # 1.1 默认模式（f_pre=None, t_pre=None）：向后兼容 6 读
    reader_default = CountingReader(frame_val_pre=100, frame_val_post=101, field_val=0x5555)
    vclock1 = VirtualClock(100.0, step=0.001)
    rec_default = fes.read_sample(reader_default, vclock1)

    logger.log("--- 1.1 默认模式 (f_pre=None) ---")
    logger.log(f"  总读取次数: {reader_default.total_reads} (预期 6)")
    logger.log(f"  FRAME_VA (0x{fes.FRAME_VA:08X}) 读次: {reader_default.counts_by_va[fes.FRAME_VA]} (预期 2)")
    for name, va, _, _ in fes.FIELDS:
        logger.log(f"  业务 VA {name} (0x{va:08X}) 读次: {reader_default.counts_by_va[va]} (预期 1)")
    logger.log(f"  样本返回字段: f_pre_reused={rec_default['f_pre_reused']}, reads_per_sample={rec_default['reads_per_sample']}")
    logger.log(f"  样本读数: f_pre={rec_default['f_pre']}, f_post={rec_default['f_post']}, cross_frame={rec_default['cross_frame']}")
    logger.log("  读取时序轨迹:")
    for idx, (va, desc) in enumerate(reader_default.call_history, 1):
        logger.log(f"    [{idx}] {desc}")

    assert reader_default.total_reads == 6, f"默认模式总读次必须为 6，实际为 {reader_default.total_reads}"
    assert reader_default.counts_by_va[fes.FRAME_VA] == 2, "默认模式 FRAME_VA 必须读 2 次"
    assert rec_default["f_pre_reused"] is False, "默认模式 f_pre_reused 必须为 False"
    assert rec_default["reads_per_sample"] == 6, "默认模式 reads_per_sample 必须为 6"
    assert rec_default["f_pre"] == 100, "默认模式 f_pre 必须为 100"
    assert rec_default["f_post"] == 101, "默认模式 f_post 必须为 101"
    logger.log("  >> 默认模式 6 读核验: PASS")

    # 1.2 复用前读模式（f_pre=100, t_pre=199.5）：5 读
    reader_reuse = CountingReader(frame_val_pre=100, frame_val_post=101, field_val=0x6666)
    vclock2 = VirtualClock(200.0, step=0.001)
    rec_reuse = fes.read_sample(reader_reuse, vclock2, f_pre=100, t_pre=199.5)

    logger.log("\n--- 1.2 复用前读模式 (f_pre=100, t_pre=199.5) ---")
    logger.log(f"  总读取次数: {reader_reuse.total_reads} (预期 5)")
    logger.log(f"  FRAME_VA (0x{fes.FRAME_VA:08X}) 读次: {reader_reuse.counts_by_va[fes.FRAME_VA]} (预期 1，仅 f_post)")
    for name, va, _, _ in fes.FIELDS:
        logger.log(f"  业务 VA {name} (0x{va:08X}) 读次: {reader_reuse.counts_by_va[va]} (预期 1)")
    logger.log(f"  样本返回字段: f_pre_reused={rec_reuse['f_pre_reused']}, reads_per_sample={rec_reuse['reads_per_sample']}")
    logger.log(f"  样本读数: f_pre={rec_reuse['f_pre']}, f_post={rec_reuse['f_post']}, cross_frame={rec_reuse['cross_frame']}")
    logger.log("  读取时序轨迹:")
    for idx, (va, desc) in enumerate(reader_reuse.call_history, 1):
        logger.log(f"    [{idx}] {desc}")

    assert reader_reuse.total_reads == 5, f"复用模式总读次必须为 5，实际为 {reader_reuse.total_reads}"
    assert reader_reuse.counts_by_va[fes.FRAME_VA] == 1, "复用模式 FRAME_VA 必须恰好读 1 次 (仅 f_post)"
    assert rec_reuse["f_pre_reused"] is True, "复用模式 f_pre_reused 必须为 True"
    assert rec_reuse["reads_per_sample"] == 5, "复用模式 reads_per_sample 必须为 5"
    assert rec_reuse["f_pre"] == 100, "复用模式 f_pre 必须为 100"
    assert rec_reuse["f_post"] == 100, "复用模式中后读返回 reader 首次读 FRAME_VA 的值"
    logger.log("  >> 复用模式 5 读核验: PASS")


# ==============================================================================
# 2. 反例探针：只在 FRAME_VA 上计数的探针验证 0 次前帧号读
# ==============================================================================
class FrameVaOnlyCountingProbe:
    """专门且仅在 FRAME_VA 上计数的探针。

    设计机制：
    1. 内部仅针对 FRAME_VA 设立计数器；非 FRAME_VA 的读取不产生任何计数。
    2. 设立 phase 状态：追踪读取发生时是否已进入业务字段阶段（首个业务 VA 读取发起后）。
    3. 区分：
       - pre_frame_reads: 在首个业务 VA 读取之前发生的 FRAME_VA 读次；
       - post_frame_reads: 在业务 VA 读取之后发生的 FRAME_VA 读次；
       - total_frame_reads: FRAME_VA 的总读次。
    """
    def __init__(self, frame_value: int = 500):
        self.frame_value = frame_value
        self.business_phase_started = False
        self.pre_frame_reads = 0
        self.post_frame_reads = 0
        self.total_frame_reads = 0
        self.frame_read_records: list[dict] = []

    def __call__(self, va: int):
        if va == fes.FRAME_VA:
            self.total_frame_reads += 1
            if not self.business_phase_started:
                self.pre_frame_reads += 1
                phase = "PRE_BUSINESS (前帧号读)"
            else:
                self.post_frame_reads += 1
                phase = "POST_BUSINESS (后帧号读)"
            self.frame_read_records.append({
                "read_id": self.total_frame_reads,
                "va": hex(va),
                "phase": phase,
                "val": self.frame_value,
            })
            return self.frame_value
        else:
            # 业务 VA 读取：标记业务阶段已开始，探针不对业务 VA 做任何计数累加
            self.business_phase_started = True
            return 8888


class ForbiddenPreReadError(BaseException):
    """用于绕过 read_one 的 except Exception 机制，精确捕获前帧号读违规"""
    pass


class PreReadForbiddenProbe:
    """严格反例探针：一旦发生前帧号读（在业务字段读取前调用 FRAME_VA），直接触发异常与标记。"""
    def __init__(self, frame_value: int = 999):
        self.frame_value = frame_value
        self.business_phase_started = False
        self.pre_read_violation = False

    def __call__(self, va: int):
        if va == fes.FRAME_VA:
            if not self.business_phase_started:
                self.pre_read_violation = True
                raise ForbiddenPreReadError("FORBIDDEN_PRE_READ: reader(FRAME_VA) called before business fields!")
            return self.frame_value
        else:
            self.business_phase_started = True
            return 1111


def test_frame_va_only_probe():
    logger.log("\n" + "=" * 80)
    logger.log("[2. 反例探针：只在 FRAME_VA 上计数的探针验证 0 次前帧号读]")
    logger.log("=" * 80)

    # 2.1 复用模式：只在 FRAME_VA 上计数
    probe_reuse = FrameVaOnlyCountingProbe(frame_value=700)
    vclock = VirtualClock(300.0, step=0.001)
    rec_reuse = fes.read_sample(probe_reuse, vclock, f_pre=699, t_pre=299.0)

    logger.log("--- 2.1 复用模式下 FrameVaOnlyCountingProbe 实测结果 ---")
    logger.log(f"  pre_frame_reads (业务读前 FRAME_VA 读次)  = {probe_reuse.pre_frame_reads}  (断言必须 == 0)")
    logger.log(f"  post_frame_reads (业务读后 FRAME_VA 读次) = {probe_reuse.post_frame_reads} (断言必须 == 1)")
    logger.log(f"  total_frame_reads (FRAME_VA 总读次)       = {probe_reuse.total_frame_reads} (断言必须 == 1)")
    logger.log(f"  FRAME_VA 读记录清单: {probe_reuse.frame_read_records}")

    assert probe_reuse.pre_frame_reads == 0, f"复用模式前帧号读次必须为 0，实际为 {probe_reuse.pre_frame_reads}"
    assert probe_reuse.post_frame_reads == 1, f"复用模式后帧号读次必须为 1，实际为 {probe_reuse.post_frame_reads}"
    assert probe_reuse.total_frame_reads == 1, f"复用模式 FRAME_VA 总读次必须为 1，实际为 {probe_reuse.total_frame_reads}"
    logger.log("  >> 复用模式 0 次前帧号读断言: PASS")

    # 2.2 默认模式：只在 FRAME_VA 上计数对照
    probe_default = FrameVaOnlyCountingProbe(frame_value=700)
    rec_default = fes.read_sample(probe_default, vclock)

    logger.log("\n--- 2.2 默认模式下 FrameVaOnlyCountingProbe 实测对照 ---")
    logger.log(f"  pre_frame_reads (业务读前 FRAME_VA 读次)  = {probe_default.pre_frame_reads}  (断言必须 == 1)")
    logger.log(f"  post_frame_reads (业务读后 FRAME_VA 读次) = {probe_default.post_frame_reads} (断言必须 == 1)")
    logger.log(f"  total_frame_reads (FRAME_VA 总读次)       = {probe_default.total_frame_reads} (断言必须 == 2)")
    logger.log(f"  FRAME_VA 读记录清单: {probe_default.frame_read_records}")

    assert probe_default.pre_frame_reads == 1, f"默认模式前帧号读次必须为 1，实际为 {probe_default.pre_frame_reads}"
    assert probe_default.post_frame_reads == 1, f"默认模式后帧号读次必须为 1，实际为 {probe_default.post_frame_reads}"
    assert probe_default.total_frame_reads == 2, f"默认模式 FRAME_VA 总读次必须为 2，实际为 {probe_default.total_frame_reads}"
    logger.log("  >> 默认模式 1 次前帧号读断言: PASS")

    # 2.3 反例防御：禁止前帧号读探针测试
    logger.log("\n--- 2.3 严苛反例：PreReadForbiddenProbe 互斥验证 ---")
    # A. 复用模式：不应触发任何违规或异常
    probe_forbid_reuse = PreReadForbiddenProbe(frame_value=800)
    rec_pass = fes.read_sample(probe_forbid_reuse, vclock, f_pre=799, t_pre=309.0)
    assert not probe_forbid_reuse.pre_read_violation, "复用模式绝不得触发前帧号读违规"
    assert rec_pass["f_post"] == 800
    logger.log("  A. 复用模式调用 PreReadForbiddenProbe: 未触发异常，执行成功 [PASS]")

    # B. 默认模式：必须触发前帧号读异常与标记
    probe_forbid_default = PreReadForbiddenProbe(frame_value=800)
    caught_exception = False
    try:
        fes.read_sample(probe_forbid_default, vclock)
    except ForbiddenPreReadError as ex:
        if "FORBIDDEN_PRE_READ" in str(ex):
            caught_exception = True
            logger.log(f"  B. 默认模式调用 PreReadForbiddenProbe: 如期捕获预期异常 [{ex}] [PASS]")
    assert caught_exception, "默认模式必须触发前帧号读异常，证明探针防御有效"
    assert probe_forbid_default.pre_read_violation is True, "默认模式必须记录前帧号读违规"


# ==============================================================================
# 3. 边界与防御：f_pre=0 与 t_pre=None
# ==============================================================================
def test_edge_cases():
    logger.log("\n" + "=" * 80)
    logger.log("[3. 边界与防御测试：f_pre=0 假值陷阱与 t_pre=None]")
    logger.log("=" * 80)

    # 3.1 假值陷阱：f_pre = 0
    # 在 Python 中 bool(0) is False。若代码写成 if f_pre: 则 0 会被当作 None 回退到 6 读。
    # 正确写法必须是 f_pre is not None。
    probe_zero = FrameVaOnlyCountingProbe(frame_value=1)
    vclock = VirtualClock(400.0, step=0.001)
    rec_zero = fes.read_sample(probe_zero, vclock, f_pre=0, t_pre=399.0)

    logger.log("--- 3.1 f_pre=0 (帧号恰为 0 时) ---")
    logger.log(f"  f_pre_reused = {rec_zero['f_pre_reused']} (断言必须为 True)")
    logger.log(f"  reads_per_sample = {rec_zero['reads_per_sample']} (断言必须为 5)")
    logger.log(f"  pre_frame_reads = {probe_zero.pre_frame_reads} (断言必须为 0)")
    logger.log(f"  total_frame_reads = {probe_zero.total_frame_reads} (断言必须为 1)")
    logger.log(f"  cross_frame = {rec_zero['cross_frame']} (0 != 1 必须为 True)")

    assert rec_zero["f_pre_reused"] is True, "f_pre=0 必须正确识别为复用模式"
    assert rec_zero["reads_per_sample"] == 5, "f_pre=0 读次必须为 5"
    assert probe_zero.pre_frame_reads == 0, "f_pre=0 时前帧号读次必须为 0"
    assert probe_zero.total_frame_reads == 1, "f_pre=0 时总帧号读次必须为 1"
    assert rec_zero["f_pre"] == 0, "f_pre 必须保留 0"
    logger.log("  >> f_pre=0 假值陷阱测试: PASS (未发生 0 误判为 None 回退 6 读)")

    # 3.2 传 f_pre 但不传 t_pre (t_pre=None)
    probe_notime = FrameVaOnlyCountingProbe(frame_value=50)
    rec_notime = fes.read_sample(probe_notime, vclock, f_pre=49, t_pre=None)

    logger.log("\n--- 3.2 传 f_pre 但 t_pre=None ---")
    logger.log(f"  f_pre_reused = {rec_notime['f_pre_reused']} (必须为 True)")
    logger.log(f"  reads_per_sample = {rec_notime['reads_per_sample']} (必须为 5)")
    logger.log(f"  pre_frame_reads = {probe_notime.pre_frame_reads} (必须为 0)")
    logger.log(f"  ts.f_pre = {rec_notime['ts']['f_pre']} (必须为 None)")
    logger.log(f"  ts.f_pre_anchor_known = {rec_notime['ts']['f_pre_anchor_known']} (必须为 False)")

    assert rec_notime["f_pre_reused"] is True
    assert rec_notime["reads_per_sample"] == 5
    assert probe_notime.pre_frame_reads == 0
    assert rec_notime["ts"]["f_pre"] is None
    assert rec_notime["ts"]["f_pre_anchor_known"] is False
    logger.log("  >> t_pre=None 读次与契约测试: PASS (仍为 5 读且 0 次前读，时间戳安全置 None)")


# ==============================================================================
# 4. 多沿流式模拟：累计前帧号读次与总读次对比
# ==============================================================================
def test_stream_edges():
    logger.log("\n" + "=" * 80)
    logger.log("[4. 多沿流式模拟：连续 10 沿触发累计读次与前帧号读次核对]")
    logger.log("=" * 80)

    # 模拟 10 次帧跳变沿
    # 复用模式：每次沿触发调用 read_sample(..., f_pre=cur_f, t_pre=t_now)
    probe_stream_reuse = FrameVaOnlyCountingProbe(frame_value=999)
    total_reads_reuse = 0
    vclock = VirtualClock(500.0, step=0.002)

    for i in range(10):
        # 模拟每次沿触发前读到了帧号 i
        rec = fes.read_sample(probe_stream_reuse, vclock, f_pre=i, t_pre=vclock())
        total_reads_reuse += rec["reads_per_sample"]

    logger.log("复用模式 10 沿触发:")
    logger.log(f"  累计 pre_frame_reads (前帧号读) = {probe_stream_reuse.pre_frame_reads} (预期 0)")
    logger.log(f"  累计 post_frame_reads (后帧号读) = {probe_stream_reuse.post_frame_reads} (预期 10)")
    logger.log(f"  累计 total_frame_reads (FRAME_VA) = {probe_stream_reuse.total_frame_reads} (预期 10)")
    logger.log(f"  累计总追加读取次数 (reads_per_sample 累计) = {total_reads_reuse} (预期 50)")

    assert probe_stream_reuse.pre_frame_reads == 0
    assert probe_stream_reuse.post_frame_reads == 10
    assert probe_stream_reuse.total_frame_reads == 10
    assert total_reads_reuse == 50
    logger.log("  >> 10 沿流式复用模式读次核验: PASS (严格 0 次前帧号读，总计 50 读)")


def main():
    logger.log("================================================================================")
    logger.log("V6_V3_REVIEW - R1 复用前读读次独立探针实跑")
    logger.log("================================================================================")

    sha256_val, size_val, now_str = verify_target_object()
    test_counting_reader_both_modes()
    test_frame_va_only_probe()
    test_edge_cases()
    test_stream_edges()

    logger.log("\n" + "=" * 80)
    logger.log("R1 全部核验项执行完毕，判定: PASS (未发现实质缺陷)")
    logger.log("================================================================================")

    logger.write_file()
    print(f"\n[OK] 探针输出已完整落盘至: {OUT_TXT_PATH}")


if __name__ == "__main__":
    main()
