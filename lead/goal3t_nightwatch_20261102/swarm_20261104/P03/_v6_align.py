# -*- coding: utf-8 -*-
"""V-P03 探针 6：MLF 尾部旗标链对齐判定（纯原始字节，两种对齐各自的 jne 目标一致性）"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
raw = eng.rd(0x55DE40, 0x34)
print("[raw 0x55DE40..0x55DE74]")
for k in range(0, len(raw), 16):
    print("   0x%08x: %s" % (0x55DE40 + k, raw[k:k+16].hex(" ")))

# 假说 A（engine 流对齐）：0x55DE60 起指令 = 67 A0 C0 41 / 8B 00 / 84 C0 / 75 5E / ...
# 假说 B（旗标链对齐）：0x55DE61 起指令 = A0 C0 41 8B 00 / 84 C0 / 75 5E（jne→0x55DEC8）
# 判定：从 0x55DE5B 与 0x55DE5C 分别起解，看哪条链上所有 jcc 目标都落在合法位置
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
for start in (0x55DE50, 0x55DE51, 0x55DE52, 0x55DE53, 0x55DE54, 0x55DE55, 0x55DE56,
              0x55DE57, 0x55DE58, 0x55DE59, 0x55DE5A, 0x55DE5B, 0x55DE5C, 0x55DE5D,
              0x55DE5E, 0x55DE5F, 0x55DE60, 0x55DE61):
    off = start - 0x55DE40
    blob = raw[off:]
    ins = list(md.disasm(blob, start))
    txt = []
    ok = True
    for i in ins[:8]:
        tgt = ""
        if i.mnemonic.startswith("j") and i.operands and i.operands[0].type == 2:
            t = i.operands[0].imm
            tgt = "->0x%x%s" % (t, "OK" if t in (0x55DEC8, 0x55DE9A) else "??")
        txt.append("0x%x:%s%s" % (i.address, i.mnemonic, tgt))
        if i.address >= 0x55DE74: break
    print("start=0x%x: %s" % (start, " | ".join(txt)))

# 检查旗标字节模式 A0 xx xx xx 00 / 84 C0 / 75 rel (rel→0x55DEC8) 在 0x55DE40..0x55DE75 内
print()
print("[flag-check pattern scan: A0 d32 | 84 C0 | 75 rel, target=0x55DEC8]")
for p in range(0x55DE40, 0x55DE70):
    b = eng.rd(p, 9)
    if b[0] == 0xA0 and b[5:7] == b"\x84\xc0" and b[7] == 0x75:
        rel = struct.unpack_from("<b", b, 8)[0]
        tgt = p + 9 + rel
        addr = struct.unpack_from("<I", b, 1)[0]
        print("   0x%x: mov al,[0x%x]; test al,al; jne ->0x%x %s" % (p, addr, tgt, "OK" if tgt == 0x55DEC8 else "??"))
# 也匹配 cmp byte [g],0 / jne 形态 (80 3D d32 00 / 75 rel)
for p in range(0x55DE40, 0x55DE70):
    b = eng.rd(p, 8)
    if b[0] == 0x80 and b[1] == 0x3D and b[6] == 0x00 and b[7] == 0x75:
        rel = struct.unpack_from("<b", b, 8)[0]
        tgt = p + 8 + rel
        addr = struct.unpack_from("<I", b, 2)[0]
        print("   0x%x: cmp byte [0x%x],0; jne ->0x%x %s" % (p, addr, tgt, "OK" if tgt == 0x55DEC8 else "??"))
