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
# ---------- 出口追加（只追加：原件 1-44 行逐字未改，仅在其末行前插入） ----------
# A. 原件「对自身的检查」及结果去向（本会话逐行实读）：
#    :13-15 sha16 == "73201cc021497c95" —— 快照完整性前置守卫，走 assert 通道（失败即 AssertionError）；
#    :26-32 cases 四项字节前缀比对，:37 ok = got.upper().startswith(exp.upper()) 为逐项二值判定；
#            :28-29 是负控双锚（验解码器/VA→file 映射），:30-31 是 GLM 转述地址（被测字节）；
#    :38 print("[PASS]/[FAIL] ...")、:39 print("     disasm:", ...) —— 逐项结果只走 stdout，零写盘；
#    :40-41 if not ok: rc = 1 —— 原件已有的合取汇总；:43 print("VERDICT:", ...) 依 rc 打印二值裁决，仍只走 stdout；
#    :44 raise SystemExit(0) 恒 0，与上述全部结果无数据通路（零信息出口）。
# B. 追加段不改原件任何判定条件/阈值/分支：只复用仍存活的只读全局量（sha16 / cases / bytes_at）
#    逐字重算 :15 与 :37 的同一比较式并喂 check()；原 :38/:43 的 print 一行不动，stdout 逐字保留。
#    原 :44 保留为不可达死行（纯追加所需），其注释所述「FAIL=预期结果，exit 0」自本段起失效。
# 模板：lead/dtrigger_compare_20261107/_check_dtrigger.py:31-35 + :226-228
ok = True
def check(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name)

check("快照 sha16 == 73201cc021497c95 (:15)", sha16 == "73201cc021497c95")
for who, va, exp, note in cases:
    got = bytes_at(va, len(exp) // 2 or 1)
    check("字节前缀 %s @%08X (:37)" % (who, va),
          got.upper().startswith(exp.upper()))
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
raise SystemExit(0)  # 期望 FAIL——本件目的是记录核验，FAIL=预期结果，exit 0
