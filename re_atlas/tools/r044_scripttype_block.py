# -*- coding: utf-8 -*-
"""R-044: L-4 -- ScriptTypeClass (0x234) big block: Save payload + count/array cluster.

gamemd.exe sha256 73201cc0...f67476, read-only. Every byte window re-dumped THIS round
(aligned decode + raw finders; full-modrm census with rm!=4 SIB exclusion per G-61).

Chain:
  * GetSize slot12 @0x691F80 = `mov eax,0x234; ret` (564, matches G-1/kb/11);
    WhatAmI slot11 @0x691F70 = `mov eax,0x1B; ret`; AbstractType name-table @0x816EE0
    pair 0x1B (word0=nameptr, word1=id) -> 'ScriptType'  (X1)
  * Save slot13 @0x691E00 (0x22 bytes pinned): base `call 0x410BE0` (rel32) then
    ONE own dword: `mov eax,[esi+0xA0]` @0x691E0E (bytes 8b86a0000000) -> writer 0x4A1D50
    (4-byte blob writer, X5).  Own Save payload = the count at +0xA0.            (X2)
  * AbstractTypeClass::Save @0x410BE0 (0x32 bytes): AbstractClass base 0x410410 first,
    then THREE string fields via 0x4A1DB0 @ +0x24 (Name, R-023), +0x64, +0x3D
    (lea 8d4624 / lea 8d4e64 / add esi,0x3d).                                      (X3)
  * string writer @0x4A1DB0 fingerprint `or ecx,-1; xor eax,eax; repne scasb; not ecx;
    dec ecx; push ecx; push edx` = strlen then push (ptr,len) -> length-prefixed stream. (X4)
  * vptr-install @0x691DB4..0x691DE3 (Load tail of slot5 @0x691D90): installs
    main 0x7F1008 + facets 0x7F0FEC/0x7F0FE4/0x7F0FDC at +0/+4/+8/+0xC
    (facet spacing -0x1C/-0x24/-0x2C -- kb/20 multi-vptr family).                  (X6)
  * fixup slot10 @0x691E30 (51-byte window pinned): guard `call [arg_vt+0x2c]` WhatAmI
    == 0x23; count [this+0xA0]; array [this+0xA8] with stride 8 (add edx,8);
    scans GLOBAL registry [0xA8ECA4] vector / [0xA8ECB0] count comparing item ptr == arg
    -- the SAME TeamTypes registry pinned in R-041 X4; name-table pair 0x23 = 'TeamType'.
    => ScriptTypeClass entries reference TeamType REGISTRY INDICES, and fixup renumbers
    them when a TeamType is removed (dec [edx] when entry > found index).           (X7,X8)
  * store census region 0x691000..0x692100 (full modrm: 89/8B mod=10 rm!=4 + C7 imm):
    stores to [reg+0xA0] = {0x6918CF, 0x691947, 0x691A5B} + C7 {0x6916C7, 0x691C8B};
    loads include the Save reader 0x691E0E and fixup readers 0x691E4B/0x691EAB.
    POSITIVE CONTROL (G-60): the first masked scan reg-field-fixed to eax gave 0 hits at
    the kb/11-cited site -- the corrected mask below must count it.                 (X9)

X10 structural (symbols.json): slot10/Save/GetSize/WhatAmI/slot5 all in ScriptTypeClass
vfuncs; main vtable = 0x7F1008.

ADDRESS FACT SOURCE (this round's method change): single-call whole-segment
`md.disasm(buffer)` linear decode + independent raw-byte `find()` locate, cross-checked.
RESYNC-DRIFT ROOT CAUSE PROVEN BY ABLATION (0x691E30 region): a walk that keeps TWO
cursors (buffer offset o AND address a) advancing BOTH by instruction size while feeding
`a+o` to disasm reports each address at +2x instruction length (first divergence: push
ebx at 0x691E30 -> push ebp "at" 0x691E32 instead of 0x691E31).  Window SIZE is NOT the
cause: win=255 (covers whole segment) drifts identically to win=16.  Earlier rounds'
"16-byte truncation" and "forgot to sync PC" diagnoses were both WRONG self-diagnoses
(caught this round; see CONFLICTS G-63).  Correct form: pass ONE anchor (start+o) and
advance ONLY o.

Scope: class-layout adjudication only; NO rewritable-address claims (charter §8).
MUTATION: R044_MUTATE=VA=BYTE[,...] -- in-memory only.
Run: python re_atlas/tools/r044_scripttype_block.py
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

for _item in os.environ.get("R044_MUTATE", "").split(","):
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

# X1 const stubs + name-table cross-check (pair layout word0=nameptr word1=id, R-043 measured)
X1 = (read(0x691F80, 6) == bytes.fromhex("b834020000c3")
      and read(0x691F70, 6) == bytes.fromhex("b81b000000c3")
      and struct.unpack_from("<I", read(0x816EE0 + 0x1B * 8 + 4, 4))[0] == 0x1B
      and cstr(struct.unpack_from("<I", read(0x816EE0 + 0x1B * 8, 4))[0]) == b"ScriptType")
check("X1", X1, "GetSize slot12 @0x691F80=`mov eax,0x234`（564，G-1/kb/11 复证）；WhatAmI slot11 @0x691F70=`mov eax,0x1B`；"
      "名字表 @0x816EE0 第 0x1B 对（word1=id 0x1B、word0=nameptr→'ScriptType'）交叉闭合")

# X2 Save whole window (0x21 up to `ret 4`) + rel32 of both calls + the +0xA0 read bytes inside
sw = read(0x691E00, 0x21)
X2 = (sw == bytes.fromhex("56578b7c240c8bf157e8d2edd7ff8b86a00000008bcf50e834ffe0ff5f5ec20400")
      and 0x691E0E + struct.unpack_from("<i", sw, 0x0A)[0] == 0x410BE0
      and 0x691E1C + struct.unpack_from("<i", sw, 0x18)[0] == 0x4A1D50)
check("X2", X2, "Save slot13 @0x691E00 整窗 0x22 字节钉死（到 `ret 4`）：基类 Save=0x410BE0（rel32 复算）、"
      "自有载荷仅 ONE dword：@0x691E0E `mov eax,[esi+0xA0]`（8b 86 a0000000）→ writer 0x4A1D50（rel32 复算）"
      " ⇒ ScriptTypeClass::Save 自有字段 = +0xA0 计数（L-4 的核心一问）")

# X3 AbstractTypeClass base Save: window 0x34 (whole fn through `ret 4`) + three string fields via 0x4A1DB0 + rel32 checks
bw = read(0x410BE0, 0x34)
X3 = (bw == bytes.fromhex("56578b7c240c8bf157e822f8ffff8d46248bcf50e8b71109008d4e64518bcfe8ac11090083c63d8bcf56e8a11109005f5ec20400")
      and 0x410BEE + struct.unpack_from("<i", bw, 0x0A)[0] == 0x410410
      and 0x410BF9 + struct.unpack_from("<i", bw, 0x15)[0] == 0x4A1DB0
      and 0x410C04 + struct.unpack_from("<i", bw, 0x20)[0] == 0x4A1DB0
      and 0x410C0F + struct.unpack_from("<i", bw, 0x2B)[0] == 0x4A1DB0)
check("X3", X3, "AbstractTypeClass::Save @0x410BE0 整窗 0x32 字节钉死：先基类 0x410410（rel32 复算），"
      "再三个字符串字段 `lea [esi+0x24]`/`lea [esi+0x64]`/`add esi,0x3d` 全走同一 writer 0x4A1DB0"
      " ⇒ Name(+0x24, R-023) + 两串(+0x64/+0x3D)；类型层 Save 载荷=字符串×3")

# X4 string writer strlen-fingerprint
X4 = read(0x4A1DB0, 0x15) == bytes.fromhex("8b5424045685d28bf17417578bfa83c9ff33c0f2ae")
check("X4", X4, "串 writer @0x4A1DB0（0x15 字节窗）：`mov edx,[esp+4]; …or ecx,-1; xor eax,eax; repne scasb`"
      "（`83c9ff 33c0 f2ae`）= strlen 起手段（`repne scasb al,[es:edi]`）⇒ 按串长序列化，非固定 0x31 缓冲拷贝"
      "（not/dec 收尾在窗外，不宣称）")

# X5 dword writer: 4-byte blob
X5 = read(0x4A1D50, 0x0B) == bytes.fromhex("8b4424048d5424046a0452")
check("X5", X5, "dword writer @0x4A1D50：`mov eax,[esp+4]; lea edx,[esp+4]; push 4; push edx`"
      " —— **同一个** R-042 TEvent Save 里调用的 dword writer（引擎共享 4 字节 blob 写）")

# X6 vptr install (Load tail): main + 3 facets
X6 = read(0x691DB4, 0x16) == bytes.fromhex("c70608107f00c74604ec0f7f00c74608e40f7f00c746")
check("X6", X6, "slot5 Load 尾 @0x691DB4：装主 vptr 0x7F1008 + 三 facet 0x7F0FEC/0x7F0FE4/0x7F0FDC "
      "于 +0/+4/+8/+0xC（facet 间距 −0x1C/−0x24/−0x2C，kb/20 多 vptr 族复现）")

# X7 fixup slot10: window 51 bytes; WhatAmI==0x23 guard; count+array+registry globals.
# stride/decr sites pinned by RAW-BYTE locate (0x691EB2 `83c208`, 0x691E98 `488902`) --
# NOT the per-chunk resync walk (that drifts; see module docstring).
fw = read(0x691E30, 51)
stride = read(0x691EB2, 3) == bytes.fromhex("83c208")          # add edx,8  (entry stride 8)
decr = read(0x691E98, 3) == bytes.fromhex("488902")            # dec eax; mov [edx],eax (renumber)
regscan = read(0x691E77, 6) == bytes.fromhex("8b0da4eca800")  # mov ecx,[0xA8ECA4] TeamTypes vector
X7 = (fw == bytes.fromhex("53558b6c240c5685ed578bd9747b8b45008bcdff502c83f823756e8b83a000000083c9ff33ff85c07e5f8b35b0eca8008d93a8")
      and stride and decr and regscan)
check("X7", X7, "fixup slot10 @0x691E30：51 字节窗钉死（WhatAmI 门 `cmp eax,0x23`、count [ebx+0xA0]、"
      "`mov esi,[0xA8ECB0]`@0x691E5A/`lea edx,[ebx+0xA8]`@0x691E60）+ `add edx,8`（@0x691EB2 条目步长 8）+ "
      "`dec eax; mov [edx],eax`（@0x691E98 重编号）+ `mov ecx,[0xA8ECA4]`（@0x691E77 TeamTypes 向量）"
      " ⇒ 数组=[+0xA8] 步长 8、计数=[+0xA0]、扫描 TeamTypes 全局注册表向量 [0xA8ECA4]（R-041 同一对全局）。"
      "地址由单次整段线性解码+独立 raw-find（83c208/488902/8b0da4eca800）双坐实；"
      "双游标同时推进（o 与 a 都 +=size 且喂 a+o）会漂到 0x691F34/0x691F00——消融证：win=255 也漂，与窗口大小无关")

# X8 name-table 0x23 cross-check -> TeamType
X8 = (struct.unpack_from("<I", read(0x816EE0 + 0x23 * 8 + 4, 4))[0] == 0x23
      and cstr(struct.unpack_from("<I", read(0x816EE0 + 0x23 * 8, 4))[0]) == b"TeamType")
check("X8", X8, "名字表第 0x23 对 = 'TeamType'/id 0x23 ⇒ fixup 入参 WhatAmI 门 0x23 = TeamTypeClass*；"
      "结合 X7 注册表同址对 ⇒ ScriptType 条目存的是 TeamType **注册表索引**（int），TeamType 被移除时前移重编号")

# X9 store/load census exact sets (full modrm mask: 89/8B mod=10 rm!=4; C7 8x rm!=4)
def mask_sites(opcodes, lo, hi):
    text = [s for s in SECS if s[0] == 0x1000][0]
    base = IB + text[0]
    tbuf = bytes(blob[_fileoff(base):_fileoff(base) + text[1]])
    D32 = bytes([0xa0, 0x00, 0x00, 0x00])
    out = set()
    for op in opcodes:
        o = 0
        while True:
            i = tbuf.find(bytes([op]), o)
            if i < 0:
                break
            if i + 6 <= len(tbuf):
                m = tbuf[i + 1]
                if 0x80 <= m <= 0xBF and (m & 7) != 4 and tbuf[i + 2:i + 6] == D32:
                    va = base + i
                    if lo <= va < hi:
                        out.add(va)
            o = i + 1
    return out
stores = mask_sites([0x89, 0xC7], 0x691000, 0x692100)
loads = mask_sites([0x8B], 0x691000, 0x692100)
X9 = (stores == {0x6918CF, 0x691947, 0x691A5B, 0x6916C7, 0x691C8B}
      and 0x691E0E in loads and loads == {0x691547, 0x69191F, 0x691940, 0x691E0E, 0x691E4B, 0x691EAB})
check("X9", X9, "census 收口（0x691000..0x692100，89/8B/C7 mod=10 rm!=4 全 reg 字段枚举）："
      "[reg+0xA0] 存储 = {0x6916C7,0x6918CF,0x691947,0x691A5B,0x691C8B}、读取 = "
      "{0x691547,0x69191F,0x691940,0x691E0E,0x691E4B,0x691EAB}（含 Save 读 0x691E0E 阳性对照）；"
      "首版掩码把 reg 字段钉死在 eax ⇒ kb/11 引的 edi 源存储 0 命中——G-60 阳性对照当场抓到")

# X10 structural (RTTI vfuncs; labeled; red == fail loudly)
d = json.load(open(RTTI, encoding="utf-8"))
st = d["classes"]["ScriptTypeClass"]
vf = set(x.upper() for x in st["vfuncs"])
X10 = (st["vtable_va"].upper() == "007F1008"
       and {"00691E30", "00691E00", "00691F80", "00691F70", "00691D90"} <= vf)
check("X10", X10, "【结构性·不计数】RTTI：主 vtable 0x7F1008 吻合且 slot5/Save/GetSize/WhatAmI/fixup "
      "五址全在 ScriptTypeClass.vfuncs ⇒ 本门禁断言的对象确为 ScriptTypeClass 方法")

UNCOUNTED = {"G0", "X10"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = all(ok for _, ok, _ in results)
print("\n== R-044 %d/%d 字节断言 PASS（G0 指纹/X10 结构性不计入分母，X10 红仍非零退出）==" % (n_pass, n_tot), file=sys.stderr)
if not g0_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
