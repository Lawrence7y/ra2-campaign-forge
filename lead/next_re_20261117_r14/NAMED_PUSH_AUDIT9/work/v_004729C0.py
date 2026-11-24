# -*- coding: utf-8 -*-
"""独立验证 004729C0 CaptureManagerClass::slot8 —— 删除式析构器 + Find(-1) ③b②。重点：② 主表 / ④ 非析构。"""
import audit_lib as L

def sec(t): print("\n===== " + t + " =====")

entry = 0x004729C0

sec("1) ② slot 007E4B60 (vt 007E4B40 +0x20, slot#8), RTTI, 主表 slot0")
sva = 0x007E4B60
print("slot bytes=%s u32=%s (entry=%s)" % (L.hexb(sva,4), L.hx(L.u32(sva)), L.hx(entry)))
print("resolve_slot ->", L.resolve_slot(sva))
print("(0x4B60-0x4B40)/4 =", (0x4B60-0x4B40)//4)
print("vtable slot0 [0x7E4B40] =", L.hx(L.u32(0x7E4B40)))
col = L.u32(0x7E4B40-4); print("COL[7E4B3C]=%s sig=%s" % (L.hx(col), L.hx(L.u32(col)) if col else None))
td = L.u32(col+0xC) if col else None; print("TD=%s name=%r" % (L.hx(td), L.read_cstr(td+8) if td else None))
# 是否被误当小成员表？检查该 vtable 是否被当成某容器内成员对象的表
print("--- 全镜像 .rdata 中等于 entry 的 dword 引用（确认槽唯一归属）---")
print([ (L.hx(a),nm) for a,nm in L.find_dword_refs(entry) ])

sec("2) ③b② 站点 0x4729C0..0x472A40 (entry 自身=析构器, call [edx+0x10] Find)")
for ins in L.disasm(0x4729C0, 0x80):
    print(L.fmt_ins(ins))

sec("2b) 判据/跳转 0x4729EE..0x472A2C 逐字节")
print("bytes @4729F3:", L.hexb(0x4729F3, 12))
for ins in L.disasm(0x4729EE, 0x40):
    print(L.fmt_ins(ins))

sec("3) 被调 Find 链：全局 0x89E0F0 静态初始化 + vtable + slot4")
# 静态初始化点
for ins in L.disasm(0x471760, 0x18):
    print(L.fmt_ins(ins))
# 全局当前值（磁盘初值)
print("u32[0x89E0F0] (disk)=", L.hx(L.u32(0x89E0F0)))
vt = 0x7E4AD4
print("global vptr writes 0x7E4AD4; COL[-4]@7E4AD0=%s" % L.hx(L.u32(0x7E4AD0)))
col2=L.u32(0x7E4AD0); print("   COL.sig=%s TD=%s name=%r" % (L.hx(L.u32(col2)), L.hx(L.u32(col2+0xC)), L.read_cstr(L.u32(col2+0xC)+8) if col2 else None))
s4=L.u32(vt+0x10); print("   slot4 @7E4AE4 = %s" % L.hx(s4))
print("   --- Find body @%s ---" % L.hx(s4))
for ins in L.disasm(s4, 0x40):
    print("     ", L.fmt_ins(ins))

sec("3b) 命中路径: count-- 回写 + 前移压缩 (调用方, 非栈写)")
# 已在 2) 中反汇编; 汇总字节
print("miss-target 0x472A28; hit site 0x472A05 dec ecx / 0x472A08 mov [0x89E100],ecx")
print("bytes @472A00:", L.hexb(0x472A00, 0x30))

sec("4) ④ 锚点：同类构造器 0x471807 (ctor 4717D0) — 非本行析构器")
print("atexit(4717D0)=", L.is_atexit_registered(0x4717D0))
print("atexit(471890)=", L.is_atexit_registered(0x471890))
print("direct callers of entry 004729C0 =", [L.hx(x) for x in L.find_direct_calls(entry)])
print("-- ctor 4717D0 安装 0x471807 --")
for ins in L.disasm(0x471803, 0xC): print(L.fmt_ins(ins))
print("-- ctor 4717D0 尾 (返 this) --")
for ins in L.disasm(0x471880, 0xE): print(L.fmt_ins(ins))

sec("4b) 本行 entry 0x4729C0 是否删除式析构器 (㉓: 证据表明它不能作 ④)")
# 析构器: 找 free / operator delete / 基类析构 call
for ins in L.disasm(0x4729C0, 0x100):
    if ins.mnemonic in ('call',) or 'free' in ins.op_str.lower():
        print("   ", L.fmt_ins(ins))
