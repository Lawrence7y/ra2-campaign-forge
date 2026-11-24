# -*- coding: utf-8 -*-
"""独立验证 00447F10 BuildingClass::vslot240（返回值搬入 ebp 再判）。"""
import audit_lib as L, csv

def sec(t): print("\n===== " + t + " =====")

entry = 0x00447F10
sec("0) ② slot 007E427C (vt 007E3EBC +0x3C0, slot#240), RTTI")
sva = 0x007E427C
print("slot bytes=%s u32=%s" % (L.hexb(sva,4), L.hx(L.u32(sva))))
print("resolve_slot ->", L.resolve_slot(sva))
print("(0x427C-0x3EBC)/4 =", (0x427C-0x3EBC)//4)
print("vtable slot0 =", L.hx(L.u32(0x007E3EBC)))

sec("1) ③b② 站点 0x447FA0..0x448070 完整反汇编")
for ins in L.disasm(0x447FA0, 0xD0):
    print(L.fmt_ins(ins))

sec("2) 被调 0x6FC0B0 返回常量枚举（atlas size 与全 ret）")
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
asz = None
with open(ATLAS, encoding="utf-8-sig") as f:
    r = csv.reader(f, delimiter="\t"); next(r)
    for row in r:
        if not row or not row[0].strip(): continue
        if int(row[0].strip().upper(),16) == 0x6FC0B0:
            asz = int(row[1]); break
print("atlas[6FC0B0] size =", asz)
span = asz if asz and asz < 0x4000 else 0x2000
res = L.eax_constants(0x6FC0B0, span)
print("ret count =", len(res))
consts = {}
for rv, c, mn, op in res:
    print("  ret @%s eax=%s  (%s %s)" % (L.hx(rv), ("0x%X"%c) if c is not None else "None", mn, op))
    if c is not None: consts.setdefault(c,0); consts[c]+=1
print("return constant set =", sorted(("0x%X"%c) for c in consts))
print("distinct values =", len(consts), " is {0,1} bool?", set(consts) <= {0,1})

sec("3) ④ 安装点 0x43B71F / atexit / direct")
print("install bytes @43B71F:", L.hexb(0x43B71F, 6))
print("atexit(43B680)=", L.is_atexit_registered(0x43B680))
print("direct callers of 00447F10 =", [L.hx(x) for x in L.find_direct_calls(entry)])
