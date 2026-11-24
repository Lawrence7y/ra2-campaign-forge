# -*- coding: utf-8 -*-
"""独立验证 0044E8F0 BuildingClass::vslot10（成员向量 Find(-1)）。"""
import audit_lib as L

def sec(t): print("\n===== " + t + " =====")

entry = 0x0044E8F0
sec("0) ② slot 007E3EE4 (vt 007E3EBC +0x28, slot#10), RTTI")
sva = 0x007E3EE4
print("slot bytes=%s u32=%s" % (L.hexb(sva,4), L.hx(L.u32(sva))))
print("resolve_slot ->", L.resolve_slot(sva))
print("(0x3EE4-0x3EBC)/4 =", (0x3EE4-0x3EBC)//4)
print("vtable slot0 =", L.hx(L.u32(0x007E3EBC)))

sec("1) ③b② 站点 0x44EA60..0x44EB10 完整反汇编")
for ins in L.disasm(0x44EA60, 0xC0):
    print(L.fmt_ins(ins))

sec("2) 成员 vptr 0x7E43C8 的 RTTI + slot4=Find")
vt = 0x7E43C8
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

sec("2b) 成员 vptr 安装点 0x43B6DB (mov [esi+0x66C], 0x7E43C8)")
print("bytes @43B6DB:", L.hexb(0x43B6DB, 10))
for ins in L.disasm(0x43B6D5, 0x20):
    print(L.fmt_ins(ins))
print("--- also 0x43B709 (this+0x684) ---")
for ins in L.disasm(0x43B703, 0x14):
    print(L.fmt_ins(ins))

sec("3) ④ 主表安装点 0x43B71F / atexit / direct")
print("install bytes @43B71F:", L.hexb(0x43B71F, 6))
print("atexit(43B680)=", L.is_atexit_registered(0x43B680))
print("direct callers of 0044E8F0 =", [L.hx(x) for x in L.find_direct_calls(entry)])
