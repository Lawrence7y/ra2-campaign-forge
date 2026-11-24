# -*- coding: utf-8 -*-
"""RE-N01 / make_test_output.py —— 用 subprocess 精确捕获各命令的 stdout + exit code。

避免 PowerShell 自动变量 $args 的坑；每条命令都在受控 cwd 下运行。
输出：TEST_OUTPUT.txt（原始 stdout，未加工）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable

COMMANDS = [
    ("离线测试主命令",
     [PY, "-X", "utf8", str(ROOT / "test_re_n01_offline.py")]),
    ("r2 采样器作者自检器（当前 danger-full-access 策略）",
     [PY, "-I", "-X", "utf8",
      str(ROOT / "candidate" / "e3_stack_sampler_candidate_r2.py"),
      "--selftest"]),
    ("生成 raw/ 样例",
     [PY, "-X", "utf8", str(ROOT / "make_fixture.py")]),
    ("计时器分辨率实测",
     [PY, "-X", "utf8", str(ROOT / "timer_calibration.py")]),
    ("变异测试（5 条，只改副本）",
     [PY, "-X", "utf8", str(ROOT / "mutation_run.py")]),
    ("语法编译检查（5 个模块）",
     [PY, "-X", "utf8", "-m", "py_compile",
      str(ROOT / "candidate" / "_run_hl_match_candidate.py"),
      str(ROOT / "candidate" / "e3_stack_sampler_candidate_r2.py"),
      str(ROOT / "candidate" / "re_n01_monitor.py"),
      str(ROOT / "replay_re_n01.py"),
      str(ROOT / "test_re_n01_offline.py")]),
    ("逐文件 replay 离线重算（raw/ 全部 7 个 NDJSON）",
     [PY, "-X", "utf8", str(ROOT / "replay_re_n01.py"),
      "--quiet", "--per-file"]),
]


def main():
    lines = ["=" * 78,
             "RE-N01 TEST_OUTPUT.txt — 原始 stdout（未经加工）",
             "run_id=NEXT_RE_20261112_R01  cwd=" + str(ROOT),
             "python=" + sys.version.split()[0],
             "=" * 78, ""]
    codes = {}
    for label, argv in COMMANDS:
        # 最后一条特殊：replay 一次只吃一个 ndjson，逐个跑
        if label.startswith("逐文件 replay"):
            for p in sorted((ROOT / "raw").glob("*.ndjson")):
                a = [PY, "-X", "utf8", str(ROOT / "replay_re_n01.py"),
                     str(p), "--quiet"]
                r = subprocess.run(a, cwd=str(ROOT), capture_output=True,
                                   text=True, encoding="utf-8",
                                   errors="replace", timeout=180)
                lines += ["-" * 78,
                          "COMMAND: python -X utf8 replay_re_n01.py %s --quiet"
                          % p.name,
                          "EXITCODE=%d" % r.returncode,
                          "STDOUT:", (r.stdout or "").rstrip(),
                          "STDERR:", (r.stderr or "").rstrip(), ""]
                codes["replay_" + p.name] = r.returncode
            continue
        r = subprocess.run(argv, cwd=str(ROOT), capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=300)
        lines += ["=" * 78,
                  "COMMAND: " + " ".join(
                      ('"%s"' % x if " " in x else x) for x in argv[1:]),
                  "LABEL: " + label,
                  "EXITCODE=%d" % r.returncode,
                  "STDOUT:", (r.stdout or "").rstrip(),
                  "STDERR:", (r.stderr or "").rstrip(), ""]
        codes[label] = r.returncode
    lines += ["=" * 78, "EXITCODE SUMMARY", ""]
    for k, v in codes.items():
        lines.append("  %-70s %d" % (k, v))
    (ROOT / "TEST_OUTPUT.txt").write_text("\n".join(lines) + "\n",
                                          encoding="utf-8")
    print("wrote TEST_OUTPUT.txt (%d bytes)" %
          (ROOT / "TEST_OUTPUT.txt").stat().st_size)
    for k, v in codes.items():
        print("  %-70s %d" % (k, v))
    return 0 if all(v == 0 for v in codes.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
