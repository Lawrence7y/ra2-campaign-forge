# -*- coding: utf-8 -*-
"""E3 端到端触发链真机验证：StallDetector（帧号停推 N=1.0s）→ StackSampler 自动采样。

目标：验证「等停滞再采」这条链真的能串起来，而不是「立即采一次」。

方法（对**受控目标**，非游戏）：
  起一个 32 位目标（charmap.exe），由本脚本**自己模拟帧号源**：
    - 阶段 A（0..1.2s）：帧号持续递增（模拟正常跑）→ 不应触发
    - 阶段 B（1.2..3.2s）：帧号冻结（模拟停滞）→ 应在 ~1.0s 后触发一次
    - 阶段 C（3.2s 起）：帧号恢复递增 → 触发后段重置
  触发时真正调 StackSampler.sample() 采目标栈。

★ 这里「帧号」是脚本内模拟的（因为不启动游戏）；
  真正接 gamemd.exe 时，帧号来源是 ReadProcessMemory(G_FRAME=0xA8ED84)。
  本次验证的是**触发逻辑与采样的串联**，不是游戏帧号读取。
"""
import ctypes
import importlib.util
import io
import contextlib
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
CAND = REPO / "lead" / "re_d13_ruling_20261112" / "e3_stack_sampler_candidate.py"


def load():
    spec = importlib.util.spec_from_file_location("e3c_e2e", str(CAND))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class ChainHarness(object):
    """把 StallDetector 与 StackSampler 串成「等停滞→采样」的链。"""

    def __init__(self, m, pid, n_seconds=1.0, min_obs=6, poll_s=0.12):
        self.m = m
        self.pid = pid
        self.det = m.StallDetector(n_seconds=n_seconds, min_obs=min_obs)
        self.poll_s = poll_s
        self.sampler = m.StackSampler(budget_ms=300.0)
        self.fired_count = 0
        self.samples = []
        self.trace = []

    def step(self, t, frame):
        """喂一次帧号观测；若判定停滞则立即采样。返回是否发生了采样。"""
        fired = self.det.observe(t, frame)
        self.trace.append((round(t, 3), frame, fired))
        if fired:
            self.fired_count += 1
            res = self.sampler.sample(self.pid)
            self.samples.append(res)
            return True
        return False


def main():
    fails = []
    n = {"v": 0}

    def t(name, cond, ev=""):
        n["v"] += 1
        print("[%s] %-52s %s" % ("OK" if cond else "RED", name, ev))
        if not cond:
            fails.append(name)

    print("=" * 78)
    print("E3 端到端触发链验证：StallDetector → StackSampler（对受控 32 位目标）")
    print("=" * 78)

    m = load()
    target = r"C:\Windows\SysWOW64\charmap.exe"
    if not Path(target).exists():
        print("!! 目标不存在"); return 2

    proc = subprocess.Popen([target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("受控目标 pid=%d (%s)" % (proc.pid, Path(target).name))
    try:
        time.sleep(1.2)
        m.bind_real_ops()
        h = ChainHarness(m, proc.pid, n_seconds=1.0, min_obs=6, poll_s=0.12)

        # ---- 阶段 A：帧号递增（不应触发）----
        print("\n-- 阶段 A：帧号持续递增 1.2s（期望：不触发）--")
        t0 = time.monotonic()
        f = 1000
        while time.monotonic() - t0 < 1.2:
            f += 7
            h.step(time.monotonic(), f)
            time.sleep(h.poll_s)
        t("A-1 递增阶段未触发", h.fired_count == 0, "fired=%d" % h.fired_count)

        # ---- 阶段 B：帧号冻结（应触发一次）----
        print("\n-- 阶段 B：帧号冻结 2.4s（期望：~1.0s 后触发恰好 1 次）--")
        tb = time.monotonic()
        frozen = f
        while time.monotonic() - tb < 2.4:
            h.step(time.monotonic(), frozen)
            time.sleep(h.poll_s)
        t("B-1 冻结阶段触发恰好 1 次", h.fired_count == 1, "fired=%d" % h.fired_count)
        t("B-2 触发时真的采到了栈", len(h.samples) == 1 and h.samples[0].get("threads"),
          "samples=%d" % len(h.samples))
        if h.samples:
            s = h.samples[0]
            got = [x for x in s.get("threads", []) if x.get("frames")]
            t("B-3 采样结果含有效 frames", len(got) > 0, "n=%d" % len(got))
            t("B-4 采样无错误", s.get("errors") == [], str(s.get("errors")))
            t("B-5 目标位宽判为 32 位", s.get("target_bits") == 32,
              str(s.get("target_bits")))
            if got:
                print("      首个栈: tid=%d bits=%s ip=%s"
                      % (got[0]["tid"], got[0].get("ctx", {}).get("bits"),
                         hex(got[0].get("ctx", {}).get("ip", 0))))

        # ---- 阶段 C：帧号恢复（触发后段重置，不再重复触发）----
        print("\n-- 阶段 C：帧号恢复递增 1.0s（期望：不再新触发）--")
        tc = time.monotonic()
        g = frozen
        while time.monotonic() - tc < 1.0:
            g += 5
            h.step(time.monotonic(), g)
            time.sleep(h.poll_s)
        t("C-1 恢复后不再新触发", h.fired_count == 1, "fired=%d" % h.fired_count)

        # ---- 阶段 D：再次冻结（应再触发一次，证明可重复）----
        print("\n-- 阶段 D：再次冻结 2.0s（期望：再触发一次，共 2 次）--")
        td = time.monotonic()
        while time.monotonic() - td < 2.0:
            h.step(time.monotonic(), g)
            time.sleep(h.poll_s)
        t("D-1 再次冻结再次触发（共 2 次）", h.fired_count == 2, "fired=%d" % h.fired_count)
        t("D-2 第二次采样同样无错误",
          len(h.samples) == 2 and h.samples[1].get("errors") == [],
          str(h.samples[1].get("errors") if len(h.samples) > 1 else "n/a"))

        # ---- 安全 ----
        print("\n-- 安全断言 --")
        t("S-1 目标进程仍存活", proc.poll() is None, "poll=%r" % proc.poll())

        # ---- 追踪摘要 ----
        print("\n-- 触发链追踪（前 6 条 + 后 6 条）--")
        for rec in h.trace[:6]:
            print("   t=%.3f frame=%s fired=%s" % rec)
        print("   ...")
        for rec in h.trace[-6:]:
            print("   t=%.3f frame=%s fired=%s" % rec)
    finally:
        try:
            proc.terminate(); proc.wait(timeout=5)
            print("\n受控目标已终止 rc=%r" % proc.returncode)
        except Exception as e:                          # noqa: BLE001
            print("\n终止失败: %s" % e)
        m.OPS.clear()

    print("\n" + "=" * 78)
    print("结果：%d 项检查，%d 项失败%s" % (n["v"], len(fails),
                                     "" if not fails else "：%s" % fails))
    print("=" * 78)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
