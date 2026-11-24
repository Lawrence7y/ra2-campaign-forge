# -*- coding: utf-8 -*-
"""容器族 Find 取证：给全局容器地址，找 .text 里 `mov dword [G], imm` 的构造安装点 → vt，
读 vt[#4] = FindItemIndex → 核 `or eax,-1` / `83 C8 FF` + `ret 4`（未命中返 -1 可伪证）；
并核 vt[#4] 槽号与 §8.4 映射（slot4=FindItemIndex）。"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C


def ctor_writes(glob):
    """.text 中 `C7 05 <glob> <imm>` 的站点 → [(va, imm)]"""
    T, B = C.TEXT_DATA, C.TEXT_VA
    pat = b"\xC7\x05" + struct.pack("<I", glob)
    out, st = [], 0
    while True:
        i = T.find(pat, st)
        if i < 0:
            break
        imm = struct.unpack_from("<I", T, i + 6)[0]
        out.append((B + i, imm))
        st = i + 1
    return out


def check_find(glob, label=""):
    print("=" * 90)
    print("容器全局 %08X %s" % (glob, label))
    ws = ctor_writes(glob)
    for va, imm in ws:
        f = C.func_of(va)
        print("  写点 %08X  imm=%08X  in_func=%s  atexit=%s" % (
            va, imm, f[1] if f else None, C.is_atexit(f[0]) if f else None))
        # vt[4]
        v4 = C.u32(imm + 0x10)
        print("     vt=%08X  vt[#0]=%s vt[#4]=%s" % (imm, C.hx(C.u32(imm)), C.hx(v4) if v4 else None))
        if v4 and C.in_text(v4):
            body = C.dump(v4, C.ATLAS.get(C.hx(v4), {}).get("size") or 96)
            print("\n".join("       " + l for l in body.splitlines()))
            # 找 or eax,-1 / ret 4
            insns = C.disasm_body(v4, C.ATLAS.get(C.hx(v4), {}).get("size") or 96)
            for ins in insns:
                if ins.bytes[:3] == b"\x83\xc8\xff":
                    print("       >> `or eax,-1` @%08X" % ins.address)
                if ins.mnemonic == "ret" and ins.op_str == "4":
                    print("       >> `ret 4` @%08X" % ins.address)
    return


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        args = ["0xA8ECB8", "0xB0F670", "0x8B4150", "0x8A3870", "0x8A0208"]
    for a in args:
        check_find(int(a, 16))
