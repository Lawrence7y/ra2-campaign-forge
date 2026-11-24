# -*- coding: utf-8 -*-
"""虚表全部写点分类：构造器 / 删除析构器 / atexit 全局析构器。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core
from np_core import *
from capstone import *

OP_DELETE = 0x7C8B3D      # operator delete
OP_NEW = 0x7C8E17

def func_start_via_atlas(addr):
    af = containing_atlas_func(addr)
    return af[0] if af else None

def scan_writes(vt):
    """穷举 vt 作为立即数写入 .text 的站点，返回 (write_va, containing_func_start)。"""
    out = []
    needle = struct.pack("<I", vt)
    for off in range(0, len(TEXT_DATA) - 4):
        if TEXT_DATA[off:off+4] != needle: continue
        va = TEXT_VA + off
        # 判定前面是 C7 (mov r/m32, imm32) 且 modrm 形状合理
        if off >= 2 and TEXT_DATA[off-2] == 0xC7:
            out.append((va - 2, TEXT_DATA[off-1]))
    return out

def classify_func(fs):
    """返回该写点所在函数的完整函数体与分类建议。"""
    af = containing_atlas_func(fs)
    if af:
        start, size = af[0], af[2]
    else:
        start, size = fs, 0x200
    insns = list(np_core._md.disasm(va_read(start, size), start))
    has_del = any(i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM
                  and (i.operands[0].imm & 0xFFFFFFFF) == OP_DELETE for i in insns)
    return start, size, insns, has_del

for vt, label in [(0x007E4A28, "CampaignClass"), (0x007F5180, "TemporalClass"),
                  (0x007F4090, "SuperWeaponTypeClass")]:
    print("\n" + "=" * 90)
    print("### vt %s  %s" % (hx(vt), label))
    ws = scan_writes(vt)
    print("  全 imm 写点 %d 个：" % len(ws))
    seen = set()
    for wva, modrm in ws:
        # modrm 的 r/m 字段：06=esi, 00=eax, 01=ecx 等
        print("   - write @ %s (modrm=%02X)" % (hx(wva), modrm))
        af = containing_atlas_func(wva)
        fstart = af[0] if af else None
        if fstart is None:
            # 回扫找 prologue
            print("       [atlas 未覆盖，回扫 prologue]")
            continue
        if fstart in seen: continue
        seen.add(fstart)
        start, size, insns, has_del = classify_func(fstart)
        ae = is_atexit_registered(fstart)
        callers = find_direct_calls(fstart)
        n_ret = sum(1 for i in insns if i.id == X86_INS_RET)
        print("       func %s size=%d rets=%d has_operator_delete=%s atexit=%s callers=%d[%s]"
              % (hx(start), size, n_ret, has_del, ae, len(callers),
                 " ".join(hx(c) for c in callers[:6])))
