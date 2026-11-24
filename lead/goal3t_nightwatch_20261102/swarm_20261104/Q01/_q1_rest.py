# -*- coding: utf-8 -*-
"""Q01 步4b：0x48C8B0 全 dump + F3 路径条件 + .data 0x870350 指针表 + 字符串收尾。"""
import sys, bisect, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage %.6f%% / %d insns / %d resync" % eng.coverage)
stream = eng.stream
heads = sorted({i.operands[0].imm for i in stream
                if i.mnemonic == "call" and i.operands and i.operands[0].type == 2})

# ---------- B. 0x48C8B0 全 dump ----------
k = bisect.bisect_left(heads, 0x48C8B0)
lo, hi = 0x48C8B0, heads[k + 1]
seq = [i for i in stream if lo <= i.address < hi]
with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/Q01/_q1_48C8B0_full.asm", "w", encoding="utf-8") as f:
    for i in seq:
        f.write("%08X  %-20s %s %s\n" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
print("0x48C8B0 window=[0x%08X,0x%08X) insns=%d -> _q1_48C8B0_full.asm" % (lo, hi, len(seq)))
print("jcc/cmp/test from head to 0x48CB2E:")
for i in seq:
    if i.address >= 0x48CB2E:
        break
    if i.mnemonic.startswith("j") or i.mnemonic in ("cmp", "test"):
        print("  %08X  %s %s" % (i.address, i.mnemonic, i.op_str))

# ---------- 表 0x870350 邻域 dump ----------
print("\n===== .data 表邻域 [0x870320, 0x870380) =====")
base = 0x870320
vals = []
for off in range(0, 0x60, 4):
    v = eng.u32(base + off)
    mark = ""
    if eng.TLO <= v < eng.THI:
        mark = "  <.text>"
    print("  0x%08X: 0x%08X%s" % (base + off, v, mark))
    vals.append((base + off, v))

# 表的基址与范围：向前/向后找连续 .text 指针
start = None
p = 0x870350
while True:
    p -= 4
    v = eng.u32(p)
    if eng.TLO <= v < eng.THI:
        start = p
    else:
        break
end = 0x870350
while True:
    end += 4
    v = eng.u32(end)
    if not (eng.TLO <= v < eng.THI):
        break
print("连续 .text 指针表范围: [0x%08X, 0x%08X] 共 %d 项" % (start, end, (end - start) // 4 + 1))
tab = []
q = start
while q <= end:
    tab.append(eng.u32(q))
    q += 4
print("表项:", [hex(x) for x in tab])
diffs = sorted({tab[i + 1] - tab[i] for i in range(len(tab) - 1)})
print("相邻差集:", [hex(d) for d in diffs])

# 谁读这张表？绝对 disp 与 [reg+disp] 两种
print("\n表内每个地址的访存普查（绝对 + reg 相对）：")
for q in range(start - 0x10, end + 0x14, 4):
    for va, tag in ((q, "abs"),):
        h = eng.disp_hits(va)
        if h:
            for a, rw, m, o in h:
                print("  [abs 0x%08X] %08X %s %s %s host=0x%08X" % (va, a, rw, m, o, heads[bisect.bisect_right(heads, a) - 1]))
    h2 = eng.disp_hits_field(q)
    if h2:
        for a, rw, m, o in h2:
            print("  [fld 0x%08X] %08X %s %s %s host=0x%08X" % (q, a, rw, m, o, heads[bisect.bisect_right(heads, a) - 1]))

# 表项目标处字节是否为合法指令头
print("\n表项目标字节：")
for v in tab:
    b = eng.rd(v, 8).hex()
    print("  0x%08X: %s" % (v, b))

# ---------- 字符串收尾 ----------
print("\n===== 字符串收尾 =====")
print("0x82A044:", eng.rd(0x82A044, 96).split(b"\0")[0])
print("0x82A038:", eng.rd(0x82A038, 12).split(b"\0")[0])
raw = eng.raw
for pat in (b"Disconnect", b"disconnect"):
    idx = 0
    n = 0
    while n < 8:
        j = raw.find(pat, idx)
        if j < 0:
            break
        s = raw[j:j + 48].split(b"\0")[0]
        # 定位 VA
        va = None
        for nm, sva, vsz, rp, rsz in eng.SEC:
            if rp <= j < rp + rsz:
                va = sva + (j - rp)
                break
        print("raw %r @file 0x%X VA=%s: %r" % (pat, j, hex(va) if va else "?", s))
        idx = j + 1
        n += 1

# 0x686570 与 0x6863E0 的完整 push/lea 字符串引用（含 mov reg,imm 形态）
print("\n===== 0x686570/0x6863E0/0x685670/0x685DC0 内 imm==串地址 的 mov/push/lea =====")
for fva, fhi in ((0x685670, 0x685DC0), (0x685DC0, 0x6863E0), (0x6863E0, 0x686570), (0x686570, 0x686730)):
    for i in stream:
        if not (fva <= i.address < fhi):
            continue
        try:
            ops = i.operands
        except Exception:
            continue
        for op in ops:
            if op.type == 2 and 0x81D000 <= op.imm < 0x870000:
                s = eng.rd(op.imm, 80).split(b"\0")[0]
                print("  [%08X] %08X %s %s -> %r" % (fva, i.address, i.mnemonic, i.op_str, s))
                break
