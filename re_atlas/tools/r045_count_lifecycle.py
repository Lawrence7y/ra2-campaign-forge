# -*- coding: utf-8 -*-
"""R-045: L-4 fine print -- the full lifecycle of ScriptTypeClass's +0xA0 COUNT field.

gamemd.exe sha256 73201cc0...f67476, read-only. Windows re-dumped this round via
single-call whole-segment linear decode + independent raw find (G-63 discipline;
no double-cursor resync anywhere).

R-044 pinned the census set: stores to [reg+0xA0] in 0x691000..0x692100 =
{0x6916C7, 0x6918CF, 0x691947, 0x691A5B, 0x691C8B} (C7-imm) + loads
{0x691547, 0x69191F, 0x691940, 0x691E0E, 0x691E4B, 0x691EAB}.
This gate attributes every site by LOCAL byte context (no fn-boundary guessing):

  Z1/Z2 ctor-cluster zeroes: @0x6916C7 and @0x691C8B are
      `mov dword [esi+0xA0], 0`  (c7 86 a0000000 00000000)
      followed within 6 bytes by `mov [esi], 0x7F1008` (main vptr install)
      and then the facet installs -> these are CONSTRUCTION paths, count:=0.
  Z3 init-adjacent: @0x691A5B `mov [esi+0xA0],ebx` immediately followed by
      `mov [esi],0x7F1008` (same vptr-install adjacency; ebx value not asserted).
  Z4 parse-entry zero: @0x6918CF `mov [esi+0xA0],edi` preceded 5 bytes by
      `xor edi,edi` (33 ff) -- edi is CONSTANTLY 0 here, so this is the parse
      path's RE-ZEROING (kb/11's original comment '计数清零' stands).
      (The first pass of this gate mislabeled it 'non-zero init' on the sole
      reason 'source is a register' -- caught by the G-63 whole-segment re-check;
      the flip is now a killable fact: Z4 pins BOTH the xor window and the store
      window, C11 targets the xor pair. See CONFLICTS G-64.)
  Z7 inc-store (add entry): @0x691940/47 `mov eax,[esi+0xA0]; inc eax; mov [esi+0xA0],eax`
      -- the +=1 form inside the parse build loop.
  Z8 build loop: element pair stores @0x69192E/39 `mov [esi+eax*8+0xA4],ecx` and
      `... +0xA8],edx` (modrm rm==4 = SIB base=esi idx=eax scale=8, legit here per
      G-61) -- L-4's 'double dword per entry' resolved: element = [key@+0xA4, value@+0xA8];
      bounds imm 0x32 (50) at 0x691925/0x69194E (value semantics NOT claimed).
  Z5 loop-bound read: @0x691547 `mov esi,[edx+0xA0]; lea eax,[ecx+1]; cmp eax,esi;
      jl ...` -- count used as loop upper bound, independent of Save.
  Z6 Save path already pinned by R-044 X2 (0x691E0E) -- cross-referenced here as
      the census membership re-assertion, NOT re-pinned (avoid duplicate windows).

MUTATION: R045_MUTATE=VA=BYTE[,...] in-memory only.
Run: python re_atlas/tools/r045_count_lifecycle.py
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

for _item in os.environ.get("R045_MUTATE", "").split(","):
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

# Z1 ctor-cluster zero @0x6916C7: store imm0 + main vptr install right after
Z1 = read(0x6916C7, 0x10) == bytes.fromhex("c786a000000000000000c70608107f00")
check("Z1", Z1, "构造簇清零 @0x6916C7：`mov [esi+0xA0],0` 后 6 字节即 `mov [esi],0x7F1008`（主 vptr 安装）"
      " ⇒ +0xA0:=0 是构造路径（计数初值）")

# Z2 same shape second ctor variant @0x691C8B
Z2 = read(0x691C8B, 0x10) == bytes.fromhex("c786a000000000000000c70608107f00")
check("Z2", Z2, "第二构造变体 @0x691C8B：同型 `mov [esi+0xA0],0`+`mov [esi],0x7F1008` ⇒ 两条构造路径"
      "（不同构造现场）同一初值；不宣称二者类层次差异")

# Z3 init-adjacent store ebx @0x691A5B
Z3 = read(0x691A5B, 0x0C) == bytes.fromhex("899ea0000000c70608107f00")
check("Z3", Z3, "@0x691A5B `mov [esi+0xA0],ebx` 紧邻主 vptr 安装 ⇒ 初始化域第三形态（ebx 取值不宣称，"
      "只钉邻接关系）")

# Z4 parse-set @0x6918CF -- store edi (count written, NOT a zero-init).
# Boundary note (G-63): RTTI vfuncs are slot ENTRIES, not body bounds; we only assert
# the site is after slot-entry 0x6918A0 and before the next RTTI entry 0x691D50 --
# we do NOT claim exact function containment beyond that.
d = json.load(open(RTTI, encoding="utf-8"))
st = d["classes"]["ScriptTypeClass"]
vf = sorted(int(x, 16) for x in st["vfuncs"])
above = [v for v in vf if v > 0x6918A0][0]  # 0x691D50
Z4 = (read(0x6918CF, 7) == bytes.fromhex("89bea000000057")
      and read(0x6918CA, 12) == bytes.fromhex("33ff8d5e2489bea000000057")
      and 0x6918A0 in vf and vf.count(0x6918A0) == 1
      and 0x6918A0 <= 0x6918CF < above)
check("Z4", Z4, "解析入口清零 @0x6918CF：`mov [esi+0xA0],edi`，且 5 字节前 `xor edi,edi`（33 ff）"
      "⇒ **edi 恒 0：这是解析路径的清零**（kb/11 §10 原注释「计数清零」成立；本轮首版把"
      "「源=寄存器」误读成「写非常量」，被现场 xor 证据纠正——见 evidence §3）。"
      "位于 vfunc 槽入口 0x6918A0 与下一入口 0x%08X 之间的邻接区间（槽入口≠体边界）" % above)

# Z8 parse-loop element pair via SIB: [esi+eax*8+0xA4] and +0xA8 (legit rm==4 SIB, G-61),
# then count inc -- the "build table <=50 entries" form.
Z8 = (read(0x69192E, 7) == bytes.fromhex("898cc6a4000000")
      and read(0x691939, 7) == bytes.fromhex("8994c6a8000000")
      and read(0x691940, 0x0E) == bytes.fromhex("8b86a0000000408986a000000047")
      and read(0x691925, 4) == bytes.fromhex("83f8327d")
      and read(0x69194E, 4) == bytes.fromhex("83ff327c"))
check("Z8", Z8, "解析建表循环 @0x6918CF..0x691951：入口清零后 `mov [esi+eax*8+0xA4],ecx`/"
      "`mov [esi+eax*8+0xA8],edx`（modrm rm==4=**SIB**：base=esi idx=eax scale=8——G-61 判读；"
      "L-4 条目双 dword 就此细分：元素=[+0xA4 键,+0xA8 值] 8 字节对）；界比较两处 imm32=0x32"
      "（元素数上限 50，值语义不宣称）；随后 `read/inc/store` 计数（0x691940 窗含 `inc edi` 尾）")

# Z5 loop-bound read @0x691547 (count as upper bound, independent of Save)
Z5 = read(0x691547, 0xD) == bytes.fromhex("8bb2a00000008d41013bc67c12")
check("Z5", Z5, "循环上界读 @0x691547：`mov esi,[edx+0xA0]; lea eax,[ecx+1]; cmp eax,esi; jl`"
      " ⇒ +0xA0 作条目循环边界（独立于 Save 的语义证据）")

# Z7 read-inc-store (Push form) @0x691940: mov eax,[esi+0xA0]; inc eax; mov [esi+0xA0],eax
Z7 = read(0x691940, 0xD) == bytes.fromhex("8b86a0000000408986a0000000")
check("Z7", Z7, "读取-自增-写回 @0x691940：`mov eax,[esi+0xA0]; inc eax; mov [esi+0xA0],eax`"
      "（0x691940 读 + 0x691947 写为同一条自增的三个字节段）⇒ 计数 +=1 形态（增条目路径）")

# Z6 census re-assertion (exact sets from R-044 must hold in the SAME byte state this round)
def census(regs, opcodes):
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
                if 0x80 <= m <= 0xBF and (m & 7) != 4 and tbuf[i + 2:i + 6] == D32 and (m >> 3) & 7 in regs:
                    va = base + i
                    if 0x691000 <= va < 0x692100:
                        out.add(va)
            o = i + 1
    return out
stores = census(range(8), [0x89, 0xC7])
loads = census(range(8), [0x8B])
Z6 = (stores == {0x6916C7, 0x6918CF, 0x691947, 0x691A5B, 0x691C8B}
      and loads == {0x691547, 0x69191F, 0x691940, 0x691E0E, 0x691E4B, 0x691EAB})
check("Z6", Z6, "census 复现（与 R-044 X9 同判据、内存态再算）：存储={0x6916C7,0x6918CF,0x691947,"
      "0x691A5B,0x691C8B}、读取={0x691547,0x69191F,0x691940,0x691E0E,0x691E4B,0x691EAB}；"
      "本轮全部生命周期站点恰落 census 集内（站点即普查，非另择子集）")

UNCOUNTED = {"G0"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = all(ok for _, ok, _ in results)
print("\n== R-045 %d/%d 字节断言 PASS（G0 指纹不入分母）==" % (n_pass, n_tot), file=sys.stderr)
if not g0_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
