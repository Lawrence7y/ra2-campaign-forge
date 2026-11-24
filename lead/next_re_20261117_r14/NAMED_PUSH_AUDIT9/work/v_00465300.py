# -*- coding: utf-8 -*-
"""独立验证 00465300 BuildingTypeClass::slot6 —— ③b② 多值 HRESULT。"""
import audit_lib as L

def sec(t): print("\n===== " + t + " =====")

entry = 0x00465300

sec("1) ② slot 007E4588 (vt 007E4570 +0x18, slot#6), RTTI, 主表 slot0")
sva = 0x007E4588
print("slot bytes=%s u32=%s (entry=%s)" % (L.hexb(sva,4), L.hx(L.u32(sva)), L.hx(entry)))
print("resolve_slot ->", L.resolve_slot(sva))
print("(0x4588-0x4570)/4 =", (0x4588-0x4570)//4)
print("vtable slot0 [0x7E4570] =", L.hx(L.u32(0x7E4570)))
col = L.u32(0x7E4570-4); print("COL[7E456C]=%s sig=%s" % (L.hx(col), L.hx(L.u32(col)) if col else None))
td = L.u32(col+0xC) if col else None; print("TD=%s name=%r" % (L.hx(td), L.read_cstr(td+8) if td else None))

sec("2) ③b② 站点 0x465300..0x465380 (call 0x716DC0 段)")
for ins in L.disasm(0x465300, 0x80):
    print(L.fmt_ins(ins))
sec("2b) 失败落点 0x46536A + 成功尾 0x465360..0x465380")
for ins in L.disasm(0x46535E, 0x28):
    print(L.fmt_ins(ins))
sec("2c) 另两站点 0x465332/0x465355")
for a in (0x46532A,0x46534D):
    print("-- @%s --" % L.hx(a))
    for ins in L.disasm(a, 0x1C):
        print(L.fmt_ins(ins))

sec("3) 被调 0x716DC0 头部")
for ins in L.disasm(0x716DC0, 0x30):
    print(L.fmt_ins(ins))
sec("3b) 被调 0x716DC0 尾 0x717088..0x71709C")
for ins in L.disasm(0x717088, 0x20):
    print(L.fmt_ins(ins))

sec("4) ④ 构造安装点 0x45E2CD / 0x45E558；析构重装 0x45E58D (排除)")
for a in (0x45E2CD, 0x45E558, 0x45E58D):
    print("-- install @%s bytes=%s --" % (L.hx(a), L.hexb(a,6)))
    for ins in L.disasm(a-3, 0x10):
        print("   ", L.fmt_ins(ins))
print("atexit(45DD90)=", L.is_atexit_registered(0x45DD90))
print("atexit(45E520)=", L.is_atexit_registered(0x45E520))
print("direct callers of entry 00465300 =", [L.hx(x) for x in L.find_direct_calls(entry)])
sec("4b) 构造体 0x45DD90 / 0x45E520 尾部 (返 this?)")
print("-- 45DD90 tail --")
for ins in L.disasm(0x45E2C7, 0x14):
    print(L.fmt_ins(ins))
print("-- 45E520 tail --")
for ins in L.disasm(0x45E552, 0x14):
    print(L.fmt_ins(ins))
sec("4c) 析构体 0x45E580 头部 (free/基类析构 => ㉓)")
for ins in L.disasm(0x45E580, 0x30):
    print(L.fmt_ins(ins))
