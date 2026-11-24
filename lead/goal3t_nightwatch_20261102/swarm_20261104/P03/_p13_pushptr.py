# -*- coding: utf-8 -*-
# P13: push 0xa8ed84 被调者检查 / MLF edi 追源 / dispatcher 循环头 / 周边身份
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

def dump(lo, hi, tag=""):
    print("  [%s %#x..%#x)" % (tag, lo, hi))
    for a in sorted(k for k in by if lo <= k < hi):
        ins = by[a]
        print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("== A. push 0xa8ed84 现场 ==")
dump(0x67F7F0, 0x67F830, "site1")
dump(0x67F9F0, 0x67FA30, "site2")

# 找 site1/site2 附近最近 call 的目标
for site in (0x67F819, 0x67FA19):
    nxt = [i for i in stream if site <= i.address < site + 0x60 and i.mnemonic == "call"]
    for i in nxt[:3]:
        t = i.operands[0].imm if i.operands and i.operands[0].type == 2 else None
        print("  site %#x 之后 call %#08x -> %#s  owner=%#x" % (site, i.address, t, owner(t)) if t else
              "  site %#x 之后 call %#08x (间接)" % (site, i.address))

print("\n== B. MLF 中 [0x55DC5C, 0x55DE7F) 全部 edi 写（含 pop/lea/mem） ==")
for a in sorted(k for k in by if 0x55DC5C <= k < 0x55DE7F):
    ins = by[a]
    if ins.mnemonic == "pop" and ins.op_str == "edi":
        print("  %#08x pop edi" % a)
    if ins.mnemonic in ("lea", "mov") and (ins.op_str.startswith("edi,") or ins.op_str == "edi"):
        print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    if ins.mnemonic in ("add", "sub", "inc", "dec") and ins.op_str.endswith("edi"):
        print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))
# 也检查 rep 之后的字符串操作（rep movsd 会推进 edi）
print("  (rep movsd/movsb 于该区间:)")
for a in sorted(k for k in by if 0x55DC5C <= k < 0x55DE7F):
    ins = by[a]
    if ins.mnemonic.startswith("rep"):
        print("  %#08x %s %s" % (a, ins.mnemonic, ins.op_str))

print("\n== C. dispatcher 循环头 [0x48CDE5, 0x48CE60) ==")
dump(0x48CDE5, 0x48CE60, "loophead")

print("\n== D. 周边身份 ==")
dump(0x684290, 0x6842B0, "684290")
print("  0x685670/0x685DC0/0x6863E0/0x686570 是否 call 0x683AB0:")
for h in (0x685670, 0x685DC0, 0x6863E0, 0x686570):
    i2 = bisect.bisect_right(HEADS, h)
    hi2 = HEADS[i2] if i2 < len(HEADS) else h + 0x800
    cs = [i.address for i in stream if h <= i.address < hi2 and i.mnemonic == "call"
          and i.operands and i.operands[0].type == 2 and i.operands[0].imm == 0x683AB0]
    print("    %#x: %s" % (h, ["%#x" % c for c in cs]))

print("\n== E. 字符串补充 ==")
def cstr(va, n=90):
    b = eng.rd(va, n); j = b.find(b"\0")
    return b[:j if j >= 0 else n].decode("gbk", "replace")
for va in (0x840BDC, 0x82A068, 0x81D514, 0x82A044):
    print("  [%#x] %r" % (va, cstr(va)))
print("  u32(0x89E3A0)=%#x  u32(0xA8F7AC)=%#x" % (eng.u32(0x89E3A0), eng.u32(0xA8F7AC)))
print("  0x89E3A0 引用:", [(hex(v), a, m) for v, a, m, _ in eng.disp_hits(0x89E3A0)])
print("  0xA8F7AC 引用:", [(hex(v), a, m) for v, a, m, _ in eng.disp_hits(0xA8F7AC)])
