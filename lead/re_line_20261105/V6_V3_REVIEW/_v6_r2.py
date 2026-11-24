# -*- coding: utf-8 -*-
"""V6 复核 R2 探针：时间戳契约独立复核脚本。

测试要点（TASK.md §2 R2）：
1. 验证复用模式下 ts["f_pre"] == 传入的 t_pre 而非进入时刻；
2. ts["segment_start"] 独立记录为业务段起点（复用模式下 != ts["f_pre"]）；
3. 传 f_pre 不传 t_pre => ts["f_pre"] is None 且 f_pre_anchor_known False；
4. 反例要求：故意传一个明显偏早的 t_pre，验证 ts["f_pre"] 用它而非当前时刻；
5. 向后兼容验证：不传 f_pre 时的原 6 读行为（ts["f_pre"] == ts["segment_start"]）；
6. 完整时间戳全序验证；
7. 静态审查 harness 调用点时序（t_now 取在 reader(FRAME_VA) 之前）。

零真机、不改任何既有文件。
"""
from __future__ import annotations

import ast
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

# 被核对象与关联文件
TARGET_SAMPLER = os.path.join(
    PROJECT_ROOT, "lead", "re_line_20261105", "A1_SAMPLER_CANDIDATE", "frame_edge_sampler.py"
)
CALLER_HARNESS = os.path.join(
    PROJECT_ROOT, "lead", "re_line_20261105", "W5_HARNESS_EXT", "qc151_trip.harness8_v4_ext.py"
)
TEST_W5 = os.path.join(
    PROJECT_ROOT, "lead", "re_line_20261105", "W5_HARNESS_EXT", "_w5_test.py"
)

# 动态加载 frame_edge_sampler
sys.path.insert(0, os.path.dirname(TARGET_SAMPLER))
import frame_edge_sampler as FES  # noqa: E402

PASS_COUNT = 0
FAIL_COUNT = 0
LOG_LINES = []


def log(msg: str = ""):
    print(msg)
    LOG_LINES.append(msg)


def check(name: str, cond: bool, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if cond:
        PASS_COUNT += 1
        log(f"  [PASS] {name}")
    else:
        FAIL_COUNT += 1
        log(f"  [FAIL] {name} - {detail}")


def sha256_of_file(path: str) -> tuple[str, int]:
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest(), len(data)


class StepClock:
    """可控可步进时钟"""

    def __init__(self, start: float = 1000.0, step: float = 0.005):
        self.t = start
        self.step = step
        self.call_history = []

    def __call__(self) -> float:
        val = self.t
        self.call_history.append(val)
        self.t += self.step
        return val


def dummy_reader(va: int):
    # 返回合法 u32
    if va == FES.FRAME_VA:
        return 200
    return 0x1234


def run_checks():
    log("=" * 80)
    log("V6_V3_REVIEW - R2 时间戳契约独立复核探针")
    log("=" * 80)

    # --------------------------------------------------------------------------
    # 0. 被核对象 SHA256 与字节数实测
    # --------------------------------------------------------------------------
    log("\n[0. 被核对象与关联文件 SHA256 实测]")
    s_sha, s_sz = sha256_of_file(TARGET_SAMPLER)
    h_sha, h_sz = sha256_of_file(CALLER_HARNESS)
    t_sha, t_sz = sha256_of_file(TEST_W5)

    log(f"  被核采样件: {TARGET_SAMPLER}")
    log(f"    SHA256 = {s_sha}")
    log(f"    字节数 = {s_sz}")
    check(
        "采样件 SHA256 吻合任务书参照值",
        s_sha == "b382e893bafc6a7f38d08572affaa663eaef56a8de7c3f361eea38cc34185f3e",
        f"got {s_sha}",
    )
    check("采样件字节数吻合 (21,411)", s_sz == 21411, f"got {s_sz}")

    log(f"  关联调用方: {CALLER_HARNESS}")
    log(f"    SHA256 = {h_sha}")
    log(f"    字节数 = {h_sz}")
    check(
        "调用方 SHA256 吻合任务书参照值",
        h_sha == "5081780c5a2e3da5c934efff4665ed248ad01b1c4c883887eb1a66cc7d83f161",
        f"got {h_sha}",
    )
    check("调用方字节数吻合 (499,047)", h_sz == 499047, f"got {h_sz}")

    log(f"  测试套件件: {TEST_W5}")
    log(f"    SHA256 = {t_sha}")
    log(f"    字节数 = {t_sz}")
    check(
        "单测 SHA256 吻合任务书参照值",
        t_sha == "df5771a830c4fa2df5445156284a65d7a5d1e2c4ac80945350a0d05c727df2c8",
        f"got {t_sha}",
    )
    check("单测字节数吻合 (36,624)", t_sz == 36624, f"got {t_sz}")

    # --------------------------------------------------------------------------
    # 1. 契约要点 1 & 2: 复用模式下 ts["f_pre"] == t_pre 且 ts["segment_start"] 独立记录
    # --------------------------------------------------------------------------
    log("\n[1. 复用模式时间戳契约测试 (传 f_pre 与 t_pre)]")
    clk1 = StepClock(start=500.0, step=0.01)
    # 设定外层传入值
    ext_f = 101
    ext_t = 499.500  # 明显早于进入函数的 clock (500.0)

    sample1 = FES.read_sample(dummy_reader, clk1, f_pre=ext_f, t_pre=ext_t)

    check(
        "ts['f_pre'] 严格等于传入的 t_pre",
        sample1["ts"]["f_pre"] == ext_t,
        f"got {sample1['ts']['f_pre']} vs {ext_t}",
    )
    check(
        "ts['segment_start'] 为进入业务读取时首次调用的 clock()",
        sample1["ts"]["segment_start"] == 500.0,
        f"got {sample1['ts']['segment_start']} vs 500.0",
    )
    check(
        "ts['f_pre'] != ts['segment_start']（两者明确分开独立记录）",
        sample1["ts"]["f_pre"] != sample1["ts"]["segment_start"],
        f"ts[f_pre]={sample1['ts']['f_pre']}, ts[segment_start]={sample1['ts']['segment_start']}",
    )
    check(
        "f_pre 锚已知标记 f_pre_anchor_known 为 True",
        sample1["ts"]["f_pre_anchor_known"] is True,
        f"got {sample1['ts']['f_pre_anchor_known']}",
    )
    check(
        "f_pre_reused 字段为 True",
        sample1["f_pre_reused"] is True,
        f"got {sample1['f_pre_reused']}",
    )
    check(
        "reads_per_sample 为 5",
        sample1["reads_per_sample"] == 5,
        f"got {sample1['reads_per_sample']}",
    )

    # --------------------------------------------------------------------------
    # 2. 契约要点 3: 传 f_pre 但不传 t_pre ⇒ ts["f_pre"] is None 且 f_pre_anchor_known False
    # --------------------------------------------------------------------------
    log("\n[2. 缺省 t_pre 契约测试 (传 f_pre 但 t_pre=None)]")
    clk2 = StepClock(start=600.0, step=0.01)
    sample2 = FES.read_sample(dummy_reader, clk2, f_pre=102, t_pre=None)

    check(
        "传 f_pre 但 t_pre 为 None 时，ts['f_pre'] 为 None（绝不拿进入时刻冒充）",
        sample2["ts"]["f_pre"] is None,
        f"got {sample2['ts']['f_pre']}",
    )
    check(
        "f_pre_anchor_known 标记严格为 False",
        sample2["ts"]["f_pre_anchor_known"] is False,
        f"got {sample2['ts']['f_pre_anchor_known']}",
    )
    check(
        "ts['segment_start'] 仍正常记录业务段起点",
        sample2["ts"]["segment_start"] == 600.0,
        f"got {sample2['ts']['segment_start']}",
    )
    check(
        "f_pre_reused 仍为 True",
        sample2["f_pre_reused"] is True,
        f"got {sample2['f_pre_reused']}",
    )
    check(
        "reads_per_sample 仍为 5",
        sample2["reads_per_sample"] == 5,
        f"got {sample2['reads_per_sample']}",
    )

    # --------------------------------------------------------------------------
    # 3. 契约要点 4: 反例要求 —— 故意传一个明显偏早的 t_pre，验证 ts["f_pre"] 用它而非当前时刻
    # --------------------------------------------------------------------------
    log("\n[3. 反例测试：故意传入明显偏早的 t_pre]")
    clk3 = StepClock(start=10000.0, step=0.01)
    early_t_pre = 12.345678  # 差距接近一万秒的偏早时刻
    sample3 = FES.read_sample(dummy_reader, clk3, f_pre=103, t_pre=early_t_pre)

    log(f"  传入偏早 t_pre = {early_t_pre}")
    log(f"  函数内首次 clock() = 10000.0")
    log(f"  sample['ts']['f_pre'] = {sample3['ts']['f_pre']}")
    log(f"  sample['ts']['segment_start'] = {sample3['ts']['segment_start']}")

    check(
        "反例验证: ts['f_pre'] 严格采用偏早的 t_pre (12.345678)，绝无被 clock 覆盖",
        sample3["ts"]["f_pre"] == early_t_pre,
        f"got {sample3['ts']['f_pre']}",
    )
    check(
        "反例验证: segment_start 仍为进入函数后的业务读起点 (10000.0)",
        sample3["ts"]["segment_start"] == 10000.0,
        f"got {sample3['ts']['segment_start']}",
    )
    diff = sample3["ts"]["segment_start"] - sample3["ts"]["f_pre"]
    check(
        f"反例验证: 两者差值保持 9987.654322 (实测 {diff:.6f})",
        abs(diff - (10000.0 - early_t_pre)) < 1e-9,
        f"got {diff}",
    )

    # --------------------------------------------------------------------------
    # 4. 向后兼容验证：缺省 f_pre=None, t_pre=None (自读前帧号 6 读模式)
    # --------------------------------------------------------------------------
    log("\n[4. 向后兼容测试：自读前帧号模式 (f_pre=None, t_pre=None)]")
    clk4 = StepClock(start=700.0, step=0.01)
    sample4 = FES.read_sample(dummy_reader, clk4, f_pre=None, t_pre=None)

    check(
        "非复用模式下 ts['segment_start'] == ts['f_pre']（为同一发起时刻）",
        sample4["ts"]["segment_start"] == sample4["ts"]["f_pre"] == 700.0,
        f"segment_start={sample4['ts']['segment_start']}, f_pre={sample4['ts']['f_pre']}",
    )
    check(
        "非复用模式下 f_pre_anchor_known 为 True",
        sample4["ts"]["f_pre_anchor_known"] is True,
        f"got {sample4['ts']['f_pre_anchor_known']}",
    )
    check(
        "非复用模式下 f_pre_reused 为 False",
        sample4["f_pre_reused"] is False,
        f"got {sample4['f_pre_reused']}",
    )
    check(
        "非复用模式下 reads_per_sample 为 6",
        sample4["reads_per_sample"] == 6,
        f"got {sample4['reads_per_sample']}",
    )

    # --------------------------------------------------------------------------
    # 5. 时间戳全序单调性校验
    # --------------------------------------------------------------------------
    log("\n[5. 时间戳全序单调性校验]")
    # 复用模式全序
    ts1 = sample1["ts"]
    order_ok1 = (
        ts1["f_pre"]
        <= ts1["segment_start"]
        <= ts1["gen_stamp"]
        <= ts1["threat_calls"]
        <= ts1["dirty_rect_count"]
        <= ts1["bullet_count"]
        <= ts1["f_post_start"]
        == ts1["f_post"]
        <= ts1["segment_end"]
    )
    check(
        "复用模式时间戳满足全序: f_pre <= segment_start <= 4业务读 <= f_post_start == f_post <= segment_end",
        order_ok1,
        f"ts1={ts1}",
    )

    # 非复用模式全序
    ts4 = sample4["ts"]
    order_ok4 = (
        ts4["f_pre"]
        == ts4["segment_start"]
        <= ts4["gen_stamp"]
        <= ts4["threat_calls"]
        <= ts4["dirty_rect_count"]
        <= ts4["bullet_count"]
        <= ts4["f_post_start"]
        == ts4["f_post"]
        <= ts4["segment_end"]
    )
    check(
        "自读模式时间戳满足全序: f_pre == segment_start <= 4业务读 <= f_post_start == f_post <= segment_end",
        order_ok4,
        f"ts4={ts4}",
    )

    # --------------------------------------------------------------------------
    # 6. 调用方静态代码 AST 审查 (qc151_trip.harness8_v4_ext.py)
    # --------------------------------------------------------------------------
    log("\n[6. 调用方静态代码审查 (qc151_trip.harness8_v4_ext.py)]")
    with open(CALLER_HARNESS, "r", encoding="utf-8") as f:
        src = f.read()

    tree = ast.parse(src)

    # 查找所有 read_sample 调用
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # 匹配 frame_edge_sampler.read_sample(...) 或 read_sample(...)
            func_name = None
            if isinstance(node.func, ast.Attribute) and node.func.attr == "read_sample":
                func_name = f"{ast.unparse(node.func.value)}.read_sample"
            elif isinstance(node.func, ast.Name) and node.func.id == "read_sample":
                func_name = "read_sample"

            if func_name:
                calls.append((node.lineno, func_name, node))

    log(f"  在 harness 中查找到 {len(calls)} 处 read_sample 调用:")
    for lineno, name, node in calls:
        call_text = ast.unparse(node)
        log(f"    行 {lineno}: {call_text}")

    check("harness 中存在且仅存在 1 处 read_sample 调用", len(calls) == 1, f"got {len(calls)}")

    lineno, name, node = calls[0]
    # 检查调用关键字实参
    kw_names = [kw.arg for kw in node.keywords]
    check("调用实参包含 f_pre", "f_pre" in kw_names, f"keywords={kw_names}")
    check("调用实参包含 t_pre", "t_pre" in kw_names, f"keywords={kw_names}")

    # 检查 t_pre 对应的变量名
    t_pre_kw = next(kw for kw in node.keywords if kw.arg == "t_pre")
    f_pre_kw = next(kw for kw in node.keywords if kw.arg == "f_pre")
    check(
        "t_pre 参数传入变量 t_now",
        isinstance(t_pre_kw.value, ast.Name) and t_pre_kw.value.id == "t_now",
        f"got {ast.unparse(t_pre_kw.value)}",
    )
    check(
        "f_pre 参数传入变量 f",
        isinstance(f_pre_kw.value, ast.Name) and f_pre_kw.value.id == "f",
        f"got {ast.unparse(f_pre_kw.value)}",
    )

    # 提取调用点上下文代码，确认 t_now = time.perf_counter() 在 f = reader(...) 之前
    lines = src.splitlines()
    ctx_start = max(0, lineno - 20)
    ctx_end = min(len(lines), lineno + 5)
    block_lines = lines[ctx_start:ctx_end]
    log("\n  [调用点上下文源码片段 (行 %d-%d)]:" % (ctx_start + 1, ctx_end))
    for idx, l in enumerate(block_lines, start=ctx_start + 1):
        log(f"    {idx:4d} | {l}")

    # 字符串/行号逻辑验证
    t_now_line = None
    reader_f_line = None
    for idx, l in enumerate(lines, start=1):
        if "t_now = time.perf_counter()" in l and idx < lineno and idx > lineno - 25:
            t_now_line = idx
        if "f = reader(MEASURE_CURRENT_FRAME_VA)" in l and idx < lineno and idx > lineno - 20:
            reader_f_line = idx

    log(f"  t_now 取样行号 = {t_now_line}")
    log(f"  reader(FRAME_VA) 执行行号 = {reader_f_line}")
    log(f"  read_sample 调用行号 = {lineno}")

    check(
        "t_now 取在 reader(FRAME_VA) 之前",
        t_now_line is not None and reader_f_line is not None and t_now_line < reader_f_line,
        f"t_now_line={t_now_line}, reader_f_line={reader_f_line}",
    )
    check(
        "reader(FRAME_VA) 执行在 read_sample 调用之前",
        reader_f_line is not None and reader_f_line < lineno,
        f"reader_f_line={reader_f_line}, call_line={lineno}",
    )

    # --------------------------------------------------------------------------
    # 总结
    # --------------------------------------------------------------------------
    log("\n" + "=" * 80)
    log(f"复核结果汇总: PASS = {PASS_COUNT}, FAIL = {FAIL_COUNT}")
    log("=" * 80)
    return FAIL_COUNT == 0


if __name__ == "__main__":
    success = run_checks()
    # 写入 _v6_r2_out.txt
    out_path = os.path.join(HERE, "_v6_r2_out.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG_LINES) + "\n")
    log(f"输出已落盘至: {out_path}")
    sys.exit(0 if success else 1)
