# -*- coding: utf-8 -*-
"""R-051: 推翻 R-050/H-038 —— TriggerClass 有**专用**注册表 DynamicVectorClass<TriggerClass*> @0xA8EAE8；
R-050 只看到 0xB0F670 一条腿，把「引擎级共享 AbstractClass 注册表」误当成唯一持有容器。

链（gamemd.exe sha256 73201cc0…f67476, read-only；全部窗机器 dump，G-65 工序）:

  TriggerClass ctor 0x725FA0..0x726130（ret 4）向**三个**向量注册 this：
    block1 @0x725FE9 → mov ecx,0xB0F670  (DynamicVector<AbstractClass*>)
    block2 @0x72603A → mov ecx,0xB0F708  (DynamicVector<AbstractClass*>，同一 vptr 0x7E91EC)
    block3 @0x72608D → mov ecx,0xA8EAE8  (**DynamicVector<TriggerClass*>**，vptr 0x7E9BE4)
  三块结构逐字节同构：capacity+count+grow-flag 三查 → `b9 <global>` → `ff 52 08`
  （容器虚槽 2=Add）→ count 自增回写 → `8b 0d <data>` + `89 34 81`（SIB 原始指针存 esi）。

  三容器布局一致（全局单例 .data）：vptr[+0]、data[+4]、capacity[+8]、grow[+0xC]、
  flag[+0xD]、count[+0x10]。

  dtor 0x726950（=vtable 0x7F5858 slot8 @+0x20）对称地三路注销：
    @0x726976 A8EAE8 / @0x7269BF B0F670 / @0x726A08 B0F708，每路 = Find(slot16)
    → count 递减 → SIB 压缩下移，形态三处逐字节同构。

  尾存阳性控制：ctor 全跨度内 `89 34 81` 恰 3 处 = {0x726037, 0x72608A, 0x7260DD}
  ⇒ 「恰三次注册」不是散文，是可数断言。

  推翻要点：R-050 证据 §2 断言「不是专用 trigger 向量」——**错**。0xA8EAE8 的 RTTI
  实参就是 PAVTriggerClass（TD 0x822EA8）。对 GOAL-3T 的实际结论随之升级：
  **遍历 trigger 不需要 WhatAmI 过滤，直接遍历 0xA8EAE8 即可**。

Run:  python re_atlas/tools/r051_trigger_three_registries.py
"""
import hashlib, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

RAW = bytearray(open(EXE, "rb").read())
MUT = {}
for _it in os.environ.get("R051_MUTATE", "").split(","):
    if "=" in _it:
        _k, _v = _it.split("=", 1)
        MUT[int(_k, 0)] = int(_v, 0) & 0xFF

e = struct.unpack_from("<I", RAW, 0x3C)[0]
nsec = struct.unpack_from("<H", RAW, e + 6)[0]
optsz = struct.unpack_from("<H", RAW, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", RAW, opt + 28)[0]
tab = opt + optsz
SEC = []  # (rva, vsize, rawptr, rawsize)
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

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
results = []
def check(tag, ok, msg):
    results.append((tag, ok, msg))
    print(f"{tag} {'PASS' if ok else 'FAIL'}: {msg}", file=sys.stderr)

fp_ok = hashlib.sha256(open(EXE, "rb").read()).hexdigest() == SHA256

G_SHARED1 = 0xB0F670   # DynamicVector<AbstractClass*>
G_SHARED2 = 0xB0F708   # DynamicVector<AbstractClass*>  (second shared registry)
G_TRIG    = 0xA8EAE8   # DynamicVector<TriggerClass*>    <-- dedicated, R-050 missed it
VT_ABS_DYN, VT_ABS_VEC = 0x7E91EC, 0x7E920C
VT_TRG_DYN, VT_TRG_VEC = 0x7E9BE4, 0x7E9C04
CTOR_LO, CTOR_HI = 0x725FA0, 0x726130   # ret 4 at 0x726130 ends ctor
DTOR, VT_MAIN = 0x726950, 0x7F5858

def u32(va):
    return struct.unpack("<I", read(va, 4))[0]

def tdname(td):
    raw = read(td + 8, 120)
    z = raw.find(b"\0")
    return (raw[:z] if z >= 0 else raw).decode("latin1")

def rtti_name(vt):
    return tdname(u32(u32(vt - 4) + 12))

s0, vs0, rp0, rs0 = SEC[0]
TBUF = bytes(RAW[rp0:rp0 + min(vs0, rs0)])
def raw_hits(pat):
    out = []; p = TBUF.find(pat)
    while p != -1:
        out.append(IB + s0 + p); p = TBUF.find(pat, p + 1)
    return out

# ---------- X1 ctor 边界：头 + 尾 ret 4 ----------
X1 = (read(0x725FA0, 5) == bytes.fromhex("53568bf1e8") and
      read(0x726130, 1) == b"\xc2" and read(0x726131, 2) == b"\x04\x00")
check("X1", X1,
      "ctor 边界 0x725FA0（`push ebx;push esi;mov esi,ecx;call`）..0x726131 `ret 4` 逐字节钉")

# ---------- X2 三注册块逐字节（唯一 leg 各一） ----------
B1 = read(0x725FE9, 0x51)
B2 = read(0x72603A, 0x53)
B3 = read(0x72608D, 0x53)
X2 = (B1 == bytes.fromhex(
        "a178f6b000390580f6b0007c2c381d7df6b00075043bc375388b0d84f6b0003bcb"
        "7e2e8b1570f6b00003c85351b970f6b000ff520884c074188b0d80f6b0008bc141"
        "890d80f6b0008b0d74f6b000893481")
      and B2 == bytes.fromhex(
        "a110f7b0008b0d18f7b0003bc87c2c381d15f7b00075043bc375388b0d1cf7b0003bcb"
        "7e2e8b1508f7b00003c85351b908f7b000ff520884c074188b0d18f7b0008bc141"
        "890d18f7b0008b0d0cf7b000893481")
      and B3 == bytes.fromhex(
        "a1f0eaa8008b0df8eaa8003bc87c2c381df5eaa80075043bc375388b0dfceaa8003bcb"
        "7e2e8b15e8eaa80003c85351b9e8eaa800ff520884c074188b0df8eaa8008bc141"
        "890df8eaa8008b0deceaa800893481"))
check("X2", X2,
      "三条注册腿整窗逐字节：block1→0xB0F670 / block2→0xB0F708（皆 DynamicVector<AbstractClass*>）"
      "/ block3→0xA8EAE8（DynamicVector<TriggerClass*>）；三块同构=三查+b9 global+ff5208+count+++893481")

# ---------- X3 尾存恰 3 处（「恰三次注册」可数断言 + 定位对照） ----------
tails = raw_hits(bytes.fromhex("893481"))
tails_in_ctor = [a for a in tails if CTOR_LO <= a <= CTOR_HI]
X3 = (tails_in_ctor == [0x726037, 0x72608A, 0x7260DD])
check("X3", X3,
      f"ctor 全跨度内 `89 34 81`（SIB 原始指针存）恰 3 处 = {[hex(x) for x in tails_in_ctor]}"
      "（全镜像同 pattern 共 %d 处，ctor 外的不作宣称）" % len(tails))

# ---------- X4 三容器 RTTI 定谳（含同 vptr 共表对照 + 降级表） ----------
names = {
    0xB0F670: rtti_name(VT_ABS_DYN),
    0xB0F708: rtti_name(VT_ABS_DYN),
    0xA8EAE8: rtti_name(VT_TRG_DYN),
}
X4 = (rtti_name(VT_ABS_DYN) == ".?AV?$DynamicVectorClass@PAVAbstractClass@@@@" and
      rtti_name(VT_ABS_VEC) == ".?AV?$VectorClass@PAVAbstractClass@@@@" and
      rtti_name(VT_TRG_DYN) == ".?AV?$DynamicVectorClass@PAVTriggerClass@@@@" and
      rtti_name(VT_TRG_VEC) == ".?AV?$VectorClass@PAVTriggerClass@@@@" and
      names[0xA8EAE8] == ".?AV?$DynamicVectorClass@PAVTriggerClass@@@@")
check("X4", X4,
      "RTTI 定谳：0xB0F670 与 0xB0F708 **共用** vptr 0x7E91EC=DynamicVector<AbstractClass*>；"
      "0xA8EAE8 vptr 0x7E9BE4=**DynamicVector<TriggerClass*>**（降级 0x7E9C04=Vector<TriggerClass*>）"
      " ⇒ **推翻 R-050「不是专用 trigger 向量」**")

# ---------- X5 三 vptr 安装/降级 pattern 全段唯一 ----------
inst = {
    0xB0F670: (raw_hits(bytes.fromhex("c70570f6b000ec917e00")), raw_hits(bytes.fromhex("c70570f6b0000c927e00"))),
    0xB0F708: (raw_hits(bytes.fromhex("c70508f7b000ec917e00")), raw_hits(bytes.fromhex("c70508f7b0000c927e00"))),
    0xA8EAE8: (raw_hits(bytes.fromhex("c705e8eaa800e49b7e00")), raw_hits(bytes.fromhex("c705e8eaa800049c7e00"))),
}
X5 = all(len(d) == 1 and len(v) == 1 for d, v in inst.values())
check("X5", X5,
      "三容器各自的 vptr 安装/降级 pattern 全 .text 各唯一 ⇒ 容器类型无第三方改写者："
      + "；".join(f"0x{g:08X}: install {[hex(x) for x in d]} demote {[hex(x) for x in v]}"
                 for g, (d, v) in inst.items()))

# ---------- X6 dtor 三路注销（槽 8 + 三段逐字节） ----------
D_UN = read(0x726976, 0x48), read(0x7269BF, 0x48), read(0x726A08, 0x48)
X6 = (u32(VT_MAIN + 0x20) == DTOR and
      read(0x726950, 0x1E) == bytes.fromhex(
          "51568bf1b201c70658587f00c746043c587f00c7460834587f00c7460c2c") and
      D_UN[0] == bytes.fromhex(
          "8b15e8eaa8008d44240450b9e8eaa80089742408ff521083f8ff742d8b0df8eaa8003bc17d23493bc1"
          "890df8eaa8007d188b0deceaa800408b1481895481fc8b0df8eaa8003bc17c") and
      D_UN[1] == bytes.fromhex(
          "8b1570f6b0008d44240450b970f6b00089742408ff521083f8ff742d8b0d80f6b0003bc17d23493bc1"
          "890d80f6b0007d188b0d74f6b000408b1481895481fc8b0d80f6b0003bc17c") and
      D_UN[2] == bytes.fromhex(
          "8b1508f7b0008d44240450b908f7b00089742408ff521083f8ff742d8b0d18f7b0003bc17d23493bc1"
          "890d18f7b0007d188b0d0cf7b000408b1481895481fc8b0d18f7b0003bc17c"))
check("X6", X6,
      "dtor 0x726950 = vtable 0x7F5858 **slot8**（退化 vptr 四连写 + call 0x7258D0），"
      "随后三路注销逐字节同构（A8EAE8 @0x726976 / B0F670 @0x7269BF / B0F708 @0x726A08）"
      "：Find(slot16) → count-- → SIB 压缩")

# ---------- X7 esi 保全（body 内唯一写点=头部；epilogue 的 pop esi 是恢复不是赋值） ----------
REGWR = {"mov", "lea", "xor", "add", "sub", "and", "or", "sbb", "adc",
         "xchg", "inc", "dec", "not", "neg", "movzx", "movsx", "bswap", "cmpxchg"}
writers = [i.address for i in md.disasm(read(CTOR_LO, 0x72612A - CTOR_LO), CTOR_LO)
           if i.mnemonic in REGWR and i.operands and i.operands[0].type == 1
           and md.reg_name(i.operands[0].reg) == "esi"]
X7 = writers == [0x725FA2]
check("X7", X7,
      f"ctor **body**（0x725FA0..0x72612A，止于 epilogue 前）写 esi 的指令集 == "
      f"{[hex(x) for x in writers]}（唯一=头部 mov esi,ecx）"
      " ⇒ 三个容器入册的都是同一个 TriggerClass this（0x72612E 的 `pop esi` 是 epilogue 恢复，"
      "不计入赋值）")

# ---------- X8 三容器引用量级（引擎级 vs 专用，量纲对照） ----------
c_shared1 = raw_hits(struct.pack("<I", G_SHARED1))
c_shared2 = raw_hits(struct.pack("<I", G_SHARED2))
c_trig = raw_hits(struct.pack("<I", G_TRIG))
X8 = (len(c_shared1) == 116 and len(c_shared2) == 12 and len(c_trig) == 8)
check("X8", X8,
      f"引用量纲明确分化：共享 Abstract 表 0xB0F670={len(c_shared1)} 站、第二共享表 0xB0F708={len(c_shared2)} 站、"
      f"**专用 Trigger 表 0xA8EAE8={len(c_trig)} 站（8，全在 trigger 族内）** ⇒ 专用表才是 trigger 遍历入口")

# ---------- S1 结构性：专用表元素类型自证（WhatAmI 0x26 与表名互证） ----------
S1 = (read(0x726940, 6) == bytes.fromhex("b826000000c3") and
      u32(VT_MAIN + 0x2C) == 0x726940 and
      rtti_name(VT_TRG_DYN).endswith("PAVTriggerClass@@@@"))
check("S1", S1,
      "【结构性·不计数】WhatAmI@0x726940=`mov eax,0x26;ret`=vtable+0x2C 且专用表名以 PAVTriggerClass 结尾"
      " ⇒ 表名与元素类型自洽（遍历无需再筛 WhatAmI）")

UNCOUNTED = {"S1"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = fp_ok and all(ok for _, ok, _ in results)
print(f"\n== R-051 {n_pass}/{n_tot} 字节断言 PASS（S1 结构性不入分母，红仍非零退出）==", file=sys.stderr)
if not fp_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
