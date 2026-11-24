# -*- coding: utf-8 -*-
"""聚焦验证：候选行全文反汇编 + callee 返回约定 + ctor 实例化链 + ㉓ 写点枚举。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from capstone.x86 import X86_OP_IMM, X86_INS_CALL

def dump_func(start, size, label):
    print("### FUNC %s @%s size=%s" % (label, core.hx(start), size))
    body = core.func_body(start, size)
    for i in body:
        print("  %s  %-20s %-8s %s" % (core.hx(i.address), i.bytes.hex(), i.mnemonic, i.op_str))
    print()

def callers_of(target):
    out = []
    for ia in core.IMM_INDEX.get(target, []):
        ins = core.INS_BY_ADDR[ia]
        if ins.id == X86_INS_CALL:
            out.append(core.hx(ia))
    return out

# ---- 候选行全文 ----
print("=" * 90)
print("== 006DBE00 Tactical::slot6 (29B) + callee 00410320 ==")
dump_func(0x006DBE00, 29, "006DBE00")
# 0x410320 = IStream::Write wrapper; dump first 0x40
dump_func(0x00410320, 0x40, "00410320 Write")

print("=" * 90)
print("== 3x QI slot0 (93B each) + callee 0055A9B0 ==")
dump_func(0x0069EE30, 93, "0069EE30 Ship::slot0")
dump_func(0x00719E30, 93, "00719E30 Teleport::slot0")
dump_func(0x0075C7F0, 93, "0075C7F0 Walk::slot0")

print("=" * 90)
print("== callee 0055A9B0 (base QI) 返回约定 ==")
body = core.func_body(0x0055A9B0, 0x120)
for i in body:
    if i.mnemonic in ("mov", "xor", "ret", "cmp", "jne", "je", "jmp") and \
       (("eax" in i.op_str) or i.mnemonic == "ret"):
        print("  %s  %-16s %-6s %s" % (core.hx(i.address), i.bytes.hex(), i.mnemonic, i.op_str))

print("=" * 90)
print("== BSurface slot2 007BBB90 / slot3 007BBCF0 callee 007BBE20 返回约定 ==")
dump_func(0x007BBE20, 0x40, "007BBE20")
print("BSurface slot18 007BA8C0 call/test/cmp/jcc 扫描:")
body = core.func_body(0x007BA8C0, 621)
for i in body:
    if i.id == X86_INS_CALL or i.mnemonic.startswith("j") or i.mnemonic in ("test", "cmp"):
        print("  %s  %-18s %-6s %s" % (core.hx(i.address), i.bytes.hex(), i.mnemonic, i.op_str))

print("=" * 90)
print("== ctor 实例化链：找各主表 ctor 的直接调用者，检查 push size/new/call ctor ==")
ctors = {
    "0069EC50": "Ship main ctor", "00719CA0": "Teleport main ctor", "0075C680": "Walk main ctor",
    "006D1C20": "Tactical main ctor (slot6)", "006D1E30": "Tactical alt ctor",
}
for ctor, label in ctors.items():
    c = callers_of(int(ctor, 16))
    print("  %s %s direct callers=%s" % (ctor, label, c))
    for ca in c:
        a = int(ca, 16)
        # 从调用点往前 0x20 找 push size / call operator new
        pre = core.dis_range(max(core.TEXT_VA, a - 0x30), 0x30)
        seg = [("%s %s %s" % (core.hx(x.address), x.mnemonic, x.op_str)) for x in pre
               if (x.id == X86_INS_CALL and x.operands and x.operands[0].type == X86_OP_IMM
                   and (x.operands[0].imm & 0xFFFFFFFF) == 0x7C8E17) or x.mnemonic == "push"]
        print("     @%s pre(new/push)=%s" % (ca, seg[-8:]))

print("=" * 90)
print("== ㉓ 写点枚举：各主表 vtable 安装点全表 (CTX/DTOR) ==")
for vt, label in [(0x007F2E58,"Ship main"),(0x007F50CC,"Teleport main"),(0x007F6AC4,"Walk main"),(0x007F4348,"Tactical main")]:
    sites = [i for i in core.install_sites(vt) if core.is_vptr_store(i, vt)]
    print("  %s vt=%s installs=%d: %s" % (label, core.hx(vt), len(sites),
          [(core.hx(i.address), i.op_str) for i in sites]))
