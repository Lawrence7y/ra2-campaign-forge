# -*- coding: utf-8 -*-
"""A02 probe2 —— 泵 0x5D4D50 内部 / PeekMessage 封装 0x53E770 / 第二自旋点 0x55D830 /
LogicUpdate 焦点门 0x55E204 / 0xA8ED80 隐写面 / 循环图与出口完备性
"""
import sys
import struct

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

H("1. 循环区 0x55D377..0x55D3B6 逐字节 + 手工算跳转目标")
L = {}
for va, bs, mn, ops in eng.disasm(0x55D377, 0x40):
    L[va] = (bs, mn, ops)
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))
print("  -- je 0x55D3AE 短跳 rel8=0xDD: 0x55D3AE+2 + (-35) = 0x%08X" % (0x55D3AE + 2 - 35))
print("  -- 0x55D38D 指令 = %s %s" % (L[0x55D38D][1], L[0x55D38D][2]))

H("2. 分支落点：0x55D3B2 之后是否检查旗标？（fall-through 判据）")
for va in (0x55D3B2, 0x55D3B4, 0x55D3B6, 0x55D3BA, 0x55D3BB):
    print("  0x%08X : %s" % (va, L.get(va, "(不在窗口)")[1:]))

H("3. 泵 0x5D4D50 内部 IAT 解析")
for va in (0x7E14C0, 0x7E14F4, 0x7E14F8, 0x7E14BC):
    print("  [0x%08X] -> %r" % (va, eng.resolve_iat(va)))

H("4. PeekMessage 封装 0x53E770 逐字节")
for va, bs, mn, ops in eng.disasm(0x53E770, 0xA0):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("5. 封装 0x53E730 逐字节")
for va, bs, mn, ops in eng.disasm(0x53E730, 0x50):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("6. 0x53E770 体内 hwnd==0 守卫 / PeekMessageA 槽位")
for va, bs, mn, ops in eng.disasm(0x53E770, 0xA0):
    if "[0xb73550]" in ops or "7e14" in ops or "j" in mn:
        print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("7. 第二自旋点 0x55D7E0..0x55D8B0（第 3 个 0xA8ED80 读 + 第二个 0x5D4D50 调用 + ret 0x55D877）")
for va, bs, mn, ops in eng.disasm(0x55D7E0, 0xD0):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("8. LogicUpdate 焦点门 0x55E1E0..0x55E230")
for va, bs, mn, ops in eng.disasm(0x55E1E0, 0x60):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("9. MainLogicFrame 入口早退链 0x55D360..0x55D376 + 0x55DEC0..0x55DEE0")
for va, bs, mn, ops in eng.disasm(0x55D360, 0x18):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))
print("  --- 早退出口 ---")
for va, bs, mn, ops in eng.disasm(0x55DEA0, 0x40):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("10. inc 点 0x55DE60..0x55DEA0")
for va, bs, mn, ops in eng.disasm(0x55DE60, 0x48):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

H("11. 0xA8ED80 隐写面：46 处 raw 命中的前导操作码分类（证明无 imm32 装载 / 无 moffs 写其它形态）")
pat = struct.pack("<I", 0x00A8ED80)
idx, found = 0, []
while True:
    j = eng.raw.find(pat, idx)
    if j < 0:
        break
    found.append(j)
    idx = j + 1
from collections import Counter
cnt = Counter()
for j in found:
    pre = eng.raw[j - 1]
    # 回到 VA
    va = None
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if rp <= j < rp + rsz:
            va = sva + (j - rp)
            break
    cnt["%02X" % pre] += 1
print("  前导字节分布: %s" % dict(cnt))
print("  a0=mov al,moffs8  a2=mov moffs8,al  80=/digit cmp/mov r/m8,imm8  38=cmp r/m8,r8")
print("  8a=mov r8,r/m8  8b=mov r32  89=mov r/m32,r32  c6=mov r/m8,imm8  ff=grp5/grp2")
bad = []
for j in found:
    pre = eng.raw[j - 1]
    if pre in (0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF, 0x68):
        bad.append((j, pre))
print("  imm32 装载形（b8..bf/68）命中 = %d %s" % (len(bad), bad))

H("12. .data 区是否含 0xA8ED80 的指针（间接写线索）")
for j in found:
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if rp <= j < rp + rsz:
            if nm != ".text":
                print("    非 .text 命中: file 0x%06X sec %s" % (j, nm))

H("13. 0xA8ED80 是否在 .data 的 BSS 部分（初值 0）")
for nm, sva, vsz, rp, rsz in eng.SEC:
    if sva <= 0xA8ED80 < sva + vsz:
        print("  归属段 %s: VA 0x%08X vsz 0x%X raw 0x%X rsz 0x%X" % (nm, sva, vsz, rp, rsz))
        print("  BSS 上界 = 段VA+rsz = 0x%08X ; 0xA8ED80 >= 该值 ? %s"
              % (sva + rsz, 0xA8ED80 >= sva + rsz))
print("  file offset of 0xA8ED80 = %r (None => BSS, 无文件字节)" % eng.fo(0xA8ED80))
print("  rd(0xA8ED80,1) = %r" % eng.rd(0xA8ED80, 1))

H("14. 0xA8ED84 CurrentFrame 是否也在 BSS")
print("  fo(0xA8ED84) = %r" % eng.fo(0xA8ED84))
print("  fo(0xAA0430) = %r" % eng.fo(0xAA0430))
print("  fo(0xB73550) = %r" % eng.fo(0xB73550))
print("  fo(0xABCD58) = %r" % eng.fo(0xABCD58))

H("15. MainLogicFrame 内全部 0xA8B238 读点上下文（GameMode 在环内被重读的证据）")
for va in (0x55D38D, 0x55D440, 0x55D597, 0x55D7C2, 0x55D8D5, 0x55DBCD, 0x55DDAA):
    print("  --- 0x%08X ---" % va)
    for a, bs, mn, ops in eng.disasm(va - 6, 0x20):
        mark = " <=" if a == va else ""
        print("    %08X  %-18s %-8s %s%s" % (a, bs, mn, ops, mark))

H("16. 0x55D830 附近 loop 结构（第二个自旋环的回到点）")
for src, tgt, mn in eng.loop_backedges(0x55D7E0, 0x55D8B0):
    print("    回边 %08X -> %08X (%s)" % (src, tgt, mn))

print("\n[DONE probe2]")
