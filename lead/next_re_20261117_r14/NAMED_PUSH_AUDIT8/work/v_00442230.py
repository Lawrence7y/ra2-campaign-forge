# -*- coding: utf-8 -*-
"""独立验证 00442230 BuildingClass::vslot91。"""
import audit_lib as L

def sec(title):
    print("\n===== " + title + " =====")

entry = 0x00442230
sec("0) entry bytes @ %s" % L.hx(entry))
print(L.hexb(entry, 24))
print(L.fmt_ins(next(iter(L.disasm(entry, 16)))))

# ② slot VA 007E4028, vtable 007E3EBC + 0x16C
sec("1) ② slot 007E4028 = 4B VA? RTTI chain")
for sva in (0x007E4028,):
    print("slot VA %s bytes=%s u32=%s" % (L.hx(sva), L.hexb(sva,4), L.hx(L.u32(sva))))
    r = L.resolve_slot(sva)
    print("resolve_slot ->", r)
# 主表槽 0
print("vtable 007E3EBC slot0 =", L.hx(L.u32(0x007E3EBC)))
print("slot# (0x4028-0x3EBC)/4 =", (0x4028-0x3EBC)//4)

# ③b② 站点 0x4424BB
sec("2) ③b② site 0x4424BB")
for ins in L.disasm(0x442480, 0xE0):
    print(L.fmt_ins(ins))

# 被调 vptr 0x7E180C 与 0x7E17AC 的 slot4
sec("3) callee via vptr 0x7E180C / 0x7E17AC slot4")
for vt in (0x7E180C, 0x7E17AC):
    col = L.u32(vt - 4)
    print("vptr %s -> [-4]COL=%s" % (L.hx(vt), L.hx(col)))
    if col:
        td = L.u32(col + 0xC)
        print("   COL.sig=%s TD=%s name=%r" % (L.hx(L.u32(col)), L.hx(td), L.read_cstr(td+8) if td else None))
    s4 = L.u32(vt + 0x10)
    print("   slot4 @%s = %s" % (L.hx(vt+0x10), L.hx(s4)))
    if s4 and L.in_text(s4):
        for ins in L.disasm(s4, 0x40):
            print("     ", L.fmt_ins(ins))

# ④ 安装点 0x43B71F
sec("4) ④ install site 0x43B71F")
print("bytes @43B715:", L.hexb(0x43B715, 24))
for ins in L.disasm(0x43B700, 0x50):
    print(L.fmt_ins(ins))
print("atexit registered?", L.is_atexit_registered(0x43B680))
print("direct callers of entry 00442230:", [L.hx(x) for x in L.find_direct_calls(entry)])
