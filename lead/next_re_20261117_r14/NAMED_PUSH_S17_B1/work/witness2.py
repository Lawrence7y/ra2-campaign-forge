# -*- coding: utf-8 -*-
"""④ 活虚表派发计数（修正 modrm 解码）+ 构造器 install 点是否活对象。"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C

def count_call_reg_disp(slot_off):
    """`call [reg+disp8]` = FF /2 with mod=01. modrm = 01 010 rrr = 0x50|rrr.
       count all FF 5? with disp8==slot_off (rm may be SIB 0x54 but still [reg+disp8]).
       Also mod=10 disp32 variant FF 9? <disp32>. Return (count8, samples8, count32)."""
    cnt8=0; samp=[]; cnt32=0
    d=len(C.TEXT_DATA)
    for off in range(0, d-3):
        if C.TEXT_DATA[off]!=0xFF: continue
        modrm=C.TEXT_DATA[off+1]
        if (modrm & 0xC0)!=0x40: continue          # mod=01 disp8
        if (modrm & 0x38)!=0x10: continue          # reg=010 = call
        if C.TEXT_DATA[off+2]==slot_off & 0xFF:
            cnt8+=1
            if len(samp)<16: samp.append(C.hx(C.TEXT_VA+off))
    for off in range(0, d-6):
        if C.TEXT_DATA[off]!=0xFF: continue
        modrm=C.TEXT_DATA[off+1]
        if (modrm & 0xC0)!=0x80: continue          # mod=10 disp32
        if (modrm & 0x38)!=0x10: continue
        disp=struct.unpack_from("<i",C.TEXT_DATA,off+2)[0] & 0xFFFFFFFF
        if disp==slot_off: cnt32+=1
    return cnt8, samp, cnt32

def find_ctor_callers(ctor_va):
    """direct E8 callers of a constructor."""
    return [C.hx(x) for x in C.find_direct_calls(int(ctor_va,16))]

def dump_func(entry_hex, maxbytes=0x60):
    ea=int(entry_hex,16)
    for ins in C.disasm_body(ea,maxbytes)[:40]:
        print("  %s: %-9s %s"%(C.hx(ins.address),ins.mnemonic,ins.op_str))

if __name__=="__main__":
    print("=== dispatch counts (fixed) ===")
    for off in [0x00,0x04,0x08,0x0C,0x10,0x14,0x1C,0x20,0x24,0x38]:
        c8,s,c32=count_call_reg_disp(off)
        print(" +%02X(slot#%d): disp8=%d disp32=%d samples=%s"%(off,off//4,c8,c32," ".join(s[:8])))
    print("\n=== ctor direct callers ===")
    for ctor in ["004A2820","006BEE40","006BF5C0"]:
        print(" ctor %s callers(%d)=%s"%(ctor,len(find_ctor_callers(ctor))," ".join(find_ctor_callers(ctor)[:12])))
    print("\n=== 004A2820 ctor full body (heap alloc -> live object) ===")
    dump_func("004A2820",0x60)
