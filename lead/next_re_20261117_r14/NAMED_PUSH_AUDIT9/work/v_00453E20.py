# -*- coding: utf-8 -*-
"""独立验证 00453E20 BuildingClass::vslot5 —— ③b② 多值 HRESULT。"""
import audit_lib as L

def sec(t): print("\n===== " + t + " =====")

entry = 0x00453E20

sec("0) 取法：delta.tsv 第1列，行2..7，共6行")
sec("1) ② slot 007E3ED0 (vt 007E3EBC +0x14, slot#5), RTTI, 主表 slot0")
sva = 0x007E3ED0
print("slot bytes=%s u32=%s (entry=%s)" % (L.hexb(sva,4), L.hx(L.u32(sva)), L.hx(entry)))
print("resolve_slot ->", L.resolve_slot(sva))
print("(0x3ED0-0x3EBC)/4 =", (0x3ED0-0x3EBC)//4)
print("vtable slot0 [0x7E3EBC] =", L.hx(L.u32(0x7E3EBC)))
col = L.u32(0x7E3EBC-4); print("COL[7E3EB8]=%s sig=%s" % (L.hx(col), L.hx(L.u32(col)) if col else None))
td = L.u32(col+0xC) if col else None; print("TD=%s name=%r" % (L.hx(td), L.read_cstr(td+8) if td else None))

sec("2) ③b② 站点 0x453E40..0x453ED0 (call 0x70BF50 段) 完整反汇编")
for ins in L.disasm(0x453E40, 0xA0):
    print(L.fmt_ins(ins))

sec("2b) 调用方判据/跳转 0x453EB0..0x453EC8")
print("bytes @453EB3:", L.hexb(0x453EB3, 12))
for ins in L.disasm(0x453EB0, 0x20):
    print(L.fmt_ins(ins))

sec("2c) 失败落点 0x45417E + 成功尾 0x454160..0x454190")
for ins in L.disasm(0x454160, 0x40):
    print(L.fmt_ins(ins))

sec("2d) 另三站点 0x453FED/0x45407A/0x45409C")
for a in (0x453FE0,0x454070,0x454090):
    print("-- @%s --" % L.hx(a))
    for ins in L.disasm(a, 0x20):
        print(L.fmt_ins(ins))

sec("3) 被调 0x70BF50 头部 (约定字节)")
for ins in L.disasm(0x70BF50, 0x30):
    print(L.fmt_ins(ins))
sec("3b) 被调 0x70BF50 尾部 0x70C238..0x70C250")
for ins in L.disasm(0x70C238, 0x20):
    print(L.fmt_ins(ins))
sec("3c) 被调 0x70BF50 返回常量集合 (eax_constants, body 0x1000)")
cs = L.eax_constants(0x70BF50, 0x1000)
print("ret count=%d consts=%s" % (len(cs), sorted(set(c for _,c,_,_ in cs if c is not None))))
for r in cs:
    print("  ", r)

sec("4) ④ 构造安装点 0x43B71F / 0x43B9FA；析构重装 0x43BCFD (排除)")
for a in (0x43B71F, 0x43B9FA, 0x43BCFD):
    print("-- install @%s bytes=%s --" % (L.hx(a), L.hexb(a,6)))
    for ins in L.disasm(a-3, 0x10):
        print("   ", L.fmt_ins(ins))
print("atexit(43B680)=", L.is_atexit_registered(0x43B680))
print("atexit(43B740)=", L.is_atexit_registered(0x43B740))
print("direct callers of entry 00453E20 =", [L.hx(x) for x in L.find_direct_calls(entry)])
sec("4b) 构造体 0x43B680 尾部 (返 this?)")
for ins in L.disasm(0x43B730, 0x14):
    print(L.fmt_ins(ins))
sec("4c) 析构体 0x43BCF0 头部 (free/vptr重装 => ㉓)")
for ins in L.disasm(0x43BCF0, 0x40):
    print(L.fmt_ins(ins))
