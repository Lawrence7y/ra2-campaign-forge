# -*- coding: utf-8 -*-
"""R-052: L-30 残余问题②定谳 —— 0x6E53A0（收割驱动，内含 0x7264C0 唯一调用点）宿主类 = TagClass。

链（gamemd.exe sha256 73201cc0…f67476, read-only；全部窗机器 dump，G-65 工序）:

  0x6E53A0（thiscall，`mov ebp,ecx`；双 ret 0x14 @0x6E554E/0x6E5556）体内
  [ebp+disp] 集合恰 = {0x24,0x28,0x2C,0x34,0x35}，其中 +0x34/+0x35 是**字节**
  访问（8a4534/8a4535 读、c6453501/c6453500 写）。

  TagClass ctor 0x6E4DE0（`mov esi,ecx`）初始化恰该五字段：+0x24=arg、+0x28=0、
  +0x2C=0（dword），+0x34=0、+0x35=0（**字节** 885e34/885e35 @0x6E4E01），随后
  装 4 个 vptr（主 0x7F44E0 RTTI=.?AVTagClass@@）。

  反证（宿主≠TriggerClass）：TriggerClass ctor 对 +0x34 是 **dword** 写（894e34
  @0x725FC4）且体内 c6 46 34/35 字节写 census=0 ⇒ 0x6E53A0 的字节 +0x34/+0x35
  与 TriggerClass 布局矛盾。

  链路同一性：Tag ctor 0x6E4F27 起循环 `push 0x48; call 0x7C8E17; push arg; call
  0x725FA0`（造 TriggerClass，rel32 复算=0x725FA0）后头插 **[esi+0x28]** 链表
  （8b5628 895028 894628 @0x6E4F41）；0x6E53A0 恰以 `mov esi,[ebp+0x28]` 起步、
  `mov esi,[esi+0x28]` 回边遍历同一根链，且对每个链成员 `mov ecx,esi; call
  0x7264C0`（R-048 收割趟，rel32 复算=0x7264C0）。

  调用侧 this 来源：0x6E92F3 `mov eax,[0x8B40CC]; …mov ecx,[eax+edi*4]; call
  0x6E53A0`；0x6EA4B1 `mov edx,[0x8B40CC]; mov ecx,[edx+edi*4]` —— 0x8B40C8 的
  vptr 安装唯一站 0x4E7FCD = 0x7EA5A4，RTTI = DynamicVector<PAVTagClass@@>
  ⇒ 迭代元素是 TagClass*，this=TagClass*。

  注册侧（新事实）：TagClass ctor 向**三**个向量注册 this：0xB0E720（**专用**
  DynamicVector<TagClass*>，安装 0x6E4D7D/降级 0x6E4DA8 各唯一站）、0xB0F670、
  0xB0F708（共享 Abstract 表）；三条腿窗口逐字节同构（R-051 同型），
  ctor 跨度内尾存 893481 恰 3 处 = {0x6E4E70, 0x6E4EC3, 0x6E4F16}。

  0x6E53A0 不在任何 vtable（.rdata 对齐 dword census=0）= TagClass **非虚**成员；
  阳性对照=同扫描法命中 TagClass slot10 0x6E5610 @0x7F4508 恰 1 处。

语义（登记不定谳）: 0x6E53A0 = TagClass 的「逐 trigger 使能收割驱动」——三重
门卫（全局 [0xA8ED6B]、本对象字节旗标 +0x34/+0x35、owner [+0x24] 非空）后置
+0x35=1 防重入，遍历 trigger 链调 0x7264C0，命中路径调 0x7265C0/0x726720，收尾
经 0x7258D0（WhatAmI==0x18 分派助手）并把本对象登记进第四共享表 0xB0F698。

诚实账: 所有窗 hex 由本轮 out/_probe_r052dump.py 机器 dump 先打印后断言（G-65）；
census 节元组 canonical 顺序 + .text 指纹断言（G-60 判据 4）；对照项内嵌。

Run:  python re_atlas/tools/r052_tagclass_host.py
Mut:  R052_MUTATE="VA=BYTE,..." 进程内注入
"""
import hashlib, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

RAW = bytearray(open(EXE, "rb").read())
PRISTINE = bytes(RAW)  # fingerprint attests the INPUT image; R-061 aux-batch-2:
                       # fp used to be computed post-injection, so every mutation
                       # run self-exited 2 and rc stopped reflecting assertions
                       # (G-84-family ordering defect).
MUT = {}
for _it in os.environ.get("R052_MUTATE", "").split(","):
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

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
results = []
def check(tag, ok, msg):
    results.append((tag, ok, msg))
    print(f"{tag} {'PASS' if ok else 'FAIL'}: {msg}", file=sys.stderr)

fp_ok = hashlib.sha256(PRISTINE).hexdigest() == SHA256

FN_LO, FN_HI = 0x6E53A0, 0x6E5557     # 双 ret 0x14 止于 0x6E5559 前；0x6E5559 起 90 填充
TAG_CTOR_LO, TAG_CTOR_HI = 0x6E4DE0, 0x6E4F59
TRG_CTOR_LO, TRG_CTOR_HI = 0x725FA0, 0x726130

# ---------- Y1 宿主字段签名：[ebp+disp] 集恰 {24,28,2C,34,35} + 字节访问四钉 ----------
BODY = [i for i in md.disasm(read(FN_LO, FN_HI - FN_LO), FN_LO) if i.address < FN_HI]
disps = set()
for i in BODY:
    for op in i.operands:
        if op.type == 3 and op.mem.base and md.reg_name(op.mem.base) == "ebp" \
           and op.mem.disp > 0 and op.mem.index == 0:
            disps.add(op.mem.disp)
Y1 = (sorted(disps) == [0x24, 0x28, 0x2C, 0x34, 0x35] and
      read(0x6E53BC, 3) == bytes.fromhex("8a4535") and
      read(0x6E53C7, 3) == bytes.fromhex("8a4534") and
      read(0x6E53E8, 4) == bytes.fromhex("c6453501") and
      read(0x6E5493, 4) == bytes.fromhex("c6453500"))
check("Y1", Y1,
      f"0x6E53A0 体内 [ebp+disp] 集合 == {sorted(hex(x) for x in disps)}（恰五字段）且 +0x34/+0x35 "
      "为字节访问（8a4534/8a4535 读、c6453501/00 写=重入旗标置/清）")

# ---------- Y2 边界：头部窗 + 双 ret 0x14 尾窗 + 填充 ----------
Y2 = (read(FN_LO, 0x16) == bytes.fromhex("51a06beda8005332db5584c08be9885c240b885c240a") and
      read(0x6E5549, 16) == bytes.fromhex("8ac35d5b59c214005d32c05b59c21400") and
      read(0x6E5559, 4) == bytes.fromhex("90909090"))
check("Y2", Y2,
      "边界逐字节：头 `push ecx; mov al,[0xA8ED6B]; push ebx; xor bl,bl; push ebp; …mov ebp,ecx`；"
      "尾两退出口皆 `ret 0x14`（0x6E554E/0x6E5556），0x6E5559 起 90 填充")

# ---------- Y3 TagClass ctor 恰初始化同一五字段（+0x34/+0x35 字节）+ 主 vptr ----------
Y3 = (read(0x6E4DE0, 0x42) == bytes.fromhex(
        "5356578bf1e886b3d2ff" "8b7c2410" "33db" "897e24" "895e28" "895e2c"
        "a100e7b000" "894630" "885e34" "885e35" "c706e0447f00" "c74604c4447f00"
        "c74608bc447f00" "c7460cb4447f00") and
      read(0x6E4E01, 6) == bytes.fromhex("885e34885e35"))
check("Y3", Y3,
      "TagClass ctor 0x6E4DE0 整窗逐字节：[esi+0x24]=arg、+0x28/+0x2C 清 dword、**+0x34/+0x35 清字节**"
      "（885e34 885e35）、+0x30=[0xB0E700]、装主 vptr 0x7F44E0 与三 facet vptr")

# ---------- Y4 反证：宿主≠TriggerClass（+0x34 是 dword；体内无字节 34/35 写） ----------
c634 = [a for a in raw_hits(bytes.fromhex("c6463400")) if TRG_CTOR_LO <= a <= TRG_CTOR_HI]
c635 = [a for a in raw_hits(bytes.fromhex("c6463500")) if TRG_CTOR_LO <= a <= TRG_CTOR_HI]
Y4 = (read(0x725FC4, 3) == bytes.fromhex("894e34") and
      read(0x725FB8, 3) == bytes.fromhex("885e30") and c634 == [] and c635 == [])
check("Y4", Y4,
      f"TriggerClass ctor 对 +0x34 是 **dword** 写（894e34 @0x725FC4）；字节写止于 +0x30（885e30）；"
      f"ctor 跨度内 c64634/c64635 census={len(c634)}/{len(c635)} ⇒ 0x6E53A0 的字节 +0x34/+0x35 与 "
      "TriggerClass 布局矛盾（排除法阳性=同 pattern 在镜像他处有命中，机制看得见）")

# ---------- Y5 Tag ctor 造 TriggerClass 并头插 [esi+0x28] 链（rel32 机械复算） ----------
rel5 = struct.unpack_from("<i", read(0x6E4F39, 4))[0]
Y5 = (read(0x6E4F27, 0x17) == bytes.fromhex("6a48e8e93e0e0083c4043bc3740a578bc8e863100400eb") and
      (0x6E4F3D + rel5) & 0xFFFFFFFF == 0x725FA0 and
      read(0x6E4F41, 9) == bytes.fromhex("8b5628895028894628"))
check("Y5", Y5,
      "Tag ctor 0x6E4F27 起：`push 0x48; call 0x7C8E17`（new TriggerClass 尺寸 0x48）、"
      f"`push arg; mov ecx,eax; call 0x725FA0`（rel32 复算=0x{(0x6E4F3D+rel5)&0xFFFFFFFF:08X}）、"
      "头插 [esi+0x28]（8b5628 895028 894628）⇒ TagClass +0x28 = trigger 链头")

# ---------- Y6 0x6E53A0 走同一根链、对每成员调 0x7264C0（R-048 收割趟） ----------
rel6 = struct.unpack_from("<i", read(0x6E5415, 4))[0]
Y6 = (read(0x6E53DE, 3) == bytes.fromhex("8b7528") and
      read(0x6E5484, 3) == bytes.fromhex("8b7628") and
      read(0x6E5412, 7) == bytes.fromhex("8bcee8a7100400") and
      (0x6E5419 + rel6) & 0xFFFFFFFF == 0x7264C0)
check("Y6", Y6,
      "0x6E53A0 起步 `mov esi,[ebp+0x28]`、回边 `mov esi,[esi+0x28]`、循环体 `mov ecx,esi; call`"
      f"（rel32 复算=0x{(0x6E5419+rel6)&0xFFFFFFFF:08X}=0x7264C0）⇒ 逐 tag-trigger 调收割趟")

# ---------- Y7 非虚成员：0x6E53A0 不在 .rdata/.data 对齐 dword；对照命中 slot10 ----------
def sect_u32_hits(secidx, val):
    s, vs, rp, rs = SEC[secidx]
    bb = bytes(RAW[rp:rp + rs])
    p = struct.pack("<I", val)
    pos = bb.find(p); hits = []
    while pos >= 0:
        if pos % 4 == 0:
            hits.append(IB + s + pos)
        pos = bb.find(p, pos + 1)
    return hits
Y7 = (sect_u32_hits(1, 0x6E53A0) == [] and sect_u32_hits(2, 0x6E53A0) == [] and
      sect_u32_hits(1, 0x6E5610) == [0x7F4508])
check("Y7", Y7,
      "0x6E53A0 在 .rdata/.data 对齐 dword census=0（非任何 vtable 槽）；**阳性对照**=同法命中 "
      "TagClass slot10 函数 0x6E5610 恰 1 处 @0x7F4508（(0x7F4508-0x7F44E0)/4=10）⇒ 机制可见，"
      "结论=TagClass 非虚成员")

# ---------- Y8 TagClass 自身三注册腿 + 专用表 0xB0E720 + 尾存恰 3 + 安装/降级唯一 ----------
L1 = read(0x6E4E45, 0x12)
L2 = read(0x6E4E98, 0x12)
L3 = read(0x6E4EEB, 0x12)
tails = [a for a in raw_hits(bytes.fromhex("893481")) if TAG_CTOR_LO <= a <= TAG_CTOR_HI]
inst8 = raw_hits(bytes.fromhex("c70520e7b000a4a57e00"))
dem8 = raw_hits(bytes.fromhex("c70520e7b000c4a57e00"))
Y8 = (L1 == bytes.fromhex("8b1520e7b00003c85351b920e7b000ff5208") and
      L2 == bytes.fromhex("8b1570f6b00003c85351b970f6b000ff5208") and
      L3 == bytes.fromhex("8b1508f7b00003c85351b908f7b000ff5208") and
      tails == [0x6E4E70, 0x6E4EC3, 0x6E4F16] and
      inst8 == [0x6E4D7D] and dem8 == [0x6E4DA8] and
      rtti_name(0x7EA5A4) == ".?AV?$DynamicVectorClass@PAVTagClass@@@@")
check("Y8", Y8,
      f"Tag ctor 三注册腿逐字节同构（→0xB0E720/0xB0F670/0xB0F708；ff5208=Add 槽2）；ctor 跨度尾存 "
      f"893481 恰 3 处={[hex(x) for x in tails]}；专用表 0xB0E720 安装/降级 pattern 全段唯一 "
      f"={[hex(x) for x in inst8]}/={[hex(x) for x in dem8]}；0x7EA5A4 RTTI=DynamicVector<PAVTagClass@@>")

# ---------- Y9 调用侧 this 来源=DynamicVector<TagClass*> @0x8B40C8（数据指针 0x8B40CC） ----------
inst9 = raw_hits(bytes.fromhex("c705c8408b00a4a57e00"))
Y9 = (read(0x6E92F3, 7) == bytes.fromhex("a1cc408b006a00") and
      read(0x6E92FC, 3) == bytes.fromhex("8b0cb8") and
      read(0x6EA4B1, 10) == bytes.fromhex("8b15cc408b0053538b0c") and
      inst9 == [0x4E7FCD] and u32(0x4E7FCD + 6) == 0x7EA5A4)
check("Y9", Y9,
      f"两代表调用点 this 皆取自 [0x8B40CC]（数据指针）索引：0x6E92FC / 0x6EA4BE `mov ecx,[reg+edi*4]`；"
      f"0x8B40C8 vptr 安装唯一站={[hex(x) for x in inst9]} imm=0x7EA5A4"
      "（与 0xB0E720 **同型**：DynamicVector<TagClass*>）⇒ 迭代元素=TagClass*，this=TagClass*")

# ---------- Y10 类同一性：RTTI 名 + WhatAmI 槽 11（kb/20 契约；0x2C≠0x26） ----------
Y10 = (rtti_name(0x7F44E0) == ".?AVTagClass@@") and \
      (u32(0x7F44E0 + 0x2C) == 0x6E58A0 and read(0x6E58A0, 6) == bytes.fromhex("b82c000000c3")) and \
      (u32(0x7F5858 + 0x2C) == 0x726940 and read(0x726940, 6) == bytes.fromhex("b826000000c3"))
check("Y10", Y10,
      "RTTI 链解 0x7F44E0=.?AVTagClass@@；槽11 WhatAmI：TagClass=0x2C（44）、TriggerClass=0x26（38）"
      "两族自证不同 ⇒ 收割驱动宿主类定谳 **TagClass**（实例类，非 TagTypeClass）")

# ---------- S1 结构性：第四共享表 0xB0F698（本轮副产物，不入分母） ----------
S1 = (raw_hits(bytes.fromhex("c70598f6b000ec917e00")) == [0x72586D] and
      raw_hits(bytes.fromhex("c70598f6b0000c927e00")) == [0x725898] and
      rtti_name(0x7E91EC) == ".?AV?$DynamicVectorClass@PAVAbstractClass@@@@" and
      read(0x6E54F4, 0x55) == bytes.fromhex(
          "a1a0f6b0008b0da8f6b0003bc87c2e8a0da5f6b00084c9750485c075388b0dacf6b00085c97e2e03c8"
          "a198f6b0006a0051b998f6b000ff500884c074188b0da8f6b0008bc141890da8f6b0008b0d9cf6b000"
          "892c81"))
check("S1", S1,
      "【结构性·不计数】0xB0F698=第四共享 Abstract 表（安装/降级唯一站 0x72586D/0x725898，vptr 与 "
      "0xB0F670 同 0x7E91EC）；0x6E53A0 尾段把**本对象**（ebp）经 Add 槽后 `892c81` 存入它 ⇒ "
      "登记不定谳：收割驱动收尾自报进入延迟处理表")

UNCOUNTED = {"S1"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = fp_ok and all(ok for _, ok, _ in results)
print(f"\n== R-052 {n_pass}/{n_tot} 字节断言 PASS（S1 结构性不入分母，红仍非零退出）==", file=sys.stderr)
if not fp_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
if not all_green:
    print("GATE: RED", file=sys.stderr)
    sys.exit(1)
print("GATE: GREEN", file=sys.stderr)
sys.exit(0)
