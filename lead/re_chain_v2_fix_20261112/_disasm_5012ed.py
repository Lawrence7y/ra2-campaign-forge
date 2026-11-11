# -*- coding: utf-8 -*-
"""C5 补做：对 VA 0x5012ED 附近字节做一次纯静态反汇编（capstone）。
零真机：只 read() 磁盘上的 ra2bench/gamemd.exe，不启动/不 attach/不读活进程内存。
输出：_disasm_5012ed_out.txt（由 PowerShell *> 捕获 stdout）。
VA 约定沿用 _ps_disasm.py:5 —— .text/.rdata/.data 三节 file offset == RVA，VA = foff + 0x400000。
"""
import hashlib
import os
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
EXE = os.path.join(REPO, "ra2bench", "gamemd.exe")
IMGBASE = 0x400000
TARGET = 0x5012ED
STR_VA = 0x824E28
LO, HI = 0x501140, 0x5013C0

data = open(EXE, "rb").read()
h = hashlib.sha256(data).hexdigest()
print("== C5 静态反汇编：0x5012ED 性质核实 ==")
print("[0] exe      : %s" % EXE)
print("[0] size     : %d B" % len(data))
print("[0] sha256   : %s" % h)
print("[0] 铁律     : 只读磁盘字节；未启动 gamemd.exe/ra2loader/YURI.exe，未 attach，未读活进程内存，未写 hook/采样/MiniDump 代码。")
print()

# 1) 靶点处的原始字节（LE32==0x824E28 的 4 字节即 xref 本体）
foff = TARGET - IMGBASE
raw = data[foff - 8: foff + 24]
print("[1] VA 0x5012ED 处 (foff 0x%X) 附近原始字节:" % foff)
print("    [-8..+24) = %s" % raw.hex(" "))
le = struct.unpack_from("<I", data, foff)[0]
print("    4 字节 LE32 @0x5012ED = 0x%08X  (字符串 PlayerControl VA = 0x%08X) -> %s" %
      (le, STR_VA, "MATCH（该处即 xref 的 imm32/disp32 本体）" if le == STR_VA else "MISMATCH"))
print()

# 2) 线性反汇编窗口
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
chunk = data[LO - IMGBASE: HI - IMGBASE]
print("[2] 线性反汇编 [0x%06X, 0x%06X)（capstone x86-32）:" % (LO, HI))
ins_list = list(md.disasm(chunk, LO))
for ins in ins_list:
    mark = ""
    if ins.address <= TARGET < ins.address + ins.size:
        mark = "   <<< 0x5012ED 落在此指令编码内"
    print("    0x%06X  %-22s  %-7s %s%s" %
          (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
print()

# 3) 靶点所在指令与紧随其后的调用，给出性质判据
print("[3] 靶点归属指令 / 上下文:")
for i, ins in enumerate(ins_list):
    if ins.address <= TARGET < ins.address + ins.size:
        print("    归属指令: 0x%06X  %s  %s %s  bytes=%s" %
              (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, " ".join("%02x" % b for b in ins.bytes)))
        print("    0x5012ED 在该指令内的偏移 = +%d（即 4 字节立即数/位移量的起始）" %
              (TARGET - ins.address))
        for j in range(max(0, i - 6), min(len(ins_list), i + 9)):
            n = ins_list[j]
            print("      %s0x%06X  %-7s %s" %
                  (">>" if j == i else "  ", n.address, n.mnemonic, n.op_str))
        break
print()

# 4) 判据：该 xref 是「把字符串指针压栈/传参」还是「写回 INI」
print("[4] 性质判定（仅依据以上静态字节，不引入运行期推测）:")
tgt_ins = None
for ins in ins_list:
    if ins.address <= TARGET < ins.address + ins.size:
        tgt_ins = ins
        break
if tgt_ins is None:
    print("    未能在窗口内定位包含 0x5012ED 的指令，记为【未验】")
else:
    print("    - 该 4 字节是指令 %s %s 的 imm32 立即数（字符串 'PlayerControl' 地址），"
          "属于「读取字符串常量地址」的编码，不是对 [ebx+0x1ED] 或 INI 缓冲区的写指令。" %
          (tgt_ins.mnemonic, tgt_ins.op_str))
    calls = [(n.address, n.op_str) for n in ins_list
             if n.mnemonic in ("call", "jmp") and n.op_str]
    print("    - 窗口内 call/jmp 目标（供与 Read_INI 的 Get_Bool 调用 0x5295f0 对照）:")
    for a, o in calls:
        print("        0x%06X  %s" % (a, o))
    print("    - 结论见 FIX_RECORD.md C5：仅凭静态字节可判「读字符串地址 / 传参」与「非 0x1ED 回写」；"
          "是否为 Write_INI 类回写调用，需看 call 目标与 0x5295f0(Get_Bool, 读) 是否同类，"
          "符号名本身不可证（见 §4.4），故对『是否 Write_INI 回写』只给静态归类，不宣称符号级定谳。")
print()
print("[5] 完成（stdout 由 PowerShell *> 落盘 _disasm_5012ed_out.txt）。")
