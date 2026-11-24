# -*- coding: utf-8 -*-
"""独立复核员 Q2 · 反例搜索探针（只读）。"""
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

def P(*a):
    print(" ".join(str(x) for x in a), flush=True)

def hx(b):
    return b.hex(" ").upper()

e = Engine()
by = e.by()
T, H, LO, HI = 0x7CFC9F, 0x7CFB13, 0x7CFB13, 0x7CFE1C

# 反例 1: 0x7CFC9F 是不是 call/jmp/jcc 的立即数落点？Q2 声称「非 call/jmp 落点」
tgt = []
for a, ins in by.items():
    try:
        if ins.operands and ins.operands[0].type == 2:
            if (ins.mnemonic.startswith("j") or ins.mnemonic == "call") \
               and ins.operands[0].imm == T:
                tgt.append((a, ins.mnemonic, ins.op_str, hx(bytes(ins.bytes))))
    except Exception:
        pass
P("[COUNTER-1] branch/call imm targets == 0x7CFC9F =", len(tgt),
  [(hex(a), m, o, b) for a, m, o, b in sorted(tgt)])

# 反例 2: 0x7CFC9F 之前的紧邻指令（确认它不是「落点在中途」）
prev = [a for a in by if a < T]
p1 = prev[-1] if prev else None
P("[COUNTER-2] last insn start before 0x7CFC9F =", hex(p1),
  by[p1].mnemonic, by[p1].op_str, "bytes=", hx(bytes(by[p1].bytes)),
  "end=", hex(p1 + by[p1].size))

# 反例 3: [0x7CF000,0x7CFB13) 内所有 ret 指令起始（Q2 称 16 个）
r_before = [a for a in sorted(by) if 0x7CF000 <= a < H and by[a].mnemonic.startswith("ret")]
P("[COUNTER-3] ret starts in [0x7CF000,0x7CFB13) =", len(r_before),
  [hex(a) for a in r_before])

# 反例 4: 所有 83 EC / 81 EC (sub esp,imm) 指令起始，且紧邻前一字节为 C3/CC/C2
subs = []
for a in sorted(by):
    if 0x7CF000 <= a < T:
        b = e.rd(a, 2)
        if b in (b"\x83\xEC", b"\x81\xEC"):
            prevb = e.rd(a - 1, 1)
            subs.append((a, hx(e.rd(a, 6)), hx(prevb), prevb[0] in (0xC3, 0xC2, 0xCC)))
P("[COUNTER-4] sub esp,imm starts in [0x7CF000,0x7CFC9F) =", len(subs))
for s in subs:
    P("   ", hex(s[0]), s[1], "prevbyte=", s[2], "prev_is_ret/int3=", s[3])
P("[COUNTER-4] those with prevbyte ret/int3 =", [hex(s[0]) for s in subs if s[3]])

# 反例 5: 0x7CFE1C 是不是被 call 的函数入口（直接 xref）
x = []
for a, ins in by.items():
    try:
        if ins.operands and ins.operands[0].type == 2:
            if (ins.mnemonic.startswith("j") or ins.mnemonic == "call") \
               and ins.operands[0].imm == HI:
                x.append((a, ins.mnemonic, hx(bytes(ins.bytes))))
    except Exception:
        pass
P("[COUNTER-5] xrefs to 0x7CFE1C =", len(x), [(hex(a), m, b) for a, m, b in sorted(x)])

# 反例 6: 窗口内是否有 jmp 立即数目标越界（外跳尾部出口）？
outj = []
for a in sorted(a for a in by if LO <= a < HI):
    ins = by[a]
    if ins.mnemonic == "jmp":
        try:
            if ins.operands and ins.operands[0].type == 2:
                t = ins.operands[0].imm
                if not (LO <= t < HI):
                    outj.append((a, hex(t)))
        except Exception:
            pass
P("[COUNTER-6] unconditional jmp with imm target outside window =", outj)

# 反例 7: 0x7CFB13 之前最近的 ret（独立确认「紧邻前 1 字节」）
lastret = max((a for a in by if a < H and by[a].mnemonic.startswith("ret")), default=None)
P("[COUNTER-7] nearest preceding ret =", hex(lastret) if lastret else None,
  "delta to HEAD =", H - lastret if lastret else None)
