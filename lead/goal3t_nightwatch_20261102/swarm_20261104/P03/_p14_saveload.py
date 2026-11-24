# -*- coding: utf-8 -*-
# P14: 序列化两站归属/方向 + dispatcher ebx + 0x686570 + [0xB07784] 写者
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
def nhead(h):
    i = bisect.bisect_right(HEADS, h)
    return HEADS[i] if i < len(HEADS) else h + 0x2000

def dump(lo, hi, tag=""):
    print("  [%s %#x..%#x)" % (tag, lo, hi))
    for a in sorted(k for k in by if lo <= k < hi):
        ins = by[a]
        print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("== A. 序列化两站归属 ==")
for site in (0x67F819, 0x67FA19):
    h = owner(site)
    print("  site %#x owner=%#x  range=[%#x,%#x)" % (site, h, h, nhead(h)))

print("\n== B. site1 宿主头部 + esi/vtable 来源 [owner1, owner1+0x60) ==")
h1 = owner(0x67F819)
dump(h1, h1 + 0x60, "owner1 head")
dump(0x67F7A0, 0x67F830, "site1 前文")

print("\n== C. 两宿主内 push 的 .data/.rdata 立即数（序列化清单） ==")
for h in (h1, owner(0x67FA19)):
    hi = nhead(h)
    pushes = []
    for a in sorted(k for k in by if h <= k < hi):
        ins = by[a]
        if ins.mnemonic == "push" and ins.operands and ins.operands[0].type == 2:
            v = ins.operands[0].imm
            if 0x84A000 <= v < 0xB800000 or 0x8100000 <= v < 0x8600000:
                pushes.append((a, v))
    print("  func %#x: %d 处" % (h, len(pushes)))
    for a, v in pushes[:40]:
        print("    %#08x push %#x" % (a, v))

print("\n== D. site2 宿主头部 ==")
h2 = owner(0x67FA19)
dump(h2, h2 + 0x50, "owner2 head")
dump(0x67F9C0, 0x67FA22, "site2 前文")

print("\n== E. 0x6CF240 头 ==")
dump(0x6CF240, 0x6CF270, "6cf240")

print("\n== F. dispatcher 头 [0x48CCC0, 0x48CDE5) 找 ebx 来源 ==")
for a in sorted(k for k in by if 0x48CCC0 <= k < 0x48CDE5):
    ins = by[a]
    if ins.mnemonic in ("xor", "mov") and (ins.op_str == "ebx, ebx" or ins.op_str.startswith("ebx,")):
        print("  %#08x  %s %s" % (a, ins.mnemonic, ins.op_str))

print("\n== G. 0x686570 头 + 前几个 call ==")
dump(0x686570, 0x6865D0, "686570")

print("\n== H. [0xB07784] 写者上下文 ==")
for va in (0x684165, 0x68420D, 0x684282, 0x6842E5):
    dump(va - 0x14, va + 0x8, "w %#x" % va)
