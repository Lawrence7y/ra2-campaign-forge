# -*- coding: utf-8 -*-
"""独立验证 004CA770 FactoryClass::slot8 —— 删除式析构器 + 两处 Find(-1) ③b②。重点：② 主表 / ④ 非析构。"""
import audit_lib as L

def sec(t): print("\n===== " + t + " =====")

entry = 0x004CA770

sec("1) ② slot 007E88F0 (vt 007E88D0 +0x20, slot#8), RTTI, 主表 slot0")
sva = 0x007E88F0
print("slot bytes=%s u32=%s (entry=%s)" % (L.hexb(sva,4), L.hx(L.u32(sva)), L.hx(entry)))
print("resolve_slot ->", L.resolve_slot(sva))
print("(0x88F0-0x88D0)/4 =", (0x88F0-0x88D0)//4)
print("vtable slot0 [0x7E88D0] =", L.hx(L.u32(0x7E88D0)))
col = L.u32(0x7E88D0-4); print("COL[7E88CC]=%s sig=%s" % (L.hx(col), L.hx(L.u32(col)) if col else None))
td = L.u32(col+0xC) if col else None; print("TD=%s name=%r" % (L.hx(td), L.read_cstr(td+8) if td else None))
print("non-text refs to entry:", [(L.hx(a),nm) for a,nm in L.find_dword_refs(entry)])

sec("2) ③b② 站点一 0x4CA7A0..0x4CA7E0 (container 0xA83E30)")
for ins in L.disasm(0x4CA7A0, 0x40):
    print(L.fmt_ins(ins))
sec("2b) 站点二 0x4CA7E8..0x4CA840 (container 0xB0F720)")
for ins in L.disasm(0x4CA7E8, 0x60):
    print(L.fmt_ins(ins))
sec("2c) 判据/跳转字节")
print("site1 @4CA7AD:", L.hexb(0x4CA7AD, 8))
print("site2 @4CA806:", L.hexb(0x4CA806, 8))

sec("3) 站点一 Find 链: 全局 0xA83E30 / vtable 0x7E9FA4")
for ins in L.disasm(0x4E6E70, 0x18): print(L.fmt_ins(ins))
vt1=0x7E9FA4
c1=L.u32(vt1-4); t1=L.u32(c1+0xC) if c1 else None
print("COL[-4]@7E9FA0=%s sig=%s TD=%s name=%r"%(L.hx(c1),L.hx(L.u32(c1)) if c1 else None,L.hx(t1),L.read_cstr(t1+8) if t1 else None))
s4a=L.u32(vt1+0x10); print("slot4 @7E9FB4=%s"%L.hx(s4a))
for ins in L.disasm(s4a,0x30): print("   ",L.fmt_ins(ins))

sec("3b) 站点二 Find 链: 全局 0xB0F720 / vtable 0x7E91EC")
for ins in L.disasm(0x7252E0, 0x18): print(L.fmt_ins(ins))
vt2=0x7E91EC
c2=L.u32(vt2-4); t2=L.u32(c2+0xC) if c2 else None
print("COL[-4]@7E91E8=%s sig=%s TD=%s name=%r"%(L.hx(c2),L.hx(L.u32(c2)) if c2 else None,L.hx(t2),L.read_cstr(t2+8) if t2 else None))
s4b=L.u32(vt2+0x10); print("slot4 @7E91FC=%s"%L.hx(s4b))
for ins in L.disasm(s4b,0x30): print("   ",L.fmt_ins(ins))

sec("4) ④ 锚点：构造器 0x4C991A (ctor 4C98B0) — 非本行析构器")
print("atexit(4C98B0)=",L.is_atexit_registered(0x4C98B0),"atexit(4CA270)=",L.is_atexit_registered(0x4CA270))
print("direct callers 004CA770=", [L.hx(x) for x in L.find_direct_calls(entry)])
print("-- ctor install 0x4C991A --")
for ins in L.disasm(0x4C9917,0xC): print(L.fmt_ins(ins))
print("-- ctor 4C98B0 tail mov eax,esi;ret --")
for ins in L.disasm(0x4C99FB,0xA): print(L.fmt_ins(ins))
sec("4b) 本行 entry 0x4CA770 是删除式析构器 (㉓)")
print("-- dtor head 0x4CA770 --")
for ins in L.disasm(0x4CA770,0x20): print(L.fmt_ins(ins))
print("-- calls in dtor body --")
for ins in L.disasm(0x4CA770,0x1A0):
    if ins.mnemonic=='call': print("   ",L.fmt_ins(ins))
