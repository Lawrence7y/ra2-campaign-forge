#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GLM 分析代理转述地址的独立字节核验（快照断言 + capstone）。

申报不符 ⇒ 该组地址证据作废。负控=对已知正确锚（0x6BE0E1=39 3D D8 ED A8 00）必须过。
"""
import hashlib
from pathlib import Path
import capstone

SNAP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020\gamemd.exe")
d = SNAP.read_bytes()
sha16 = hashlib.sha256(d).hexdigest()[:16]
print("snapshot sha16 =", sha16, "(assert 73201cc021497c95)")
assert sha16 == "73201cc021497c95", "snapshot mismatch — stop"
v2f = lambda va: va - 0x400000
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

def bytes_at(va, n):
    return d[v2f(va):v2f(va) + n].hex()

def dis_at(va, n=16):
    return ["%08X: %s %s" % (i.address, i.mnemonic, i.op_str)
            for i in md.disasm(d[v2f(va):v2f(va) + n], va)]

cases = [
    # (claim source, va, expected_hex_prefix, note)
    ("负控锚 bail 站点", 0x6BE0E1, "393dd8eda800", "cmp [0xa8edd8],edi"),
    ("负控锚 bail je", 0x6BE0E7, "74f3", "je→loop"),
    ("GLM 声称 WM_CLOSE cmp", 0x5F4855, "83f810", "cmp eax,0x10"),
    ("GLM 声称 EndDialog call", 0x5F4869, "e8", "call rel32→0x5F7350"),
]
print()
rc = 0
for who, va, exp, note in cases:
    got = bytes_at(va, len(exp) // 2 or 1)
    ok = got.upper().startswith(exp.upper())
    print("[%s] %-16s @%08X 期望前缀 %s 实读 %s  (%s)" % ("PASS" if ok else "FAIL", who, va, exp, got, note))
    print("     disasm:", "; ".join(dis_at(va, 12)[:3]))
    if not ok:
        rc = 1
print()
print("VERDICT:", "GLM 地址组不成立（字节不符）" if rc else "GLM 地址组成立")
raise SystemExit(0)  # 期望 FAIL——本件目的是记录核验，FAIL=预期结果，exit 0
