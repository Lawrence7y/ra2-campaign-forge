#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01-V1 综合真机探针（只读）：
  A. EIP 原始值分桶（per-EIP Counter）+ 函数区间分类（entry+size 区间包含）
  B. 帧号 [0xA8ED84] + 墙钟 + GetProcessTimes（供 3 个 >=10s 窗算帧率）
  C. 栈回溯采样：在主线程栈上找落在主循环函数区间内的返回地址，
     用于验证「哪个调用点 → 哪个 callee」的调用边（定序替代观测）。
全部只读：OpenProcess(VM_READ|QUERY_INFORMATION) + ReadProcessMemory
        + Wow64GetThreadContext + GetProcessTimes。未写内存/未注入/未 Hook。
"""
import argparse, ctypes, json, struct, subprocess, sys, time, collections
from ctypes import wintypes as wt

import w159_probe as W

k32 = ctypes.windll.kernel32
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.GetProcessTimes.argtypes = [wt.HANDLE, ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME),
                                ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME)]

A_FRAME, A_MODE, A_BULLETS = 0x00A8ED84, 0x00A8B238, 0x00A8ED50

# 函数区间（entry, size 来自 function_atlas.tsv；区间包含 = [entry, entry+size)）
FUNCS = [
    ("mainloop_48CCC0",   0x48CCC0, 780),
    ("conquer_48C8B0",    0x48C8B0, 978),
    ("perframe_55D360",   0x55D360, 2940),
    ("predicate_55CFD0",  0x55CFD0, 786),
    ("dispatch_55AFB0",   0x55AFB0, 1901),
    ("sub_69BAB0",        0x69BAB0, 144),
    ("crashguard_7241A0", 0x7241A0, 87),
    ("orevalue_485020",   0x485020, 51),
    ("greatestthreat_6F8DF0", 0x6F8DF0, 4031),
    ("ftol_7C5F00",       0x7C5F00, 61),
    ("blitterfactory_48EBF0", 0x48EBF0, 6145),
]
# 主循环调用点返回地址（call 指令 5 字节，ret=site+5）
RET_SITES = {
    0x48CE62: "ret_after_call_7241A0@48CE5D",
    0x48CE8A: "ret_after_call_69BAB0@48CE85",
    0x48CE8F: "ret_after_call_55D360@48CE8A",
    0x48CE98: "ret_after_call_55CFD0@48CE93",
    0x48CEA1: "ret_after_call_48C8B0@48CE9C",
    0x48CEA6: "ret_after_call_55CFD0@48CEA1",
    0x48CEE7: "ret_after_call_4068E0@48CEE2",
}
ML_LO, ML_HI = 0x48CCC0, 0x48CCC0 + 780

TEXT_LO, TEXT_HI = 0x401000, 0x7DF38D  # .text VA 区间 (ImageBase+VA..+VSize)

class WOW64_CONTEXT(ctypes.Structure):
    # 必须与 w159_probe.WOW64_CONTEXT 逐字段一致（Dr0-Dr3,Dr6,Dr7 无 Dr4/Dr5），
    # 否则 Eip/Esp 偏移错位。此处只用于取 Esp 做栈采样；EIP 用 W.eip_of()。
    _fields_ = [("ContextFlags", wt.DWORD), ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD),
                ("Dr3", wt.DWORD), ("Dr6", wt.DWORD), ("Dr7", wt.DWORD),
                ("FloatSave", wt.BYTE * 112),
                ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
                ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
                ("Ecx", wt.DWORD), ("Eax", wt.DWORD), ("Ebp", wt.DWORD), ("Eip", wt.DWORD),
                ("SegCs", wt.DWORD), ("EFlags", wt.DWORD), ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
                ("ExtendedRegisters", wt.BYTE * 512)]
CTX = WOW64_CONTEXT()
CTX.ContextFlags = 0x00010001  # CONTEXT_CONTROL

def get_ctx(tid):
    h = k32.OpenThread(0x0008 | 0x0040, False, tid)
    if not h: return None
    try:
        c = WOW64_CONTEXT(); c.ContextFlags = 0x00010001
        return c if k32.Wow64GetThreadContext(h, ctypes.byref(c)) else None
    finally:
        k32.CloseHandle(h)

def ft2ms(ft): return ((ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 10000.0

def proc_cpu_ms(h):
    c,e,k,u = wt.FILETIME(),wt.FILETIME(),wt.FILETIME(),wt.FILETIME()
    return (ft2ms(k)+ft2ms(u)) if k32.GetProcessTimes(h,ctypes.byref(c),ctypes.byref(e),ctypes.byref(k),ctypes.byref(u)) else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=float, default=45.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--raw", required=True, help="raw EIP histogram output")
    ap.add_argument("--stack", required=True, help="stack-return-site output")
    ap.add_argument("--eip-burst", type=int, default=300)
    ap.add_argument("--stack-every", type=int, default=8, help="每 N 次外层循环采一次栈")
    a = ap.parse_args()

    pid = W.pid_of()
    if not pid: print("gamemd not running"); return 2
    m = W.Mem(pid)
    ph = k32.OpenProcess(0x0010 | 0x0400, False, pid)
    tids = [t for t in W.list_threads(pid) if W.eip_of(t) is not None]
    print("pid=%d threads=%d eip_burst=%d secs=%.0f" % (pid,len(tids),a.eip_burst,a.secs))
    print("initial frame=%s mode=%s" % (m.rd(A_FRAME), m.rd(A_MODE)))

    raw = collections.Counter()
    region_hits = {n:0 for n,_,_ in FUNCS}
    eip_total = 0; eip_text = 0
    ret_site_hits = collections.Counter()
    samples = 0
    sc_buf = ctypes.create_string_buffer(0x4000)
    got = ctypes.c_size_t(0)

    t0 = time.perf_counter()
    with open(a.out,"w",encoding="utf-8") as f, open(a.stack,"w",encoding="utf-8") as fs:
        while time.perf_counter()-t0 < a.secs:
            t = time.perf_counter()-t0
            frame = m.rd(A_FRAME); mode = m.rd(A_MODE); bullets = m.rd(A_BULLETS)
            cpu = proc_cpu_ms(ph)
            # EIP burst
            for _ in range(a.eip_burst):
                for tid in tids:
                    e = W.eip_of(tid)
                    if e is None: continue
                    eip_total += 1
                    raw[e] += 1
                    if TEXT_LO <= e < TEXT_HI: eip_text += 1
                    for n,lo,sz in FUNCS:
                        if lo <= e < lo+sz:
                            region_hits[n] += 1
                            break
            # stack sample（每 N 次外层循环）
            if samples % a.stack_every == 0:
                for tid in tids:
                    c = get_ctx(tid)
                    if not c: continue
                    esp = c.Esp
                    if k32.ReadProcessMemory(ph, ctypes.c_void_p(esp), sc_buf, 0x4000, ctypes.byref(got)) and got.value>=4:
                        nwords = got.value//4
                        words = struct.unpack_from("<%dI"%nwords, sc_buf.raw, 0)
                        for w in words:
                            if w in RET_SITES:
                                ret_site_hits[w] += 1
                            if ML_LO <= w < ML_HI:
                                ret_site_hits[("mlrange",w)] += 1
            f.write(json.dumps({"t":round(t,4),"frame":frame,"mode":mode,
                                "bullets":bullets,"cpu_ms":cpu,"eip_n":a.eip_burst*len(tids)})+"\n")
            samples += 1
            time.sleep(0.05)
    k32.CloseHandle(ph)

    # raw histogram 全量落盘（不截断）
    with open(a.raw,"w",encoding="utf-8") as f:
        f.write("# eip_hex8\thits\tpct_of_total\tpct_of_text\n")
        for e,c in raw.most_common():
            f.write("%08X\t%d\t%.6f\t%.6f\n" % (e,c,100.0*c/max(1,eip_total),100.0*c/max(1,eip_text)))
    # stack sites 落盘
    with open(a.stack+".summary","w",encoding="utf-8") as f:
        f.write("# return_site_hex8\tname\thits\n")
        for w,c in ret_site_hits.most_common():
            if isinstance(w,tuple):
                f.write("%08X\t%s(ml-range)\t%d\n" % (w[1], RET_SITES.get(w[1],"?"), c))
            else:
                f.write("%08X\t%s\t%d\n" % (w, RET_SITES.get(w,"?"), c))

    print("samples=%d eip_total=%d eip_in_text=%d (%.2f%%) distinct_eip=%d"
          % (samples,eip_total,eip_text,100.0*eip_text/max(1,eip_total),len(raw)))
    print("frame %s -> %s" % (json.loads(open(a.out).readline())["frame"],
                              json.loads(open(a.out).readlines()[-1])["frame"]))
    print("\n%-26s %10s %9s" % ("region","hits","per-1e4-text"))
    for n,lo,sz in FUNCS:
        print("%-26s %10d %9.2f" % (n,region_hits[n],10000.0*region_hits[n]/max(1,eip_text)))
    print("\ntop-10 EIP values (raw buckets, %% of ALL samples):")
    for e,c in raw.most_common(10):
        print("  %08X %8d %6.3f%%" % (e,c,100.0*c/max(1,eip_total)))
    print("\nstack return sites (top-15):")
    for w,c in ret_site_hits.most_common(15):
        print("  %s  %d" % (str(w) if isinstance(w,tuple) else "%08X %s"%(w,RET_SITES.get(w,"?")), c))
    return 0

if __name__ == "__main__":
    sys.exit(main())
