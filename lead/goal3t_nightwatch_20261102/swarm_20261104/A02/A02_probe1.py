# -*- coding: utf-8 -*-
"""A02 probe1 —— MainLogicFrame 0x55D360 头部 Sleep+泵 自旋环 / 泵 0x5D4D50 / 焦点旗标 0xA8ED80 冲突裁定

只读 gamemd.exe（sha256 断言在 ra2tool.Engine）。
产物：stdout（重定向到 A02_probe1_out.txt）。

口径：全部重同步线性解码（ra2tool.Engine.stream），禁 md.disasm(blob) 扫全镜像。
"""
import sys

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()

def H(t):
    print("\n" + "=" * 78)
    print("== " + t)
    print("=" * 78)

H("0. 现场自证")
cov, nins, resync = eng.coverage
print("eng.coverage = %.2f%% / %d insns / %d resync" % (cov, nins, resync))
print("sha256 = %s" % eng.sha)
print("ImageBase = 0x%X" % eng.IB)
for nm, va, vsz, rp, rsz in eng.SEC:
    print("  sec %-8s VA 0x%08X vsz 0x%06X raw 0x%06X rsz 0x%06X" % (nm, va, vsz, rp, rsz))
print(".text = [0x%08X, 0x%08X) size 0x%X" % (eng.TLO, eng.THI, eng.TSZ))

H("1. MainLogicFrame 头部 0x55D360..0x55D3E0 逐字节")
for va, bs, mn, ops in eng.disasm(0x55D360, 0x90):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("2. 0x55D3B2..0x55D3E0 之后（jne 目标 0x55D3BB 起的帧体）")
for va, bs, mn, ops in eng.disasm(0x55D3B0, 0x70):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("3. 泵 0x5D4D50 全函数反汇编")
for va, bs, mn, ops in eng.disasm(0x5D4D50, 0x140):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("4. IAT 解析：0x7E11F0 / 0x7E1530 / 0x7E13CC(SetFocus ref) 等")
for va in (0x7E11F0, 0x7E1530):
    print("  [0x%08X] -> %r" % (va, eng.resolve_iat(va)))

H("5. 0xA8ED80 全镜像 disp 命中（绝对寻址普查）")
hits = eng.disp_hits(0x00A8ED80)
print("  总计 %d 处" % len(hits))
nw = 0
for va, rw, mn, ops in hits:
    if rw == "W":
        nw += 1
    print("  %08X  %s  %-8s %s" % (va, rw, mn, ops))
print("  写 = %d / 读 = %d" % (nw, len(hits) - nw))

H("6. 0xA8ED80 raw abs32 扫描（独立于 capstone，防漏）")
target = eng.u32(0x0)  # noop
import struct
pat = struct.pack("<I", 0x00A8ED80)
idx, found = 0, []
while True:
    j = eng.raw.find(pat, idx)
    if j < 0:
        break
    found.append(j)
    idx = j + 1
print("  raw 命中 %d 处" % len(found))
for j in found:
    # file offset -> VA
    va = None
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if rp <= j < rp + rsz:
            va = sva + (j - rp)
            sec = nm
            break
    print("     file 0x%06X -> VA 0x%08X (%s)  bytes=%s" % (j, va, sec, eng.raw[j - 2:j + 8].hex()))

H("7. 0xA8ED81 / 0xA8ED84 写者对照（邻位）")
for g in (0x00A8ED81, 0x00A8ED84):
    h = eng.disp_hits(g)
    w = [x for x in h if x[1] == "W"]
    print("  0x%08X: 共 %d 处, 写 %d 处" % (g, len(h), len(w)))
    for va, rw, mn, ops in w:
        print("      W %08X  %-8s %s" % (va, mn, ops))

H("8. MainLogicFrame 出口枚举（0x55D360..0x55DEE0）")
rets, succ = eng.func_rets(0x55D360, 0x55DEE0)
print("  ret 数 = %d" % len(rets))
for r in rets:
    print("    %08X  %-8s %s" % (r.address, r.mnemonic, r.op_str))

H("9. 0x55D360..0x55DEE0 内回边")
for src, tgt, mn in eng.loop_backedges(0x55D360, 0x55DEE0):
    print("    %08X -> %08X  (%s)" % (src, tgt, mn))

H("10. 0x5D4D50 函数边界：前向闭包/ret")
rets2, succ2 = eng.func_rets(0x5D4D50, 0x5D4F00)
print("  ret 数 = %d" % len(rets2))
for r in rets2:
    print("    %08X  %-8s %s" % (r.address, r.mnemonic, r.op_str))
print("  -- 从 0x5D4D50 出发、绕开 [0x5D4D70,0x5D4D7A] 仍可达 --")
reach = eng.reach_without(0x5D4D50, 0x5D4F00, 0x5D4D70, 0x5D4D7A)
print("    reach size = %d ; max = 0x%08X" % (len(reach), max(reach)))

H("11. 0x5D4D50 的调用者普查（E8 直呼）")
callers = []
for ins in eng.stream:
    if ins.mnemonic == "call":
        try:
            if ins.operands and ins.operands[0].type == 2 and ins.operands[0].imm == 0x5D4D50:
                callers.append(ins.address)
        except Exception:
            pass
print("  call 0x5D4D50 命中 %d 处" % len(callers))
for c in callers:
    print("    0x%08X" % c)

H("12. DispatchMessageA / PeekMessageA 在 0x5D4D50 体内")
for va, bs, mn, ops in eng.disasm(0x5D4D50, 0x140):
    if "call" in mn and ("0x7E1" in ops or "[" in ops):
        print("  %08X  %-20s %s" % (va, bs, ops))

H("13. 0x7778CE 上下文逐字节（写者）")
for va, bs, mn, ops in eng.disasm(0x777890, 0x60):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("14. 0xA8B238 GameMode 读点（MainLogicFrame 内 + 全镜像计数）")
h = eng.disp_hits(0x00A8B238)
print("  0xA8B238 共 %d 处引用" % len(h))
inmlf = [x for x in h if 0x55D360 <= x[0] < 0x55DEE0]
print("  其中落在 MainLogicFrame 内: %d 处" % len(inmlf))
for va, rw, mn, ops in inmlf:
    print("    %08X %s %-8s %s" % (va, rw, mn, ops))
w = [x for x in h if x[1] == "W"]
print("  全镜像写者 %d 处:" % len(w))
for va, rw, mn, ops in w:
    print("    W %08X %-8s %s" % (va, mn, ops))

H("15. 0xA8E9A0 局内标志写者/读点")
h = eng.disp_hits(0x00A8E9A0)
print("  0xA8E9A0 共 %d 处" % len(h))
for va, rw, mn, ops in h:
    print("    %08X %s %-8s %s" % (va, rw, mn, ops))

H("16. 0xABCD58 '帧处理中' 写者")
h = eng.disp_hits(0x00ABCD58)
print("  0xABCD58 共 %d 处" % len(h))
for va, rw, mn, ops in h:
    print("    %08X %s %-8s %s" % (va, rw, mn, ops))

H("17. 0xAA0430 泵计数 写者")
h = eng.disp_hits(0x00AA0430)
print("  0xAA0430 共 %d 处" % len(h))
for va, rw, mn, ops in h:
    print("    %08X %s %-8s %s" % (va, rw, mn, ops))

H("18. 0x55D3BB 起的帧体里 0xA8ED80 的读点")
h = eng.disp_hits(0x00A8ED80)
for va, rw, mn, ops in h:
    if 0x55D360 <= va < 0x55DEE0:
        print("    %08X %s %-8s %s" % (va, rw, mn, ops))

print("\n[DONE probe1]")
