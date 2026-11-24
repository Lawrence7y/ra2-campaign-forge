# -*- coding: utf-8 -*-
"""VERIFY-P05 引擎字节复核（自写；共享引擎 ra2tool.Engine；只读镜像，零真机）。

复核项（P05 REPORT §2.1 / keyFacts）：
  ① eng.coverage 两次独立初始化 = (99.99837567729335, 1394120, 66)
  ② func_rets(0x55D360,0x55DF00) = [0x55d877, 0x55dec7, 0x55dedb]
  ③ inc edx@0x55DE7E 原始字节=42；写回 mov [0xa8ed84],edx@0x55DE81 原始字节=891584eda800
  ④ 0x55DE73..0x55DE86 指令流上下文（mov edx,[0xa8ed84] / mov eax,[0xb07784] / inc edx /
     cmp eax,edi / mov dword ptr [0xa8ed84],edx）
  ⑤ reach_without(0x55D360,0x55DF00,0x55DE7E,0x55DE86)：
     0x55D877∈R(True) / 0x55DEDB∈R(True) / 0x55DEC7∉R(False) / |R|=787（下近似）
  ⑥ 附带：镜像 sha256 == 引擎内置期望（防漂移）
"""
import sys

sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, EXPECT_SHA
import hashlib

print("== 独立初始化 #1 ==")
e1 = Engine()
sha1 = hashlib.sha256(e1.raw).hexdigest()
print("image sha256:", sha1)
print("sha==EXPECT_SHA:", sha1 == EXPECT_SHA)
print("coverage:", e1.coverage)

print("== 独立初始化 #2 ==")
e2 = Engine()
print("coverage:", e2.coverage)

eng = e1
by = eng.by()
print("== ③ 原始字节 ==")
print("rd(0x55DE7E,1).hex =", eng.rd(0x55DE7E, 1).hex(), "(期望 42 = inc edx)")
print("rd(0x55DE81,6).hex =", eng.rd(0x55DE81, 6).hex(), "(期望 891584eda800 = mov [0xa8ed84],edx)")
print("== ④ 指令流上下文 0x55DE73..0x55DE8C ==")
for a in sorted(k for k in by if 0x55DE70 <= k <= 0x55DE90):
    i = by[a]
    print(f"{a:08X}  {i.bytes.hex():<18} {i.mnemonic} {i.op_str}")

rets, _succ = eng.func_rets(0x55D360, 0x55DF00)
print("== ② func_rets(0x55D360,0x55DF00) ==")
print([hex(i.address) for i in rets])

print("== ⑤ reach_without ==")
r = eng.reach_without(0x55D360, 0x55DF00, 0x55DE7E, 0x55DE86)
for va in (0x55D877, 0x55DEC7, 0x55DEDB):
    print(f"0x{va:X} in R = {va in r}")
print("|R| =", len(r))
