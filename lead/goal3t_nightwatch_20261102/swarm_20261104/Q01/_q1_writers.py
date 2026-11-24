# -*- coding: utf-8 -*-
"""Q01 步3b：写者上下文 + 守卫 + 调用者 + 死块残留引用 + MLF 门读点 1/2 字节 + 0xABCD58 读点。"""
import sys, struct, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage %.6f%% / %d insns / %d resync" % eng.coverage)
stream = eng.stream
heads = sorted({i.operands[0].imm for i in stream
                if i.mnemonic == "call" and i.operands and i.operands[0].type == 2})
def host(va):
    k = bisect.bisect_right(heads, va) - 1
    return heads[k] if k >= 0 else None
def callers(fva):
    return [(i.address, hex(fva)) for i in stream
            if i.mnemonic == "call" and i.operands and i.operands[0].type == 2
            and i.operands[0].imm == fva]
def win(fva):
    k = bisect.bisect_left(heads, fva)
    return fva, (heads[k + 1] if k + 1 < len(heads) else eng.THI)

def dump(lo, hi, tag, mark=()):
    print("\n----- %s [0x%08X,0x%08X) -----" % (tag, lo, hi))
    for i in stream:
        if lo <= i.address < hi:
            s = "  %08X  %-20s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str)
            if i.address in mark:
                s += "   <<<<"
            print(s)

def push_strings(flo, fhi, tag):
    print("\n--- push-immediates(字符串候选) in %s ---" % tag)
    for i in stream:
        if not (flo <= i.address < fhi) or i.mnemonic != "push":
            continue
        ops = i.operands
        if not ops or ops[0].type != 2:
            continue
        v = ops[0].imm
        if 0x401000 <= v < 0x8E0000:
            s = eng.rd(v, 72).split(b"\0")[0]
            if s and all(9 <= c < 127 for c in s[:60]):
                try:
                    txt = s.decode("gbk")
                except Exception:
                    txt = repr(s[:40])
                print("   %08X push 0x%08X -> %r" % (i.address, v, txt))

# ---------- A. MLF 门读点 1/2 精确字节（流对齐） ----------
print("===== MLF 门读点全 4 组（流对齐字节） =====")
for i in stream:
    if 0x55DE40 <= i.address < 0x55DE73:
        print("  %08X  %-20s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

# ---------- B. F3 写者守卫：0x48C8B0 全函数关键段 ----------
lo, hi = win(0x48C8B0)
print("\n===== 0x48C8B0 窗口 = [0x%08X, 0x%08X) =====" % (lo, hi))
dump(0x48CA80, 0x48CB60, "0x48C8B0 内 F3 写点周边", mark=(0x48CB2E,))
# 头部到写点之间的条件结构：先看 0x48C8B0..0x48CB30 里的 jcc 链
print("\n-- 0x48C8B0 头部 --")
dump(0x48C8B0, 0x48C920, "0x48C8B0 头")
rets48 = [i.address for i in stream if lo <= i.address < hi and i.mnemonic.startswith("ret")]
print("rets:", [hex(x) for x in rets48])

# ---------- C. F1/F2 写者：0x4F7870 上下文 ----------
lo2, hi2 = win(0x4F7870)
print("\n===== 0x4F7870 窗口 = [0x%08X, 0x%08X) =====" % (lo2, hi2))
dump(0x4F8630, 0x4F87E0, "0x4F7870 内旗标写点周边", mark=(0x4F867C, 0x4F8692, 0x4F86EE, 0x4F86F7, 0x4F879C, 0x4F87B2, 0x4F87BB))
dump(0x4F7870, 0x4F78E0, "0x4F7870 头")
push_strings(lo2, hi2, "0x4F7870")
print("callers of 0x4F7870:", [(hex(a), ) for a, _ in callers(0x4F7870)])

# ---------- D. F4 写者：0x4C6CB0 上下文 ----------
lo3, hi3 = win(0x4C6CB0)
print("\n===== 0x4C6CB0 窗口 = [0x%08X, 0x%08X) =====" % (lo3, hi3))
dump(0x4C78D0, 0x4C7960, "0x4C6CB0 内 F4 写点周边", mark=(0x4C7917,))
push_strings(lo3, hi3, "0x4C6CB0")
print("callers of 0x4C6CB0:", [(hex(a),) for a, _ in callers(0x4C6CB0)])

# ---------- E. 0x48C8B0 调用者 + 头部 + push 串 ----------
print("\ncallers of 0x48C8B0:", [(hex(a),) for a, _ in callers(0x48C8B0)])
push_strings(win(0x48C8B0)[0], win(0x48C8B0)[1], "0x48C8B0")

# ---------- F. 0x55CBF0（[0xABCD58]=1 的另一个写者） ----------
lo4, hi4 = win(0x55CBF0)
print("\n===== 0x55CBF0 窗口 = [0x%08X, 0x%08X) =====" % (lo4, hi4))
dump(lo4, min(hi4, lo4 + 0x70), "0x55CBF0 头", mark=(0x55CC00, 0x55CC10))
print("callers of 0x55CBF0:", [(hex(a),) for a, _ in callers(0x55CBF0)])
# 0xABCD58 的读点
print("\n0xABCD58 all hits:")
for i in stream:
    try:
        ops = i.operands
    except Exception:
        continue
    for op in ops:
        if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp == 0xABCD58:
            print("   %08X %s %s %s host=0x%08X" % (i.address, "W" if (op.access & 2) else "R", i.mnemonic, i.op_str, host(i.address) or 0))
            break

# ---------- G. 死块残留引用 0x470350 定位 ----------
print("\n===== 文件偏移 0x470350 定位 =====")
off = 0x470350
for nm, sva, vsz, rp, rsz in eng.SEC:
    if rp <= off < rp + rsz:
        va = sva + (off - rp)
        print("section %s -> VA 0x%08X" % (nm, va))
        print("context bytes:", eng.rd(va - 8, 24).hex())
        dump(va - 16, va + 16, "0x470350->VA 0x%08X 周边" % va)
        break
else:
    print("offset 0x470350 不在任何节内（头部/数据目录）")

# ---------- H. 四转换处理器 push 串（修正版） ----------
for f in (0x685670, 0x685DC0, 0x6863E0, 0x686570):
    l, h = win(f)
    push_strings(l, h, hex(f))
    print("callers of 0x%08X:" % f, [(hex(a),) for a, _ in callers(f)])
