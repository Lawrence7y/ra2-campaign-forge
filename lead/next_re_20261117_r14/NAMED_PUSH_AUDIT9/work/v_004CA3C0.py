# -*- coding: utf-8 -*-
"""独立验证 004CA3C0 FactoryClass::slot6 —— ③b② 多值 HRESULT (E_POINTER)。"""
import audit_lib as L

def sec(t): print("\n===== " + t + " =====")

entry = 0x004CA3C0

sec("1) ② slot 007E88E8 (vt 007E88D0 +0x18, slot#6), RTTI, 主表 slot0")
sva = 0x007E88E8
print("slot bytes=%s u32=%s (entry=%s)" % (L.hexb(sva,4), L.hx(L.u32(sva)), L.hx(entry)))
print("resolve_slot ->", L.resolve_slot(sva))
print("(0x88E8-0x88D0)/4 =", (0x88E8-0x88D0)//4)
print("vtable slot0 [0x7E88D0] =", L.hx(L.u32(0x7E88D0)))
col = L.u32(0x7E88D0-4); print("COL[7E88CC]=%s sig=%s" % (L.hx(col), L.hx(L.u32(col)) if col else None))
td = L.u32(col+0xC) if col else None; print("TD=%s name=%r" % (L.hx(td), L.read_cstr(td+8) if td else None))
print("non-text refs to entry:", [(L.hx(a),nm) for a,nm in L.find_dword_refs(entry)])

sec("2) ③b② 站点 0x4CA3C0..0x4CA430 (call 0x410320 段)")
for ins in L.disasm(0x4CA3C0, 0x70):
    print(L.fmt_ins(ins))
sec("2b) 失败落点 0x4CA41F + 成功尾 0x4CA410..0x4CA430")
for ins in L.disasm(0x4CA408, 0x2C):
    print(L.fmt_ins(ins))

sec("3) 被调 0x410320 (E_POINTER 同 row3, 复核) ")
for ins in L.disasm(0x410320, 0x14): print(L.fmt_ins(ins))

sec("4) ④ 构造安装点 0x4C991A / 0x4CA2C7；析构重装 0x4CA776 (排除)")
for a in (0x4C991A, 0x4CA2C7, 0x4CA776):
    print("-- install @%s bytes=%s --" % (L.hx(a), L.hexb(a,6)))
    for ins in L.disasm(a-3, 0x10):
        print("   ", L.fmt_ins(ins))
print("atexit(4C98B0)=", L.is_atexit_registered(0x4C98B0))
print("atexit(4CA270)=", L.is_atexit_registered(0x4CA270))
print("direct callers of entry 004CA3C0 =", [L.hx(x) for x in L.find_direct_calls(entry)])
sec("4b) 构造体 0x4C98B0 尾部 (返 this?)")
for ins in L.disasm(0x4C9910, 0x18): print(L.fmt_ins(ins))
sec("4c) 析构体 0x4CA770 头部 (free/基类析构 => ㉓)")
for ins in L.disasm(0x4CA770, 0x40): print(L.fmt_ins(ins))
