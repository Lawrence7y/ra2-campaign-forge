# -*- coding: utf-8 -*-
"""攻击 c：operand_write() 的写入判定覆盖度。
用 capstone 真解码硬编码字节，再喂给被审脚本的 operand_write / classify_source。
"""
import sys
from pathlib import Path

import capstone

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _verify_ecx_dataflow as G  # noqa: E402

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

CASES = [
    # (bytes, 说明, 期望: 是否应判为「写 ecx」, 期望语义)
    (b"\x8b\x0d\x68\x73\x88\x00", "mov ecx,[0x887368]", "write", "GLOBAL"),
    (b"\x23\x0d\x68\x73\x88\x00", "and ecx,[0x887368]", "write", "NOT-global"),
    (b"\x0b\x0d\x68\x73\x88\x00", "or  ecx,[0x887368]", "write", "NOT-global"),
    (b"\x03\x0d\x68\x73\x88\x00", "add ecx,[0x887368]", "write", "NOT-global"),
    (b"\x2b\x0d\x68\x73\x88\x00", "sub ecx,[0x887368]", "write", "NOT-global"),
    (b"\x0f\xaf\x0d\x68\x73\x88\x00", "imul ecx,[0x887368]", "write", "NOT-global"),
    (b"\x0f\xb1\x0d\x68\x73\x88\x00", "cmpxchg ecx,[0x887368]", "cond-write", "NOT-global"),
    (b"\x0f\xa5\xf1", "shld ecx,esi,cl", "write", "NOT-esi"),
    (b"\x0f\xab\xc8", "bts eax,ecx", "write-eax", "-"),
    (b"\x0f\xab\xc1", "bts ecx,eax", "write", "NOT-eax"),
    (b"\x0f\xc1\xf1", "xadd ecx,esi", "write", "NOT-esi"),
    (b"\x0f\x94\xc1", "sete cl", "write-ecx-low", "NOT-global"),
    (b"\x0f\xb6\xc9", "movzx ecx,cl", "write", "NOT-global"),
    (b"\x66\x0f\xb6\x0d\x68\x73\x88\x00", "movzx ecx,byte[0x887368]", "write", "NOT-dword"),
    (b"\x0f\xb7\x0d\x68\x73\x88\x00", "movzx ecx,word[0x887368]", "write", "NOT-dword"),
    (b"\x66\x0f\xbe\x0d\x68\x73\x88\x00", "movsx ecx,word[0x887368]", "write", "NOT-dword"),
    (b"\x66\x0f\x6e\xc8", "movd ecx,xmm0", "write", "NOT-global"),
    (b"\xf3\x0f\xb8\xc8", "popcnt ecx,eax", "write", "NOT-global"),
    (b"\x0f\xc7\xf1", "rdrand ecx", "write", "NOT-global"),
    (b"\xf2\x0f\x38\xf1\xc8", "crc32 ecx,eax", "write", "NOT-global"),
    (b"\x9f", "lahf", "write-ah", "-"),
    (b"\x0f\xa4\xc8\x04", "shld eax,ecx,4", "write-eax", "-"),
    (b"\xf3\xa5", "rep movsd", "clobber-ecx", "NOT-global"),
    (b"\xf3\xab", "rep stosd", "clobber-ecx", "NOT-global"),
    (b"\x0f\xa2", "cpuid", "clobber-ecx", "NOT-global"),
    (b"\xc8\x10\x00\x00", "enter 0x10,0", "no-ecx", "-"),
    (b"\xc9", "leave", "no-ecx", "-"),
    (b"\xf7\xe1", "mul ecx", "clobber-ecx", "NOT-global"),
    (b"\xf7\xe9", "imul ecx (1-op)", "clobber-ecx", "NOT-global"),
    (b"\xf7\xf1", "div ecx", "clobber-ecx", "NOT-global"),
    (b"\x0f\xaf\xc1", "imul eax,ecx", "write-eax", "-"),
    (b"\x87\xc8", "xchg eax,ecx", "write-both", "-"),
    (b"\x8b\xc8", "mov ecx,eax", "write", "REG-eax"),
    (b"\x8b\xc9", "mov ecx,ecx", "no-change", "-"),
    (b"\xd1\xe1", "shl ecx,1", "write", "RMW"),
    (b"\x0f\xbc\xc8", "bsf ecx,eax", "write", "NOT-global"),
    (b"\x0f\xbd\xc8", "bsr ecx,eax", "write", "NOT-global"),
    (b"\x0f\x4e\xc8", "cmovle ecx,eax", "cond-write", "NOT-global"),
]


def main():
    print("WRITE_MNEM  (%d): %s" % (len(G.WRITE_MNEM), sorted(G.WRITE_MNEM)))
    print("EXTRA_WRITE (%d): %s" % (len(G.EXTRA_WRITE), sorted(G.EXTRA_WRITE)))
    print("CLOBBER_MULTI (%d): %s" % (len(G.CLOBBER_MULTI), sorted(G.CLOBBER_MULTI)))
    print("PARTIAL (%d): %s" % (len(G.PARTIAL), sorted(G.PARTIAL)))
    print()

    print("%-34s %-16s %-10s %-22s %s"
          % ("bytes", "disasm", "operand_write", "classify_source", "判定"))
    print("-" * 130)
    bad = []
    for bs, note, kind, expect in CASES:
        ins = list(md.disasm(bs, 0x1000))
        if not ins:
            print("%-34s  <undecodable> %s" % (bs.hex(" "), note))
            continue
        ins = ins[0]
        d, s = G.operand_write(ins)
        if d == "__IMPLICIT__":
            cs = "IMPLICIT"
        elif d is None:
            cs = "-"
        else:
            k, v = G.classify_source(ins, s)
            cs = "%s/%s" % (k, v)
        judged = "d=%s src=%s" % (d, s)
        print("%-34s %-16s %-10s %-22s %s"
              % (bs.hex(" "), "%s %s" % (ins.mnemonic, ins.op_str), judged, cs, note))

        # 判定正确性
        if expect == "NOT-global" and cs.startswith("GLOBAL"):
            bad.append((note, "被判 GLOBAL（假绿）", cs))
        if expect == "NOT-esi" and cs == "REG/esi":
            bad.append((note, "被判 REG esi（假绿：ecx 实际不是 esi）", cs))
        if expect == "NOT-eax" and cs == "REG/eax":
            bad.append((note, "被判 REG eax（假绿）", cs))
        if expect == "NOT-dword" and cs.startswith("GLOBAL"):
            bad.append((note, "被判 GLOBAL（宽度不符，值不等）", cs))
        if expect in ("write", "write-ecx-low", "write-both", "clobber-ecx") \
                and d is None:
            bad.append((note, "完全漏判：不认为写 ecx", str((d, s))))

    print("\n=== 覆盖缺口 ===")
    if not bad:
        print("  无")
    for n, why, cs in bad:
        print("  ★ %-28s %s  (classify=%s)" % (n, why, cs))


if __name__ == "__main__":
    main()
