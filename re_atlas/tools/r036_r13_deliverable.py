# -*- coding: utf-8 -*-
"""R-036 (D-03 execution): the R1-3 deliverable, computed instead of asserted.

R-035 measured the CEILING of R1-3 and falsified its original goal: the image
can name at most 17 functions (0.15%), so R1-3 cannot raise coverage.  What
R-035 did NOT hand over was the substance behind that number.  This script
computes it and gates it.

WHAT IS DELIVERED (each value below is gated)
  A  17 functions that push a `Class::Method` literal, with the literal(s)
     each one pushes and the entry address of the function body
  B  69 source files from `__FILE__` = 74 distinct basenames, of which 5 have
     zero attributable sites
  C  2,589 debug string sites (path 1,299 + format 351 + text 939) and the
     ident class 3,688, i.e. the full 6,277-site population

WHAT IS **NOT** REPRODUCED (registered as a new debt, not silently "fixed")
  R-035 §六 reports debug = 761 functions.  Twelve independent (entry set,
  attribution rule) combinations bracket that number between 730 and 838 and
  none lands on 761.  The nearest is 758 (flat|T2 entry set, earliest-start
  first-wins), which is 3 short.  Per §7 of the charter a number that cannot be
  re-derived is registered rather than copied forward.

ATTRIBUTION RULE
  Per-entry CFG closure (no global `covered` short circuit -- that is right for
  counting entries and wrong for attribution, because the first function to
  reach a shared tail block would own every later site).  A site belongs to
  every entry whose closure contains it; ties are resolved by "earliest start
  address wins", which is the rule that reproduces R-035's path-class count
  exactly (425).

MUTATION SUPPORT (discipline #44)
  R036_MUTATE=VA=BYTE flips one byte in the in-memory image.

Run: python re_atlas/tools/r036_r13_deliverable.py
Writes the markdown table set to evidence/r036_r13_deliverable.txt via stdout
redirect; prints PASS/FAIL lines for the gate.
"""

import hashlib
import json
import os
import re
import struct
import sys

import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
RTTI = ROOT + r"\re_atlas\evidence\rtti\symbols.json"

IB = 0x400000
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
TLO, THI = 0x401000, 0x7E1000

SECTIONS = [
    (0x001000, 0x3DF38D, 0x001000, 0x3E0000),
    (0x3E1000, 0x030074, 0x3E1000, 0x031000),
    (0x412000, 0x367BE4, 0x412000, 0x06C000),
]

RAW = bytearray(open(EXE, "rb").read())

MUTATIONS = {}
for _item in os.environ.get("R036_MUTATE", "").split(","):
    if "=" in _item:
        _k, _v = _item.split("=", 1)
        MUTATIONS[int(_k, 0)] = int(_v, 0) & 0xFF


def _fileoff(va):
    rva = va - IB
    for s_rva, _vs, rp, rs in SECTIONS:
        if s_rva <= rva < s_rva + rs:
            return rp + (rva - s_rva)
    return None


for _va, _b in MUTATIONS.items():
    _fo = _fileoff(_va)
    if _fo is None:
        raise SystemExit(f"mutation target 0x{_va:08X} is not disk-backed")
    RAW[_fo] = _b
RAW = bytes(RAW)


def read_va(va, n):
    rva = va - IB
    for s_rva, _vs, rp, rs in SECTIONS:
        if s_rva <= rva < s_rva + rs:
            o = rp + (rva - s_rva)
            return RAW[o:o + n]
    return b""


TEXT = read_va(TLO, THI - TLO)
NT = len(TEXT)
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
XS = capstone.x86

# Expected values, measured 2026-10-23 on sha256 73201cc0..f67476.
EXP_PURE = 5
EXP_PREFIXED = 30
EXP_METHODS = 21
EXP_NAME_SITES = 35
EXP_NAME_FUNCS = 17
EXP_PATH_SITES = 1299
EXP_FMT_SITES = 351
EXP_TEXT_SITES = 939
EXP_IDENT_SITES = 3688
EXP_ALL_SITES = 6277
EXP_DEBUG_SITES = 2589
# R-039: aligned-decode re-verification of the 0x68 push sites. The byte scan
# (re.finditer(rb"\x68")) counts every 0x68 BYTE, including operand bytes of
# other instructions. Exactly ONE such site exists in the text class:
# 0x005BA0CE is the imm8 operand of `cmp ...,0x68` at 0x005BA0CC, and the four
# following bytes spell a pointer to an (unrelated) string, so it passes the
# printable-string filter. path/format/ident/name have zero such phantoms.
EXP_TEXT_ALIGNED = 938
EXP_ALL_ALIGNED = 6276
EXP_DEBUG_ALIGNED = 2588

EXP_FILES_ALL = 74
EXP_FILES_ATTR = 69
EXP_T2 = 886
EXP_FLATT2 = 16110
# R-035 §六's claim, quoted for the record -- NOT asserted, see module doc.
R035_DEBUG_FUNCS = 761

FAILS = []
RAN = []


def check(tag, ok, msg, extra=""):
    RAN.append(tag)
    print(("PASS\t" if ok else "FAIL\t") + tag + "\t" + msg
          + (("\t" + str(extra).replace("\n", " | ")) if extra else ""),
          file=sys.stderr)
    if not ok:
        FAILS.append(tag)


# ---------------------------------------------------------------- image
check("P1", hashlib.sha256(RAW).hexdigest() == SHA256,
      "sha256 与交付锚一致", hashlib.sha256(RAW).hexdigest()[:16])

# ---------------------------------------------------------------- entry set
e8_t, e9_t = set(), set()
for op, bucket in ((b"\xe8", e8_t), (b"\xe9", e9_t)):
    for m in re.finditer(op, TEXT):
        i = m.start()
        if i + 5 > NT:
            continue
        d = struct.unpack_from("<i", TEXT, i + 1)[0]
        t = TLO + i + 5 + d
        if TLO <= t < THI:
            bucket.add(t)

vt = set()
for _k, c in json.load(open(RTTI, encoding="utf-8"))["classes"].items():
    for s in c.get("vfuncs") or []:
        try:
            v = int(s, 16)
        except (TypeError, ValueError):
            continue
        if TLO <= v < THI:
            vt.add(v)

PE = 0x7CD80F
roots_call = e8_t | vt | {PE}
flat = e8_t | e9_t | vt | {PE}

_DC = {}


def dec1(cur):
    if cur in _DC:
        return _DC[cur]
    off = cur - TLO
    if off < 0 or off + 16 > NT:
        _DC[cur] = None
        return None
    out = None
    for insn in MD.disasm(TEXT[off:off + 16], cur):
        ops = [("imm", o.imm) if o.type == XS.X86_OP_IMM else ("x", None)
               for o in insn.operands]
        out = (insn.mnemonic, insn.op_str, insn.size, ops)
        break
    _DC[cur] = out
    return out


def closure(entry, cap=8000):
    """Per-entry reachable set.  `call` is NOT followed: that is another function."""
    seen = set()
    stack = [entry]
    while stack:
        cur = stack.pop()
        g = 0
        while True:
            g += 1
            if g > cap:
                break
            if not (TLO <= cur < THI) or cur in seen:
                break
            r = dec1(cur)
            if r is None:
                break
            mn, _o, size, ops = r
            seen.add(cur)
            nxt = cur + size
            if mn == "call":
                cur = nxt
                continue
            if mn == "jmp":
                if ops and ops[0][0] == "imm" and TLO <= ops[0][1] < THI:
                    cur = ops[0][1]
                    continue
                break
            if mn.startswith("j"):
                if ops and ops[0][0] == "imm" and TLO <= ops[0][1] < THI:
                    stack.append(ops[0][1])
                cur = nxt
                continue
            if mn.startswith("ret") or mn in ("hlt", "ud2", "iretd", "retf"):
                break
            cur = nxt
    return seen


PROLOGUE = re.compile(rb"^(?:\x55\x8b\xec|\x83\xec|\x81\xec|\x53|\x56|\x57|\x8b\xff|\x6a)")


def insns_to_ret(va, limit=0x800):
    n = 0
    off = va - TLO
    if off < 0 or off >= NT:
        return 0, False
    for insn in MD.disasm(TEXT[off:off + limit], va):
        n += 1
        if insn.mnemonic.startswith("ret"):
            return n, True
        if n > 900:
            break
    return n, False


# T2 = prologue-shaped heads that are NOT already flat roots (R-034's candidate
# definition, without the reachability filter).  flat | T2 = 16,110, the entry
# set R-035 §2 says the attribution ran on.
T2 = []
for pat, skip in ((rb"\xc3", 1), (rb"\xc2", 3)):
    for m in re.finditer(pat, TEXT):
        i = m.start()
        j = i + skip
        npad = 0
        while j < NT and TEXT[j] in (0x90, 0xCC):
            npad += 1
            j += 1
        if npad < 2:
            continue
        a = TLO + j
        if a in flat or not PROLOGUE.match(read_va(a, 8)):
            continue
        n, ok = insns_to_ret(a)
        if ok and n >= 3:
            T2.append(a)
T2 = sorted(set(T2))
flatT2 = sorted(flat | set(T2))
check("P2", len(T2) == EXP_T2 and len(flatT2) == EXP_FLATT2,
      f"归属用的入口集复现：T2 候选 **{len(T2)}** 个，`flat|T2` = "
      f"**{len(flatT2):,}**（= R-035 §2 所述的 16,110）",
      f"T2={len(T2)} flatT2={len(flatT2)}")

# ---------------------------------------------------------------- strings
PATHRE = re.compile(r"[\\/].*\.(cpp|h|c|hpp)$", re.I)
IDENT = re.compile(r"^[A-Za-z_~][A-Za-z0-9_:~<>@$]*$")
FMTSPEC = re.compile(r"%[-+ #0-9.*lhI]*[diouxXeEfgGaAcCsp%]")

str_sites = []
for m in re.finditer(rb"\x68", TEXT):
    i = m.start()
    if i + 5 > NT:
        continue
    imm = struct.unpack_from("<I", TEXT, i + 1)[0]
    b = read_va(imm, 400)
    z = b.find(b"\0")
    if z < 0 or z < 4:
        continue
    s = b[:z]
    if any(c < 0x20 or c > 0x7E for c in s):
        continue
    t = s.decode("ascii")
    if PATHRE.search(t):
        kind = "path"
    elif IDENT.match(t):
        kind = "ident"
    elif FMTSPEC.search(t):
        kind = "format"
    else:
        kind = "text"
    str_sites.append((TLO + i, t, kind))

KIND_ORDER = ("path", "format", "text", "ident")
by_kind = {k: [] for k in KIND_ORDER}
for va, t, k in str_sites:
    by_kind[k].append((va, t))

check("P3", len(by_kind["path"]) == EXP_PATH_SITES
      and len(by_kind["format"]) == EXP_FMT_SITES
      and len(by_kind["text"]) == EXP_TEXT_SITES
      and len(by_kind["ident"]) == EXP_IDENT_SITES
      and len(str_sites) == EXP_ALL_SITES,
      f"字符串站点四分类复现（**字节扫描口径**，R-039 对齐复核见 P3b）："
      f"path **{len(by_kind['path']):,}** / "
      f"format **{len(by_kind['format'])}** / text **{len(by_kind['text'])}** / "
      f"ident **{len(by_kind['ident']):,}** = 合计 **{len(str_sites):,}**",
      f"path={len(by_kind['path'])} fmt={len(by_kind['format'])} "
      f"text={len(by_kind['text'])} ident={len(by_kind['ident'])}")

# ---------------------------------------------------------------- P3b (R-039)
# R-038's lesson applied to THIS gate: `re.finditer(rb"\x68")` counts every
# 0x68 BYTE. A site is real only if the byte starts a `push imm32` whose
# immediate equals the scanned one. Linear decode with +1 resync (same method
# as verify_r035_claims.py P2b / r039_push_aligned.py).
_pushstart = {}
_cur = TLO
while _cur < THI:
    _r = dec1(_cur)
    if _r is None:
        _cur += 1
        continue
    _pushstart[_cur] = (_r[0], _r[3])
    _cur += _r[2]


def is_aligned_push(va):
    d = _pushstart.get(va)
    if not d or d[0] != "push" or not d[1] or d[1][0][0] != "imm":
        return False
    return d[1][0][1] == struct.unpack_from("<I", TEXT, va - TLO + 1)[0]


aligned_by_kind = {k: 0 for k in KIND_ORDER}
nonaligned_sites = []
for va, t, k in str_sites:
    if is_aligned_push(va):
        aligned_by_kind[k] += 1
    else:
        nonaligned_sites.append(va)
aligned_all = sum(aligned_by_kind.values())

# the single known phantom: 0x5BA0CE is the imm8 byte of `cmp eax,0x68`
# (83 F8 68) at 0x5BA0CC; its next four bytes spell a pointer into .data, so
# the printable-string filter accepts it. Confirm the covering instruction.
_phantom = 0x005BA0CE
_cov = dec1(_phantom - 2)
cov_is_cmp = (_cov is not None and _cov[0] == "cmp" and _cov[2] == 3)

check("P3b", aligned_all == EXP_ALL_ALIGNED
      and aligned_by_kind["text"] == EXP_TEXT_ALIGNED
      and aligned_by_kind["path"] == EXP_PATH_SITES
      and aligned_by_kind["format"] == EXP_FMT_SITES
      and aligned_by_kind["ident"] == EXP_IDENT_SITES
      and nonaligned_sites == [_phantom] and cov_is_cmp,
      f"**对齐复核**：四分类里只有 **{len(nonaligned_sites)}** 个字节扫描幻影，"
      f"落在 text 类：`0x{_phantom:08X}` 是 `0x{_phantom-2:08X}` 处 "
      f"`cmp eax,0x68`（83 F8 68）的 imm8 字节，其后四字节恰好拼出一个"
      f"合法字符串指针 ⇒ 通过可打印过滤。对齐口径 "
      f"path {aligned_by_kind['path']:,} / format {aligned_by_kind['format']} / "
      f"text **{aligned_by_kind['text']:,}**（字节扫描 939） / "
      f"ident {aligned_by_kind['ident']:,} = **{aligned_all:,}**"
      f"（字节扫描 {len(str_sites):,}）⇒ **交付数字差 1 个站点**，"
      f"debug 合计对齐口径 **{aligned_by_kind['path']+aligned_by_kind['format']+aligned_by_kind['text']:,}**（字节扫描 2,589）",
      f"aligned={aligned_all} phantoms={[hex(v) for v in nonaligned_sites]} "
      f"cov_is_cmp={cov_is_cmp}")


# ---------------------------------------------------------------- A: 17 functions
# The name literals end in a newline, so the strict printable filter that builds
# str_sites drops them.  They are scanned separately and their push sites are
# added to the attribution set below.
PREFIX = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_~][A-Za-z0-9_]*)+)")
PURE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_~][A-Za-z0-9_]*)+$")

starts = {}
for _lbl, rva, rp, rs in ((".rdata", 0x3E1000, 0x3E1000, 0x031000),
                          (".data", 0x412000, 0x412000, 0x06C000)):
    blob = RAW[rp:rp + rs]
    for m in re.finditer(rb"[\x20-\x7E]{4,400}", blob):
        starts[IB + rva + m.start()] = m.group().decode("ascii", "replace")

pure = {va: s for va, s in starts.items() if PURE.match(s.rstrip())}
pref = {va: PREFIX.match(s.rstrip()).group(1) for va, s in starts.items()
        if PREFIX.match(s.rstrip())}
methods = set(pref.values())

name_sites = []
for m in re.finditer(rb"\x68", TEXT):
    i = m.start()
    if i + 5 > NT:
        continue
    imm = struct.unpack_from("<I", TEXT, i + 1)[0]
    if imm in pref:
        name_sites.append((TLO + i, pref[imm]))

# ---------------------------------------------------------------- attribution
SITE_SET = {va for va, _t, _k in str_sites} | {va for va, _l in name_sites}
CL = {e: closure(e) for e in flatT2}
OWN = {}
for e in flatT2:
    for a in CL[e] & SITE_SET:
        OWN.setdefault(a, []).append(e)


def attribute(va):
    """Earliest-start owner: the rule that reproduces R-035's path-class count."""
    own = OWN.get(va)
    if not own:
        return []
    return [min(own)]

check("P4", len(pure) == EXP_PURE and len(pref) == EXP_PREFIXED
      and len(methods) == EXP_METHODS and len(name_sites) == EXP_NAME_SITES,
      f"函数名字面量复现：纯名 **{len(pure)}**、带前缀 **{len(pref)}**、"
      f"不同方法名 **{len(methods)}**、push 站点 **{len(name_sites)}**",
      f"pure={len(pure)} pref={len(pref)} methods={len(methods)} "
      f"sites={len(name_sites)}")

name_funcs = {}
for va, lit in name_sites:
    for o in attribute(va):
        name_funcs.setdefault(o, set()).add(lit)

check("P5", len(name_funcs) == EXP_NAME_FUNCS,
      f"35 个 push 站点去嵌套后归属到 **{len(name_funcs)}** 个函数"
      f"（R-035 报 17）⇒ 天花板 {len(name_funcs)}/14,242 = "
      f"{100.0*len(name_funcs)/14242:.2f}%",
      f"functions={len(name_funcs)}")

# ---------------------------------------------------------------- B: source files
def basename(t):
    return re.split(r"[\\/]", t)[-1]


file_sites = {}
file_funcs = {}
srcfiles = {}
for va, t in by_kind["path"]:
    key = basename(t).lower()
    srcfiles.setdefault(key, basename(t))
    file_sites[key] = file_sites.get(key, 0) + 1
    for o in attribute(va):
        file_funcs.setdefault(key, set()).add(o)

files_all = set(file_sites)
files_attr = {k for k in file_sites if file_funcs.get(k)}
check("P6", len(files_all) == EXP_FILES_ALL and len(files_attr) == EXP_FILES_ATTR,
      f"`__FILE__` 去重后 **{len(files_all)}** 个源文件，其中至少一个站点能归属的 "
      f"**{len(files_attr)}** 个（差 {len(files_all)-len(files_attr)} 个零归属）"
      f"⇒ R-035 的 69 的口径是「可归属文件数」",
      f"all={len(files_all)} attributed={len(files_attr)}")

# ---------------------------------------------------------------- C: debug sites
funcs_by_kind = {k: set() for k in KIND_ORDER}
unattributed = {k: 0 for k in KIND_ORDER}
attr_rows = []
for k in KIND_ORDER:
    for va, t in by_kind[k]:
        own = attribute(va)
        if not own:
            unattributed[k] += 1
            continue
        for o in own:
            funcs_by_kind[k].add(o)
        attr_rows.append((k, va, t, own))

debug_sites = sum(len(by_kind[k]) for k in ("path", "format", "text"))
debug_funcs = set()
for k in ("path", "format", "text"):
    debug_funcs |= funcs_by_kind[k]

check("P7", debug_sites == EXP_DEBUG_SITES,
      f"debug 类站点合计（path+format+text）= **{debug_sites:,}**",
      f"debug_sites={debug_sites}")

# The R-035 §六 figure is REGISTERED, not asserted.  Twelve closure-based
# rule/set combinations bracket it 730..838 and none lands on it; a 13th family
# (address-order rules, R-036b) does hit the TOTAL 761 but not the four columns.
# Either way there is no byte whose change would flip a "reproduces 761"
# assertion in a way that also pins the columns, so writing one would be a
# tautology.  Per §7 this is a structural census, kept out of the PASS count.
r035_gap = len(debug_funcs) - R035_DEBUG_FUNCS
print(f"REGISTER\tN1\tR-035 §六 报 debug 归属 **{R035_DEBUG_FUNCS}** 个函数"
      f"（path 425 / fmt 147 / text 289 / ident 277）。本轮闭包类 12 种口径落在 "
      f"730…838，无一命中；本轮「最早入口优先」得 **{len(debug_funcs)}**"
      f"（差 {r035_gap:+d}）。R-036b 的地址类规则（入口集 `roots_call|T2`=14,238 "
      f"+「最近前驱且闭包包含」）**命中合计 761，但四列为 418/149/290/289**，"
      f"与 425/147/289/277 不符 ⇒ **合计可复现、分列不可复现**，"
      f"该表不随 R-036 交付（结构性普查，不计入 PASS 数）",
      file=sys.stderr)



# ---------------------------------------------------------------- output
out = []
P = out.append
P("# R-036 · R1-3 交付件（D-03 裁决 A）")
P("")
P(f"镜像 sha256 `{hashlib.sha256(RAW).hexdigest()}`")
P("")
P(f"入口集：`flat|T2` = **{len(flatT2):,}**（flat {len(flat):,} + T2 候选 "
  f"{len(T2)}）。归属规则 = 逐入口 CFG 闭包 ∩ 站点集，冲突时**最早入口优先**。")
P("")
P("## A · 17 个函数名（可命名函数的全部产出）")
P("")
P(f"带 `Class::Method` 前缀的字面量 **{len(pref)}** 个（纯名 **{len(pure)}** 个），"
  f"不同方法名 **{len(methods)}** 个，push 站点 **{len(name_sites)}** 个，"
  f"去嵌套后归属到 **{len(name_funcs)}** 个函数。")
P("")
P("| 函数体入口 | 该函数 push 的名字 | 站点数 |")
P("|:--|:--|--:|")
for o in sorted(name_funcs):
    lits = sorted(name_funcs[o])
    ns = sum(1 for va, _l in name_sites if o in attribute(va))
    P(f"| `0x{o:08X}` | " + " · ".join("`%s`" % x for x in lits) + f" | {ns} |")
P("")
P("**注意**：`RadarClass::One_Time` 的 push 站点在 `0x652CF3`，函数体在 "
  "`0x652CF0`；归属给出 `0x63F7B0` 是因为 `0x63F7B0` 是 `jmp 0x652CF0` 的尾调用"
  "thunk（`e9 3b 35 01 00` + 11×`90`）且地址更早。「最早入口优先」会选中 thunk。"
  "两者指向同一函数体，本表登记入口，不据此断言本体地址。")
P("")
P("## B · 源文件归属（`__FILE__`）")
P("")
P(f"`__FILE__` 站点 **{len(by_kind['path']):,}** 个，去重后 **{len(files_all)}** "
  f"个源文件；其中 **{len(files_attr)}** 个至少有一个站点可归属。")
P("")
P("零归属的 5 个文件（全部站点都落在任何入口闭包之外）：")
P("")
zero = sorted(k for k in file_sites if not file_funcs.get(k))
P("| 源文件 | 站点 |")
P("|:--|--:|")
for k in zero:
    P(f"| `{srcfiles[k]}` | {file_sites[k]} |")
P("")
P("| 源文件 | 站点 | 归属函数数 |")
P("|:--|--:|--:|")
for key in sorted(file_sites, key=lambda k: (-file_sites[k], k)):
    P(f"| `{srcfiles[key]}` | {file_sites[key]} | {len(file_funcs.get(key, ()))} |")
P("")
P("## C · 站点归属总表")
P("")
P("| 类 | 站点 | 未归属 | 归属函数 |")
P("|:--|--:|--:|--:|")
for k in KIND_ORDER:
    P(f"| `{k}` | {len(by_kind[k]):,} | {unattributed[k]} | {len(funcs_by_kind[k])} |")
P(f"| **debug 合计** | **{debug_sites:,}** | "
  f"{sum(unattributed[k] for k in ('path','format','text'))} | **{len(debug_funcs)}** |")
P("")
P(f"站点合计 {len(str_sites):,}（字节扫描口径；对齐口径 **{aligned_all:,}**，"
  f"差 1 = `0x005BA0CE` 幻影，见 P3b 与 LEDGER R-039）。")

P("")
P("### C-注 · R-035 §六 的 761 不可复现")
P("")
P(f"R-035 §六 报 path 425 / format 147 / text 289 / ident 277，debug **761**。")
P(f"本轮在 12 种(入口集, 归属规则)组合下实测 debug 归属落在 **730…838**，")
P(f"无一命中 761；「最早入口优先」得 **{len(debug_funcs)}**（差 "
  f"{len(debug_funcs)-R035_DEBUG_FUNCS:+d}），其中 path 类 **{len(funcs_by_kind['path'])}** "
  f"精确等于 R-035 的 425。")
P("")
P("⇒ **R-035 §六 的函数列（425/147/289/277/761）中只有 path=425 可复现**；"
  "其余三列各差 1–3、合计差 3。该表**不是本轮交付的一部分**，登记为欠账。")
P("")
P("## D · 逐站点明细（可复核任意一行）")
P("")
P("| 类 | 站点 VA | 字符串 | 归属函数 |")
P("|:--|:--|:--|:--|")
for k, va, t, own in attr_rows:
    P(f"| `{k}` | `0x{va:08X}` | `{t}` | "
      + " · ".join(f"`0x{o:08X}`" for o in own) + " |")

sys.stdout.write("\n".join(out) + "\n")
print(f"\nRESULT: {len(RAN)-len(FAILS)}/{len(RAN)} PASS"
      + ("" if not FAILS else "  FAILED=" + ",".join(FAILS)),
      file=sys.stderr)
raise SystemExit(1 if FAILS else 0)
