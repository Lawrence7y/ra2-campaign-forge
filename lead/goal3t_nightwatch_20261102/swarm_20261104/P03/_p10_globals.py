# -*- coding: utf-8 -*-
# P10: 0x6B8B10 身份 / 守卫旗标写者 / 全局槽普查 / IAT / 0x7970D0 函数指针搜索 / 0x4068E0·0x48D080
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME

eng = Engine()
by = eng.by()

def dump(lo, hi, tag=""):
    print("  [%s %#x..%#x)" % (tag, lo, hi))
    for a in sorted(k for k in by if lo <= k < hi):
        ins = by[a]
        print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("== A. 0x6B8B10 头 64 字节 ==")
dump(0x6B8B10, 0x6B8B50, "6b8b10")
print("  0x6B8B10 是否调用 0x684620/0x686730/0x4068E0?")
sites = [i.address for i in eng.stream
         if 0x6B8B10 <= i.address < 0x6B9000 and i.mnemonic == "call"
         and i.operands and i.operands[0].type == 2
         and i.operands[0].imm in (0x684620, 0x686730, 0x4068E0)]
print("  命中:", ["%#x" % s for s in sites])

print("\n== B. W2 四守卫旗标的全部写点 ==")
for g in (0xA83D49, 0xA8ECD0, 0x8B41C0, 0xA83D48):
    hits = [h for h in eng.disp_hits(g) if h[1] == "W"]
    print("  [%#x] W 写点 %d 处: %s" % (g, len(hits),
          " ".join("%#x(%s)" % (va, mn) for va, _, mn, _ in hits[:10])))

print("\n== C. 全局槽普查（W=写点数） ==")
for g in (0xA8B24C, 0xA8B550, 0xA8B554, 0x841F30, 0xA8E7AC, 0xA8E2E4,
          0xB07784, 0xA8E2C8, 0xABCD58, 0xAC0268, 0x81D4E0, 0xA8E960,
          0xA8B260, 0xA8B31D, 0xA8B254, 0xA8DA84):
    hits = eng.disp_hits(g)
    ws = [h for h in hits if h[1] == "W"]
    print("  [%#x] total=%d W=%d  写点: %s" % (g, len(hits), len(ws),
          " ".join("%#x" % va for va, _, _, _ in ws[:12])))

print("\n== D. IAT ==")
for s in (0x7E14A4, 0x7E14A8, 0x7E4C30, 0x7E1194, 0x7E11F0, 0x7E1530):
    print("  [%#x] -> %s" % (s, eng.resolve_iat(s)))

print("\n== E. 全镜像搜函数指针 0x7970D0（含数据节） ==")
pat = struct.pack("<I", 0x7970D0)
raw = eng.raw
pos = 0
while True:
    j = raw.find(pat, pos)
    if j < 0:
        break
    # 文件偏移 -> VA
    va = None
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if rp <= j < rp + rsz:
            va = sva + (j - rp)
            break
    print("  file_off=%#x  va=%s  sec_ctx=%s" % (j, "%#x" % va if va else "?(头表区)", eng.raw[max(0, j-8):j+12].hex()))
    pos = j + 1

print("\n== F. 0x4068E0 头部 + 0x48D080 头部 ==")
dump(0x4068E0, 0x406930, "4068e0")
dump(0x48D080, 0x48D0C0, "48d080")
