# -*- coding: utf-8 -*-
"""R-048: L-30 消费侧收口 —— 收割函数 0x7264C0 的宿主类 = TriggerClass。

链（gamemd.exe sha256 73201cc0…f67476, read-only）:

  事件 +0x54（R-042 运行时缓存）的**唯一活读路径** = getter 0x71FA30
  （E8 入口集恰 {0x726551,0x72655c}，R-042 G9 在册），两处调用都落在
  函数 0x7264C0..0x7265B1（`ret 0x14`）体内；该函数体内 handler 0x71E940
  （+0x54 唯一存活写入者）入口 0x726540 亦在此 ⇒ 整条 +0x54 写+收割链
  只经这一个函数可达（R-047 T5 在册：handler 全镜像 E8 入口集恰 {0x726540}）。

  宿主类取证（V2/V3 字段签名互校，非形态词）:
    * 函数头 `push ecx; push esi; mov esi,ecx` = thiscall，this→esi。
    * 体内全部 `[esi+disp]` 访问的 disp 集合恰 =
      {0x24,0x2C,0x30,0x34,0x40,0x44}（读 0x24/0x30/0x40/0x44，lea 0x34，
      写 0x2C 收割 @0x726561、写 0x40 位图 @0x726582）。
    * TriggerClass ctor 0x725FA0（vptr `c70658587f00` @0x725FCE 在册 R-047 T1）
      初始化的 esi-disp 集合 ⊇ 该集合（另含 0x00 主 vptr、0x04/0x08/0x0C facet
      vptr、0x3C、0x28；+0x44 出厂置 1 = 消费方入口守卫 `mov al,[esi+0x44]`）。
    * 三件套佐证 +0x2C 是标量对端字段（修正 R-043「容器」措辞）:
      slot10 detach @0x726690 对 {+0x24,+0x28,+0x2C} 做「==arg⇒清 0/回链摘除」；
      取回 0x726910 `mov eax,[ecx+0x2C]; ret`；置位 0x726920 `ret 4`；
      使能清 0x726900 `mov byte [ecx+0x44],0`。
    * 调用侧 0x6E53A0 以 `mov esi,[ebp+0x28]` 起步、回边 `mov esi,[esi+0x28]`
      走链、`mov ecx,esi; call 0x7264C0` ⇒ 链成员即宿主对象（+0x28 是 TriggerClass
      自身链环，ctor 清零、detach 摘环，与消费方 this 同源）。

  语义（登记不定谳）: 0x7264C0 = TriggerClass 的「对端解析/使能收割」趟——
  经 [this+0x24]（owner，ctor arg1）+0xA4/+0xB4 取 arg2，逐事件（owner+0xAC
  起 +0x28 回链）过门 0x502D30（R-043 Y1）调 handler 写事件 +0x54，再把
  非零 +0x54 收割进 this+0x2C；命中事件位图记 this+0x40；未命中位置
  [esp 局部] 失败旗标并按 arg3 清位图。owner 类（[T+0x24]）与调用方宿主
  （0x6E53A0，72 个 E8 入口）仍属 L-30 未闭残量。

  L-20 影响（候选机制升级，仍不闭）: 消费方非 Save、重算路径已具形
  （使能趟重建 +0x54/+0x2C，R-047 证 +0x2C 不在 Save 字段集）；
  「载入后必跑该趟」未证 ⇒ L-20 维持开放。

诚实账（v5 §7）:
  V0 指纹恒真不入分母；S1 RTTI-JSON 结构性不入分母（红⇒非零退出）。
  V2/V3 的 disp 集合按 capstone 单点线性解码实测值先打印再断言（G-65 工序）；
  解码窗起点 = 权威函数头（V1 钉字节），杜绝 G-63 双游标漂移。
  变异 R048_MUTATE="VA=BYTE,..."（进程内，不落盘）。

Run:  python re_atlas/tools/r048_triggerclass_host.py
"""
import hashlib, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
RTTI = ROOT + r"\re_atlas\evidence\rtti\symbols.json"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

RAW = bytearray(open(EXE, "rb").read())
MUT = {}
for _it in os.environ.get("R048_MUTATE", "").split(","):
    if "=" in _it:
        _k, _v = _it.split("=", 1)
        MUT[int(_k, 0)] = int(_v, 0) & 0xFF

e = struct.unpack_from("<I", RAW, 0x3C)[0]
nsec = struct.unpack_from("<H", RAW, e + 6)[0]
optsz = struct.unpack_from("<H", RAW, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", RAW, opt + 28)[0]
tab = opt + optsz
SECS = []  # (name, vsize, va, rawsz, rp)
for i in range(nsec):
    nm = bytes(RAW[tab + i * 40:tab + i * 40 + 8]).rstrip(b"\0").decode("latin1")
    vs, va, rs, rp = struct.unpack_from("<IIII", RAW, tab + i * 40 + 8)
    SECS.append((nm, vs, IB + va, rs, rp))

def fileoff(va):
    for nm, vs, base, rs, rp in SECS:
        if base <= va < base + vs:
            fo = rp + (va - base)
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

def decode(lo, hi):
    """single-call linear decode anchored at lo (caller must pass a real head)."""
    buf = read(lo, hi - lo)
    return list(md.disasm(buf, lo))

def esi_disps(ins_list, bases=("esi",)):
    """set of disp for memory operands whose base register is in `bases` (no SIB index)."""
    out = set()
    for i in ins_list:
        for op in i.operands:
            if op.type == 3 and op.mem.base:
                bnm = md.reg_name(op.mem.base)
                if bnm in bases and op.mem.index == 0:
                    out.add(op.mem.disp & 0xFFFFFFFF)
    return out

results = []
def check(tag, ok, msg):
    results.append((tag, ok, msg))
    print(f"{tag} {'PASS' if ok else 'FAIL'}: {msg}", file=sys.stderr)

fp_ok = hashlib.sha256(open(EXE, "rb").read()).hexdigest() == SHA256

# ---------- V1 消费方函数头（thiscall 取形 + 入口两守卫） ----------
HEAD = 0x7264C0; HEAD_END = 0x7265B1  # ret 0x14 tail addr (inclusive of 0xB3? ret at 0xB1..0xB3)
b = read(0x7264C0, 0x12)
V1 = b == bytes.fromhex("51568bf18a464484c00f84e50000008a4630")
check("V1", V1,
      "消费方头 @0x7264C0 `push ecx;push esi;mov esi,ecx`（this→esi）+ 守卫读 [esi+0x44]/[esi+0x30]（18 字节钉死）")

# ---------- V2 消费方体内 esi-disp 集合恰 = {0x24,0x2C,0x30,0x34,0x40,0x44} ----------
body = decode(HEAD, 0x7265B4)  # through ret 0x14 at 0x7265B1 (+3)
dset = esi_disps(body)
EXP2 = {0x24, 0x2C, 0x30, 0x34, 0x40, 0x44}
V2 = (len(body) > 60 and dset == EXP2)
check("V2", V2,
      f"消费方体 0x7264C0..0x7265B3 全部 [esi+disp]（无 SIB）= {sorted(hex(x) for x in dset)}（恰 6 字段；含收割写 +0x2C、位图写 +0x40）")

# ---------- V3 TriggerClass ctor 初始化字段 ⊇ 消费方字段（宿主签名互校） ----------
ctor = decode(0x725FA0, 0x725FD4)  # head..just after main vptr store (facet stores next)
cset = {d & 0xFFFFFFFF for d in esi_disps(ctor)}
EXP3_MIN = EXP2 | {0x28, 0x3C}
V3 = (ctor and read(0x725FA0, 0x36) == bytes.fromhex(
        "53568bf1e8c7a1ceff8b44240c33db894624895e28895e2c885e308b0d84eda800895e3c894e34895e40c6464401c70658587f00c746")
      and EXP3_MIN <= cset)
check("V3", V3,
      "ctor 0x725FA0 字节窗（54B，vptr 0x7F5858 安装在内）+ 其 [esi+disp] 初始化集 ⊇ 消费方字段集∪{+0x28,+0x3c}"
      f"（实测 {sorted(hex(x) for x in cset)}）⇒ 消费方 this 的字段全部由 TriggerClass ctor 建立")

# ---------- V4 收割块：双 getter 调用 + mov [esi+0x2C],eax ----------
b = read(0x72654F, 0x17)
# e8 rel32s: first at window idx 0x03 (call @0x726551, nxt 0x726556);
# second at idx 0x0E (call @0x72655C, nxt 0x726561)
t1 = 0x726556 + struct.unpack_from("<i", b, 0x03)[0]
t2 = 0x726561 + struct.unpack_from("<i", b, 0x0E)[0]
V4 = (b == bytes.fromhex("8bcfe8da94ffff85c0740a8bcfe8cf94ffff89462c8a44")
      and t1 == 0x71FA30 and t2 == 0x71FA30)
check("V4", V4,
      f"收割块 @0x72654F: `mov ecx,edi; call 0x{t1:08X}` ×2 后 `mov [esi+0x2C],eax`（两 rel32 均复算到 getter 0x71FA30）")

# ---------- V5 getter 头 = 读事件 +0x54（R-042 衔接） ----------
V5 = read(0x71FA30, 4) == bytes.fromhex("8b4154c3")
check("V5", V5, "getter @0x71FA30 `mov eax,[ecx+0x54]; ret` —— 收割源即 R-042 定谳的运行时缓存字段")

# ---------- V6 handler 调用块（this=edi 事件；rel32→0x71E940）+ arg2 取链尾 ----------
b = read(0x726538, 0x0D)
# e8 sits at window idx 8 (call @0x726540), rel32 idx 9..12, next insn 0x726545
th = 0x726545 + struct.unpack_from("<i", b, 9)[0]
b2 = read(0x72651F, 0x19)
# e8 @0x726533 (window idx 0x14), rel32 idx 0x15..0x18, next insn 0x726538
tf = 0x726538 + struct.unpack_from("<i", b2, 0x15)[0]
V6 = (b == bytes.fromhex("8b4c242850518bcfe8fb83ffff") and th == 0x71E940
      and b2 == bytes.fromhex("8b56248d4634508b82a4000000518b88b4000000e8f8c7ddff")
      and tf == 0x502D30)
check("V6", V6,
      f"@0x72651F arg2 取链 `[esi+0x24]→+0xa4→+0xb4`（finder 0x{tf:08X}=0x502D30，R-043 Y1）；"
      f"@0x726538 `mov ecx,edi; call 0x{th:08X}`（handler=+0x54 唯一存活写入者，R-042）")

# ---------- V7 消费方入口 census 恰 = {0x6E5414}（内嵌阳性对照：同扫描须命中 handler 入口 0x726540） ----------
nm, vs, tbase, rs, rp = SECS[0]
tbuf = bytes(RAW[rp:rp + rs])
def e8_census(tgt):
    out = []
    p = 0
    while True:
        p = tbuf.find(b"\xe8", p)
        if p == -1: break
        if p + 5 <= len(tbuf):
            rel = struct.unpack_from("<i", tbuf, p + 1)[0]
            if tbase + p + 5 + rel == tgt:
                out.append(tbase + p)
        p += 1
    return out
callers = e8_census(0x7264C0)
ctl = e8_census(0x71E940)   # G-13 阳性对照：机制必须看得见已知入口
bs = read(0x6E5408, 0x14)
V7 = (callers == [0x6E5414] and ctl == [0x726540]
      and bs == bytes.fromhex("83fa020f94c2525057518bcee8a710040084c074"))
check("V7", V7,
      f"消费方全镜像 E8 入口集恰 = {[hex(x) for x in callers]}（唯一调用点 0x6E5414，字节含 `mov ecx,esi; call`）"
      f"+ 阳性对照 handler 入口集 = {[hex(x) for x in ctl]}（同扫描机制，非恒真）")

# ---------- V8 +0x2C 生命周期三件套（标量字段佐证；修正 R-043「容器」措辞） ----------
b = read(0x726690, 0x2C)
V8 = (b == bytes.fromhex("8b5424048b41243bc27507c74124000000008b41283bc275068b402889412839512c7507c7412c00000000c2")
      and read(0x726910, 4) == bytes.fromhex("8b412cc3")
      and read(0x726920, 0xA) == bytes.fromhex("8b44240489412cc20400")
      and read(0x726900, 5) == bytes.fromhex("c6414400c3"))
check("V8", V8,
      "slot10 detach @0x726690 对 {+0x24,+0x28,+0x2C} 做等值摘除/清零；+0x2C 取回 0x726910、置位 0x726920(ret 4)、"
      "使能清 0x726900（[+0x44]=0）⇒ +0x2C 是 TriggerClass 标量对端字段（非 VectorClass 容器——R-043 措辞修正）")

# ---------- V9 事件侧默认值：TEventClass ctor 清零 +0x54 ----------
b = read(0x71E6A0, 0x24)
V9 = b == bytes.fromhex("53568bf1e8c71acfff33dbc74624ffffffff895e28895e2c895e30885e38895e54c70678")
check("V9", V9,
      "事件 ctor @0x71E6A0 窗（+0x24=-1、+0x28/+0x2C/+0x30=0、+0x38=0、**+0x54=0**、主 vptr 0x7F5578 起）"
      "⇒ 收割读到的 0 有出厂来源；链默认态字节钉死")

# ---------- V10 vtable 槽交叉（detach/Save 同为 TriggerClass 虚法，宿主同名域） ----------
VT = 0x7F5858
s10 = struct.unpack_from("<I", read(VT + 0x28, 4))[0]
s13 = struct.unpack_from("<I", read(VT + 0x34, 4))[0]
V10 = (s10 == 0x726690 and s13 == 0x726790)
check("V10", V10,
      f"vtable 0x{VT:08X} slot10=0x{s10:08X}（detach）、slot13=0x{s13:08X}（Save，R-047 T1 复证）"
      "⇒ 消费方操作的 +0x24/+0x28/+0x2C 与虚法 detach/Save 同字段域，宿主同一性双证")

# ---------- S1 结构性（RTTI，不入分母） ----------
import json
d = json.load(open(RTTI, encoding="utf-8"))
tcl = d["classes"]["TriggerClass"]
vf = [x.upper() for x in tcl["vfuncs"]]
S1 = ("00726690" in vf and "00726790" in vf and "007264C0" not in vf
      and tcl["vtable_va"].upper() == "007F5858")
check("S1", S1,
      "【结构性·不计数】RTTI：0x726690/0x726790 ∈ TriggerClass.vfuncs、0x7264C0 ∉（直接调用法，非虚）；主表吻合")

UNCOUNTED = {"V0", "S1"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = fp_ok and all(ok for _, ok, _ in results)
print(f"\n== R-048 {n_pass}/{n_tot} 字节断言 PASS（V0 指纹 + S1 结构性不入分母，红仍非零退出）==", file=sys.stderr)
if not fp_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
