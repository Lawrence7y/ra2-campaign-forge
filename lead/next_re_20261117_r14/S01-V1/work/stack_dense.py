#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""密集栈采样：只扫主游戏线程，尽量抓到短命的调用点返回地址。
只读：Wow64GetThreadContext(Esp) + ReadProcessMemory。"""
import ctypes, struct, time, json, collections, sys
from ctypes import wintypes as wt
import w159_probe as W

k32 = ctypes.windll.kernel32
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

class WCTX(ctypes.Structure):
    _fields_ = [("ContextFlags", wt.DWORD), ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD),
                ("Dr3", wt.DWORD), ("Dr6", wt.DWORD), ("Dr7", wt.DWORD), ("FloatSave", wt.BYTE*112),
                ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
                ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
                ("Ecx", wt.DWORD), ("Eax", wt.DWORD), ("Ebp", wt.DWORD), ("Eip", wt.DWORD),
                ("SegCs", wt.DWORD), ("EFlags", wt.DWORD), ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
                ("ExtendedRegisters", wt.BYTE*512)]

def get_ctx(tid):
    h = k32.OpenThread(0x0008|0x0040, False, tid)
    if not h: return None
    try:
        c = WCTX(); c.ContextFlags = 0x00010001
        return c if k32.Wow64GetThreadContext(h, ctypes.byref(c)) else None
    finally:
        k32.CloseHandle(h)

RET_SITES = {
    0x48CE62: "ret_after_call_7241A0@48CE5D",
    0x48CE8A: "ret_after_call_69BAB0@48CE85",
    0x48CE8F: "ret_after_call_55D360@48CE8A",
    0x48CE98: "ret_after_call_55CFD0@48CE93",
    0x48CEA1: "ret_after_call_48C8B0@48CE9C",
    0x48CEA6: "ret_after_call_55CFD0@48CEA1",
    0x48CEE7: "ret_after_call_4068E0@48CEE2",
    0x48CFB6: "ret_after_call_52D9A0@48CFAA",
}
ML_LO, ML_HI = 0x48CCC0, 0x48CCC0+780

def main():
    secs = float(sys.argv[1]) if len(sys.argv)>1 else 15.0
    out = sys.argv[2] if len(sys.argv)>2 else r"..\EVIDENCE\stack_dense.ndjson"
    pid = W.pid_of(); m = W.Mem(pid)
    ph = k32.OpenProcess(0x0010|0x0400, False, pid)
    tids = W.list_threads(pid)
    # 找主游戏线程：栈上有 0x48CE8F
    main_tid = None
    buf = ctypes.create_string_buffer(0x2000); got = ctypes.c_size_t(0)
    for tid in tids:
        c = get_ctx(tid)
        if not c: continue
        if k32.ReadProcessMemory(ph, ctypes.c_void_p(c.Esp), buf, 0x2000, ctypes.byref(got)) and got.value>=4:
            words = struct.unpack_from("<%dI"%(got.value//4), buf.raw, 0)
            if 0x48CE8F in words:
                main_tid = tid; break
    print("main_tid=%s (all_tids=%d)" % (main_tid, len(tids)))
    if main_tid is None:
        print("WARN: main thread not found by 0x48CE8F; scanning all")
        scan_tids = tids
    else:
        scan_tids = [main_tid]
    hits = collections.Counter()
    n = 0
    t0=time.perf_counter()
    with open(out,"w",encoding="utf-8") as f:
        while time.perf_counter()-t0 < secs:
            frame = m.rd(0xA8ED84)
            for tid in scan_tids:
                c = get_ctx(tid)
                if not c: continue
                if k32.ReadProcessMemory(ph, ctypes.c_void_p(c.Esp), buf, 0x2000, ctypes.byref(got)) and got.value>=4:
                    words = struct.unpack_from("<%dI"%(got.value//4), buf.raw, 0)
                    for w in words:
                        if w in RET_SITES:
                            hits[w]+=1
                            f.write(json.dumps({"t":round(time.perf_counter()-t0,4),
                                                "frame":frame,"site":"%08X"%w,
                                                "name":RET_SITES[w]})+"\n")
            n+=1
    k32.CloseHandle(ph)
    print("stack samples=%d over %.1fs" % (n, time.perf_counter()-t0))
    for w,c in hits.most_common():
        print("  %08X %6d  %s" % (w,c,RET_SITES[w]))

if __name__=="__main__": main()
