# -*- coding: utf-8 -*-
"""独立验证 004728E0 CaptureManagerClass::slot6 —— ③b② 多值 (E_POINTER)。"""
import audit_lib as L

def sec(t): print("\n===== " + t + " =====")

entry = 0x004728E0

sec("1) ② slot 007E4B58 (vt 007E4B40 +0x18, slot#6), RTTI, 主表 slot0")
sva = 0x007E4B58
print("slot bytes=%s u32=%s (entry=%s)" % (L.hexb(sva,4), L.hx(L.u32(sva)), L.hx(entry)))
print("resolve_slot ->", L.resolve_slot(sva))
print("(0x4B58-0x4B40)/4 =", (0x4B58-0x4B40)//4)
print("vtable slot0 [0x7E4B40] =", L.hx(L.u32(0x7E4B40)))
col = L.u32(0x7E4B40-4); print("COL[7E4B3C]=%s sig=%s" % (L.hx(col), L.hx(L.u32(col)) if col else None))
td = L.u32(col+0xC) if col else None; print("TD=%s name=%r" % (L.hx(td), L.read_cstr(td+8) if td else None))

sec("2) ③b② 站点 0x4728C0..0x472970 (call 0x410320 段)")
for ins in L.disasm(0x4728C0, 0xB0):
    print(L.fmt_ins(ins))
sec("2b) 失败落点 0x472956 + 收尾")
for ins in L.disasm(0x472950, 0x18):
    print(L.fmt_ins(ins))
sec("2c) 另两站点 0x472915/0x472942")
for a in (0x47290D,0x47293A):
    print("-- @%s --" % L.hx(a))
    for ins in L.disasm(a, 0x1C):
        print(L.fmt_ins(ins))

sec("3) 被调 0x410320 返回集 (87B)")
for ins in L.disasm(0x410320, 0x40):
    print(L.fmt_ins(ins))
sec("3b) 被调成功尾 0x41036C..0x410378")
for ins in L.disasm(0x41036A, 0x12):
    print(L.fmt_ins(ins))
sec("3c) 被调 0x410320 eax 常量集 (body 0x100)")
cs=L.eax_constants(0x410320,0x100)
print("ret=%d consts=%s"%(len(cs),sorted(set(c for _,c,_,_ in cs if c is not None))))
for r in cs: print("  ",r)

sec("4) ④ 构造安装点 0x471807 / 0x4718BC；析构重装 0x4729CD (排除)")
for a in (0x471807, 0x4718BC, 0x4729CD):
    print("-- install @%s bytes=%s --" % (L.hx(a), L.hexb(a,6)))
    for ins in L.disasm(a-3, 0x10):
        print("   ", L.fmt_ins(ins))
print("atexit(4717D0)=", L.is_atexit_registered(0x4717D0))
print("atexit(471890)=", L.is_atexit_registered(0x471890))
print("direct callers of entry 004728E0 =", [L.hx(x) for x in L.find_direct_calls(entry)])
sec("4b) 构造体 0x4717D0 尾部 (返 this?)")
for ins in L.disasm(0x4717F8, 0x18):
    print(L.fmt_ins(ins))
sec("4c) 析构体 0x4729C0 头部 (free/基类析构 => ㉓)")
for ins in L.disasm(0x4729C0, 0x30):
    print(L.fmt_ins(ins))
