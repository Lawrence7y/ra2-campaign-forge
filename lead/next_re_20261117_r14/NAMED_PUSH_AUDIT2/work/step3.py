import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q, core as C, fnd

ROWS = [("00691EE0", 0x7F0F78), ("00691FA0", 0x7F1008), ("006A48A0", 0x7F2EC0),
        ("006A4930", 0x7F2EC0), ("006E87F0", 0x7F4680), ("006E9140", 0x7F4730),
        ("00410C30", 0x7E2000), ("00414290", 0x7E22A4), ("0041CFE0", 0x7E2868),
        ("00524D70", 0x7EB610), ("005F9950", 0x7EF2D8)]

regs = q.atexit_targets()
regfns = set(t for t, s in regs)
print("atexit-registered functions:", ", ".join("%08X" % t for t in sorted(regfns)))

for e, vt in ROWS:
    print("\n== entry %s vt=%08X  name=%s" % (e, vt, (C.rtti_of_vt(vt) or {}).get("name")))
    for site, m in q.vt_installs(vt):
        lo, end = fnd.fn_range(site)
        kind = []
        if lo in regfns:
            kind.append("ATEXIT-REGISTERED(dtor)")
        # 该函数内是否有 free / base dtor / 其他 vtable 安装
        frees = [a for a, x in q.CALLS if x == 0x7C8B3D and lo <= a < (end or site + 0x80)]
        if frees:
            kind.append("free@%s" % ",".join("%08X" % a for a in frees[:3]))
        others = [(a, imm) for a, imm, mm in q.VINST if lo <= a < (end or site + 0x80)]
        if len(others) > 1:
            kind.append("install_count=%d" % len(others))
        print("   site %08X in fn %08X..%s mem=%s  %s" % (site, lo, "%08X" % end if end else "?", m, " ".join(kind)))
