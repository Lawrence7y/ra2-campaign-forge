# -*- coding: utf-8 -*-
"""R-050: L-30 残量再收口 —— TriggerClass 注册表容器定谳 =
DynamicVectorClass<AbstractClass*> @0xB0F670（不是 <TriggerClass*>！G-62 同族：
持有 Trigger 实例的容器，静态类型参数是 AbstractClass*）。

链（gamemd.exe sha256 73201cc0…f67476, read-only; 窗全部机器 dump 自
tools/_probe_r050_registry.py，G-65 工序）:

  W1 全局 ctor 0x725350 整窗 0x3D：清零 [0xB0F674/78/80]、grow 旗标 [0xB0F67C]=1、
     [0xB0F67D]=0、vptr=0x7E91EC、cap [0xB0F684]=0xA，call atexit 助手（rel32 复算 0x7C978A）。
  W2 vptr 安装/降级两 pattern 全 .text 唯一（raw-find == 1 站 each）。
  W3 RTTI 名定谳：vt->COL(vt-4)->TD(COL+12)->name(TD+8)：
     0x7E91EC='.?AV?$DynamicVectorClass@PAVAbstractClass@@@@'、
     0x7E920C='.?AV?$VectorClass@PAVAbstractClass@@@@'；
     阳性对照=同法解 House 对（0x7E9EE4/0x7E9F04 ⇒ PAVHouseClass，R-043 在册）；
     反证对照='PAVTriggerClass' 名串在镜像存在、但 0xB0F670 装的**不是**它。
  W4 全局 dtor 0x725390 窗（降级 c7 05→0x7E920C）与 House 降级站 0x4E6D28 同形态。
  W5 TriggerClass ctor 注册块 0x725FE9..0x726037：容量查 [0xB0F680]<cap[0xB0F684]、
     grow 查旗标 [0xB0F67D]、`mov ecx,0xB0F670` + `call [edx+8]`（容器虚槽 2=Add，
     与 R-043 House 向量 [edx+8] 同形）、计数自增、尾 `mov ecx,[0xB0F674]; mov
     [ecx+eax*4], esi`（SIB 89 34 81 原始指针存储）。
  W6 esi 保全：ctor 头..存点之间唯一写 esi 的指令 = 头 `mov esi,ecx`（capstone
     寄存器目的谓词——首版探针谓词把「内存基址 esi」当「写 esi」，虚警 0 条，
     修正后真值：0x725FA2 唯一）⇒ 入册值 = TriggerClass 的 this。
  W7 全局用量 census：`mov ecx,0xB0F670`（b9 70f6b000）全 .text == 58 站含 0x726016
     ⇒ 引擎级共享注册表（非 trigger 专属）；「遍历全部 trigger」= 遍历此向量筛
     WhatAmI==0x26（slot11 契约 kb/20）。

诚实账: W0 指纹、S1 结构性（名串存在性=字符串事实）不计数但红⇒非零退出；
变异预期先实测后写死（R-04x 流程）。

Run:  python re_atlas/tools/r050_trigger_registry.py
"""
import hashlib, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

RAW = bytearray(open(EXE, "rb").read())
MUT = {}
for _it in os.environ.get("R050_MUTATE", "").split(","):
    if "=" in _it:
        _k, _v = _it.split("=", 1)
        MUT[int(_k, 0)] = int(_v, 0) & 0xFF

e = struct.unpack_from("<I", RAW, 0x3C)[0]
nsec = struct.unpack_from("<H", RAW, e + 6)[0]
optsz = struct.unpack_from("<H", RAW, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", RAW, opt + 28)[0]
tab = opt + optsz
SEC = []  # (rva, vsize, rawptr, rawsize)  ← canonical order
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
VT_DYN, VT_VEC = 0x7E91EC, 0x7E920C
HVT_DYN, HVT_VEC = 0x7E9EE4, 0x7E9F04
GLOB = 0xB0F670

def u32(va):
    return struct.unpack("<I", read(va, 4))[0]

def tdname(td):
    raw = read(td + 8, 120)
    z = raw.find(b"\0")
    return (raw[:z] if z >= 0 else raw).decode("latin1")

def rtti_name(vt):
    return tdname(u32(u32(vt - 4) + 12))

# ---------- W1 全局 ctor 整窗 + atexit rel32 ----------
b = read(0x725350, 0x3D)
# e8 sits at window idx 0x36 -> rel32 bytes at 0x37..0x3A; next insn VA = 0x725350+0x3B = 0x72538B
rel = struct.unpack_from("<i", b, 0x37)[0]
tgt = 0x72538B + rel
W1 = (b == bytes.fromhex(
        "33c06890537200a374f6b000a378f6b000c6057cf6b00001a27df6b000c70570f6b000ec917e00"
        "c70584f6b0000a000000a380f6b000e8ff430a0059c3") and tgt == 0x7C978A)
check("W1", W1,
      f"全局 ctor 0x725350 整窗 0x3D（vptr 0x7E91EC / cap 0xA / grow 旗标 / atexit push 0x725390，"
      f"rel32 复算=0x{tgt:08X}=atexit 助手）")

# ---------- W2 安装/降级 pattern 全 .text 唯一 ----------
s, vs, rp, rs = SEC[0]
tbuf = bytes(RAW[rp:rp + min(vs, rs)])
def raw_hits_all(pat):
    out = []; p = tbuf.find(pat)
    while p != -1:
        out.append(IB + s + p); p = tbuf.find(pat, p + 1)
    return out
h1 = raw_hits_all(bytes.fromhex("c70570f6b000ec917e00"))
h2 = raw_hits_all(bytes.fromhex("c70570f6b0000c927e00"))
W2 = (h1 == [0x72536D] and h2 == [0x725398])
check("W2", W2,
      f"vptr 安装 pattern 唯一站 {h1} + 降级 pattern 唯一站 {h2}（raw-find 全段，唯一性=注册表单写主双站）")

# ---------- W3 RTTI 名定谳 + 阳性对照 + 反证对照 ----------
W3 = (rtti_name(VT_DYN) == ".?AV?$DynamicVectorClass@PAVAbstractClass@@@@" and
      rtti_name(VT_VEC) == ".?AV?$VectorClass@PAVAbstractClass@@@@" and
      rtti_name(HVT_DYN) == ".?AV?$DynamicVectorClass@PAVHouseClass@@@@" and
      rtti_name(HVT_VEC) == ".?AV?$VectorClass@PAVHouseClass@@@@" and
      b".?AV?$DynamicVectorClass@PAVTriggerClass@@@@" in bytes(RAW))
check("W3", W3,
      "RTTI 名定谳：0x7E91EC/0x7E920C = DynamicVector/Vector<AbstractClass*>；"
      "阳性对照=同法解 House 对得 PAVHouseClass（R-043 在册）；反证对照='PAVTriggerClass' "
      "名串在镜像存在但 0xB0F670 装的不是它（持有≠类型参数，G-62）")

# ---------- W4 全局 dtor 降级窗 + House 同形态 ----------
b4 = read(0x725390, 0x12)
hb = read(0x4E6D28, 10)
W4 = (b4 == bytes.fromhex("a174f6b0005333dbc70570f6b0000c927e00") and
      hb[:2] == b"\xc7\x05" and hb[6:] == bytes.fromhex("049f7e00"))
check("W4", W4,
      "全局 dtor 0x725390 窗（读 [0xB0F674]、降级 vptr→0x7E920C）+ House 降级站 0x4E6D28 "
      "同形态阳性对照（c7 05 …+demote-imm）⇒ 双站语义同型")

# ---------- W5 ctor 注册块整窗（含 call [edx+8] 与 SIB 尾存） ----------
b5 = read(0x725FE9, 0x51)
W5 = (b5 == bytes.fromhex(
        "a178f6b000390580f6b0007c2c381d7df6b00075043bc375388b0d84f6b0003bcb"
        "7e2e8b1570f6b00003c85351b970f6b000ff520884c074188b0d80f6b0008bc141"
        "890d80f6b0008b0d74f6b000893481") and b5[0x32:0x35] == bytes.fromhex("ff5208")
      and b5[-3:] == bytes.fromhex("893481"))
check("W5", W5,
      "TriggerClass ctor 注册块 0x725FE9..0x726037 整窗：容量/计数/旗标三查 + `b9 70f6b000`"
      "（this=容器）+ `ff 52 08`（虚槽 2 Add，与 R-043 House 向量同形）+ 尾 `89 34 81`"
      "（mov [data+idx*4],esi 原始指针入册）")

# ---------- W6 esi 保全（修正谓词：寄存器目的） ----------
REGWR = {"mov", "lea", "pop", "xor", "add", "sub", "and", "or", "sbb", "adc",
         "xchg", "inc", "dec", "not", "neg", "movzx", "movsx", "bswap", "cmpxchg"}
writers = []
for i in md.disasm(read(0x725FA0, 0x726037 - 0x725FA0), 0x725FA0):
    if i.mnemonic in REGWR and i.operands and i.operands[0].type == 1 and \
       md.reg_name(i.operands[0].reg) == "esi":
        writers.append(i.address)
head_ok = read(0x725FA0, 5) == bytes.fromhex("53568bf1e8")
W6 = head_ok and writers == [0x725FA2]
check("W6", W6,
      f"头 `mov esi,ecx` 字节钉 + ctor 头..存点之间写 esi 的指令集 == {[hex(x) for x in writers]}"
      "（唯一=头部本身）⇒ 入册 esi=TriggerClass 的 this（首版探针谓词错写 mem-base，虚警 0 条，"
      "修正后此断言才有内容）")

# ---------- W7 全局用量 census（结构量，配内嵌定位对照） ----------
cnt = raw_hits_all(bytes.fromhex("b970f6b000"))
W7 = (len(cnt) == 58 and 0x726016 in cnt)
check("W7", W7,
      f"`mov ecx,0xB0F670` 全 .text == 58 站（实测 {len(cnt)}）且含注册站点 0x726016"
      "（内嵌定位对照）⇒ 引擎级共享 AbstractClass 注册表")

# ---------- S1 结构性：WhatAmI 筛法（kb/20 契约引用，不计数） ----------
S1 = read(0x726940, 6) == bytes.fromhex("b826000000c3") and struct.unpack_from("<I", read(0x7F5858 + 0x2C, 4))[0] == 0x726940
check("S1", S1,
      "【结构性·引用 kb/20+R-047 T1】slot11 WhatAmI@0x726940=`mov eax,0x26;ret` 且 = vtable 0x7F5858+0x2C"
      " ⇒ 遍历 0xB0F670 筛 0x26 即得全部 trigger")

UNCOUNTED = {"W0", "S1"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = fp_ok and all(ok for _, ok, _ in results)
print(f"\n== R-050 {n_pass}/{n_tot} 字节断言 PASS（S1 结构性不入分母，红仍非零退出）==", file=sys.stderr)
if not fp_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
