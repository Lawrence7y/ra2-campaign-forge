# -*- coding: utf-8 -*-
"""A02 probe3 —— 泵内层 PeekMessage / WndProc 守卫链 edi=hwnd 证明 /
MainLogicFrame 全文落盘 / 0x55E160 焦点门 / hwnd 写者 / 46 处 raw 命中与指令边界对齐
"""
import sys
import struct

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
by = eng.by()

def H(t):
    print("\n" + "=" * 78)
    print("== " + t)
    print("=" * 78)

def dump(va, n, mark=()):
    """用已解码流（指令边界对齐）转储，遇非边界则标注。"""
    end = va + n
    a = va
    while a < end:
        ins = by.get(a)
        if ins is None:
            print("  %08X  !!! 非指令边界（线性解码未覆盖）" % a)
            a += 1
            continue
        m = " <<<" if a in mark else ""
        print("  %08X  %-22s %-8s %s%s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str, m))
        a += ins.size

H("0. 现场自证")
cov, nins, resync = eng.coverage
print("eng.coverage = %.2f%% / %d insns / %d resync" % (cov, nins, resync))

H("1. 补解 IAT：0x7E11E8 / 0x7E13C0 / 0x7E13C4 等")
for va in (0x7E11E8, 0x7E13C0, 0x7E13C4, 0x7E14B8, 0x7E14BC, 0x7E14C0, 0x7E14F4, 0x7E14F8):
    print("  [0x%08X] -> %r" % (va, eng.resolve_iat(va)))

H("2. 全镜像 IAT 中所有 PeekMessage* / PostQuitMessage / DestroyWindow / SetForegroundWindow 槽位")
dd = eng.opt + 96
imp_rva = struct.unpack_from("<I", eng.raw, dd + 8)[0]
o = eng.fo(eng.IB + imp_rva)
k = 0
want = ("PeekMessage", "PostQuitMessage", "DestroyWindow", "SetForegroundWindow",
        "SetActiveWindow", "DispatchMessage", "GetMessage", "SetFocus", "ShowWindow",
        "ValidateRect", "BeginPaint", "IsWindow")
while True:
    d = eng.raw[o + k * 20: o + k * 20 + 20]
    if len(d) < 20 or d == b"\0" * 20:
        break
    oft, _ts, _fc, name_rva, ft = struct.unpack_from("<IIIII", d, 0)
    no = eng.fo(eng.IB + name_rva)
    dll = eng.raw[no:eng.raw.index(b"\0", no)].decode("ascii", "replace")
    thunk = oft or ft
    j = 0
    while True:
        tv = struct.unpack_from("<I", eng.raw, eng.fo(eng.IB + thunk) + j * 4)[0]
        if tv == 0:
            break
        slot = eng.IB + ft + j * 4
        if tv & 0x80000000:
            nm = "ord#%d" % (tv & 0xFFFF)
        else:
            ho = eng.fo(eng.IB + tv + 2)
            nm = eng.raw[ho:eng.raw.index(b"\0", ho)].decode("ascii", "replace")
        if any(nm.startswith(w) for w in want):
            print("  %-28s 0x%08X" % (dll + "!" + nm, slot))
        j += 1
    k += 1

H("3. 内层 peek 封装 0x53E770 全函数（指令边界对齐）")
dump(0x53E770, 0x120)

H("4. 泵 0x5D4D50 全函数（指令边界对齐，重录）")
dump(0x5D4D50, 0x120)

H("5. WndProc 头 0x7775C0..0x7776B0（证明 edi=hwnd / uMsg 栈位）")
dump(0x7775C0, 0xF0)

H("6. uMsg>0x18 链 0x77782B..0x777960（写点守卫全链）")
dump(0x77782B, 0x140)

H("7. 写点后 0x777930..0x7779A0（激活沿后继 / 收尾出口）")
dump(0x777930, 0x80)

H("8. 0x777949 收尾出口")
dump(0x777940, 0x40)

H("9. MainLogicFrame 全文落盘到 A02_mlf_disasm.txt")
with open(r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\A02\A02_mlf_disasm.txt", "w", encoding="utf-8") as f:
    a = 0x55D360
    while a < 0x55DEE0:
        ins = by.get(a)
        if ins is None:
            f.write("%08X  !!!非边界\n" % a)
            a += 1
            continue
        f.write("%08X  %-22s %-8s %s\n" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        a += ins.size
print("  已写 A02_mlf_disasm.txt")
print("  -- MainLogicFrame 内对 IAT 的间接 call（找有没有会抛/会退出的调用）--")
a = 0x55D360
while a < 0x55DEE0:
    ins = by.get(a)
    if ins is None:
        a += 1
        continue
    if ins.mnemonic == "call" and "dword ptr [0x7e" in ins.op_str:
        slot = int(ins.op_str.split("[")[1].split("]")[0], 16)
        print("    %08X  call [0x%08X] -> %r" % (a, slot, eng.resolve_iat(slot)))
    a += ins.size

H("10. LogicUpdate 0x55E160 头 + 焦点门 0x55E1E0..0x55E230")
dump(0x55E160, 0xD0)

H("11. hwnd 全局 0xB73550 的全部访存（谁可能把它清 0）")
h = eng.disp_hits(0x00B73550)
print("  0xB73550 共 %d 处" % len(h))
for va, rw, mn, ops in h:
    print("    %08X %s %-8s %s" % (va, rw, mn, ops))

H("12. 46 处 raw 命中 ↔ 指令边界对齐校验（证明 xref 完备、无隐写形态）")
pat = struct.pack("<I", 0x00A8ED80)
idx, raw_hits = 0, []
while True:
    j = eng.raw.find(pat, idx)
    if j < 0:
        break
    raw_hits.append(j)
    idx = j + 1
print("  raw 命中 = %d" % len(raw_hits))
va_of = {}
for nm, sva, vsz, rp, rsz in eng.SEC:
    va_of[nm] = (sva, vsz, rp, rsz)
bad, secs = [], {}
mapped = {}
for j in raw_hits:
    hit = None
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if rp <= j < rp + rsz:
            hit = (nm, sva + (j - rp))
            break
    if hit is None:
        bad.append((j, "不在任何段"))
        continue
    nm, pva = hit
    secs[nm] = secs.get(nm, 0) + 1
    found = None
    for back in range(0, 12):
        ins = by.get(pva - back)
        if ins is not None and ins.address <= pva < ins.address + ins.size:
            found = ins
            break
    if found is None:
        bad.append((j, "非指令边界 VA=0x%X" % pva))
    else:
        mapped.setdefault(found.address, []).append(pva)
print("  按段分布: %s" % secs)
print("  无法归到指令的点: %d %s" % (len(bad), bad))
print("  归到的独立指令数 = %d（应 = 46）" % len(mapped))
for a in sorted(mapped):
    ins = by[a]
    print("    %08X  %-22s %-8s %-38s 命中位移=%s"
          % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str,
             [p - a for p in mapped[a]]))

H("13. 0xA8ED80 读点语义分类（宿主聚簇：是否在 '等焦点' 自旋环里）")
h = eng.disp_hits(0x00A8ED80)
for va, rw, mn, ops in h:
    if rw == "W":
        continue
    ctx = []
    for back in (4, 8, 12, 16, 20):
        p = va - back
        ins = by.get(p)
        if ins is not None and ins.mnemonic == "call":
            ctx.append("call@%X" % p)
    print("    %08X  %-8s %-34s 前20B内call=%s" % (va, mn, ops, ctx or "-"))

print("\n[DONE probe3]")
