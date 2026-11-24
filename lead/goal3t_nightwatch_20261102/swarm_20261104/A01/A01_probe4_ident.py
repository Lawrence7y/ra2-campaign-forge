# -*- coding: utf-8 -*-
"""A01 probe 4: 定函数边界 + 解 0x6C8C40(计时) + 0x684060/0x684180 调用者。
只读 gamemd.exe。"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== coverage ==")
print("coverage: %.2f%%  insns=%d  resync=%d" % eng.coverage)
by = eng.by()

def head_of(va, limit=0x600):
    """向上找最近的 ret/int3 填充之后的第一个指令。"""
    a = va
    while a > va - limit:
        ins = by.get(a)
        if ins and ins.mnemonic.startswith("ret"):
            # skip padding
            b = a + ins.size
            while True:
                n = by.get(b)
                if n is None:
                    return b
                if n.mnemonic in ("nop", "int3"):
                    b += n.size
                    continue
                return b
        a -= 1
    return None

def show(lo, hi, mark=()):
    print("\n--- 0x%08X .. 0x%08X ---" % (lo, hi))
    for a, b, m, o in eng.disasm(lo, hi - lo):
        t = " <<<" if a in mark else ""
        print("0x%08X  %-22s %-8s %s%s" % (a, b, m, o, t))

for t in (0x684174, 0x684180, 0x684060, 0x6840BC, 0x6836D2, 0x665EDE, 0x67181C, 0x71106E, 0x714622):
    print("head_before(0x%08X) = 0x%s" % (t, head_of(t)))

print("\n=== 0x6C8C40 (计时原语) ===")
show(0x6C8C40, 0x6C8CC0)

print("\n=== callers of 0x684060 ===")
for ins in eng.stream:
    if ins.mnemonic == "call" and ins.op_str == "0x684060":
        print("0x%08X" % ins.address)

print("\n=== callers of 0x684120-0x68417E 函数 (猜: 0x684130?) — 扫描 call 到 0x6841xx 之前 ===")
for ins in eng.stream:
    if ins.mnemonic == "call" and ins.op_str.startswith("0x6841"):
        print("0x%08X  call %s" % (ins.address, ins.op_str))

print("\n=== 0x665650 identity: 调用者/前 64 字节 ===")
show(0x665650, 0x6656C0)
print("\n callers of 0x665650:")
for ins in eng.stream:
    if ins.mnemonic == "call" and ins.op_str == "0x665650":
        print("  0x%08X" % ins.address)

print("\n=== 0x53B560 (MLF 0x55D83A 调) 头部 ===")
show(0x53B560, 0x53B5C0)

print("\n=== 0x4F4480 (MLF 0x55D84F 调) 头部 ===")
show(0x4F4480, 0x4F44C0)
