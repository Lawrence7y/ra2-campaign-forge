# -*- coding: utf-8 -*-
# P11: 格式串 / 关键数据 / 旗标设置者归属 / 0xA8B24C 相位值 / MLF edi / 上层调用链
import sys, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME

eng = Engine()
by = eng.by()
stream = eng.stream

heads = set()
for ins in stream:
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
        t = ins.operands[0].imm
        if eng.TLO <= t < eng.THI:
            heads.add(t)
HEADS = sorted(heads)

def owner(va):
    i = bisect.bisect_right(HEADS, va) - 1
    return HEADS[i] if i >= 0 else None

def cstr(va, n=90):
    b = eng.rd(va, n)
    j = b.find(b"\0")
    if j < 0: j = n
    try:
        return b[:j].decode("gbk", "replace")
    except Exception:
        return repr(b[:j])

print("== A. 格式串 ==")
for va in (0x81D55C, 0x81D53C, 0x82CC04, 0x82CBF4, 0x83DA88, 0x831A60,
           0x84C540, 0x820C54, 0x82C1BC, 0x82C9A4, 0x82CBA4, 0x82CB8C,
           0x82CB28, 0x82CB4C, 0x83D000, 0x84C540):
    print("  [%#x] %r" % (va, cstr(va)))

print("\n== B. 关键数据 ==")
print("  [0xA8E2E4] = %#x (%d)" % (eng.u32(0xA8E2E4), eng.u32(0xA8E2E4)))
print("  [0x7E4C30] = %#x" % eng.u32(0x7E4C30))
print("  [0x81C1D0] = %#x" % eng.u32(0x81C1D0))
hits7e = eng.disp_hits(0x7E4C30)
print("  0x7E4C30 引用:", [(hex(va), acc, mn) for va, acc, mn, _ in hits7e])
print("  [0x841F30] 读点:")
for va, acc, mn, ops in eng.disp_hits(0x841F30):
    if acc == "R":
        print("    %#08x %s %s %s" % (va, acc, mn, ops))

print("\n== C. 四旗标设置者归属 ==")
for va in (0x55D129, 0x55D1B1, 0x55D219, 0x55D25C, 0x4F867C, 0x48CB2E, 0x4C7917, 0x52DA78):
    print("  %#x -> head %#x" % (va, owner(va)))
print("  0x55D0xx 设置者函数头 = %#x" % owner(0x55D129))
print("  其上下文:")
lo, hi = 0x55D100, 0x55D150
for a in sorted(k for k in by if lo <= k < hi):
    ins = by[a]
    print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("\n== D. 0xA8B24C 写点值 ==")
for va in (0x52E3D2, 0x52F467, 0x5B633B, 0x5B7333, 0x5BA3FE, 0x5BB212, 0x5E18E4, 0x5E5515, 0x5E74C3):
    ins = by[va]
    print("  %#08x  %s %s   (owner %#x)" % (va, ins.mnemonic, ins.op_str, owner(va)))

print("\n== E. MLF 中 edi 的来源（0x55DE7F cmp eax,edi） ==")
for a in sorted(k for k in by if 0x55D360 <= k < 0x55DE7F):
    ins = by[a]
    if ins.mnemonic == "mov" and ins.op_str.startswith("edi,"):
        print("  %#08x  mov %s" % (a, ins.op_str))

print("\n== F. 上层调用链（各宿主的 E8 调用者） ==")
for h in (0x5B6020, 0x5B77E0, 0x5E00B0, 0x7A41A0, 0x683AB0, 0x77F900, 0x5DC350, 0x5C3EC0, 0x48CCC0):
    cs = [i.address for i in stream if i.mnemonic == "call"
          and i.operands and i.operands[0].type == 2 and i.operands[0].imm == h]
    ups = sorted({owner(c) for c in cs})
    print("  %#x: %d callers %s <- 上层头 %s" % (h, len(cs),
          " ".join("%#x" % c for c in cs[:10]), ["%#x" % u for u in ups]))
