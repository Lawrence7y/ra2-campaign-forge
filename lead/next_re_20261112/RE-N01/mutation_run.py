# -*- coding: utf-8 -*-
"""RE-N01 / mutation_run.py —— 变异测试驱动器（证明测试能失败）。

流程（每次变异都在**副本**上，原件目录里的候选文件永不被改）：
  1. 把干净件的 4 个 .py + replay + test 复制到 out/_mutation/<id>/
  2. 对副本里**指定文件**做一次精确文本替换（old 必须恰好出现 1 次）
  3. 在副本根目录起一个**全新 Python 进程**跑 test_re_n01_offline.py，
     收集 stdout + 退出码 ⇒ 期望变红
  4. 复原：用干净件覆盖副本（= 重新拷贝），再跑一遍 ⇒ 期望回绿
  5. 原始输出写 out/mutation_results.txt，供 MUTATION_LOG.md 引用

用法：python -X utf8 mutation_run.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAND = ROOT / "candidate"
MUT = ROOT / "out" / "_mutation"
OUT = ROOT / "out" / "mutation_results.txt"

FILES = [
    "candidate/re_n01_monitor.py",
    "candidate/_run_hl_match_candidate.py",
    "candidate/e3_stack_sampler_candidate_r2.py",
    "replay_re_n01.py",
    "test_re_n01_offline.py",
]

MUTATIONS = [
    {
        "id": "M-A1",
        "target_test": "T-A1",
        "file": "candidate/re_n01_monitor.py",
        "what": "把 build_event 的 only_tid 分支条件改成恒 False ⇒ "
                "--only-tid 退化成先调全线程 sample(pid)（问题 A 回归）",
        "old": "    if only_tid:\n        raw = sampler.sample_single(int(want_tid), int(pid), timer=timer)",
        "new": "    if False:\n        raw = sampler.sample_single(int(want_tid), int(pid), timer=timer)",
    },
    {
        "id": "M-C2",
        "target_test": "T-C2",
        "file": "candidate/re_n01_monitor.py",
        "what": "把 _RunScanner.push 的缺测/间隔处理整段改成朴素合并 ⇒ "
                "过滤读失败、忽略 gap_ns 与段边界，两端同值被拼成连续冻结",
        "old": """        ok = (r.get("read_status") == "ok" and r.get("frame") is not None)
        if not ok:
            self._close("gap_interrupted")
            self.pending_gap = True
            self.prev = r
            return
        gap = int(r.get("gap_ns") or 0)
        if self.prev is not None:
            if (self.prev.get("segment") != r.get("segment")
                    or self.prev.get("read_status") != "ok"
                    or gap > self.gap_max_ns):
                self._close("gap_interrupted")
                self.pending_gap = True
        if self.cur is not None:
            if (self.cur["segment"] != r.get("segment")
                    or gap > self.gap_max_ns):
                self._close("gap_interrupted")
                self.pending_gap = True
            elif self.cur["frame"] != r.get("frame"):
                self._close("frame_change")""",
        "new": """        ok = (r.get("read_status") == "ok" and r.get("frame") is not None)
        if not ok:
            self.prev = r
            return
        gap = 0""",
    },
    {
        "id": "M-C4",
        "target_test": "T-C4",
        "file": "candidate/re_n01_monitor.py",
        "what": "OnlineAccumulator.summary 的 n_frame_reads 故意 +1 ⇒ "
                "在线摘要与 replay 离线重算不再逐字段一致",
        "old": '            "n_frame_reads": self.n_frame_reads,\n',
        "new": '            "n_frame_reads": self.n_frame_reads + 1,\n',
    },
    {
        "id": "M-B2",
        "target_test": "T-B2",
        "file": "candidate/re_n01_monitor.py",
        "what": "SAMPLE_STATES 把 resume_verified_ok 改成 ok ⇒ "
                "五态塌成四态（用 null/同值兼表状态的回归）",
        "old": 'SAMPLE_STATES = ("not_attempted", "ok", "resume_verified_ok",\n'
               '                 "resume_failed", "error")',
        "new": 'SAMPLE_STATES = ("not_attempted", "ok", "ok",\n'
               '                 "resume_failed", "error")',
    },
    {
        "id": "M-A3",
        "target_test": "T-A3",
        "file": "candidate/re_n01_monitor.py",
        "what": "event_total_ns 只取 resume→end（最后一次调用）⇒ "
                "重新退回「只记最后一次函数调用耗时」的问题 B",
        "old": '        "event_total_ns": d(t_cand, t_end),\n',
        "new": '        "event_total_ns": d(t_res, t_end),\n',
    },
]


def clean_copy(dst):
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for rel in FILES:
        src = ROOT / rel
        d = dst / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, d)
    return dst


def run_tests(dst, label, log):
    p = subprocess.run([sys.executable, "-X", "utf8",
                        str(dst / "test_re_n01_offline.py")],
                       cwd=str(dst), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    text = (p.stdout or "") + (p.stderr or "")
    log.append("---- %s (exit=%d) ----" % (label, p.returncode))
    log.append(text.rstrip())
    log.append("")
    return p.returncode, text


def main():
    lines = []
    lines.append("=" * 78)
    lines.append("RE-N01 变异测试原始输出（每次变异均在副本上；原件零改动）")
    lines.append("命令：python -X utf8 test_re_n01_offline.py  （cwd=副本根目录）")
    lines.append("=" * 78)
    lines.append("")
    summary = []
    for m in MUTATIONS:
        dst = MUT / m["id"]
        clean_copy(dst)
        f = dst / m["file"]
        txt = f.read_text(encoding="utf-8")
        n = txt.count(m["old"])
        if n != 1:
            lines.append("[SETUP-FAIL] %s old 出现 %d 次（要求恰好 1 次）" %
                         (m["id"], n))
            summary.append({"id": m["id"], "setup_fail": True, "n_old": n})
            continue
        f.write_text(txt.replace(m["old"], m["new"], 1), encoding="utf-8")
        red_rc, red_txt = run_tests(dst, "%s MUTATED" % m["id"], lines)
        red_lines = [x for x in red_txt.splitlines() if "[RED]" in x]
        reds = [x.split()[1] for x in red_lines if len(x.split()) > 1]
        # 复原：干净件覆盖副本，再跑一次
        clean_copy(dst)
        green_rc, green_txt = run_tests(dst, "%s RESTORED" % m["id"], lines)
        green_ok = (green_rc == 0 and "0 项失败" in green_txt)
        hit = m["target_test"] in reds
        summary.append({
            "id": m["id"], "target": m["target_test"],
            "red_exit": red_rc, "red_lines": red_lines,
            "red_names": reds, "target_red": hit,
            "green_exit": green_rc, "green_ok": green_ok,
            "what": m["what"],
        })
    lines.append("=" * 78)
    lines.append("汇总（机器可读）")
    lines.append(json.dumps(summary, ensure_ascii=False, indent=1))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    bad = [s for s in summary
           if s.get("setup_fail") or not s.get("target_red")
           or not s.get("green_ok")]
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
