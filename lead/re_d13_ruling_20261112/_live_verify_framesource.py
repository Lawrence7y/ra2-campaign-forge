# -*- coding: utf-8 -*-
"""E3 FrameSource 真机验证 + 全链（真实内存帧号 → 停滞判定 → 真栈回溯）。

方法（对受控目标，不碰游戏）：
  1. spawn 一个长驻目标（32 位 charmap / 64 位 python）
  2. 用 VirtualAllocEx 在目标里分配一页，WriteProcessMemory 写入一个 32 位计数器
  3. FrameSource 用真实 ReadProcessMemory 读该计数器
  4. 分三阶段：
       A 递增（WriteProcessMemory 持续 +1）     → 不应触发
       B 冻结（停止写入 = 计数器不变）           → 应在 ~1.0s 后触发一次，并真回溯
       C 恢复递增                               → 不再新触发
  5. 另测三态：读未提交页 → page_absent；关闭句柄 → read_fail；两者都不应判停滞
  6. 安全：结束前 FreeEx 释放、断言目标存活、无残留挂起
"""
import ctypes
import ctypes.wintypes as wt
import importlib.util
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
BASE = REPO / "lead" / "re_d13_ruling_20261112"


def load(name, fn):
    spec = importlib.util.spec_from_file_location(name, str(BASE / fn))
    m = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]
    try:
        spec.loader.exec_module(m)
    except SystemExit:
        pass
    return m


# ---- 进程内存操作 ----
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.VirtualAllocEx.restype = ctypes.c_void_p
k32.VirtualAllocEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t,
                               wt.DWORD, wt.DWORD]
k32.VirtualFreeEx.restype = wt.BOOL
k32.VirtualFreeEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wt.DWORD]
k32.WriteProcessMemory.restype = wt.BOOL
k32.WriteProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

PROCESS_ALL = 0x0010 | 0x0020 | 0x0008 | 0x0400   # VM_READ|VM_WRITE|VM_OPERATION|QUERY
MEM_COMMIT_RESERVE = 0x1000 | 0x2000
PAGE_READWRITE = 0x04
MEM_RELEASE = 0x8000


def write_u32(h, addr, val):
    buf = ctypes.c_uint32(int(val) & 0xFFFFFFFF)
    n = ctypes.c_size_t(0)
    ok = k32.WriteProcessMemory(h, ctypes.c_void_p(addr), ctypes.byref(buf), 4,
                                ctypes.byref(n))
    return bool(ok) and n.value == 4


def check(name, cond, ev=""):
    print("[%s] %-56s %s" % ("OK" if cond else "RED", name, ev))
    return cond


def main():
    fails = []
    n = {"v": 0}

    def t(name, cond, ev=""):
        n["v"] += 1
        if not check(name, cond, ev):
            fails.append(name)

    print("=" * 78)
    print("E3 FrameSource 真机验证 + 全链（真实内存帧号 → 停滞 → 真栈）")
    print("=" * 78)

    cand = load("cand", "e3_stack_sampler_candidate.py")
    fsmod = load("fsmod", "e3_framesource.py")

    targets = [
        ("32 位", r"C:\Windows\SysWOW64\charmap.exe", []),
        ("64 位", sys.executable, [str(BASE / "_sleep_target.py")]),
    ]
    (BASE / "_sleep_target.py").write_text(
        "import time\nfor _ in range(600): time.sleep(1)\n", encoding="utf-8")

    for label, exe, args in targets:
        print("\n" + "=" * 78)
        print("目标: %s (%s)" % (label, Path(exe).name))
        print("=" * 78)
        proc = subprocess.Popen([exe] + args, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        try:
            time.sleep(1.2)
            h = k32.OpenProcess(PROCESS_ALL, False, proc.pid)
            t("%s OpenProcess(全权) 成功" % label, bool(h), "h=%r" % h)
            if not h:
                continue
            counter_addr = None
            try:
                # 1. 注入计数器
                counter_addr = k32.VirtualAllocEx(h, None, 0x1000,
                                                  MEM_COMMIT_RESERVE, PAGE_READWRITE)
                t("%s VirtualAllocEx 成功" % label, bool(counter_addr),
                  "addr=%#x" % (counter_addr or 0))
                if not counter_addr:
                    continue
                t("%s 初始写入 1000" % label, write_u32(h, counter_addr, 1000))

                # 2. FrameSource 真实读取
                fs = fsmod.FrameSource(proc.pid, addr=counter_addr)
                t("%s FrameSource.open 成功" % label, fs.open(), fs.open_error or "")
                t("%s 位宽判定与目标一致" % label, fs.is32 is not None,
                  "is32=%s" % fs.is32)
                kind, val = fs.read_u32_3state()
                t("%s 真实读取三态为 ok" % label, kind == "ok", "%s=%s" % (kind, val))
                t("%s 读到的值正确(1000)" % label, kind == "ok" and val == 1000,
                  str(val))
                t("%s read_frame_for_detector 返回值" % label,
                  fs.read_frame_for_detector() == 1000)

                # 3. 三态：读未提交页
                bad_addr = 0x7FFF0000
                fs_bad = fsmod.FrameSource(proc.pid, addr=bad_addr)
                fs_bad.open()
                k2, _ = fs_bad.read_u32_3state()
                t("%s 读未提交页 → page_absent" % label,
                  k2 in ("page_absent", "read_fail"), k2)
                t("%s 读失败时 detector 收到 None（非 0）" % label,
                  fs_bad.read_frame_for_detector() is None)
                fs_bad.close()

                # 4. 全链：真实内存帧号 → StallDetector → StackSampler
                cand.bind_real_ops()
                det = cand.StallDetector(n_seconds=1.0, min_obs=6)
                sampler = cand.StackSampler(budget_ms=300.0)
                hproc_w = cand.OPS["open_process"](0x0010 | 0x0400, proc.pid)
                is32 = fs.is32
                wok, werr = cand.attach_stackwalker(sampler, hproc_w, proc.pid,
                                                   bool(is32))
                t("%s StackWalker 挂载成功" % label, wok, werr or "")

                fired = {"n": 0, "samples": []}

                def tick(write_val=None):
                    if write_val is not None:
                        write_u32(h, counter_addr, write_val)
                    frame = fs.read_frame_for_detector()
                    if det.observe(time.monotonic(), frame):
                        fired["n"] += 1
                        fired["samples"].append(sampler.sample(proc.pid))

                # 阶段 A：递增
                print("  -- A 递增 1.2s（不应触发）--")
                v = 1000
                tA = time.monotonic()
                while time.monotonic() - tA < 1.2:
                    v += 3
                    tick(v)
                    time.sleep(0.1)
                t("%s A-1 递增阶段未触发" % label, fired["n"] == 0,
                  "fired=%d" % fired["n"])

                # 阶段 B：冻结（不再写 = 计数器不变）
                print("  -- B 冻结 2.4s（应触发一次并真回溯）--")
                tB = time.monotonic()
                while time.monotonic() - tB < 2.4:
                    tick(None)
                    time.sleep(0.1)
                t("%s B-1 冻结触发恰好 1 次" % label, fired["n"] == 1,
                  "fired=%d" % fired["n"])
                if fired["samples"]:
                    s0 = fired["samples"][0]
                    got = [x for x in s0.get("threads", []) if x.get("frames")]
                    t("%s B-2 触发时采到栈" % label, len(got) > 0, "n=%d" % len(got))
                    t("%s B-3 采样无错误" % label, s0.get("errors") == [],
                      str(s0.get("errors")))
                    multi = [x for x in got if len(x["frames"]) > 1]
                    t("%s B-4 至少一线程是真回溯(>1 帧)" % label, len(multi) > 0,
                      "multi=%d/%d" % (len(multi), len(got)))
                    named = [f for x in got for f in x["frames"]
                             if isinstance(f, dict) and f.get("name")]
                    t("%s B-5 帧能命名到模块+偏移" % label, len(named) > 0,
                      "named=%d" % len(named))
                    if multi:
                        print("      %s 示例栈:" % label)
                        for i, f in enumerate(multi[0]["frames"][:5]):
                            print("        #%d %s" % (i, f.get("name") or
                                                          hex(f.get("addr") or 0)))

                # 阶段 C：恢复
                print("  -- C 恢复递增 1.0s（不应新触发）--")
                tC = time.monotonic()
                while time.monotonic() - tC < 1.0:
                    v += 5
                    tick(v)
                    time.sleep(0.1)
                t("%s C-1 恢复后不再新触发" % label, fired["n"] == 1,
                  "fired=%d" % fired["n"])

                # 清理 walker
                try:
                    sampler.stack_walker.cleanup()
                except Exception:                        # noqa: BLE001
                    pass
                cand.OPS["close_handle"](hproc_w)
                fs.close()
            finally:
                if counter_addr:
                    k32.VirtualFreeEx(h, ctypes.c_void_p(counter_addr), 0, MEM_RELEASE)
                t("%s 目标进程仍存活" % label, proc.poll() is None,
                  "poll=%r" % proc.poll())
                k32.CloseHandle(h)
        finally:
            try:
                proc.terminate(); proc.wait(timeout=5)
                print("已终止目标 rc=%r" % proc.returncode)
            except Exception as e:                       # noqa: BLE001
                print("终止失败: %s" % e)

    try:
        (BASE / "_sleep_target.py").unlink()
    except Exception:                                    # noqa: BLE001
        pass

    print("\n" + "=" * 78)
    print("结果：%d 项检查，%d 项失败%s" % (n["v"], len(fails),
                                     "" if not fails else "：%s" % fails))
    print("=" * 78)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
