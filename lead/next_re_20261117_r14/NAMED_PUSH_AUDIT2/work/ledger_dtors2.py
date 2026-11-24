import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C, q, capstone

X86 = capstone.x86
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
proved = []
with open(COV, encoding="utf-8") as f:
    next(f)
    for ln in f:
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 5 and p[4].strip() == "[已证]":
            try:
                proved.append((int(p[0], 16), p[1], p[2]))
            except ValueError:
                pass

rows = []
for e, sub, nm in proved:
    fa = C.fn_at(e)
    if not fa or fa[1] < 8 or fa[1] > 0x2000:
        continue
    ins = C.disasm(e, 10 ** 6, nbytes=fa[1])
    test_flag = False
    free = False
    vtdisp = set()
    cmp_m1 = False
    je_after = False
    prev = None
    for i in ins:
        if i.mnemonic == "test" and i.operands and i.operands[0].type == X86.X86_OP_MEM \
           and i.operands[0].mem.base == X86.X86_REG_ESP and "1" == i.op_str.split(",")[-1].strip():
            test_flag = True
        if i.mnemonic == "call":
            if q.callee_at(i.address) == 0x7C8B3D:
                free = True
            if i.operands and i.operands[0].type == X86.X86_OP_MEM:
                vtdisp.add(i.operands[0].mem.disp)
        if i.mnemonic == "cmp" and i.op_str.replace(" ", "") in ("eax,-1", "eax,0xffffffff"):
            cmp_m1 = True
        if prev is not None and prev.mnemonic == "cmp" and "eax" in prev.op_str and "1" in prev.op_str \
           and i.mnemonic in ("je", "jne"):
            je_after = True
        prev = i
    is_dtor = test_flag and free
    rows.append((e, sub, nm, is_dtor, 0x10 in vtdisp, cmp_m1, je_after))

dt = [r for r in rows if r[3]]
print("proved rows:", len(rows))
print("dtor-shaped (test byte[esp+..],1 + call 0x7C8B3D):", len(dt))
both = [r for r in dt if r[4] and r[5] and r[6]]
print("  of which with call [reg+0x10] AND cmp eax,-1 AND je:", len(both))
for r in dt:
    print("   %08X %-4s %-40s vt+0x10=%s cmpm1=%s je=%s" % (r[0], r[1], r[2][:40], r[4], r[5], r[6]))
