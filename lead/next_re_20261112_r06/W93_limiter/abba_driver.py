# -*- coding: utf-8 -*-
"""W93 ABBA 观测器扰动标定驱动脚本（外部只读启停，不注入、不写目标内存）。

依据 `lead/next_re_20261112_r06/OBSERVER_ABBA_PROTOCOL.md`：
  - 按区组执行 A -> B -> B -> A（默认 3 区组，每段 60s，前 10s 预热由分析脚本丢弃）
  - 相位 A：以独立子进程启动 `exp_rpm_framebeat.py` 采集目标 PID 的帧节拍，记录其 PID
  - 相位 B：不启动观测器，等待一个段时长
  - 每次切换立即写入并落盘一行 NDJSON 至 `switch_log.ndjson`（含 `t_perf_ns`、段号、A/B、观测器 PID）
  - 支持 Ctrl-C / SIGINT 优雅退出（停止观测器子进程并写入 `finished` 标记）
  - 支持段中崩溃检测：若相位 A 观测器子进程在段结束前提前退出，记录 `crash` 与 `finished` 标记并停止后续区组
"""
from __future__ import annotations

import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PATTERN = ("A", "B", "B", "A")
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OBSERVER_CANDIDATES = [
    REPO_ROOT / "lead" / "next_re_20261112_r05" / "W90_replicates" / "work" / "tools" / "exp_rpm_framebeat.py",
    REPO_ROOT / "lead" / "next_re_20261112_r03" / "W86_render_channel" / "experiment" / "exp_rpm_framebeat.py",
]


def find_default_observer() -> Optional[Path]:
    for cand in DEFAULT_OBSERVER_CANDIDATES:
        if cand.is_file():
            return cand
    return None


def write_ndjson_line(fp, record: Dict[str, Any]) -> None:
    fp.write(json.dumps(record, ensure_ascii=False) + "\n")
    fp.flush()
    try:
        os.fsync(fp.fileno())
    except OSError:
        pass


def stop_observer_process(proc: subprocess.Popen, wait_sec: float = 3.0) -> Optional[int]:
    """优雅终止观测器子进程；仅作用于己方拉起的外部只读子进程，不触碰目标游戏进程。"""
    rc = proc.poll()
    if rc is not None:
        return rc
    try:
        proc.terminate()
    except OSError:
        return proc.poll()
    deadline = time.perf_counter() + wait_sec
    while time.perf_counter() < deadline:
        rc = proc.poll()
        if rc is not None:
            return rc
        time.sleep(0.05)
    try:
        proc.kill()
        return proc.wait(timeout=2.0)
    except Exception:
        return proc.poll()


def build_parser() -> argparse.ArgumentParser:
    default_obs = find_default_observer()
    p = argparse.ArgumentParser(
        description="按 A->B->B->A 协议外部启停只读观测器（exp_rpm_framebeat.py）并记录 switch_log.ndjson。"
    )
    p.add_argument("--pid", type=int, required=True, help="被测目标进程 PID（透传给只读观测器；本脚本绝不注入或写内存）")
    p.add_argument("--blocks", type=int, default=3, help="ABBA 区组数（每区组 4 段，默认 3 => 共 12 段）")
    p.add_argument("--seg-sec", type=float, default=60.0, help="每段持续墙钟秒数（默认 60）")
    p.add_argument("--warm-sec", type=float, default=10.0, help="写入元数据的每段预热秒数，供分析阶段丢弃（默认 10）")
    p.add_argument(
        "--switch-log",
        type=Path,
        default=Path("switch_log.ndjson"),
        help="切换日志输出路径（默认 ./switch_log.ndjson）",
    )
    p.add_argument(
        "--obs-out-dir",
        type=Path,
        default=None,
        help="相位 A 观测器输出目录根路径（默认 <switch_log 同目录>/observer_segments）",
    )
    p.add_argument(
        "--observer-script",
        type=Path,
        default=default_obs,
        help=f"相位 A 观测器脚本路径（默认自动探测：{default_obs}）",
    )
    p.add_argument(
        "--python-exe",
        default=sys.executable,
        help="启动观测器子进程所用的 Python 解释器（默认当前解释器）",
    )
    p.add_argument(
        "--poll-interval",
        type=float,
        default=0.1,
        help="段内轮询观测器存活与中断标志的间隔秒数（默认 0.1）",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.pid <= 0:
        print(f"[FATAL] --pid 必须为正整数，当前={args.pid}", file=sys.stderr)
        return 2
    if args.blocks < 1:
        print(f"[FATAL] --blocks 必须 >= 1，当前={args.blocks}", file=sys.stderr)
        return 2
    if args.seg_sec <= 0:
        print(f"[FATAL] --seg-sec 必须 > 0，当前={args.seg_sec}", file=sys.stderr)
        return 2
    if args.warm_sec < 0 or args.warm_sec >= args.seg_sec:
        print(
            f"[FATAL] --warm-sec 必须满足 0 <= warm_sec < seg_sec，当前 warm={args.warm_sec}, seg={args.seg_sec}",
            file=sys.stderr,
        )
        return 2
    if args.observer_script is None or not Path(args.observer_script).is_file():
        print(f"[FATAL] 未找到观测器脚本：{args.observer_script}", file=sys.stderr)
        return 2

    switch_log_path = Path(args.switch_log).resolve()
    switch_log_path.parent.mkdir(parents=True, exist_ok=True)
    obs_out_root = (
        Path(args.obs_out_dir).resolve()
        if args.obs_out_dir is not None
        else switch_log_path.parent / "observer_segments"
    )
    obs_out_root.mkdir(parents=True, exist_ok=True)

    stop_requested = False

    def _on_signal(signum, frame) -> None:  # noqa: ARG001
        nonlocal stop_requested
        stop_requested = True

    prev_sigint = signal.getsignal(signal.SIGINT)
    prev_sigterm = signal.getsignal(signal.SIGTERM) if hasattr(signal, "SIGTERM") else None
    prev_sigbreak = signal.getsignal(signal.SIGBREAK) if hasattr(signal, "SIGBREAK") else None
    signal.signal(signal.SIGINT, _on_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _on_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _on_signal)

    creationflags = 0
    if sys.platform == "win32" and hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    completed_segments = 0
    crashed = False
    crash_reason = ""
    active_proc: Optional[subprocess.Popen] = None
    active_log_fp = None

    try:
        with switch_log_path.open("w", encoding="utf-8", buffering=1) as log_fp:
            write_ndjson_line(
                log_fp,
                {
                    "event": "meta",
                    "t_perf_ns": time.perf_counter_ns(),
                    "t_epoch_ns": time.time_ns(),
                    "target_pid": args.pid,
                    "blocks": args.blocks,
                    "seg_sec": args.seg_sec,
                    "warm_sec": args.warm_sec,
                    "pattern": list(PATTERN),
                    "observer_script": str(Path(args.observer_script).resolve()),
                    "driver_pid": os.getpid(),
                },
            )

            total_segs = args.blocks * len(PATTERN)
            # 传给观测器的时长略大于 seg_sec，确保段内若提前退出即可判定为“段中崩溃”
            obs_duration_arg = max(1, int(math.ceil(args.seg_sec)) + 5)

            for block_idx in range(1, args.blocks + 1):
                for pos_idx, phase in enumerate(PATTERN):
                    if stop_requested:
                        break
                    seg_id = (block_idx - 1) * len(PATTERN) + pos_idx
                    obs_pid: Optional[int] = None
                    seg_obs_dir = obs_out_root / f"seg_{seg_id:02d}_b{block_idx}_{phase}"

                    if phase == "A":
                        seg_obs_dir.mkdir(parents=True, exist_ok=True)
                        stdout_path = seg_obs_dir / "observer_stdio.log"
                        active_log_fp = stdout_path.open("w", encoding="utf-8", errors="replace")
                        cmd = [
                            args.python_exe,
                            "-B",
                            str(Path(args.observer_script).resolve()),
                            str(args.pid),
                            str(obs_duration_arg),
                            str(seg_obs_dir),
                        ]
                        try:
                            active_proc = subprocess.Popen(
                                cmd,
                                stdout=active_log_fp,
                                stderr=subprocess.STDOUT,
                                creationflags=creationflags,
                            )
                            obs_pid = active_proc.pid
                        except Exception as exc:
                            active_log_fp.close()
                            active_log_fp = None
                            crashed = True
                            crash_reason = f"seg={seg_id} 启动观测器失败: {exc}"
                            write_ndjson_line(
                                log_fp,
                                {
                                    "event": "crash",
                                    "t_perf_ns": time.perf_counter_ns(),
                                    "t_epoch_ns": time.time_ns(),
                                    "block": block_idx,
                                    "pos_in_block": pos_idx,
                                    "seg_id": seg_id,
                                    "phase": phase,
                                    "observer_pid": None,
                                    "returncode": None,
                                    "reason": crash_reason,
                                },
                            )
                            break

                    seg_start_ns = time.perf_counter_ns()
                    write_ndjson_line(
                        log_fp,
                        {
                            "event": "switch",
                            "t_perf_ns": seg_start_ns,
                            "t_epoch_ns": time.time_ns(),
                            "block": block_idx,
                            "pos_in_block": pos_idx,
                            "seg_id": seg_id,
                            "phase": phase,
                            "observer_pid": obs_pid,
                        },
                    )
                    print(
                        f"[SEG {seg_id + 1:02d}/{total_segs:02d}] block={block_idx} phase={phase} observer_pid={obs_pid}",
                        flush=True,
                    )

                    seg_deadline_ns = seg_start_ns + int(round(args.seg_sec * 1e9))
                    while True:
                        if stop_requested:
                            break
                        now_ns = time.perf_counter_ns()
                        if now_ns >= seg_deadline_ns:
                            break
                        if active_proc is not None:
                            rc = active_proc.poll()
                            if rc is not None:
                                crashed = True
                                elapsed_s = (now_ns - seg_start_ns) / 1e9
                                crash_reason = (
                                    f"seg={seg_id} (block={block_idx}, phase=A, obs_pid={obs_pid}) "
                                    f"在段中提前退出 rc={rc}，已运行 {elapsed_s:.2f}s / {args.seg_sec:.2f}s"
                                )
                                write_ndjson_line(
                                    log_fp,
                                    {
                                        "event": "crash",
                                        "t_perf_ns": now_ns,
                                        "t_epoch_ns": time.time_ns(),
                                        "block": block_idx,
                                        "pos_in_block": pos_idx,
                                        "seg_id": seg_id,
                                        "phase": phase,
                                        "observer_pid": obs_pid,
                                        "returncode": rc,
                                        "elapsed_seg_s": round(elapsed_s, 3),
                                        "reason": crash_reason,
                                    },
                                )
                                active_proc = None
                                if active_log_fp is not None:
                                    active_log_fp.close()
                                    active_log_fp = None
                                break
                        remain_s = (seg_deadline_ns - now_ns) / 1e9
                        time.sleep(min(args.poll_interval, max(0.005, remain_s)))

                    if crashed:
                        break

                    stop_rc: Optional[int] = None
                    if active_proc is not None:
                        stop_rc = stop_observer_process(active_proc)
                        active_proc = None
                    if active_log_fp is not None:
                        active_log_fp.close()
                        active_log_fp = None

                    if stop_requested:
                        break

                    write_ndjson_line(
                        log_fp,
                        {
                            "event": "seg_end",
                            "t_perf_ns": time.perf_counter_ns(),
                            "t_epoch_ns": time.time_ns(),
                            "block": block_idx,
                            "pos_in_block": pos_idx,
                            "seg_id": seg_id,
                            "phase": phase,
                            "observer_pid": obs_pid,
                            "observer_exit_code": stop_rc,
                        },
                    )
                    completed_segments += 1

                if stop_requested or crashed:
                    break

            if stop_requested:
                status = "interrupted"
            elif crashed:
                status = "aborted_crash"
            else:
                status = "completed"

            write_ndjson_line(
                log_fp,
                {
                    "event": "finished",
                    "t_perf_ns": time.perf_counter_ns(),
                    "t_epoch_ns": time.time_ns(),
                    "status": status,
                    "completed_segments": completed_segments,
                    "expected_segments": total_segs,
                    "reason": crash_reason if crashed else ("KeyboardInterrupt/Signal" if stop_requested else "ok"),
                },
            )
            print(
                f"[FINISHED] status={status} completed_segments={completed_segments}/{total_segs}"
                + (f" reason={crash_reason}" if crashed else ""),
                flush=True,
            )
            if crashed:
                return 3
            return 0
    except KeyboardInterrupt:
        if active_proc is not None:
            stop_observer_process(active_proc)
            active_proc = None
        if active_log_fp is not None:
            active_log_fp.close()
            active_log_fp = None
        try:
            with switch_log_path.open("a", encoding="utf-8", buffering=1) as log_fp:
                write_ndjson_line(
                    log_fp,
                    {
                        "event": "finished",
                        "t_perf_ns": time.perf_counter_ns(),
                        "t_epoch_ns": time.time_ns(),
                        "status": "interrupted",
                        "completed_segments": completed_segments,
                        "expected_segments": args.blocks * len(PATTERN),
                        "reason": "KeyboardInterrupt",
                    },
                )
        except OSError:
            pass
        print("[FINISHED] 收到 KeyboardInterrupt，已终止观测器并写入 finished 标记。", flush=True)
        return 0
    finally:
        if active_proc is not None:
            stop_observer_process(active_proc)
        if active_log_fp is not None:
            active_log_fp.close()
        signal.signal(signal.SIGINT, prev_sigint)
        if prev_sigterm is not None and hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, prev_sigterm)
        if prev_sigbreak is not None and hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, prev_sigbreak)


if __name__ == "__main__":
    sys.exit(main())
