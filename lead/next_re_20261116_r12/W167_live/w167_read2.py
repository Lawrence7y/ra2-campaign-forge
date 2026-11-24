"""W167：只读两个 dword（本轮授权范围严格限定为这两个量）。

读：
  1. P = [0x8871E0]                    全局对象基址指针
  2. N = [P + 0x1808]                  节流除数（FootClass::AI 的 idiv 分母）
  3. V = [P]                           该对象的 vptr -> 可反查类名
附带（只读、非侵入）：把 P 附近若干 dword 与 frame/mode 一起打印，便于交叉核对。

不做任何写入、不注入输入、不改游戏文件。
"""
import ctypes
import json
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

k32 = ctypes.windll.kernel32
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

A_PTR = 0x008871E0
A_FRAME = 0x00A8ED84
A_MODE = 0x00A8B238
OFF_N = 0x1808

VTJSON = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"


def pid_of(name="gamemd"):
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process %s -ErrorAction SilentlyContinue).Id" % name],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0010 | 0x0400, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed")
        self.b = ctypes.create_string_buffer(4)
        self.got = ctypes.c_size_t(0)

    def u32(self, va):
        if k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), self.b, 4, ctypes.byref(self.got)) \
                and self.got.value == 4:
            return struct.unpack("<I", self.b.raw)[0]
        return None


def vtables():
    d = json.load(open(VTJSON, encoding="utf-8"))
    m = {}
    for v in d["vtables"]:
        m.setdefault(v["vt"], []).append((v["class"], v["col_offset"]))
    return m


def read_once(m, label):
    p = m.u32(A_PTR)
    frame = m.u32(A_FRAME)
    mode = m.u32(A_MODE)
    rec = dict(label=label, t=round(time.time(), 3), ptr_8871E0=p,
               frame=frame, mode=mode, n=None, vptr=None)
    if p:
        rec["n"] = m.u32(p + OFF_N)
        rec["vptr"] = m.u32(p)
        rec["near_p"] = [m.u32(p + 4 * k) for k in range(0, 6)]
    return rec


def main():
    pid = pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    m = Mem(pid)
    vt = vtables()
    print("pid=%d" % pid)

    snapshots = []
    for i in range(5):
        r = read_once(m, "t+%d" % i)
        snapshots.append(r)
        print("  %-5s frame=%-6s mode=%-2s P=[0x8871E0]=%s  N=[[P]+0x1808]=%s  vptr=[P]=%s"
              % (r["label"], r["frame"], r["mode"],
                 hex(r["ptr_8871E0"]) if r["ptr_8871E0"] else r["ptr_8871E0"],
                 r["n"], hex(r["vptr"]) if r["vptr"] else r["vptr"]))
        if r["vptr"]:
            hits = vt.get(r["vptr"], [])
            if hits:
                print("        vptr 反查类名: %s" % ["%s(col_off=%d)" % h for h in hits])
            else:
                print("        vptr 不在 canonical 虚表表里（可能是 sub-vtable 或非对象）")
        time.sleep(0.8)

    print()
    print("=== 汇总（同一进程内是否稳定）===")
    for k in ("ptr_8871E0", "n", "vptr"):
        vals = {r[k] for r in snapshots}
        print("  %-12s distinct=%s" % (k, [hex(v) if isinstance(v, int) else v for v in vals]))

    json.dump(snapshots, open("EVIDENCE/w167_snapshots.json", "w", encoding="utf-8"), indent=2)
    print()
    print("written: EVIDENCE/w167_snapshots.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
