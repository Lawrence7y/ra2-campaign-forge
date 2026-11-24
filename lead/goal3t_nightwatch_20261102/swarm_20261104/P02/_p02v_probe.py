# -*- coding: utf-8 -*-
"""P02 核验探针（VERIFY）：独立从字节复算 REPORT.md 全部 keyFacts。只读 gamemd.exe。"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== A. scene ==")
print("sha256", eng.sha)
cov = eng.coverage
print("coverage", cov)

def show(lo, hi, tag):
    print("-- disasm %s [0x%X,0x%X)" % (tag, lo, hi))
    for va, b, m, o in eng.disasm(lo, hi - lo):
        print("  0x%06X  %-14s %s %s" % (va, b, m, o))

def raw(va, n, tag):
    print("raw %s @0x%06X: %s" % (tag, va, eng.rd(va, n).hex(" ")))

def cstr(va, tag, maxlen=64):
    o = eng.fo(va)
    e = eng.raw.index(b"\0", o) if o is not None and b"\0" in eng.raw[o:o+maxlen] else o+maxlen
    print("cstr %s @0x%06X = %r" % (tag, va, eng.raw[o:e]))

# ============ B. KF1 : MLF 等待块 ============
print("\n== B. KF1 MLF wait block ==")
show(0x55D360, 0x55D3D0, "MLF head")
raw(0x55D377, 0x1A, "0x55D377..0x55D391")
show(0x55DECF, 0x55DEE0, "freeze exit path")
print("backedges MLF[0x55D360,0x55DEE0):", [(hex(a), hex(t), m) for a, t, m in eng.loop_backedges(0x55D360, 0x55DEE0)])
print("backedges waitblk[0x55D387,0x55D3BB):", [(hex(a), hex(t), m) for a, t, m in eng.loop_backedges(0x55D387, 0x55D3BB)])
# Sleep(10) 支：0x55D3B2..0x55D3BB 内是否有任何跳转回 0x55D38D
print("backedges sleep10[0x55D3B2,0x55D3BB):", [(hex(a), hex(t), m) for a, t, m in eng.loop_backedges(0x55D3B2, 0x55D3BB)])
raw(0x55DE73, 0x12, "inc block")

# ============ C. KF2 : 泵 0x5D4D50 ============
print("\n== C. KF2 pump 0x5D4D50 ==")
show(0x5D4D50, 0x5D4E78, "pump")
# 闭包检查：窗口内所有 jcc/jmp 目标
seq = [i for i in eng.stream if 0x5D4D50 <= i.address < 0x5D4E6E]
escape, rets = [], []
for i in seq:
    if i.mnemonic.startswith("ret"):
        rets.append(i.address); continue
    if i.mnemonic in ("jmp",) or i.mnemonic.startswith("j"):
        try:
            t = i.operands[0].imm
            if not (0x5D4D50 <= t < 0x5D4E6E):
                escape.append((hex(i.address), i.mnemonic, hex(t)))
        except Exception:
            pass
print("closure insns=%d rets=%s escape=%s" % (len(seq), [hex(x) for x in rets], escape))
raw(0x5D4E66, 0x0A, "0x5D4E66..0x5D4E70 (tail+pad)")
print("IAT 0x7E14C0 =", eng.resolve_iat(0x7E14C0))
for slot in (0x7E14BC, 0x7E14F4, 0x7E14F8, 0x7E1484, 0x7E14D4, 0x7E14D8, 0x7E13C0, 0x7E11E8, 0x7E11EC, 0x7E11F0, 0x7E1530):
    print("IAT 0x%06X = %s" % (slot, eng.resolve_iat(slot)))
# 直呼泵者（E8 扫描，走已解码流）
callers = [i.address for i in eng.stream
           if i.mnemonic == "call" and i.operands and i.operands[0].type == 2 and i.operands[0].imm == 0x5D4D50]
print("direct callers of 0x5D4D50 : %d -> %s" % (len(callers), [hex(x) for x in callers]))
show(0x6BDD00, 0x6BDD40, "WinMain busy loops")

# ============ D. KF3 : 队列模式 [0xAA0444] ============
print("\n== D. KF3 queue mode 0xAA0444 ==")
hits = eng.disp_hits(0xAA0444)
print("refs=%d writers=%s" % (len(hits), [hex(a) for a, k, m, o in hits if k == "W"]))
for a, k, m, o in hits:
    if k == "W":
        print("  0x%06X %s %s %s" % (a, k, m, o))
show(0x53E510, 0x53E535, "writer=1 ctx")
show(0x53E585, 0x53E5A8, "writer=2 ctx")
show(0x53E670, 0x53E682, "writer=0 ctx")
show(0x53E948, 0x53E960, "writer ebp ctx A")
show(0x53EAC8, 0x53EAE0, "writer ebp ctx B")
show(0x53E2B0, 0x53E2C5, "writer esi ctx")
cstr(0x828138, "mode str A"); cstr(0x82813C, "mode str B")
show(0x7CA845, 0x7CA865, "0x7CA845 body")
show(0x7CA814, 0x7CA830, "0x7CA814 head")
# BSS 判定：0xAA0444 所在节的 raw 覆盖
def sec_of(va):
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if sva <= va < sva + vsz:
            inraw = (rp + (va - sva)) < rp + rsz
            return nm, inraw, vsz, rsz
sec = sec_of(0xAA0444)
print("section of 0xAA0444:", sec)
# mode2 路径
show(0x53E860, 0x53E8B8, "mode2 path")

# ============ E. KF4 : hwnd 3 写者 + 旗标写链 ============
print("\n== E. KF4 hwnd + flag writer chain ==")
h = eng.disp_hits(0xB73550)
print("hwnd refs=%d writers=%s" % (len(h), [(hex(a), m, o) for a, k, m, o in h if k == "W"]))
show(0x777CC8, 0x777CE0, "hwnd writer A")
show(0x777D70, 0x777D88, "hwnd writer B")
show(0x7777F8, 0x777830, "hwnd writer 0 ctx")
show(0x777CA0, 0x777CB8, "fullscreen gate")
show(0x77782B, 0x777950, "flag write chain")
for va, n, tag in ((0x849E94, 16, "Focus_Loss"), (0x849ECC, 18, "Focus_Restore"),
                   (0x849EF8, 16, "gained"), (0x849F08, 14, "lost"), (0x849F48, 16, "Yuri")):
    raw(va, n, tag)
raw(0x7775C0, 16, "WndProc head")
raw(0x777C79, 8, "lpfnWndProc store")
print("IAT 0x7E14D4 =", eng.resolve_iat(0x7E14D4), " 0x7E14D8 =", eng.resolve_iat(0x7E14D8))

# ============ F. KF5 : GameMode 写值点 + 时间算术 ============
print("\n== F. KF5 GameMode write points ==")
g = eng.disp_hits(0xA8B238)
print("GameMode refs=%d writers=%s" % (len(g), [(hex(a), m, o) for a, k, m, o in g if k == "W"]))
show(0x48CF8C, 0x48CFA0, "gm=0 ctx")
show(0x52E105, 0x52E118, "gm=5 ctx")
show(0x52DD78, 0x52DD88, "gm=3 ctx")
show(0x52DD5A, 0x52DD6A, "gm=4 ctx")
for T, k in ((21.156, "freeze21"), (2.56, "freeze2.56"), (24.73, "freeze24.73")):
    lo, hi = T / 0.516, T / 0.500
    print("T=%s s -> rounds [%.2f, %.2f] => %d-%d" % (k, lo, hi, int(lo // 1) if lo == int(lo) else int(lo) , int(hi) if hi == int(hi) else int(hi) + 1))

# ============ G. KF6 : 普查 ============
print("\n== G. KF6 census ==")
f = eng.disp_hits(0xA8ED80)
w = [(hex(a), m, o) for a, k, m, o in f if k == "W"]
print("FOCUS refs=%d W=%s" % (len(f), w))
fr = eng.disp_hits(0xA8ED84)
print("CURFRAME refs=%d" % len(fr))
pc = eng.disp_hits(0xAA0430)
pw = [(hex(a), m, o) for a, k, m, o in pc if k == "W"]
print("PUMPCNT refs=%d writers=%s" % (len(pc), pw))
latch = eng.disp_hits(0xABCD58)
print("LATCH 0xABCD58 refs=%d : %s" % (len(latch), [(hex(a), k, m, o) for a, k, m, o in latch]))
n1 = eng.disp_hits(0xABFD34)
print("[0xABFD34] refs=%d : %s" % (len(n1), [(hex(a), k) for a, k, m, o in n1]))
print("done")
