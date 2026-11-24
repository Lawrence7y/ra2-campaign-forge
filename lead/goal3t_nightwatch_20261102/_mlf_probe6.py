# -*- coding: utf-8 -*-
"""§533 probe F -- 追 [0xA8B230]+0x62C 的类身份与写点（第二条「帧不推进」出口）。

只读 gamemd.exe。零真机、零写入（除 stdout）。

已钉（probe B/E）：
  0x55D7C2  mov eax,[0xA8B238]      ; GameMode
  0x55D7C7  test eax,eax ; je -> 0x55D7D4   (Mode==0 Campaign)
  0x55D7CB  cmp eax,5    ; je -> 0x55D7D4   (Mode==5 Skirmish)
  0x55D7CE  jne 0x55D878             ; 其它 Mode -> 正常帧体
  0x55D821  mov eax,[0xA8B230]
  0x55D826  mov ecx,[eax+0x62C]
  0x55D82C  test ecx,ecx
  0x55D82E  je 0x55D878              ; ==0 -> 正常帧体（会走 inc）
  0x55D830  .. pump / 0x48D080 / 0x53B560 / vtable+0x5C / 0x4F4480 / LogicUpdate(0x55E160)
  0x55D877  ret                      ; ★ 帧号不推进，但世界更新照跑

本探针：0xA8B230 的类身份、+0x62C 的读写点、以及它是不是「暂停」语义。
"""
import hashlib
import struct
from collections import defaultdict

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == EXPECT_SHA, "image drift"

e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    nm = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append((nm, IB + va, vsz, rp, rsz))
TEXT = next(s for s in SEC if s[0] == ".text")
TLO, THI = TEXT[1], TEXT[1] + TEXT[4]
DATA = next(s for s in SEC if s[0] == ".data")


def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            off = rp + (va - sva)
            return off if off < rp + rsz else None
    return None


def rd(va, n):
    o = fo(va)
    return raw[o:o + n] if o is not None else b"\0" * n


print("sections:")
for nm, sva, vsz, rp, rsz in SEC:
    print("  %-9s VA=[%08X,%08X) raw_off=%07X raw_sz=%07X %s" % (
        nm, sva, sva + vsz, rp, rsz, "BSS(虚>实)" if vsz > rsz else ""))

# ---- 0xA8B230 初值 ---------------------------------------------------------
print()
print("=" * 74)
print("T1 [0xA8B230] 磁盘初值（.data 内则非零；BSS 则 0）")
print("=" * 74)
o = fo(0xA8B230)
print("  file_off=%s value=%08X" % (o, struct.unpack_from("<I", rd(0xA8B230, 4), 0)[0]))

# ---- 写点普查（mov [0xA8B230], reg / c7 05） -------------------------------
print()
print("=" * 74)
print("T2 [0xA8B230] 的**写**点普查（全镜像）")
print("=" * 74)
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
b = rd(TLO, THI - TLO)
writes, reads = [], []
for ins in MD.disasm(b, TLO):
    try:
        ops = ins.operands
    except Exception:
        continue
    if not ops:
        continue
    d = ops[0]
    if d.type != 3:      # x86_op_type X86_OP_MEM
        continue
    # mem operand with disp == 0xA8B230 and no base/index
    mem = d.mem
    if mem.disp == 0xA8B230 and mem.base == 0 and mem.index == 0:
        is_write = ins.mnemonic in ("mov", "movzx", "movsx", "and", "or", "xor",
                                    "add", "sub", "inc", "dec", "push")
        (writes if is_write else reads).append((ins.address, ins.mnemonic, ins.op_str,
                                                ins.bytes.hex()))
print("  absolute [0xA8B230] 直接访存: write-candidate=%d read=%d" % (len(writes), len(reads)))
for w in writes[:25]:
    print("   W %08X  %-20s %-7s %s" % w)

# ---- [+0x62C] 全镜像 disp32 形态 -------------------------------------------
print()
print("=" * 74)
print("T3 [+0x62C] / [+0x620] / [+0x628] / [+0x630] disp32 全镜像命中")
print("=" * 74)
for disp in (0x620, 0x624, 0x628, 0x62C, 0x630):
    hits = []
    for ins in MD.disasm(b, TLO):
        try:
            ops = ins.operands
        except Exception:
            continue
        for op in ops:
            if op.type == 3 and op.mem.disp == disp:
                mr = "W" if (op.access & 2) else "R"
                hits.append((ins.address, mr, ins.mnemonic, ins.op_str))
                break
    print("  +0x%03X : %d 处" % (disp, len(hits)))
    for h in hits[:12]:
        print("     %s %08X  %-7s %s" % (h[1], h[0], h[2], h[3]))
