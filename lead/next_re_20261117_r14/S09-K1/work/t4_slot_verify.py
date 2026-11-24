"""T4：虚表槽语义字节级核验。读指定槽地址处的 4 字节函数指针，并与线索文档期望值对照。
同时反汇编槽函数首指令给一句语义（能证的才写语义，否则[未证]）。"""
import re_lib as R

b = R.Bin()
m = R.md32(True)

# (class, vtable, slot, expected_func, expected_semantic, source)
CLAIMS = [
    ("SidebarClass", 0x7F3058, 16, 0x6A6C30, "Draw(每帧壳)", "R8 §21.1"),
    ("SidebarClass", 0x7F3058, 33, 0x6AC210, "Draw_It", "R8 §21.1"),
    ("SidebarClass", 0x7F3058, 34, 0x6ABD30, "tooltip/悬停", "R8 §21.1"),
    ("SidebarClass", 0x7F3058, 50, 0x6A5BF0, "建按钮", "R8 §21.1"),
    ("SelectClass@Strip@Sidebar", 0x7F2FCC, 31, 0x6AAD00, "Cameo点击(生产)", "R8 §21.1/S09-F1"),
    ("DisplayClass", 0x7E6114, 48, 0x4AB9B0, "LMBUp点选/框选收口", "R8 §21.1/S09-F1"),
    ("DisplayClass", 0x7E6114, 47, 0x4AC380, "LMBDown", "R8 §21.1"),
    ("DisplayClass", 0x7E6114, 45, 0x4AC310, "清拖拽状态", "R8 §21.1"),
    ("DisplayClass", 0x7E6114, 33, 0x4AE4F0, "Draw_It(world)", "R8 §21.1"),
    ("MouseClass", 0x7E1964, 19, 0x5BDC80, "SetCursor", "R8 §21.1"),
    ("MouseClass", 0x7E1964, 40, 0x40D280, "RightMouseButtonUp", "R8 §21.1"),
    ("CommandClass", 0x7EBE3C, 8, 0x4C9150, "Execute抽象桩", "R8 §21.1"),
    ("WWMouseClass", 0x7F7B2C, 0x44//4, None, "v[0x44]ScreenToClient", "ui_cmd §1.2"),  # 后面单独核对
]

def slot_addr(vt, n): return vt + n * 4

print("%-26s %-5s %-10s %-10s %-10s %-6s %s" % (
    "class", "slot", "slot_addr", "expected", "actual", "match", "semantic"))
for cls, vt, sl, exp, sem, src in CLAIMS:
    sa = slot_addr(vt, sl)
    act = b.u32(sa)
    match = "OK" if (exp is None or act == exp) else "MISMATCH"
    print("%-26s %-5d %08X   %-10s %08X   %-6s %s" % (
        cls, sl, sa, ("%08X" % exp) if exp else "-", act, match, sem))

# WWMouseClass 用 byte offset: call [eax+0x44] -> slot 0x44/4=17; call [edx+0x38] -> slot14
print("\n--- WWMouseClass v[0x38/4=14], v[0x44/4=17] ---")
for off in (0x38, 0x44):
    sl = off // 4
    sa = 0x7F7B2C + off
    print("  v[%d] (off 0x%X) @%08X = %08X" % (sl, off, sa, b.u32(sa)))

# SelectClass v[31] 的调用点（Cameo生产）独立验证：全.text 找 call [reg+0x7C]? 
# v[31] -> offset 31*4 = 0x7C。搜 call dword [reg+0x7c] 附近是否 0x4C6970
print("\n--- SelectClass v[31] slot offset = 0x7C; check 0x6AAD00 body ---")
d = b.read(0x6AAD00, 0x40)
for ins in m.disasm(d, 0x6AAD00):
    print("  %08X %-20s %s %s" % (ins.address, ins.bytes.hex(' '), ins.mnemonic, ins.op_str))
    if ins.address >= 0x6AAD30: break
