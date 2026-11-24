# -*- coding: utf-8 -*-
"""按 AUDIT2 方法：对每个容器全局，扫 .text 里 mov [global],<imm32> 写点，
分类宿主(构造器 vs atexit析构)，取活表 -> vt+0x10 = Find -> 核 or eax,-1 字节。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone.x86 import X86_INS_CALL, X86_OP_IMM

ROWS = {
  "00421730": [0x88A0F0, 0xB0F720],
  "004370C0": [0x8B4190],
  "00491210": [0x89ECF8],
  "00555150": [0xABCA10],
}
TEXT = R.TEXT_DATA
TVA = R.TEXT_VA

def find_global_writes(g):
    """找 C7 05 <g> <imm32> = mov dword[abs g], imm32 以及 C7 05 变体。"""
    needle = b"\xc7\x05" + struct.pack("<I", g)
    res = []
    st = 0
    while True:
        i = TEXT.find(needle, st)
        if i < 0: break
        imm = struct.unpack_from("<I", TEXT, i+6)[0]
        res.append((TVA+i, imm))
        st = i+1
    return res

def classify_host(va):
    f = W.find_containing_atlas_func(va)
    if not f:
        return (None, "no_func", False)
    atexit = bool(W.is_atexit_registered(f[0]))
    info = R.ATLAS.get(f[2], {})
    size = info.get("size", 0)
    insns = R.disasm(f[0], R.read_va(f[0], size if size else 256))
    has_free = any(ins.id==X86_INS_CALL and ins.operands and ins.operands[0].type==X86_OP_IMM and
                   (ins.operands[0].imm & 0xFFFFFFFF)==0x7C8B3D for ins in insns)
    # base ctor call heuristic: any direct call in first 20 insns
    kind = "DTOR/atexit" if (atexit or has_free) else "ctor/normal"
    return (f[0], kind, atexit)

for e, globals_ in ROWS.items():
    print("="*90)
    print("ROW", e)
    for g in globals_:
        writes = find_global_writes(g)
        print("  global %08X: %d writes" % (g, len(writes)))
        candidates = []
        for wa, imm in writes:
            hf, kind, atexit = classify_host(wa)
            print("    write@%08X imm=%08X host=%s kind=%s atexit=%s" % (
                wa, imm, ("%08X"%hf) if hf else "None", kind, atexit))
            candidates.append((wa, imm, kind, atexit))
        # pick live = ctor/normal (not DTOR)
        live = [c for c in candidates if c[2]=="ctor/normal"]
        for wa, vt, kind, atexit in live:
            if R.in_text(vt):
                continue
            findva = W.u32(vt+0x10)
            fs = ("%08X"%findva) if findva else "None"
            ors = ""
            if findva and R.in_text(findva):
                code = R.read_va(findva, 128)
                has_or = b"\x83\xc8\xff" in code
                insns = R.disasm(findva, code)
                or_lines = ["%08X:%s %s|%s"%(i.address,i.mnemonic,i.op_str,i.bytes.hex())
                            for i in insns if i.mnemonic=="or" and "eax" in i.op_str and "-1" in i.op_str]
                ret_lines = ["%08X:%s|%s"%(i.address,i.mnemonic,i.bytes.hex())
                             for i in insns if i.mnemonic.startswith("ret")]
                cmp_lines = ["%08X:%s %s"%(i.address,i.mnemonic,i.op_str)
                             for i in insns if i.mnemonic=="cmp" and "[" in i.op_str]
                ors = " or_eax_ff=%s or@=%s ret@=%s cmp_mem=%s" % (has_or, or_lines, ret_lines[:3], cmp_lines[:3])
            else:
                ors = " (Find not in .text)"
            print("      LIVE vt=%08X (write@%08X) vt+0x10=Find=%s%s" % (vt, wa, fs, ors))
