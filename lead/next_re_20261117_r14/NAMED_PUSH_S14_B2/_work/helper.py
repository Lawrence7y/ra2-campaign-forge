# -*- coding: utf-8 -*-
"""辅助取证：
1) 转储若干 helper 函数（0x410320 / 0x410380 / 0x4101f0 / 0x4109c0 / 0x7258d0 ...）
2) 给一个「全局对象首 dword 作 vptr」的地址（如 0x8872b0），找 .text 中
   `mov dword ptr [global], imm` 的安装点 -> 解析该 vt 的 RTTI 名 -> 列出槽。
用法: python helper.py funcs 0x410320 0x410380
      python helper.py vptr 0x8872b0 0x8b41c8 0x8b4120
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
from capstone import *
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))

def dump_func(va, n=None):
    key = "%08X" % va
    size = (R.ATLAS.get(key) or {}).get("size") or n or 96
    print("--- func %s size=%s ---" % (key, size))
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
    for ins in md.disasm(R.read_va(va, size), va):
        print("  %08X  %-20s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

def vtable_at(vt):
    """列出一张 vt 的槽 0..40 与其 RTTI 名。"""
    out = {}
    c = C2.u32(vt - 4)
    ci = C2.parse_col(c) if c else None
    name = None
    if ci:
        tdi = C2.parse_td(ci["td"])
        name = tdi["name"] if tdi else None
    print("--- vtable %08X  [vt-4]=%s  rtti=%s ---" % (vt, ("%08X" % c) if c else None, name))
    return name

def find_vptr_install(global_va):
    """找 .text 中 `mov dword ptr [global], imm32`（C7 05 disp32 imm32）与 `mov dword ptr [reg+disp], imm`。"""
    hits = []
    T = R.TEXT_DATA; B = R.TEXT_VA
    pat = b"\xc7\x05" + struct.pack("<I", global_va)
    st = 0
    while True:
        i = T.find(pat, st)
        if i < 0:
            break
        imm = struct.unpack_from("<I", T, i + 6)[0]
        hits.append((B + i, imm))
        st = i + 1
    return hits

def slots_of(vt, n=40):
    res = []
    for k in range(n):
        v = C2.u32(vt + 4 * k)
        res.append((k, v))
    return res

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "funcs":
        for a in sys.argv[2:]:
            dump_func(int(a, 16))
            print()
    elif mode == "vptr":
        for a in sys.argv[2:]:
            g = int(a, 16)
            print("=" * 90)
            print("GLOBAL %08X  cur_dword=%08X" % (g, C2.u32(g) or 0))
            for va, imm in find_vptr_install(g):
                print("  install @%08X -> vt=%08X  (in func %s)" % (va, imm,
                      (C2.find_containing_atlas_func(va) or (None, None, None))[1]))
                nm = vtable_at(imm)
                for k, v in slots_of(imm, 30):
                    if v:
                        print("     slot#%-2d off=0x%02X -> %08X" % (k, 4 * k, v))
            print()
