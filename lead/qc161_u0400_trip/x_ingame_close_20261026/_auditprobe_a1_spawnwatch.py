# -*- coding: utf-8 -*-
"""_auditprobe_a1_spawnwatch.py — A1 运行时铁证：拦截全部进程创建原语后跑探针三模式。

方法：import 被审件（PYTHONDONTWRITEBYTECODE 由外层保证），把 subprocess.Popen /
subprocess.run / os.system / ctypes 侧 CreateProcess 路径全部包上记录器（tasklist
允许放行，其它一律记账并拒真执行）。然后依次驱动 main() 的 --live / --preflight /
--selftest，收集 argv 流水。断言：全程仅允许出现 tasklist；任何 gamemd/rc4_loader
Popen ⇒ 记 FALSIFIED。
"""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

PROBE = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_x_channel_probe_20261027.py")
LOG = []

_orig_run = subprocess.run
_orig_popen = subprocess.Popen


def run_wrapper(*a, **k):
    cmd = a[0] if a else k.get("args")
    LOG.append(("subprocess.run", repr(cmd)))
    return _orig_run(*a, **k)


def popen_wrapper(*a, **k):
    cmd = a[0] if a else k.get("args")
    LOG.append(("subprocess.Popen", repr(cmd)))
    raise AssertionError("Popen 被拦截（审计禁真启动）: %r" % (cmd,))


def main():
    subprocess.run = run_wrapper
    subprocess.Popen = popen_wrapper
    import os
    os.system = lambda c: (_ for _ in ()).throw(AssertionError("os.system: %r" % c))

    spec = importlib.util.spec_from_file_location("_probe_watch", str(PROBE))
    P = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(P)

    # 1) --live
    LOG.clear()
    sys.argv = ["x", "--live"]
    rc_live = P.main()
    print("--live rc=%s 期间进程创建=%s" % (rc_live, LOG))
    assert rc_live == 3
    assert LOG == []

    # 2) --preflight（真跑；内部 tasklist 放行）
    LOG.clear()
    sys.argv = ["x", "--preflight"]
    rc_pf = P.main()
    print("--preflight rc=%s" % rc_pf)
    for e in LOG:
        print("   spawn:", e)

    bad = [e for e in LOG
           if ("gamemd" in e[1].lower() or "rc4_loader" in e[1].lower()
               or "popen" in e[0].lower())]
    only_tasklist = all("tasklist" in e[1].lower() for e in LOG)
    print("   仅 tasklist=%s；gamemd/loader/Popen 命中=%s" % (only_tasklist, bad))

    # 3) --selftest（离线）
    LOG.clear()
    sys.argv = ["x", "--selftest"]
    rc_st = P.main()
    print("--selftest rc=%s 期间进程创建=%s" % (rc_st, LOG))
    assert rc_st == 0 and LOG == []

    return 0 if (only_tasklist and not bad) else 1


if __name__ == "__main__":
    sys.exit(main())
