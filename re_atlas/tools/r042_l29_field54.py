# -*- coding: utf-8 -*-
"""R-042: L-29 — TEventClass+0x54 attribution. (gamemd.exe sha256 73201cc0...f67476, read-only)

Every byte window below was re-dumped THIS round (capstone with md.detail=True on a
resync walk + raw modrm scan + PE-jump-table anchors), not carried from prose.

Chain:
  * ctor 0x71E6BE zeroes [esi+0x54] BEFORE installing main/facet vptrs  -> +0x54 is a member field
  * Load ctor-slot5 @0x71F91B `add esi,0x54` — swizzle-register alongside +0x28/+0x30 (kb/21 §1.1)
  * Save @0x71F820 whole-window pinned: serializes +0x28/+0x2C/+0x30/+0x34, NO +0x54 (L-20)
  * dead setter 0x71FA44: `mov [ecx+0x54],eax; ret 4` — ZERO references (E8/E9/imm) image-wide
  * live writer = handler 0x71E940 (thiscall: prolog `mov ebp,ecx` -> this=ebp; [ebp+disp] are
    FIELD reads; rm==4 would be SIB/esp — trap pinned by G8's modrm filter):
      - guard @0x71F1DA: [this+0x34] vs (arg object's slot14 ID) — else fail-path
      - store block @0x71F1FB: out-flag byte ([esp+0x40]) := 1; then [this+0x54] := (arg's slot15
        +0x3c) result  -- value comes from VTABLE slot15 @+0x3c on the passed object
      - main TEvent vtable slot15 (+0x3c) = 0x4104A0 = stub `xor eax,eax; ret` (returns NULL for
        a bare TEventClass) — handler runs on DERIVED/attached objects
  * getter 0x71FA30 consumed @0x72654F/0x72655C (harvest into container [esi+0x2C] if non-NULL)
  * handler's ONLY entry: E8 from 0x726540; E9/imm refs none; not in any RTTI vfuncs

CENSUS (cluster 0x71E000..0x71FC00, raw modrm): stores `89 <mod01 rm!=4> 54` (+rm==5 disp8 form)
  == {0x71E6BE (ctor zero), 0x71F209 (handler store), 0x71FA44 (dead setter)} — exact set.
NOTE (erratum-avoided): an early resync walker here printed the store as 0x71F216 (address
drift when skipping undecodable bytes). Raw bytes at 0x71F209 = `89 45 54` (true-aligned
window 0x71F1FB decode) confirm R-041's registration 0x71F209 was correct; the phantom
0x71F216 is not used anywhere in the assertions.

MUTATION: R042_MUTATE=VA=BYTE[,...] in-memory only.  Run:
  python re_atlas/tools/r042_l29_field54.py
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

for _item in os.environ.get("R042_MUTATE", "").split(","):
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

# G0 image fingerprint (tautology by design; NOT counted in denominator)
g0_ok = (h0 == SHA256)

# G1 ctor zero-site: field zeroing precedes vptr install
G1 = read(0x71E6BB, 0x12) == bytes.fromhex("885e38895e54c70678557f00c746045c557f")
check("G1", G1, "ctor @0x71E6BB: `mov byte[esi+0x38],bl; mov [esi+0x54],ebx(ebx=0)` 紧接 `mov [esi],0x7F5578`（主 vptr）⇒ +0x54 是构造即清零的成员字段")

# G2 swizzle registration of +0x54 (third interface field)
G2 = read(0x71F91B, 6) == bytes.fromhex("83c654566810")
check("G2", G2, "Load-ctor @0x71F91B: `add esi,0x54; push esi; push 0xB0C110` ⇒ 与 +0x28/+0x30 并列入 swizzle 登记（指针重定位字段，kb/21 §1.1 同窗复证）")

# G3 Save whole window pinned; four items, no +0x54 touch
save_hex = ("56578b7c240c8bf157e8e20bcfff8b462885c074128b480483c00450ff5110508bcfe80925d8ff"
            "8b562c8bcf52e8fe24d8ff8b463085c074128b480483c00450ff5110508bcfe8e524d8ff"
            "8b56348bcf52e8da24d8ff5f5ec20400")
win = read(0x71F820, 0x5B)  # exactly through `ret 4` at 0x71F878 (0x5C would swallow a pad 0x90)
G3 = (win == bytes.fromhex(save_hex))
check("G3", G3, "Save @0x71F820..0x71F87A（0x5B 字节整窗逐字节钉死，含 `ret 4`）：仅 +0x28/+0x2C/+0x30/+0x34 四项、基类 Save 在前 ⇒ 整窗锁死即排除任何 `[reg+0x54]` 形态（capstone 复核：窗内 0 个 +0x54 操作数）⇒ L-20 坐实：+0x54 不进 Save")

# G4 handler prolog: thiscall this->ebp (field access base, NOT frame args; rm==4=SIB trap excluded in G8)
G4 = read(0x71E940, 0x16) == bytes.fromhex("83ec1c53558be95657896c24108b4d2c8d41f383f830")
check("G4", G4, "handler @0x71E940 序言 `sub esp,0x1c; push ebx; push ebp; mov ebp,ecx(=this); mov ecx,[ebp+0x2c]; lea eax,[ecx-0xd]; cmp eax,0x30` ⇒ Kind 主 switch（0xd..0x3d），ebp=this ⇒ 体内 [ebp+0x54] 为字段写")

# G5 store block @0x71F1FB (29 bytes, ends ret 0x18)
G5 = read(0x71F1FB, 0x1D) == bytes.fromhex("8b4c2440c601018b168bceff523c8945545f5e5db0015b83c41cc21800")
check("G5", G5, "handler store 块 @0x71F1FB: `mov ecx,[esp+0x40]; mov byte[ecx],1; mov edx,[esi]; mov ecx,esi; call [edx+0x3c]; mov [ebp+0x54],eax`（89 45 54：mod=01/reg=eax/rm=101=ebp+disp8） ⇒ 存活写入把 arg 对象的 slot15(+0x3c) 返回值存入事件自身 +0x54，并置出参字节")

# G6 guard window + vtable slot15 stub + getter bytes
G6 = (read(0x71F1DA, 0x21) == bytes.fromhex("8b7d3483ffff74198b068bceff50388bcf8bd8e83e3bdeff3b58300f8568ffffff")
      and struct.unpack_from("<I", read(0x7F5578 + 0x3C, 4))[0] == 0x4104A0
      and read(0x4104A0, 3) == bytes.fromhex("33c0c3")
      and read(0x71FA30, 4) == bytes.fromhex("8b4154c3"))
check("G6", G6, "handler 门 @0x71F1DA: edi=[ebp+0x34]；==-1 跳过，否则 `call [arg2表+0x38]` 结果 ebx 与 `0x502d30(edi)+0x30` 比对（call 目标只登记虚表派发，不臆断语义）；主表 slot15(+0x3c)=0x4104A0=`xor eax,eax; ret`；getter `mov eax,[ecx+0x54]; ret`")

# G7 consumer pair: harvest + handler-call site windows
G7 = (read(0x726538, 0xD) == bytes.fromhex("8b4c242850518bcfe8fb83ffff")
      and read(0x72654F, 0x15) == bytes.fromhex("8bcfe8da94ffff85c0740a8bcfe8cf94ffff89462c"))
check("G7", G7, "消费方 @0x726538: `call 0x71E940`（rel32 复算 =0x71E940）；@0x72654F/0x72655C: 两 call 均落 0x71FA30（rel32 复算），非零则 `mov [esi+0x2c],eax` ⇒ 读侧唯一消费：事件 +0x54 收割进容器 +0x2C")

# G8 cluster store census, EXACT SET (modrm mod=01; rm==4 SIB excluded; rm==5 disp8 form included)
text = [s for s in SECS if s[0] == 0x1000][0]
base = IB + text[0]
tbuf = bytes(blob[_fileoff(base):_fileoff(base) + text[1]])
def store_sites(lo_va, hi_va):
    sites = []
    for o in range(len(tbuf) - 3):
        va = base + o
        if not (lo_va <= va < hi_va):
            continue
        if tbuf[o] != 0x89:
            continue
        m = tbuf[o + 1]
        if (m >> 6) != 1:
            continue
        rm = m & 7
        if rm == 4:
            continue  # SIB byte follows -- never plain [reg+0x54]
        if tbuf[o + 2] == 0x54:
            sites.append(va)
    return sites
G8 = set(store_sites(0x71E000, 0x71FC00)) == {0x71E6BE, 0x71F209, 0x71FA44}
check("G8", G8, "簇域 census 收口（0x71E000..0x71FC00）：`mov [reg+0x54],r32` 命中集合恰 = {0x71E6BE ctor 清零, 0x71F209 handler 存活写, 0x71FA44 死 setter}；rm==4（SIB [esp+..]）假阳性由 modrm 过滤排除")

# G9 setter dead + handler single entry (E8/E9/imm three-face)
def rel_hits(op, tgt):
    hits, o = [], 0
    while True:
        i = tbuf.find(bytes([op]), o)
        if i < 0:
            break
        if i + 5 <= len(tbuf) and base + i + 5 + struct.unpack_from("<i", tbuf, i + 1)[0] == tgt:
            hits.append(base + i)
        o = i + 1
    return hits
def imm_hits(tgt):
    pat = struct.pack("<I", tgt)
    hits = []
    for s_rva, vs, rp, rs in SECS:
        seg = bytes(blob[rp:rp + rs])
        o = 0
        while True:
            i = seg.find(pat, o)
            if i < 0:
                break
            hits.append(IB + s_rva + i)
            o = i + 1
    return hits
G9 = (read(0x71FA40, 10) == bytes.fromhex("8b442404894154c20400")
      and rel_hits(0xE8, 0x71FA40) == [] and rel_hits(0xE9, 0x71FA40) == [] and imm_hits(0x71FA40) == []
      and rel_hits(0xE8, 0x71E940) == [0x726540]
      and rel_hits(0xE9, 0x71E940) == [] and imm_hits(0x71E940) == []
      and rel_hits(0xE8, 0x71FA30) == [0x726551, 0x72655C] and imm_hits(0x71FA30) == [])
check("G9", G9, "三面引用普查：setter 字节钉死且 E8/E9/立即数全镜像零引用（死访问器）；handler E8 唯一入口 0x726540、无 E9/立即数第二入口；getter 调用者恰 {0x726551,0x72655c}（立即数零）")

# structural (RTTI; labeled, NOT counted in denominator but red == fail loudly)
d = json.load(open(RTTI, encoding="utf-8"))
te = d["classes"]["TEventClass"]
vf = [x.upper() for x in te["vfuncs"]]
S1 = ("0071E940" not in vf and "0071FA30" not in vf and "0071FA40" not in vf
      and te["vtable_va"].upper() == "007F5578")
check("S1", S1, "【结构性·不计数】handler/getter/setter 均不在 TEventClass 24 槽 vfuncs 内 ⇒ 皆非虚方法（自由函数/访问器）；主表 0x7F5578 吻合")

UNCOUNTED = {"G0", "S1"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = all(ok for _, ok, _ in results)
print("\n== R-042 %d/%d 字节断言 PASS（G0 指纹/S1 结构性不计入分母，S1 红仍非零退出）==" % (n_pass, n_tot), file=sys.stderr)
if not g0_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
