# -*- coding: utf-8 -*-
"""E3 FrameSource —— 从目标进程真实读取帧号（取代脚本模拟）。

沿用母本 `_drive_c2_x_probe_v2.tri_read_u32` 的三态语义：
    ("ok", value)         —— 读到
    ("page_absent", info) —— 页未提交（读不到，但这不是停滞证据）
    ("read_fail", info)   —— 读失败

★ 语义约定（与 StallDetector 的 C1 一致）：
    只有 "ok" 才把帧号喂给 StallDetector;
    page_absent / read_fail 一律喂 **None**（StallDetector 对 None 不推进、不重置、不判停滞）。

地址：G_FRAME = 0x00A8ED84（来自母本，已由其 #define 与台账 §532 复算确认）。
     ★ 该地址是 **gamemd.exe（32 位）** 的绝对 VA；对其它进程无意义。
       所以本模块对任意目标都只是「读某个地址」，语义上是否正确取决于目标。
"""
import ctypes
import ctypes.wintypes as wt

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000

# 母本常量（只读引用，不复制母本代码）
G_FRAME = 0x00A8ED84          # 帧号
G_EXITSTATE = 0x00A8EDD8      # 退出态（目标②；本模块只登记不读）
G_TICK = 0x00A8ED80           # tick

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.ReadProcessMemory.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                               ctypes.c_size_t]
k32.IsWow64Process.restype = wt.BOOL
k32.IsWow64Process.argtypes = [wt.HANDLE, ctypes.POINTER(wt.BOOL)]


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p),
                ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wt.DWORD),
                ("RegionSize", ctypes.c_size_t),
                ("State", wt.DWORD),
                ("Protect", wt.DWORD),
                ("Type", wt.DWORD)]


class FrameSource(object):
    """从目标进程读帧号。三态语义 + 可选「逐次读差异」诊断。"""

    def __init__(self, pid, addr=G_FRAME, open_access=PROCESS_VM_READ | PROCESS_QUERY_INFORMATION):
        self.pid = int(pid)
        self.addr = int(addr)
        self._access = open_access
        self.h = None
        self.open_error = None
        self.is32 = None
        self.reads_ok = 0
        self.reads_absent = 0
        self.reads_fail = 0

    # ---------- 生命周期 ----------
    def open(self):
        self.h = k32.OpenProcess(self._access, False, self.pid)
        if not self.h:
            self.open_error = "open_process_fail:%d" % ctypes.get_last_error()
            return False
        flag = wt.BOOL(0)
        if k32.IsWow64Process(self.h, ctypes.byref(flag)):
            self.is32 = bool(flag.value)
        return True

    def close(self):
        if self.h:
            try:
                k32.CloseHandle(self.h)
            except Exception:                            # noqa: BLE001
                pass
            self.h = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *a):
        self.close()

    # ---------- 读 ----------
    def read_u32_3state(self):
        """返回 ("ok", v) / ("page_absent", info) / ("read_fail", info)。"""
        if not self.h:
            return ("read_fail", {"reason": "no_handle"})
        buf = (ctypes.c_char * 4)()
        n = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(self.h, ctypes.c_void_p(self.addr), buf, 4,
                                   ctypes.byref(n))
        if ok and n.value == 4:
            self.reads_ok += 1
            return ("ok", int.from_bytes(buf.raw, "little"))
        err = ctypes.get_last_error()
        # 三态细分：查询该地址所在页是否已提交
        mbi = MEMORY_BASIC_INFORMATION()
        got = k32.VirtualQueryEx(self.h, ctypes.c_void_p(self.addr),
                                 ctypes.byref(mbi), ctypes.sizeof(mbi))
        if got:
            if mbi.State != MEM_COMMIT:
                self.reads_absent += 1
                return ("page_absent", {"rpm_err": err, "state": mbi.State})
            self.reads_fail += 1
            return ("read_fail", {"rpm_err": err, "state": mbi.State,
                                  "protect": mbi.Protect})
        self.reads_fail += 1
        return ("read_fail", {"rpm_err": err, "vquery_got": 0})

    def read_frame_for_detector(self):
        """给 StallDetector 用：读到就返回值，读不到一律返回 **None**。

        ★ 这是 C1 的关键语义：读失败**不是**停滞证据，必须是 None 而不是 0。
        """
        kind, val = self.read_u32_3state()
        return val if kind == "ok" else None

    def stats(self):
        return {"pid": self.pid, "addr": "0x%08X" % self.addr,
                "is32": self.is32, "ok": self.reads_ok,
                "page_absent": self.reads_absent, "read_fail": self.reads_fail}


def selftest():
    """离线自证（不 touch 任何目标）。"""
    ok = True

    def c(n, cond, ev=""):
        nonlocal ok
        print("[%s] %-46s %s" % ("OK" if cond else "RED", n, ev))
        ok = ok and cond

    print("FrameSource 模块自证")
    c("G_FRAME == 0x00A8ED84", G_FRAME == 0x00A8ED84, hex(G_FRAME))
    c("MBI 结构大小合理", ctypes.sizeof(MEMORY_BASIC_INFORMATION) in (48, 40, 64),
      str(ctypes.sizeof(MEMORY_BASIC_INFORMATION)))
    # 无句柄时应返回 read_fail 而不是崩溃
    fs = FrameSource(0, addr=0x1234)
    k, v = fs.read_u32_3state()
    c("无句柄时返回 read_fail（不崩）", k == "read_fail", str(k))
    c("read_frame_for_detector 无句柄返回 None",
      fs.read_frame_for_detector() is None)
    print("结果:", "全部通过" if ok else "有失败")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
