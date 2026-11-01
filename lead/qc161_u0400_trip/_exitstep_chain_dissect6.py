#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""退出步进链解剖 v6：IAT 名解析 + 两兄弟函数（0x6BE0xx / 0x6BECxx）判据 + 守卫交叉。

v5 实锤（待登记台账）：
  - 链 = 两个同构「等待对等线程退出」函数：
    A@~0x6BD7C7: 写 exitstate=1 (0x6BE0B6) → pump 循环 0x6BE0DC..E7:
       call [0x7E14AC] / call 0x5D4D50 / cmp [0xA8EDD8],edi / je 回循环
       → 出环后 call 0x5D7E50 / 0x65FD50 / mov ecx,0x87F7E8; call 0x6D0270
       / …20 个 call… / call [0x7E15DC] / call [0x7E15D0]
    B@0x6BEC50+: 同构（exitstate 也写 1 @0x6BEC72）；多出 [0x887640] 双虚表调用（test 守卫！）
  - pump 的返回值被丢弃；**循环闸门是 exitstate 值本身** ⇒ 卡死=无人把 exitstate 推进到 !=1
  - push 0x89A29C（PostQuit 的 hwnd 参数?）——需 IAT 名定夺

本 v6：
  1) 解析 IAT：[0x7E14AC] [0x7E1384] [0x7E15DC] [0x7E15D0] 的导入名
  2) 0x5D4D50 / 0x5D7E50 / 0x6D0270 头字节 + 就近调试串（RA2 二进制普遍带 push "XXX.CPP"）
  3) 全 .text 扫 [0xA8EDD8] 的 cmp/mov 站点（含 disp32 前缀字节分类）
  4) 守卫 12 头（0x724xxx 族）是否落在这两个函数的任何 call 目标里（直接集）
"""
import struct, hashlib
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

GAME_SRC = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020")
GAMEMD = GAME_SRC / "gamemd.exe"
assert hashlib.sha256(GAMEMD.read_bytes()).hexdigest()[:16] == "73201cc021497c95"
DATA = GAMEMD.read_bytes()
BASE = 0x400000
md = Cs(CS_ARCH_X86, CS_MODE_32)
f = lambda v: v - BASE

pe = struct.unpack_from("<I", DATA, 0x3C)[0]
nsec = struct.unpack_from("<H", DATA, pe + 6)[0]
optsz = struct.unpack_from("<H", DATA, pe + 20)[0]
opt = pe + 24
# 数据目录：import 表 = entry[1]
dd_off = opt + 96
imp_rva, imp_size = struct.unpack_from("<II", DATA, dd_off + 8 * 1)
print("ImportDirectory RVA=%08X size=%08X" % (imp_rva, imp_size))

def rva_to_fo(rva):
    for i in range(nsec):
        so = pe + 24 + optsz + i * 40
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", DATA, so + 8)
        if va <= rva < va + max(vsize, rawsize):
            return raw + (rva - va)
    return None

def read_ptr(va):
    return struct.unpack_from("<I", DATA, f(va))[0]

def read_cstr_fo(fo_, maxlen=80):
    end = fo_
    while end < len(DATA) and end - fo_ < maxlen and 0x20 <= DATA[end] < 0x7F:
        end += 1
    return DATA[fo_:end].decode("ascii", "replace")

# 遍历 INT/IAT：IAT 项 VA = BASE + first_thunk_rva + k*4，名由 INT 项查
iat_names = {}
o = rva_to_fo(imp_rva)
while True:
    orig_first, tstamp, fwd, name_rva, first_thunk = struct.unpack_from("<IIIII", DATA, o)
    if name_rva == 0:
        break
    dll = read_cstr_fo(rva_to_fo(name_rva))
    lookup = orig_first if orig_first else first_thunk
    lo = rva_to_fo(lookup)
    k = 0
    while True:
        p, = struct.unpack_from("<I", DATA, lo + k * 4)
        if p == 0:
            break
        if not (p & 0x80000000):
            nm = read_cstr_fo(rva_to_fo(p + 2))
            iat_names[BASE + first_thunk + k * 4] = (dll, nm)
        k += 1
    o += 20
print("\n== 目标 IAT 项名 ==")
for tv in (0x7E14AC, 0x7E1384, 0x7E15DC, 0x7E15D0):
    got = iat_names.get(tv)
    print("  [0x%08X] = %s!%s" % (tv, got[0] if got else "?", got[1] if got else "?"))

# 函数头字节 + 就近调试串
def head_probe(va, label):
    o3 = f(va)
    ins = list(md.disasm(DATA[o3:o3 + 0x20], va))
    print("\n== %s @0x%08X 头 ==" % (label, va))
    for x in ins[:8]:
        print("  %08X  %s %s" % (x.address, x.mnemonic, x.op_str))
    # 头后 0x400 内找 push imm32 指向 .rdata 串
    for x in md.disasm(DATA[o3:o3 + 0x400], va):
        if x.mnemonic == "push" and x.op_str.startswith("0x"):
            pv = int(x.op_str, 16)
            fo2 = f(pv)
            if 0 < fo2 < len(DATA):
                s = read_cstr_fo(fo2)
                if s and (".CPP" in s.upper() or ".H" in s.upper() or "Error" in s):
                    print("   dbg-str @%08X: %r" % (x.address, s))
                    break

head_probe(0x5D4D50, "pump-body(循环内 call)")
head_probe(0x5D7E50, "post-loop #1")
head_probe(0x6D0270, "ecx=0x87F7E8 那个（RC-4 单例!）")
head_probe(0x720770, "ecx=0xA83D10 call")

# 0x89A29C 是什么：读它
for probe in (0x89A29C,):
    fo4 = f(probe)
    s = read_cstr_fo(fo4) if fo4 and fo4 < len(DATA) else None
    print("\n[0x89A29C] 前 32 字节:", DATA[fo4:fo4 + 32].hex(), " ascii=", repr(s))

# 全 .text 扫 exitstate 站点（字节先决）
print("\n== [0xA8EDD8] 全镜像站点 ==")
needle = struct.pack("<I", 0xA8EDD8)
i = f(0x401000)
sites = []
while True:
    j = DATA.find(needle, i, f(0x7E0000))
    if j == -1:
        break
    sites.append(j + BASE + 1)
    i = j + 1
for sv in sites:
    fo5 = f(sv - 2)
    try:
        x = next(md.disasm(DATA[f(sv - 2):f(sv - 2) + 12], sv - 2))
    except StopIteration:
        x = None
    print("  %08X  %s" % (sv - 2, ("%s %s" % (x.mnemonic, x.op_str)) if x else "?"))

# 守卫 12 头是否出现在两兄弟直接 call 集
GUARDS = [0x7241A0, 0x7241F4, 0x724200, 0x72429B, 0x724520, 0x724530, 0x724540,
          0x724580, 0x7245CA, 0x724730, 0x7248AE, 0x724C00]
for rng, lab in ((0x6BD7C7, "A"), (0x6BEC50, "B")):
    o6 = f(rng)
    tgts = set()
    span = 0xA00 if lab == "A" else 0x400
    for x in md.disasm(DATA[o6:o6 + span], rng):
        if x.mnemonic == "call" and x.op_str.startswith("0x"):
            try:
                tgts.add(int(x.op_str, 16))
            except ValueError:
                pass
        if x.mnemonic == "call" and "0x" in x.op_str and "[" in x.op_str:
            pass
    hit = [hex(g) for g in GUARDS if g in tgts]
    print("\n== 函数%s 直接 call 集 ∩ 守卫头 ==", lab, hit if hit else "空")
    if lab == "A":
        # 也看 ecx=0 风险间接调用：call [0x...] 目标解析
        pass
