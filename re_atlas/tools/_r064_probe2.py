# _r064_probe2.py -- R-064 仲裁探针2：关键帧线性反汇编窗口（stamp ↔ witness lea 之间指令流）
# 只读。capstone 线性解码指定窗口，标注 stamp/lea/ret/call/push/pop/sub-esp/add-esp。
import struct, capstone
from _r064_probe1 import rd, secs, EXE, data  # 复用装载器（只读函数）

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False

def dis(win_lo, win_hi, marks):
    """线性反汇编 [win_lo,win_hi)，打印助记符+字节；marks: {va: 标签}"""
    va = win_lo
    while va < win_hi:
        b = rd(va, min(16, win_hi - va))
        if b is None:
            print("   %#x <不可读>" % va); break
        try:
            ins = next(md.disasm(b, va))
        except StopIteration:
            print("   %#x  db %s   <解码缝隙>" % (va, b[:1].hex())); va += 1; continue
        tag = ""
        for mva, lab in marks.items():
            if ins.address <= mva < ins.address + ins.size:
                tag = "  <<< " + lab
        t = ins.mnemonic + " " + (ins.op_str or "")
        print("   %#x  %-22s %s%s" % (ins.address, ins.bytes.hex(), t, tag))
        va += ins.size

print("== 帧 A 窗口：0x7787C0(GenericList stamp) .. 0x7787F7(INIClass stamp) .. 0x77884F(lea) ==")
marks = {0x7787C0: "R-062窗1 stamp [esp+0x38],0x7E1B04",
         0x7787F7: "补stampA [esp+0x30],0x7EA5F4",
         0x77884F: "witness lea [esp+0x38] 行1",
         0x77890C: "witness lea [esp+0x38] 行2",
         0x778956: "witness lea [esp+0x38] 行3"}
dis(0x7787A0, 0x778860, marks)
print("   ---- 行2/行3 ----")
dis(0x778900, 0x778960, marks)

print("\n== 帧 B 窗口：0x779BB3 stamp .. 0x779BEA 补stamp .. 0x779C3D lea ==")
marks = {0x779BB3: "R-062窗2 stamp [esp+0x24],0x7E1B04",
         0x779BEA: "补stampB [esp+0x1C],0x7EA5F4",
         0x779C3D: "witness lea [esp+0x24] 行4"}
dis(0x779B90, 0x779C50, marks)

print("\n== 帧 C 窗口：0x779E33 stamp .. 0x779E6A 补stamp .. 0x779EBD lea ==")
marks = {0x779E33: "R-062窗3 stamp [esp+0x24],0x7E1B04",
         0x779E6A: "补stampC [esp+0x1C],0x7EA5F4",
         0x779EBD: "witness lea [esp+0x24] 行5"}
dis(0x779E10, 0x779ED0, marks)

print("\n== 帧 D（0x5CEE00..）：0x5CEF41 stamp .. 0x5CEFC5 lea（行6） ==")
marks = {0x5CEF41: "R-063b stamp1 [esp+0x28],0x7EA5F4",
         0x5CEFC5: "witness lea [esp+0x38] 行6", 0x5CEFC9: "call 行6"}
dis(0x5CEEF0, 0x5CEFD5, marks)

print("\n== 帧 E（0x76C290..）：0x76C4A4 stamp .. 0x76C551 lea（行12） ==")
marks = {0x76C4A4: "R-063b stamp2 [esp+0x30],0x7EA5F4",
         0x76C551: "witness lea [esp+0x38] 行12", 0x76C555: "call 行12"}
dis(0x76C480, 0x76C560, marks)

print("\n== 帧 F 窗口：0x778B20 stamp .. 0x778B95('epilogue') .. 0x778BCB lea（行13） ==")
marks = {0x778B20: "R-063b stamp3 [esp+0x2C],0x7EA5F4",
         0x778BCB: "witness lea [esp+0x38] 行13", 0x778BCF: "call 行13"}
dis(0x778B00, 0x778BD5, marks)
print("   ---- 0x778B95 前后（判函数边界） ----")
dis(0x778B88, 0x778BB5, marks)

print("\n== 行13/14/15 窗口 ==")
dis(0x778DC0, 0x778E30, marks)

print("\n== 行16（0x5D76A9）帧：0x5D761D stamp .. 0x5D76A2 lea ==")
marks = {0x5D761D: "INIClass stamp [esp+0x78],0x7EA5F4",
         0x5D76A2: "witness lea [esp+0x88] 行16", 0x5D76A9: "call 行16"}
dis(0x5D7600, 0x5D76B5, marks)
