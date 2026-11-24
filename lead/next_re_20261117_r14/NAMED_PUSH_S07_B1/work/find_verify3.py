# -*- coding: utf-8 -*-
"""对每个容器全局的两个写点表(相差0x20)，解析 vt+0x10 的 Find 函数，
检查 or eax,-1 (83 C8 FF) + ret，以字节伪证 -1 哨兵；判定活表。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

# entry -> [(global, [table candidates]), ...]  (tables from find_verify2)
ROWS = {
  "00421730": [(0x88A0F0,[0x7E3238,0x7E3258]),(0xB0F720,[0x7E91EC,0x7E920C])],
  "004370C0": [(0x8B4190,[0x7E9C24,0x7E9C44])],
  "00491210": [(0x89ECF8,[0x7E5318,0x7E5338])],
  "00555150": [(0xABCA10,[0x7ECF7C,0x7ECF9C])],
}
for e, ginfo in ROWS.items():
    print("="*90); print("ROW", e)
    for g, tables in ginfo:
        print("  global %08X"%g)
        for vt in tables:
            findva = W.u32(vt+0x10)
            fs = ("%08X"%findva) if findva else "None"
            tag = ""
            if findva and R.in_text(findva):
                code = R.read_va(findva, 128)
                insns = R.disasm(findva, code)
                or_lines = ["%08X|%s"%(i.address,i.bytes.hex()) for i in insns
                            if i.mnemonic=="or" and "eax" in i.op_str and "-1" in i.op_str]
                ret_lines = ["%08X|%s|%s"%(i.address,i.mnemonic,i.bytes.hex()) for i in insns
                             if i.mnemonic.startswith("ret")]
                # 命中返下标：找 je 到某处 eax 为 index；简化：cmp [..],reg + je + mov eax,[...]
                tag = " or_eax_ff=%s ret=%s" % (or_lines, ret_lines[:2])
                if or_lines and ret_lines:
                    tag += "  <== FIND OK"
                    print("    vt=%08X Find=%s%s"%(vt,fs,tag))
                    for i in insns[:16]:
                        print("       %08X: %s %s | %s"%(i.address,i.mnemonic,i.op_str,i.bytes.hex()))
                    continue
            print("    vt=%08X Find=%s%s"%(vt,fs,tag))
