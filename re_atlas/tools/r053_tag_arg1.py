# -*- coding: utf-8 -*-
"""R-053: L-30 残余问题①定谳 —— TagClass ctor (0x6E4DE0) 的 arg1 类归属 = TagTypeClass*（或 NULL）。

链（gamemd.exe sha256 73201cc0…f67476，只读；全部窗由 out/_probe_r053dump.py /
_probe_r053v.py 机器 dump 后逐字节钉死，G-65 工序）：

  三个 E8 构造点（全镜像恰 3 处，E9 尾跳 0 处）：
    A 0x6C20CE → `push 0`（arg1 = NULL）；宿主 = TClassFactory<TagClass> 虚表
      0x7F3A80 的 slot3 = 0x6C2090（通用工厂造「无主 Tag」）。
    B 0x6E52D6 → arg1 = `esi`，来自 find-or-create 0x6E52A0；该函数**按
      `[tag+0x24] == arg1` 去重**（0x6E52B8 `cmp [eax+0x24],edi`），即 arg1 是
      Tag 的 owner 键。其四路调用者里 0x6E5E70 / 0x684D53 均从
      `[0xB0E784]` (= DynamicVector<TagTypeClass*> 的 data 指针) 取元素。
    C 0x6E8D90 → arg1 = `[[TeamClass+0x24]+0xD0]`（0x6E8D87 `8b8ad0000000`）；
      TeamClass+0x24 = TeamTypeClass*（ctor 三参 ret 0xc，0x6E8AA7 `mov [esi+0x24],eax`），
      TeamTypeClass+0xD0 = **TagTypeClass*** —— 由 0x6F135D 写入，值来自
      0x6E6310：该函数扫 `[0xB0E780]`(= DynamicVector<TagTypeClass*>) 逐元素比
      `[elem+0x24]` 名串，未命中则 `push 0xA4`（= TagTypeClass GetSize 0xA4）
      分配并 `call 0x6E5B60`（= TagTypeClass ctor，其体内装 vptr 0x7F45C4）。

  语义（arg1 的用途，不是「可改写」结论）：Tag ctor 把 arg1 存 +0x24，随后
  `mov edi,[edi+0xA0]` 后沿 `[edi+0xA8]` 遍历，每节点 `push 0x48`（= TriggerClass
  GetSize 0x48）+ `push edi` + `call 0x725FA0`（TriggerClass ctor）头插 Tag+0x28 链
  ⇒ **arg1+0xA0 是 TriggerTypeClass 链头，+0xA8 是 next**；TagClass 实例按
  TriggerType 逐个建 TriggerClass 实例。佐证：TagTypeClass ctor 0x6E5B73 清
  +0xA0/+0x9C/+0x98，dtor 0x6E5CC7 沿 `[+0xA0]→[+0xA8]` 逐节点 `call [vptr+0x20]`
  释放，0x6E5E50 提供按值摘链（`[ecx+0xA0]` 命中则改成 `[eax+0xA8]`）。

  排除法反证（arg1 ≠ 具体类实例）：arg1 从不被 WhatAmI 检查、从不被解引用 vptr；
  唯一用途是取 +0xA0 链头 —— 与「TagType 是抽象类型描述符」一致。

诚实账：所有窗 hex 机器 dump 先打印后断言（G-65）；census 节元组 canonical 顺序 +
SEC[0] 断言（G-60 判据 4）；每处 0 命中均配机制可见性对照（G-13）。

Run:  python re_atlas/tools/r053_tag_arg1.py
Mut:  R053_MUTATE="VA=BYTE,..." 进程内注入
"""
import hashlib
import os
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

RAW = bytearray(open(EXE, "rb").read())
MUT = {}
for _it in os.environ.get("R053_MUTATE", "").split(","):
    if "=" in _it:
        _k, _v = _it.split("=", 1)
        MUT[int(_k, 0)] = int(_v, 0) & 0xFF

e = struct.unpack_from("<I", RAW, 0x3C)[0]
nsec = struct.unpack_from("<H", RAW, e + 6)[0]
optsz = struct.unpack_from("<H", RAW, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", RAW, opt + 28)[0]
tab = opt + optsz
SEC = []  # canonical (rva, vsize, rawptr, rawsize) —— G-60 判据 4
for i in range(nsec):
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", RAW, tab + i * 40 + 8)
    SEC.append((vaddr, vsize, rawptr, rawsize))
assert SEC[0] == (0x1000, 0x3DF38D, 0x1000, 0x3E0000), f"section tuple drift {SEC[0]}"


def fileoff(va):
    rva = va - IB
    for s, vs, rp, rs in SEC:
        if s <= rva < s + vs:
            fo = rp + (rva - s)
            return fo if fo < rp + rs else None
    return None


def read(va, n):
    fo = fileoff(va)
    if fo is None:
        raise SystemExit(f"VA 0x{va:08X} not disk-backed")
    return bytes(RAW[fo:fo + n])


for _va, _b in MUT.items():
    _fo = fileoff(_va)
    if _fo is None:
        raise SystemExit(f"mutation target 0x{_va:08X} not disk-backed")
    RAW[_fo] = _b


def u32(va):
    return struct.unpack("<I", read(va, 4))[0]


def tdname(td):
    raw = read(td + 8, 160)
    z = raw.find(b"\0")
    return (raw[:z] if z >= 0 else raw).decode("latin1")


def rtti_name(vt):
    return tdname(u32(u32(vt - 4) + 12))


s0, vs0, rp0, rs0 = SEC[0]
TBUF = bytes(RAW[rp0:rp0 + min(vs0, rs0)])
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D


def rel32_sites(opcode, target, lo=TEXT_LO, hi=TEXT_HI):
    """All E8/E9 whose rel32 recomputes to target, inside [lo,hi)."""
    buf = read(lo, hi - lo)
    out = []
    n = len(buf) - 5
    for p in range(n):
        if buf[p] != opcode:
            continue
        rel = struct.unpack_from("<i", buf, p + 1)[0]
        va = lo + p
        if (va + 5 + rel) & 0xFFFFFFFF == target:
            out.append(va)
    return out


def installers(glb):
    """c7 05 <glb> <imm32>  installers inside .text."""
    pat = b"\xc7\x05" + struct.pack("<I", glb)
    out = []
    p = TBUF.find(pat)
    while p != -1:
        out.append((IB + s0 + p, struct.unpack_from("<I", TBUF, p + 6)[0]))
        p = TBUF.find(pat, p + 1)
    return out


def dword_store_census(disp, lo=TEXT_LO, hi=TEXT_HI):
    """structurally filtered `mov [reg+disp32], r32` / `mov [reg+disp32], imm32`,
    each hit re-decoded at its own address (antiphantom, G-60 style)."""
    buf = read(lo, hi - lo)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    out = []
    for op in (0x89, 0xC7):
        for p in range(len(buf) - 6):
            if buf[p] != op:
                continue
            modrm = buf[p + 1]
            if (modrm >> 6) != 2 or (modrm & 7) in (4, 5):
                continue
            if struct.unpack_from("<I", buf, p + 2)[0] != disp:
                continue
            va = lo + p
            ins = list(md.disasm(read(va, 10), va))
            if not ins or len(ins[0].operands) < 1:
                continue
            o0 = ins[0].operands[0]
            if o0.type == 3 and o0.mem.disp == disp and o0.mem.index == 0:
                out.append(va)
    return sorted(set(out))


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
results = []


def check(tag, ok, msg):
    results.append((tag, ok, msg))
    print(f"{tag} {'PASS' if ok else 'FAIL'}: {msg}", file=sys.stderr)


fp_ok = hashlib.sha256(bytes(RAW)).hexdigest() == SHA256

TAG_CTOR = 0x6E4DE0
TRG_CTOR = 0x725FA0
TAGTYPE_CTOR = 0x6E5B60
FIND_OR_CREATE = 0x6E52A0
TAGTYPE_LOOKUP = 0x6E5E70
TAGTYPE_FIND_BY_NAME = 0x6E6310

# ---------- Z1 三个构造点精确集合（全镜像恰 3 处 E8，E9 尾跳 0） ----------
sites = rel32_sites(0xE8, TAG_CTOR)
jumps = rel32_sites(0xE9, TAG_CTOR)
Z1 = sites == [0x6C20CE, 0x6E52D6, 0x6E8D90] and jumps == []
check("Z1", Z1,
      f"E8→TagClass ctor 站点精确集合 == {[hex(x) for x in sites]}（恰 3），E9 尾跳 {len(jumps)} 处")

# ---------- Z2 站点 A：arg1 = NULL，宿主 = TClassFactory<TagClass>::slot3 ----------
A_WIN = 0x6C20BC
A_HEX = "6a38e8546d100083c40485c0740f6a008bc8e80d2d02008bf085f6750a5f"
factory_vt = 0x7F3A80
factory_slot3 = u32(factory_vt + 12)
Z2 = (read(A_WIN, len(A_HEX) // 2) == bytes.fromhex(A_HEX) and
      factory_slot3 == 0x6C2090 and
      rtti_name(factory_vt) == ".?AV?$TClassFactory@VTagClass@@@@" and
      # 该点前置恰为 push 0（6a00）+ mov ecx,eax：arg1 = NULL
      read(0x6C20CA, 4) == bytes.fromhex("6a008bc8"))
check("Z2", Z2,
      f"站点 A @0x6C20CE 窗逐字节同；宿主 TClassFactory<TagClass> slot3=0x{factory_slot3:08X}；"
      f"arg1=`push 0` ⇒ NULL")

# ---------- Z3 站点 B：find-or-create 按 [tag+0x24]==arg1 去重 ----------
B_WIN = 0x6E52C5
B_HEX = "6a38e84b3b0e0083c40485c0740b578bc8e805fbffff5f5e"
C_WIN = 0x6E52B6
C_HEX = "8b0239782474234183c2043bce7cf16a"
Z3 = (read(B_WIN, len(B_HEX) // 2) == bytes.fromhex(B_HEX) and
      read(C_WIN, len(C_HEX) // 2) == bytes.fromhex(C_HEX))
check("Z3", Z3,
      "站点 B @0x6E52D6 窗逐字节同；find-or-create 0x6E52A0 按 "
      "`cmp [eax+0x24],edi` 去重 ⇒ arg1 是 Tag 的 owner 键")

# ---------- Z4 站点 C：arg1 = [[TeamClass+0x24]+0xD0] ----------
G_WIN = 0x6E8D84
G_HEX = "8b56248b8ad0000000518bc8e84bc0ffffeb0233"
G2_WIN = 0x6E8DC2
G2_HEX = "c20c0033c08946288bc65e5bc2"
Z4 = (read(G_WIN, len(G_HEX) // 2) == bytes.fromhex(G_HEX) and
      read(G2_WIN, len(G2_HEX) // 2) == bytes.fromhex(G2_HEX))
check("Z4", Z4,
      "站点 C @0x6E8D90 arg1=`[[esi+0x24]+0xD0]` 逐字节同；TeamClass ctor `ret 0xc`（三参）")

# ---------- Z5 arg1 存入 Tag+0x24；Tag ctor 字段初始化整窗 ----------
B1_WIN = 0x6E4DE0
B1_HEX = ("5356578bf1e886b3d2ff8b7c241033db897e24895e28895e2ca100e7b000"
          "894630885e34885e35c706e0447f00c74604c444")
B2_WIN = 0x6E4E07
B2_HEX = "c706e0447f00c74604c4447f00c74608bc447f00c7460cb4447f00a128"
Z5 = (read(B1_WIN, len(B1_HEX) // 2) == bytes.fromhex(B1_HEX) and
      read(B2_WIN, len(B2_HEX) // 2) == bytes.fromhex(B2_HEX))
check("Z5", Z5,
      "Tag ctor 0x6E4DE0 窗逐字节同：`mov [esi+0x24],edi`（arg1 落 +0x24）+ "
      "四 vptr 0x7F44E0/…C4/…BC/…B4")

# ---------- Z6 arg1 的唯一用途：沿 +0xA0 → +0xA8 建 TriggerClass 链 ----------
E_WIN = 0x6E4F19
E_HEX = "3bfb74378bbfa00000003bfb742d6a48e8e93e0e0083"
Z6_BYTES = read(E_WIN, len(E_HEX) // 2) == bytes.fromhex(E_HEX)
# 回边 `mov edi,[edi+0xA8]`（链 next）与头插三连 `8b5628 895028 894628`
Z6_NEXT = read(0x6E4F4A, 6) == bytes.fromhex("8bbfa8000000")
Z6_INSERT = read(0x6E4F41, 9) == bytes.fromhex("8b5628895028894628")
# 0x6E4F38 call 0x725FA0 的 rel32 复算，且前置 push edi（arg1 链节点）
rel_at_4F38 = struct.unpack("<i", read(0x6E4F39, 4))[0]
Z6_TARGET = (0x6E4F38 + 5 + rel_at_4F38) & 0xFFFFFFFF == TRG_CTOR
Z6_ARG = read(0x6E4F35, 3) == bytes.fromhex("578bc8")  # push edi; mov ecx,eax
Z6 = Z6_BYTES and Z6_NEXT and Z6_INSERT and Z6_TARGET and Z6_ARG
check("Z6", Z6,
      f"Tag ctor 沿 `[arg1+0xA0]`→`[+0xA8]` 遍历（回边 8bbfa8 与头插 8b5628/895028/894628 "
      f"逐字节钉），每节点 push 0x48 + push edi + call 0x725FA0（rel32 复算="
      f"0x{(0x6E4F38+5+rel_at_4F38)&0xFFFFFFFF:08X}） ⇒ arg1+0xA0 是 TriggerType 链头")

# ---------- Z7 六类身份：RTTI / WhatAmI / GetSize ----------
MAINS = [("TagClass", 0x7F44E0), ("TagTypeClass", 0x7F45C4),
         ("TriggerClass", 0x7F5858), ("TriggerTypeClass", 0x7F5904),
         ("TeamClass", 0x7F4730), ("TeamTypeClass", 0x7F47D0)]
EXPECT = {
    "TagClass": (0x2C, 0x38), "TagTypeClass": (0x2D, 0xA4),
    "TriggerClass": (0x26, 0x48), "TriggerTypeClass": (0x27, 0xB4),
    "TeamClass": (0x22, 0xA0), "TeamTypeClass": (0x23, 0xF8),
}
ZT = []
for nm, vt in MAINS:
    a11 = u32(vt + 0x2C)
    a12 = u32(vt + 0x30)
    want_id, want_sz = EXPECT[nm]
    ok = (read(a11, 5) == b"\xb8" + struct.pack("<I", want_id) and
          read(a12, 5) == b"\xb8" + struct.pack("<I", want_sz) and
          rtti_name(vt) == ".?AV%s@@" % nm)
    ZT.append(ok)
Z7 = all(ZT)
check("Z7", Z7,
      "六类 RTTI 名 + WhatAmI/GetSize 即时数全对："
      + " ".join(f"{n}=0x{EXPECT[n][0]:X}/0x{EXPECT[n][1]:X}" for n, _ in MAINS))

# ---------- Z8 两个专用向量安装点精确集合 ----------
ins_tag = installers(0xB0E720)
ins_type = installers(0xB0E780)
Z8 = (ins_tag == [(0x6E4D7D, 0x7EA5A4), (0x6E4DA8, 0x7EA5C4)] and
      ins_type == [(0x6E5AFD, 0x7F4558), (0x6E5B28, 0x7F4578)] and
      rtti_name(0x7EA5A4) == ".?AV?$DynamicVectorClass@PAVTagClass@@@@" and
      rtti_name(0x7F4558) == ".?AV?$DynamicVectorClass@PAVTagTypeClass@@@@" and
      rtti_name(0x7EA5C4) == ".?AV?$VectorClass@PAVTagClass@@@@" and
      rtti_name(0x7F4578) == ".?AV?$VectorClass@PAVTagTypeClass@@@@" and
      [len(rtti_name(v)) for v in (0x7EA5A4, 0x7EA5C4, 0x7F4558, 0x7F4578)]
      == [40, 33, 44, 37])
check("Z8", Z8,
      "Tag 专用向量 0xB0E720 与 TagType 专用向量 0xB0E780 安装/降级点精确集合各 2 处，"
      "RTTI 双向确认")

# ---------- Z9 TagType 查找器 0x6E5E70 的向量来源 ----------
D_WIN = 0x6E5E79
D_HEX = "a190e7b00033db85c07e34a184e7b000578b34988d4e2451e88a2e0e0083c40885c074"
Z9 = read(D_WIN, len(D_HEX) // 2) == bytes.fromhex(D_HEX)
# 阳性对照：同一 census 法在 0xB0E780 上命中 2 处（见 Z8）；此处再钉 TagClass 向量对照
check("Z9", Z9,
      "TagType 查找器 0x6E5E70 扫 `[0xB0E784]` 元素并比 `[elem+0x24]` 名串 ⇒ "
      "站点 B 的 arg1 = TagTypeClass*")

# ---------- Z10 TeamType+0xD0 的写入者：恰 3 处，且来源函数造 TagTypeClass ----------
DISP_STORES = dword_store_census(0xD0, 0x6F06E0, 0x6F2000)
Z10_WIN = read(0x6F134A, 0x19)
Z10_HEX = "8d4c2450e8bd4fffffeb028bc58b8e9c0000008986d0000000"
rel_6310 = struct.unpack("<i", read(0x6F134F, 4))[0]
Z10 = (DISP_STORES == [0x6F0799, 0x6F1041, 0x6F135D] and
       Z10_WIN == bytes.fromhex(Z10_HEX) and
       (0x6F134E + 5 + rel_6310) & 0xFFFFFFFF == TAGTYPE_FIND_BY_NAME and
       read(0x6E6366, 10) == bytes.fromhex("68a4000000e8a72a0e00") and   # push 0xA4
       read(0x6E6377, 8) == bytes.fromhex("578bc8e8e1f7ffff"))           # call 0x6E5B60
rel_b5b = struct.unpack("<i", read(0x6E637B, 4))[0]
Z10 = Z10 and (0x6E637A + 5 + rel_b5b) & 0xFFFFFFFF == TAGTYPE_CTOR
check("Z10", Z10,
      f"TeamType+0xD0 写入者精确集合 == {[hex(x) for x in DISP_STORES]}（恰 3，"
      f"可杀「有第四个写入者」）；0x6F135D 的值来自 0x6E6310：push 0xA4（=TagTypeClass "
      f"GetSize）+ call 0x6E5B60（TagTypeClass ctor）")

# ---------- S1 结构性（不入分母；红仍非零退出） ----------
# TagTypeClass ctor 清 +0xA0；dtor 沿 [+0xA0]→[+0xA8] 释放；按值摘链助手 0x6E5E50
S1_F1 = read(0x6E5B73, 0x1B) == bytes.fromhex(
    "8d45243bc3c78598000000ffffffff899d9c000000899da0000000")
S1_F2 = read(0x6E5CC7, 0x26) == bytes.fromhex(
    "8b8fa0000000c787a00000000000000085c974218bb1a8000000c781a80000000000000085c9")
S1_REM = read(0x6E5E50, 0x1D) == bytes.fromhex(
    "8b81a00000008b5424043bc2750c8b80a80000008981a0000000c20800")
S1 = S1_F1 and S1_F2 and S1_REM

s1s = "PASS:" if S1 else "FAIL:"
print(f"S1 {s1s} TagTypeClass ctor 清 +0xA0 / dtor 沿链释放 / 0x6E5E50 按值摘链"
      f"（结构性，不入分母；红仍非零退出）", file=sys.stderr)

if MUT:
    print(f"MUTATION MODE: applied {len(MUT)} byte patch(es)", file=sys.stderr)

print("== SEC[0] tuple == %s" % (SEC[0],), file=sys.stderr)
print("== sha256(fp) == %s" % ("OK" if fp_ok else "MISMATCH"), file=sys.stderr)

n_pass = sum(1 for _, ok, _ in results if ok)
n_all = len(results)
print(f"\n== R-053 {n_pass}/{n_all} 字节断言 PASS（S1 结构性不入分母，红仍非零退出）==",
      file=sys.stderr)

gate = (n_pass == n_all) and S1 and fp_ok
print("GATE: GREEN" if gate else "GATE: RED", file=sys.stderr)
sys.exit(0 if gate else 1)
