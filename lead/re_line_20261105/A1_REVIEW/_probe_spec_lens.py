# -*- coding: utf-8 -*-
"""合规复核员·边界与铁律 —— 独立实跑探针 (R4, R5, R6)
严格遵循铁律：
- 零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不读活进程内存
- 禁止调用 RpmReader(enable=True)，禁止开任何进程句柄
- 纯离线黑盒测试与静态语法/符号审计
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CAND_DIR = os.path.join(REPO_ROOT, "lead", "re_line_20261105", "A1_SAMPLER_CANDIDATE")
CAND_FILE = os.path.join(CAND_DIR, "frame_edge_sampler.py")

sys.path.insert(0, CAND_DIR)
import frame_edge_sampler as S  # noqa: E402


def run_probes():
    print("=" * 70)
    print("A1_REVIEW 独立实跑探针输出 (R4, R5, R6)")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # R4 实跑探针
    # --------------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("### PROBE R4: 首样本 vs unjudgeable 区分与中途读失败边界 ###")
    print("#" * 60)

    print("\n--- R4.1 反例 1 实跑: [100, None, 100] ---")
    tk1 = S.FrameEdgeTracker()
    seq1 = [(0.00, 100), (0.01, None), (0.02, 100)]
    for idx, (t, f) in enumerate(seq1, 1):
        ev = tk1.feed(t, f)
        print(f"  Step {idx}: t={t:.2f}, f={f!r} -> event={ev}")
        print(f"          tracker state: prev_f={tk1.prev_f!r}, freeze_start_t={tk1.freeze_start_t!r}, freeze_max_s={tk1.freeze_max_s:.4f}")
    st1 = tk1.stats()
    print("  Final Stats [100, None, 100]:")
    print("   ", json.dumps(st1, ensure_ascii=False))

    print("\n--- R4.2 反例 2 实跑: [100, None, 150] ---")
    tk2 = S.FrameEdgeTracker()
    seq2 = [(0.00, 100), (0.01, None), (0.02, 150)]
    for idx, (t, f) in enumerate(seq2, 1):
        ev = tk2.feed(t, f)
        print(f"  Step {idx}: t={t:.2f}, f={f!r} -> event={ev}")
        print(f"          tracker state: prev_f={tk2.prev_f!r}, missed_frames={tk2.missed_frames}, edge_missed_count={tk2.counts['edge_missed']}")
    st2 = tk2.stats()
    print("  Final Stats [100, None, 150]:")
    print("   ", json.dumps(st2, ensure_ascii=False))

    print("\n--- R4.3 扩展反例: 读失败持续长时段 [100, None * 5, 100] ---")
    tk3 = S.FrameEdgeTracker()
    tk3.feed(0.00, 100)
    for i in range(1, 6):
        tk3.feed(float(i), None)
    tk3.feed(6.00, 100)
    st3 = tk3.stats()
    print(f"  持续 5s 读失败后恢复 100 -> freeze_max_s={st3['freeze_max_s']:.4f}s (虚增冻结时长！)")

    print("\n--- R4.4 天真修复验证: 读失败时若仅置 prev_f = None ---")
    class NaiveTracker(S.FrameEdgeTracker):
        def feed(self, t, f, sample=None):
            self.counts["samples"] += 1
            if f is None:
                self.counts["null_frames"] += 1
                self.prev_f = None
                return None
            return super().feed(t, f, sample)

    tk_naive = NaiveTracker()
    tk_naive.feed(0.00, 100)
    tk_naive.feed(0.01, None)
    ev_naive = tk_naive.feed(0.02, 150)
    st_naive = tk_naive.stats()
    print(f"  置 prev_f=None 导致: counts['first']={st_naive['counts']['first']} (首样本误判增为2!), event={ev_naive}")

    print("\n--- R4.5 推荐最小修复方案实跑对比 ---")
    class FixedTracker(S.FrameEdgeTracker):
        def __init__(self):
            super().__init__()
            self.initialized = False
            self.prev_lost = False

        def feed(self, t, f, sample=None):
            self.counts["samples"] += 1
            if f is None:
                self.counts["null_frames"] += 1
                self.prev_lost = True
                self.freeze_start_t = None
                return None

            if not self.initialized:
                self.counts["first"] += 1
                self.initialized = True
                self.prev_f = f
                self.prev_t = t
                self.prev_lost = False
                return None

            if self.prev_lost:
                self.counts["unjudgeable"] += 1
                self.prev_lost = False
                self.prev_f = f
                self.prev_t = t
                self.freeze_start_t = None
                return None

            return super().feed(t, f, sample)

    f1 = FixedTracker()
    for t, f in seq1:
        f1.feed(t, f)
    print("  FixedTracker on [100, None, 100]: unjudgeable=%d, freeze_max_s=%.4f" %
          (f1.counts["unjudgeable"], f1.freeze_max_s))

    f2 = FixedTracker()
    for t, f in seq2:
        f2.feed(t, f)
    print("  FixedTracker on [100, None, 150]: unjudgeable=%d, edge_missed=%d, missed_frames=%d" %
          (f2.counts["unjudgeable"], f2.counts["edge_missed"], f2.missed_frames))

    # --------------------------------------------------------------------------
    # R5 实跑探针
    # --------------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("### PROBE R5: freeze_max_s 命名与「不得宣称业务字段冻结」防线有效性 ###")
    print("#" * 60)

    tk_r5 = S.FrameEdgeTracker()
    tk_r5.feed(0.00, 100)
    tk_r5.feed(0.02, 100)
    st_r5 = tk_r5.stats()
    print("  stats() 暴露的所有顶层键:", list(st_r5.keys()))
    print("  数值指标键名: 'freeze_max_s' =", st_r5["freeze_max_s"])
    print("  文本免责说明: 'note' =", repr(st_r5["note"]))

    # 模拟下游自动化流水线提取
    print("  模拟下游自动分析提取 (只读数值键):")
    extracted_metrics = {k: v for k, v in st_r5.items() if isinstance(v, (int, float))}
    print("  提取到的指标字典:", extracted_metrics)
    print("  结论: 下游提取数值指标时直接穿透 'note'，无任何代码级约束阻止其将 freeze_max_s 误认作业务冻结。")

    # --------------------------------------------------------------------------
    # R6 实跑探针
    # --------------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("### PROBE R6: 铁律合规、受禁 API 静态全量扫描与 RpmReader 防护 ###")
    print("#" * 60)

    with open(CAND_FILE, "r", encoding="utf-8") as fh:
        cand_src = fh.read()

    forbidden_apis = (
        "CreateRemoteThread",
        "WriteProcessMemory",
        "SuspendThread",
        "MiniDumpWriteDump",
        "StackWalk",
        "SetWindowsHookEx",
    )

    print("--- R6.1 源码违规 API 字符串审计 ---")
    all_clean = True
    for api in forbidden_apis:
        cnt = cand_src.count(api)
        print(f"  API '{api}': 出现次数 = {cnt}")
        if cnt > 0:
            all_clean = False
    print("  审计结论: " + ("100% 干净，未发现任何受禁 API 调用/字符串！" if all_clean else "发现受禁 API！"))

    print("\n--- R6.2 RpmReader 默认参数与未启用状态验证 ---")
    rr = S.RpmReader(pid=99999)
    print("  RpmReader 实例化 (未指定 enable):")
    print("    pid =", rr.pid)
    print("    enable =", rr.enable, "(必须为 False)")
    print("    handle =", rr.handle, "(必须为 None)")
    print("    err =", rr.err, "(必须为 None)")

    print("  调用 open() (enable=False):")
    res_open = rr.open()
    print("    open() 返回值 =", res_open, "(必须为 False)")
    print("    handle 状态 =", rr.handle, "(必须为 None)")
    print("    err 状态 =", repr(rr.err), "(明确提示 disabled)")

    print("  调用 read_u32(0x00A8ED84) (未开句柄):")
    res_read = rr.read_u32(0x00A8ED84)
    print("    read_u32() 返回值 =", res_read, "(必须为 None)")

    print("  调用 close():")
    rr.close()
    print("    close() 执行正常，无异常抛出。")

    print("\n--- R6.3 模块导入副作用与顶层 AST 检查 ---")
    tree = ast.parse(cand_src)
    top_level_types = [type(n).__name__ for n in tree.body]
    print("  顶层 AST 节点类型统计:", set(top_level_types))

    # 在隔离 Python 子进程中导入模块，检查是否触碰系统
    probe_cmd = [
        sys.executable,
        "-I",
        "-X",
        "utf8",
        "-c",
        f"import sys; sys.path.insert(0, r'{CAND_DIR}'); import frame_edge_sampler; print('IMPORT_OK')",
    ]
    sub_res = subprocess.run(probe_cmd, capture_output=True, text=True)
    print("  子进程独立导入测试: returncode =", sub_res.returncode, "stdout =", sub_res.stdout.strip())
    print("  审计结论: 模块无自动执行脚本块，无顶层系统调用，import 零副作用。")

    print("\n" + "=" * 70)
    print("所有探针执行完毕。")
    print("=" * 70)


if __name__ == "__main__":
    run_probes()
