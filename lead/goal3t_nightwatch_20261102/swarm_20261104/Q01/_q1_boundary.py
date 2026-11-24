# -*- coding: utf-8 -*-
"""Q01 步1：0x55CFD0 函数边界（E8 头集 + ret 扫描 + 分支闭包）。"""
import sys, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage %.6f%% / %d insns / %d resync" % eng.coverage)
stream = eng.stream

# --- E8 rel32 调用目标全集（用重同步流，天然对齐） ---
call_targets = set()
for ins in stream:
    if ins.mnemonic == "call":
        try:
            if ins.operands and ins.operands[0].type == 2:
                call_targets.add(ins.operands[0].imm)
        except Exception:
            pass

heads = sorted(call_targets)
print("E8/immediate call-target heads total:", len(heads))

VA = 0x55CFD0
# --- 头部确认：0x55CFD0 是否为某 call 的目标 ---
idx = bisect.bisect_left(heads, VA)
print("0x55CFD0 in call-target set:", idx < len(heads) and heads[idx] == VA)

# --- 尾部候选：下一个 call-target 头 ---
nxt = heads[idx + 1] if idx + 1 < len(heads) else eng.THI
prev = heads[idx - 1] if idx > 0 else eng.TLO
print("prev call-target head = 0x%08X, next call-target head = 0x%08X" % (prev, nxt))

# --- ret 扫描 [VA, nxt) ---
lo, hi = VA, nxt
succ, seq = eng._edges(lo, hi)
rets = [i for i in seq if i.mnemonic.startswith("ret")]
print("rets in [0x%08X, 0x%08X): %s" % (lo, hi, [hex(r.address) for r in rets]))

# --- 分支闭包检查：内部跳转是否全落窗内；窗内地址是否被外部跳入 ---
outs = []
ext_in = []
for ins in seq:
    tgts = []
    try:
        if ins.operands and ins.operands[0].type == 2:
            tgts.append(ins.operands[0] and ins.operands[0].imm)
    except Exception:
        pass
    for t in tgts:
        if t is None:
            continue
        if not (lo <= t < hi):
            outs.append((ins.address, t, ins.mnemonic))
for va in (lo, hi):
    pass
# 谁跳入窗口（外部跳入 = 不经 call）？
for ins in stream:
    if ins.mnemonic in ("jmp", "jne", "je", "jz", "jnz", "ja", "jae", "jb", "jbe", "jg", "jge", "jl", "jle", "js", "jns", "jo", "jno", "jp", "jnp"):
        try:
            t = ins.operands[0].imm
        except Exception:
            continue
        if lo <= t < hi and not (lo <= ins.address < hi):
            ext_in.append((ins.address, t, ins.mnemonic))
print("branch-out edges (target outside window):", [(hex(a), hex(t), m) for a, t, m in outs])
print("external jump-ins:", [(hex(a), hex(t), m) for a, t, m in ext_in])

# --- 头部回扫：0x55CFD0 前面的字节（padding? ret?） ---
print("\nbytes before head:")
for a, b, m, o in eng.disasm(0x55CFC0, 0x10):
    print("  %08X  %-22s %s %s" % (a, b, m, o))
print("raw [0x55CFC0..0x55CFD0):", eng.rd(0x55CFC0, 0x10).hex())

# --- 全窗反汇编落盘供后续引用 ---
with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/Q01/_q1_55CFD0_full.asm", "w", encoding="utf-8") as f:
    cur = lo
    for i in seq:
        f.write("%08X  %-22s %s %s\n" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
print("full window disasm -> _q1_55CFD0_full.asm, %d insns" % len(seq))
