# -*- coding: utf-8 -*-
"""独立验证 00447210 BuildingClass::vslot29（返回值搬入 ebx 再判）。"""
import audit_lib as L

def sec(t): print("\n===== " + t + " =====")

entry = 0x00447210
sec("0) ② slot 007E3F30 (vt 007E3EBC +0x74, slot#29), RTTI")
sva = 0x007E3F30
print("slot bytes=%s u32=%s" % (L.hexb(sva,4), L.hx(L.u32(sva))))
print("resolve_slot ->", L.resolve_slot(sva))
print("(0x3F30-0x3EBC)/4 =", (0x3F30-0x3EBC)//4)
print("vtable slot0 =", L.hx(L.u32(0x007E3EBC)))

sec("1) ③b② 站点 0x447230..0x4473D0 完整反汇编")
for ins in L.disasm(0x447230, 0x1A0):
    print(L.fmt_ins(ins))

sec("2) 被调 0x6FFEC0 返回常量枚举（atlas size 与全 ret）")
# 查 atlas 边界
import csv, os
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
asz = None
with open(ATLAS, encoding="utf-8-sig") as f:
    r = csv.reader(f, delimiter="\t"); next(r)
    for row in r:
        if not row or not row[0].strip(): continue
        if int(row[0].strip().upper(),16) == 0x6FFEC0:
            asz = int(row[1]); break
print("atlas[6FFEC0] size =", asz)
span = asz if asz and asz < 0x2000 else 0xA00
res = L.eax_constants(0x6FFEC0, span)
print("ret count =", len(res))
consts = {}
for rv, c, mn, op in res:
    print("  ret @%s eax=%s  (%s %s)" % (L.hx(rv), ("0x%X"%c) if c is not None else "None", mn, op))
    if c is not None: consts.setdefault(c,0); consts[c]+=1
print("return constant set =", sorted(("0x%X"%c) for c in consts))
print("is {0,1} bool?", set(consts) <= {0,1})

sec("3) ④ 安装点 0x43B71F / atexit / direct")
print("install bytes @43B71F:", L.hexb(0x43B71F, 6))
print("atexit(43B680)=", L.is_atexit_registered(0x43B680))
print("direct callers of 00447210 =", [L.hx(x) for x in L.find_direct_calls(entry)])
