#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""退出步进链解剖 v5：真头回溯（trampoline 判据）、esi 来源全列、名字串按段表读、exitstate 消费者。

v4 教训（登记）：
  - 0x6BD700 前无 CC 填充也无 prologue ⇒ 链不是以 0x6BD7C7 处独立函数开头，
    头部在更前或是长函数中段。用「trampoline 判据」找：前一函数以 E9 rel32 jmp
    开头 = 新函数头。
  - DATA.find 用 file offset，别再拿 VA 当索引（v3 死因）。
  - 0x6C7400 本体解码错位（头部即 je 开头可疑），须用函数头对齐再核。
关键新证据（v4 字节读）：0x6BD76E `mov esi,[0x81C1D0]`；被守卫的 8 头全在
  0x724xxx 与 0x6C14C0..0x6C3740 直接 call 集**不相交**。
"""
import struct, hashlib
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

GAME_SRC = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020")
GAMEMD = GAME_SRC / "gamemd.exe"
assert hashlib.sha256(GAMEMD.read_bytes()).hexdigest()[:16] == "73201cc021497c95"
DATA = GAMEMD.read_bytes()
BASE = 0x400000
WRITER = 0x6BE0B6
md = Cs(CS_ARCH_X86, CS_MODE_32)
f = lambda v: v - BASE

# 段表（v2 已证）
pe_off = struct.unpack_from("<I", DATA, 0x3C)[0]
nsec = struct.unpack_from("<H", DATA, pe_off + 6)[0]
opt_size = struct.unpack_from("<H", DATA, pe_off + 20)[0]
IMAGE_BASE = struct.unpack_from("<I", DATA, pe_off + 24 + 28)[0]
secs = []
for i in range(nsec):
    so = pe_off + 24 + opt_size + i * 40
    name = DATA[so:so + 8].rstrip(b"\0").decode("ascii", "replace")
    vsize, va, rawsize, raw = struct.unpack_from("<IIII", DATA, so + 8)
    secs.append((name, IMAGE_BASE + va, vsize, raw, rawsize))
def va_to_fo(va):
    for name, sva, svsize, sraw, srawsize in secs:
        if sva <= va < sva + max(svsize, srawsize):
            return sraw + (va - sva)
    return None

# ---- 真头：在 .text 里找 push ebp; mov ebp,esp 且 [ebp-0xa34] 出现在其后 ----
pat = bytes.fromhex("558bec")
cands = []
i = f(0x6B8000)
endw = f(WRITER)
while True:
    j = DATA.find(pat, i, endw)
    if j == -1:
        break
    va = j + BASE
    blob = DATA[j:j + 0x60]
    # lea ecx,[ebp-0xa34] = 8D 8D CC F5 FF FF（-0xa34 的补码）
    m_a34 = b"\x8d\x8d\xcc\xf5\xff\xff"
    hit_a34 = m_a34 in DATA[j:j + 0x400]
    cands.append((va, hit_a34, DATA[j - 1] if j else None))
    i = j + 1
print("== push ebp;mov ebp,esp 候选（0x6B8000..WRITER），含[ebp-0xa34]者： ==")
for va, h34, prev in cands:
    if h34:
        print("   %08X  prevbyte=%02X  <== 有 lea ecx,[ebp-0xa34]" % (va, prev))
head = None
for va, h34, prev in cands:
    if h34:
        head = va  # 取最后一个含 a34 的（最近）
print("采用真头 =", hex(head) if head else None)

if head:
    o = f(head)
    ins_all = list(md.disasm(DATA[o:o + 0x1500], head))
    cut = [n for n, x in enumerate(ins_all) if x.address > WRITER + 0x120]
    if cut:
        ins_all = ins_all[:cut[0]]
    print("\n== 序言 20 条 ==")
    for x in ins_all[:20]:
        print("  %08X  %s %s" % (x.address, x.mnemonic, x.op_str))
    print("\n== 全部 mov esi,*（callee 指针装载点） ==")
    for x in ins_all:
        if x.mnemonic == "mov" and x.op_str.startswith("esi,"):
            print("  %08X  mov %s" % (x.address, x.op_str))

# 名字串：用段表读 file offset，取 0x7e8000..0x7ea000 的 push
print("\n== push 名字串（段表定位，取块区 0x6BD7C7..0x6BE0C0） ==")
o2 = f(0x6BD7C7)
names = []
for x in md.disasm(DATA[o2:o2 + 0x900], 0x6BD7C7):
    if x.mnemonic == "push" and x.op_str.startswith("0x"):
        try:
            pv = int(x.op_str, 16)
        except ValueError:
            continue
        fo_ = va_to_fo(pv)
        if fo_ is None:
            continue
        raw = DATA[fo_:fo_ + 40]
        a = b""
        k = 0
        while k < len(raw) and 0x20 <= raw[k] < 0x7F:
            a += bytes([raw[k]]); k += 1
        s = a.decode("ascii", "replace")
        if len(s) >= 2:
            names.append((x.address, pv, s))
seen = set()
for a, pv, s in names:
    if pv not in seen:
        seen.add(pv)
        print("  @%08X push %08X = %r" % (a, pv, s))

# exitstate 消费者：全 .text 找 disp a8 ed d8 00（cmp/test/jz 之后跟 ret 的块）
print("\n== exitstate [0xA8EDD8] 全镜像读写点（字节先决 + 对齐分类） ==")
needle = struct.pack("<I", 0xA8EDD8)
hits = []
i = f(BASE + 0x1000)
while True:
    j = DATA.find(needle, i, f(BASE + 0x3E0000))
    if j == -1:
        break
    hits.append(j + BASE)
    i = j + 1
for h in hits:
    va = h - 1  # disp 起于 modrm 后一字节
    fo_ = va_to_fo(va)
    try:
        ins = next(md.disasm(DATA[fo_:fo_ + 16], va))
    except StopIteration:
        ins = None
    print("  disp@%08X  ins=%s" % (h, ("%08X %s %s" % (ins.address, ins.mnemonic, ins.op_str)) if ins else "?"))

# 0x6C7400 真头对齐解码（找它自己的 prologue）
print("\n== 0x6C7400 头前 8 字节（判真头） ==")
print("  ", DATA[f(0x6C73F0):f(0x6C7400) + 8].hex())
o3 = f(0x6C7400)
for n, x in enumerate(md.disasm(DATA[o3:o3 + 0x60], 0x6C7400)):
    print("  %08X  %s %s" % (x.address, x.mnemonic, x.op_str))
    if n > 14:
        break

# 守卫 8 头 vs 直接 call 集
GUARDS = {0x7241A0, 0x7241F4, 0x724200, 0x72429B, 0x724520, 0x724530, 0x724540, 0x724580, 0x7245CA, 0x724730, 0x7248AE, 0x724C00}
direct = set()
if head:
    for x in ins_all:
        if x.mnemonic == "call" and x.op_str.startswith("0x"):
            try:
                direct.add(int(x.op_str, 16))
            except ValueError:
                pass
inter = direct & GUARDS
print("\n== 直接 call 集 ∩ 守卫头集 ==", sorted(hex(a) for a in inter) if inter else "空")
