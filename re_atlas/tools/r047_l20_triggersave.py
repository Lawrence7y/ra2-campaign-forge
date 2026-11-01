# -*- coding: utf-8 -*-
"""R-047: L-20 检验 -- 猜想「TEventClass+0x54 或由 TriggerClass 的存档负责」.

gamemd.exe sha256 73201cc0...f67476, read-only. Fact source (G-63): single-call whole-segment
linear decode (ret-anchored) + raw byte census. NO double-cursor resync.

Pinned facts this round (all re-dumped THIS round, G-65 procedure: dump first, then code):

  T1 TriggerClass constants: main vtable 0x7F5858; slot11(+0x2C)=WhatAmI @0x726940
     = `mov eax,0x26; ret`; slot12(+0x30)=GetSize @0x726930 = `mov eax,0x48` (=72,
     matches the 触发器族 ID+尺寸双命中 ledger entry); AbstractType name-table pair
     0x26 (word0=nameptr, word1=id, layout MEASURED in R-043) -> 'Trigger'.
  T2 TriggerClass::Save = vtable slot13(+0x34) @0x726790, WHOLE window 0x86 bytes
     (53 instrs, head -> `ret 4`) pinned byte-for-byte.
  T3 +0x54 disp-form census over the Save window: ZERO. Positive controls (G-60/G-65
     self-application): disp8 field forms in window = {+0x24,+0x28,+0x30,+0x34,+0x3c,
     +0x40,+0x44} (7 present -- the parser CAN see +0x54-style operands, it just
     doesn't find any); stack operand [esp+0xc] is SIB (rm==4) and is excluded from
     the FIELD list per G-61 rule -- recorded, not counted as field.
  T4 E8 target set inside the Save window = {0x410410 (AbstractClass::Save -- same
     base Save TEvent::Save calls, R-041/R-042 windows), 0x4a1ca0 x2 (byte writer),
     0x4a1d50 x4 (dword writer -- SAME writer pinned in R-042 X5/R-045)}. NO callee
     that could serialize events' +0x54.
  T5 handler 0x71E940 (the ONLY live writer of event+0x54, R-042) image-wide E8 caller
     set = {0x726540}; 0x726540 lies in consumer fn 0x7264C0's body -- TriggerClass::Save
     window (0x726790..0x726816) neither calls the handler nor contains 0x726540.
  S1 structural: 0x726790/0x726940/0x726930/0x726860 in TriggerClass.vfuncs;
     0x7264C0/0x726540 NOT in vfuncs. (labeled, not counted; red == fail loudly)

VERDICT (scope-honest): the conjecture is FALSIFIED for the TriggerClass::Save path --
it serializes only its own fields (via the 4 pinned writers) and touches no +0x54 in any
form. The field's only image-wide non-self consumer remains the harvest into container
[esi+0x2C] (R-042), host class unadjudicated => the 'who archives it' answer converges
to the R-042 runtime-cache hypothesis but stays OPEN (L-20 cannot be CLOSED statically
without adjudicating the container's owner; we state what is falsified and what remains).

MUTATION: R047_MUTATE=VA=BYTE[,...] in-memory only.
Run: python re_atlas/tools/r047_l20_triggersave.py
"""
import hashlib, struct, sys, json, os

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
RTTI = ROOT + r"\re_atlas\evidence\rtti\symbols.json"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

blob = bytearray(open(EXE, "rb").read())
h0 = hashlib.sha256(bytes(blob)).hexdigest()

e = struct.unpack_from("<I", blob, 0x3C)[0]
nsec = struct.unpack_from("<H", blob, e + 6)[0]
optsz = struct.unpack_from("<H", blob, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", blob, opt + 28)[0]
tab = opt + optsz
SECS = []
for i in range(nsec):
    o = tab + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", blob, o + 8)
    SECS.append((va, vs, rp, rs))

def _fileoff(va):
    rva = va - IB
    for s_rva, vs, rp, rs in SECS:
        if s_rva <= rva < s_rva + vs and rva - s_rva < rs:
            return rp + (rva - s_rva)
    return None

def read(va, n):
    fo = _fileoff(va)
    if fo is None:
        raise SystemExit("VA 0x%X not disk-backed" % va)
    return bytes(blob[fo:fo + n])

def cstr(va, n=64):
    return read(va, n).split(b"\x00")[0]

for _item in os.environ.get("R047_MUTATE", "").split(","):
    if "=" in _item:
        k, v = _item.split("=", 1)
        fo = _fileoff(int(k, 0))
        if fo is None:
            raise SystemExit("mutation target not disk-backed")
        blob[fo] = int(v, 0) & 0xFF

results = []
def check(tag, ok, msg):
    results.append((tag, ok, msg))
    print("%s %s: %s" % (tag, "PASS" if ok else "FAIL", msg), file=sys.stderr)

g0_ok = (h0 == SHA256)

VT = 0x7F5858
SAVE = 0x726790
WLEN = 0x86

# T1 constants + name-table cross
T1 = (read(0x726940, 6) == bytes.fromhex("b826000000c3")
      and read(0x726930, 6) == bytes.fromhex("b848000000c3")
      and struct.unpack_from("<I", read(VT + 0x2C, 4))[0] == 0x726940
      and struct.unpack_from("<I", read(VT + 0x30, 4))[0] == 0x726930
      and struct.unpack_from("<I", read(VT + 0x34, 4))[0] == SAVE
      and struct.unpack_from("<I", read(0x816EE0 + 0x26 * 8 + 4, 4))[0] == 0x26
      and cstr(struct.unpack_from("<I", read(0x816EE0 + 0x26 * 8, 4))[0]) == b"Trigger")
check("T1", T1, "常量与交叉：vtable 0x7F5858 slot11=WhatAmI 0x726940(`mov eax,0x26`)、slot12=GetSize "
      "0x726930(`mov eax,0x48`=72，触发器族尺寸台账复证)、slot13=Save=0x726790；"
      "名字表 @0x816EE0 第 0x26 对 word1=0x26/word0='Trigger'（R-043 实测对布局）⇒ 类身份闭合")

# T2 whole Save window pinned byte-for-byte
W = read(SAVE, WLEN)
T2 = W == bytes.fromhex(
    "56578b7c240c8bf157e8729cceff8b462483c004508b08ff5110508bcfe89eb5d7ff"
    "8b462885c074128b500483c00450ff5210508bcfe885b5d7ff8a46308bcf50e8cab4d7ff"
    "8a4e44518bcfe8bfb4d7ff8b56348b463c83faff74128b0d84eda8002bca3bc87d042bc1eb0233c050"
    "8bcfe84ab5d7ff8b56408bcf52e83fb5d7ff5f5ec20400")
check("T2", T2, "TriggerClass::Save 整窗 0x86 字节（53 指令，head→`ret 4`）逐字节钉死；"
      "基类 Save 在前（`call 0x410410`，与 TEvent::Save 同基类 Save，R-041/42 交叉）")

# T3 +0x54 disp-form census over window; positive-control field set (G-60 self-application)
def disp_forms(buf, base_va):
    fields, sibs = {}, []
    o = 0
    while o < len(buf) - 2:
        op = buf[o]
        if op in (0x8B, 0x89, 0x8A, 0x88, 0xC6, 0xC7):
            m = buf[o + 1]
            mod, rm = m >> 6, m & 7
            if mod == 1 and rm != 4:
                fields.setdefault(buf[o + 2], []).append(base_va + o)
                o += 3
                continue
            if mod == 1 and rm == 4:  # SIB disp8 -- stack/indexed form, NOT a plain field
                sibs.append(base_va + o)
                o += 4
                continue
            if mod == 2 and rm != 4:
                fields.setdefault(struct.unpack_from("<I", buf, o + 2)[0], []).append(base_va + o)
                o += 6
                continue
        o += 1
    return fields, sibs
fields, sibs = disp_forms(W, SAVE)
T3 = (0x54 not in fields and set(fields.keys()) >= {0x24, 0x28, 0x30, 0x34, 0x3C, 0x40, 0x44}
      and len(sibs) >= 1)
check("T3", T3, "窗口内 +0x54 disp 形态 = **0 处**；阳性对照（同解析器可见性证明）：字段 disp8 集合 ⊇ "
      "{+0x24,+0x28,+0x30,+0x34,+0x3c,+0x40,+0x44}（7 个都在⇒解析器没瞎），另 [esp+0xc] 是 SIB(rm==4) "
      "按 G-61 排除出字段表。⇒ TriggerClass::Save 不解引用任何 +0x54")

# T4 E8 target set inside window (exact set; raw recompute, G-61: E8-in-imm false hits
# impossible here because we only accept aligned starts? -- we scan ALL offsets but the
# set equality to known callees is the guard; phantom would ADD targets, not hide them)
tgts = []
for o in range(len(W) - 5):
    if W[o] == 0xE8:
        rel = struct.unpack_from("<i", W, o + 1)[0]
        tgts.append(SAVE + o + 5 + rel)
# T4 call-target census over the Save window -- derived from capstone LINEAR decode
# (single md.disasm pass), NOT a raw 0xE8 byte scan (that hits phantom E8 bytes inside
# rel32 immediates -> the bytescan-phantom trap; the first draft of this gate fell for it
# and its target set disagreed with the authoritative decode). G-60/G-61 discipline.
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM
_md = Cs(CS_ARCH_X86, CS_MODE_32); _md.detail = True
calls = []
for _ins in _md.disasm(W, SAVE):
    if _ins.mnemonic == "call" and _ins.operands and _ins.operands[0].type == CS_OP_IMM:
        calls.append(_ins.operands[0].imm)
uniq = sorted(set(calls))
T4 = (uniq == [0x410410, 0x4A1CA0, 0x4A1D50]
      and calls.count(0x4A1D50) == 4 and calls.count(0x4A1CA0) == 2 and calls.count(0x410410) == 1
      and read(0x4A1D50, 11) == bytes.fromhex("8b4424048d5424046a0452")
      and read(0x4A1CA0, 8) == bytes.fromhex("8b410433d23bc275")
      and read(0x410410, 8) == bytes.fromhex("568bf1578b7c240c"))
check("T4", T4, "Save 窗口内**直接 call** 目标集合（**capstone 线性解码**取 imm 操作数，非裸 0xE8 "
      "扫描——首版用字节扫描撞上 rel32 内的幻影 E8，目标集与权威解码不符，已纠正）= 恰 "
      "{0x410410 基类Save ×1, 0x4A1CA0 ×2, 0x4A1D50 ×4}（后两者头字节复证=字段 writer 族，"
      "0x4A1D50 与 R-042 X5 同一 writer）。另有 2 个**间接 call** `[ecx+0x10]`/`[edx+0x10]`"
      "（与 R-042 X2 **同形态**：+0x24/+0x28 存子对象指针、`+4` 取 facet vptr、调 slot4 后把"
      "返回值写流——该形态在 R-042 解出 ID-getter；TriggerClass 的这两处 facet 未重解，登记）"
      "⇒ Save 无任何可序列化事件 +0x54 的被调方")

# T5 handler (sole live writer of event+0x54) entry census + non-membership in Save path
text = [s for s in SECS if s[0] == 0x1000][0]
base = IB + text[0]
tbuf = bytes(blob[_fileoff(base):_fileoff(base) + text[1]])
def e8_callers(tgt):
    out, o = [], 0
    while True:
        i = tbuf.find(b"\xe8", o)
        if i < 0:
            break
        if base + i + 5 + struct.unpack_from("<i", tbuf, i + 1)[0] == tgt:
            out.append(base + i)
        o = i + 1
    return out
T5 = (e8_callers(0x71E940) == [0x726540]
      and not (SAVE <= 0x726540 < SAVE + WLEN)
      and 0x71E940 not in calls)
check("T5", T5, "handler 0x71E940（event+0x54 唯一存活写入者，R-042）全镜像 E8 入口集恰={0x726540}"
      "（消费循环体内）；0x726540 不在 Save 窗口地址域、Save 的 E8 集也不含 handler ⇒ Save 路径根本不"
      "经过写 +0x54 的那条链（间接调用不可排除，按 charter 只登记直调面）")

# structural S1 (RTTI vfuncs; labeled, red == fail loudly)
d = json.load(open(RTTI, encoding="utf-8"))
tc = d["classes"]["TriggerClass"]
vf = set(x.upper() for x in tc["vfuncs"])
S1 = ("00726790" in vf and "00726940" in vf and "00726930" in vf and "00726860" in vf
      and "007264C0" not in vf and "00726540" not in vf
      and tc["vtable_va"].upper() == "007F5858")
check("S1", S1, "【结构性·不计数】RTTI：Save/WhatAmI/GetSize/slot5 入 vfuncs、0x7264C0/0x726540 不在"
      "（消费循环非 TriggerClass 虚方法）、主表 0x7F5858 吻合 ⇒ 门禁钉的 Save 确属 TriggerClass")

UNCOUNTED = {"G0", "S1"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = all(ok for _, ok, _ in results)
print("\n== R-047 %d/%d 字节断言 PASS（G0 指纹/S1 结构性不入分母，S1 红仍非零退出）==" % (n_pass, n_tot), file=sys.stderr)
if not g0_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
