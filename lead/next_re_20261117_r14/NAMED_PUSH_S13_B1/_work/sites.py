# -*- coding: utf-8 -*-
"""打印指定地址区间反汇编（含字节）；并打印 00468670 的 vt slot#124 上下文。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C2

def show(a, b):
    print("  --- [%08X,%08X) ---" % (a,b))
    for ins in R.disasm(a, R.read_va(a, b-a)):
        print("    %08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

ranges = [
 (0x00468620,0x00468668,"004684E0 ③b"),
 (0x0062A0D0,0x0062A112,"00629FD0 ③b#1"),
 (0x005F9955,0x005F996E,"callee 005F9950"),
 (0x0075E0E8,0x0075E145,"0075E0C0 ③b+install"),
 (0x0075E2C8,0x0075E2DE,"0075E2C0 ③b"),
 (0x00772CF4,0x00772D10,"00772CD0 ③b"),
 (0x00772EB8,0x00772ECE,"00772EB0 ③b"),
 (0x0046C730,0x0046C74D,"0046C730 full"),
]
for a,b,tag in ranges:
    print("\n### %s" % tag); show(a,b)

print("\n### 00468670 vt slot#124 check")
vt=0x007E46E4
for k in [0,4,0x40,0x14,0x18,0x1EC,0x1F0,0x1F4]:
    print("  vt+%04X @%08X = %08X" % (k, vt+k, C2.u32(vt+k) or 0))
print("  COL @vt-4 = %08X" % (C2.u32(vt-4) or 0))
c=C2.parse_col(C2.u32(vt-4)); print("  COL sig=%s td=%08X" % (c["sig"],c["td"]))
tdi=C2.parse_td(c["td"]); print("  name=%s @%08X" % (tdi["name"],tdi["name_va"]))
# 找 00468670 在 vt 内的所有引用
needle=struct.pack("<I",0x00468670)
data=R.RDATA_DATA
base=R.RDATA_VA
st=0
while True:
    i=data.find(needle,st)
    if i<0: break
    print("  ref @%08X = slot#%d" % (base+i,(base+i-vt)//4))
    st=i+1
