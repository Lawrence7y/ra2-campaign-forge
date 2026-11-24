# -*- coding: utf-8 -*-
"""深度验证：写点函数 ctor/dtor 分类、slot0 返回约定、atexit、活虚表派发计数。"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C

def dump_func(entry_hex, maxbytes=0x120, title=""):
    ea = int(entry_hex, 16)
    insns = C.disasm_body(ea, maxbytes)
    print("--- func %s %s (atlas=%s) ---" % (entry_hex, title, C.ATLAS.get(entry_hex)))
    for ins in insns[:60]:
        print("  %s: %-9s %s" % (C.hx(ins.address), ins.mnemonic, ins.op_str))
    print()

def classify_write_sites():
    print("========== vtable write-site functions (ctor vs dtor) ==========")
    for f in ["004A2820","004A2880","004A3110","006BEE40","006BF5C0"]:
        dump_func(f, title="write-site host")
    print("========== slot0 functions (what call [vptr+0] invokes) ==========")
    for f in ["004A2990","006BEE50","006BF5D0"]:
        dump_func(f, 0xA0, title="slot0")

def atexit_check():
    print("========== atexit registration of write-site hosts ==========")
    for f in ["004A2820","004A2880","004A3110","006BEE40","006BF5C0","004A2990","006BEE50","006BF5D0"]:
        sites = C.is_atexit_registered(int(f,16))
        print("  %s atexit_sites=%s" % (f, sites))

def dispatch_count(slot_off):
    """count `call [reg+disp8]` where disp8==slot_off across .text (mod=01, reg=010 call).
       modrm = 01 010 rrr = 0x50 | rrr ; rm!=100 (SIB) -> 0x50..0x57 except 0x54."""
    cnt=0; samples=[]
    for off in range(0, len(C.TEXT_DATA)-3):
        if C.TEXT_DATA[off]!=0xFF: continue
        modrm=C.TEXT_DATA[off+1]
        if (modrm & 0xC7)==0x50 and (modrm & 0x38)==0x10 and C.TEXT_DATA[off+2]==slot_off:
            # mod=01 (01), reg=010 (call), rm=reg (000-111 incl 100->SIB but mod=01 rm=100 is [reg+disp8])
            cnt+=1
            if len(samples)<12: samples.append(C.hx(C.TEXT_VA+off))
    return cnt, samples

def dispatch_scan():
    print("========== live vtable dispatch `call [reg+disp8]` counts ==========")
    for off in [0x0C,0x10,0x20,0x38]:
        cnt,samp=dispatch_count(off)
        print("  slot_off=+%02X (slot#%d): count=%d samples=%s" % (off, off//4, cnt, " ".join(samp)))

if __name__=="__main__":
    classify_write_sites()
    atexit_check()
    dispatch_scan()
