# -*- coding: utf-8 -*-
"""R-046: L-4 residual -- the two +0xA0 "ctor variants" adjudicated: plain ctor vs INI find-or-create factory.

gamemd.exe sha256 73201cc0...f67476, read-only. Fact source (G-63): every window
re-dumped this round by single-call whole-segment linear decode (ret-anchored) +
independent raw find; NO double-cursor resync.

R-045 left a question: two sites zero the count (`0x6916C7`, `0x691C8B`) with identical
bytes -- 'one per class, one per derived/reuse' was NOT adjudicated. This gate closes it.
Naming discipline (G-64): shared helper 0x410800 is NOT called a 'base ctor' (unproven
semantics); we pin its head bytes and call it 'init helper', asserting only what bytes show.

  C1 plain-ctor head @0x6916B0: `mov eax,[esp+4]; push esi; mov esi,ecx(=this); push eax;
     call 0x410800` (rel32; init helper invoked directly on this, NO allocation in fn) = PLAIN CTOR.
  C2 factory head @0x691C00: `push edi; push '<none>'(0x817474); call 0x7C8D20 (strcmp-form),
     je fail; push edi; push 'none'(0x817694); call 0x7C8D20, je fail; scan vector [0x8B41CC]
     (`add ecx,0x24` = AbstractType Name slot) via 0x7C8D20; miss: `push 0x234; call 0x7C8E17`
     (alloc wrapper head `6a01 ff742408 e8..`), fresh this -> call 0x410800. = FIND-OR-CREATE.
  C3 shared init tail 0x1A bytes byte-equal at both sites: [+0x9C]:=0,[+0xA0]:=0,
     main vptr 0x7F1008 + facets 0x7F0FEC/0x7F0FE4/0x7F0FDC => SAME class (ScriptTypeClass).
  C4 both end with `mov [esi+0x98],eax` (registry index) @0x691763/@0x691D26.
  C5 dtor @0x691770: `mov dl,1` (deleting flag), reinstall vptrs, call 0x7258D0, then
     unregister+compaction: count `--`@0x6917BD, `mov edx,[ecx+eax*4];
     mov [ecx+eax*4-4],edx` (SIB shifts later entries down)@0x6917CE/7D1, call 0x4109C0
     (destructor helper, head pinned) => [0x8B41CC]/[0x8B41D8] is the ScriptTypes registry.
  C6 exact sets (raw find 0x691000..0x692100): double-zero pattern {0x6916BD,0x691C81},
     `[reg+0x98],eax` writes {0x691763,0x691D26} -- exactly 2 each (no third variant).
  C7 helper-head positive controls: 0x7C8D20 strcmp-form head + 0x7C8E17 alloc head +
     two guard windows (21 bytes each) pinned.

DEBT note (bytes only, NOT claimed as engine bug): dtor compaction shifts later registry
entries down but each object keeps its stored +0x98 index; whether a later pass re-fixes
them is un-adjudicated (runtime, out of static scope). Registered, not concluded.

MUTATION: R046_MUTATE=VA=BYTE[,...] in-memory only.
Run: python re_atlas/tools/r046_ctor_vs_factory.py
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

def rel32_at(va):
    return va + 5 + struct.unpack_from("<i", read(va + 1, 4), 0)[0]

for _item in os.environ.get("R046_MUTATE", "").split(","):
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

# C1 plain-ctor head + init-helper call target + "no allocation in body" census.
# E8 rel32 sites strictly inside ctor body [0x6916B0,0x69176D): exactly one, to 0x410800.
text0 = [s for s in SECS if s[0] == 0x1000][0]
b0 = IB + text0[0]
tb = bytes(blob[_fileoff(b0):_fileoff(b0) + text0[1]])
def e8_targets(lo, hi):
    out = []
    for i in range(lo, hi - 5):
        fo = _fileoff(i)
        if fo is not None and blob[fo] == 0xE8:      # absolute file offset on the WHOLE blob
            rel = struct.unpack_from("<i", blob, fo + 1)[0]  # (single addressing model, G-60)
            out.append(i + 5 + rel)
    return out
ctor_calls = e8_targets(0x6916B0, 0x69176D)
C1 = (read(0x6916B0, 16) == bytes.fromhex("8b442404568bf150e843f1d7ffc7869c")
      and rel32_at(0x6916B8) == 0x410800
      and ctor_calls == [0x410800])
check("C1", C1, "plain ctor 头 @0x6916B0：`mov eax,[esp+4]; push esi; mov esi,ecx(this); push eax; "
      "call 0x410800`（rel32 复算=共享 init 助手，直调于 this）；**census：ctor 体内 [0x6916B0,0x69176D) "
      "的 E8 调用点集合恰={0x410800}（唯一调用，无分配器）⇒ '全函数零分配调用' 由散文升为可杀 census**"
      "（G-57 精神：散文声明必须落到取值）")

# C2 factory head + string guards + name-scan + alloc wrapper + init-helper on fresh obj
C2 = (read(0x691C00, 8) == bytes.fromhex("56578bf957687474")
      and cstr(0x817474) == b"<none>" and cstr(0x817694) == b"none"
      and rel32_at(0x691C0A) == 0x7C8D20 and rel32_at(0x691C20) == 0x7C8D20
      and read(0x691C41, 9) == bytes.fromhex("8b0cb083c12451e8d3")
      and rel32_at(0x691C48) == 0x7C8D20
      and read(0x691C62, 12) == bytes.fromhex("6834020000e8ab7113008bf0")
      and rel32_at(0x691C67) == 0x7C8E17
      and rel32_at(0x691C7C) == 0x410800)
check("C2", C2, "工厂 头 @0x691C00：双串守卫 `<none>`/`none`→`call 0x7C8D20`（strcmp 形态助手，"
      "rel32 复算）je-fail；名字扫 `mov ecx,[eax+esi*4]; add ecx,0x24`（AbstractType Name 槽）再 "
      "call 0x7C8D20；未命中 `push 0x234; call 0x7C8E17`（分配包装，rel32 复算，尺寸 0x234=GetSize）；"
      "新对象 `mov ecx,esi` 后 call 0x410800 ⇒ find-or-create 工厂")

# C3 shared init tail byte-equal at both sites (same vptr set => same class)
TRI = "c7869c00000000000000c786a000000000000000c70608107f00c74604ec0f7f00c74608e40f7f00c7460cdc0f7f00"
C3 = (read(0x6916BD, 0x2F) == bytes.fromhex(TRI)
      and read(0x691C81, 0x2F) == bytes.fromhex(TRI))
check("C3", C3, "共享 init 尾 0x2F 字节两站**逐字节相等**：[+0x9C]←0、[+0xA0]←0（R-045 双零对）、"
      "主 vptr 0x7F1008、三 facet 0x7F0FEC/+8 0x7F0FE4/+0xC 0x7F0FDC ⇒ 两站构造**同一类**（vptr 组全同）"
      "——R-045「两 ctor 变体归属」定谳：非派生变体，是同一 ScriptTypeClass 的构造器 vs 工厂两入口")

# C4 registry-index write at both tails
C4 = (read(0x691763, 6) == bytes.fromhex("898698000000")
      and read(0x691D26, 6) == bytes.fromhex("898698000000"))
check("C4", C4, "两站尾同型 `mov [esi+0x98],eax`（@0x691763/@0x691D26）——注册表下标字段；"
      "前邻线性查自 [0x8B41CC]/[0x8B41D8]（构造器与工厂都把自身登记进 ScriptTypes 向量并记下标）")

# C5 dtor head + deleting flag + unregister-compaction + destructor helper
C5 = (read(0x691770, 8) == bytes.fromhex("51568bf1b201c706")
      and rel32_at(0x691791) == 0x7258D0
      and read(0x6917BF, 6) == bytes.fromhex("890dd8418b00")
      and read(0x6917CE, 10) == bytes.fromhex("8b1481895481fc8b0dd8")
      and rel32_at(0x6917E1) == 0x4109C0)
check("C5", C5, "dtor @0x691770：`push ecx; push esi; mov esi,ecx; mov dl,1`（deleting 标志）+"
      "`call 0x7258D0`；unregister：count 写回 `[0x8B41D8]`@0x6917BF + SIB 压缩 "
      "`mov edx,[ecx+eax*4]; mov [ecx+eax*4-4],edx`@0x6917CE/7D1（后项下移！）+ `call 0x4109C0`"
      "（析构助手，rel32）⇒ [0x8B41CC]/[0x8B41D8] 确为 ScriptTypes 注册表向量")

# C6 exact-set census: double-zero and +0x98 writes appear exactly twice
text = [s for s in SECS if s[0] == 0x1000][0]
base = IB + text[0]
tbuf = bytes(blob[_fileoff(base):_fileoff(base) + text[1]])
def find_all(pat, lo, hi):
    out, o = [], 0
    while True:
        i = tbuf.find(pat, o)
        if i < 0:
            break
        va = base + i
        if lo <= va < hi:
            out.append(va)
        o = i + 1
    return out
dblzero = find_all(bytes.fromhex("c7869c00000000000000c786a000000000000000"), 0x691000, 0x692100)
idxw = find_all(bytes.fromhex("898698000000"), 0x691000, 0x692100)
C6 = (set(dblzero) == {0x6916BD, 0x691C81} and set(idxw) == {0x691763, 0x691D26})
check("C6", C6, "census 精确集合（raw find，0x691000..0x692100）：双零对 [+0x9C][+0xA0] 恰 "
      "{0x6916BD,0x691C81}、`[reg+0x98],eax` 写恰 {0x691763,0x691D26} ⇒ 构造形态全区仅此两处，"
      "与 C1/C2 的一 ctor 一工厂吻合（无第三变体）")

# C7 helper-head positive controls + guard windows
C7 = (read(0x7C8D20, 12) == bytes.fromhex("558bec5756538b750c8b7d08")
      and read(0x7C8E17, 12) == bytes.fromhex("6a01ff742408e82006000059")
      and read(0x410800, 12) == bytes.fromhex("83ec44535556578be9e862f9")
      and read(0x691C05, 21) == bytes.fromhex("6874748100e81171130083c40885c00f8423010000")
      and read(0x691C1B, 21) == bytes.fromhex("6894768100e8fb70130083c40885c00f840d010000"))
check("C7", C7, "对照件（G-60 阳性对照）：strcmp 助手 0x7C8D20 头 / 分配包装 0x7C8E17 头 / "
      "init 助手 0x410800 头（`83ec44…`，被两入口 call）三处字节钉死；两守卫窗各 21 字节钉死 "
      "⇒ 工厂入参等于 '<none>'/'none' 即走失败返回")

# structural (RTTI; labeled, red == fail loudly)
d = json.load(open(RTTI, encoding="utf-8"))
vf = set(x.upper() for x in d["classes"]["ScriptTypeClass"]["vfuncs"])
S1 = ("006916B0" not in vf and "00691C00" not in vf and "00691770" not in vf
      and "006917F0" in vf)
check("S1", S1, "【结构性·不计数】0x6916B0/0x691C00/0x691770 均不在 ScriptTypeClass.vfuncs"
      "（自由 ctor/工厂/dtor，非虚方法）；0x6917F0 ∈ vfuncs（紧邻 dtor 的虚槽入口，不宣称用途）")

UNCOUNTED = {"G0", "S1"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = all(ok for _, ok, _ in results)
print("\n== R-046 %d/%d 字节断言 PASS（G0 指纹/S1 结构性不入分母，S1 红仍非零退出）==" % (n_pass, n_tot), file=sys.stderr)
if not g0_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
