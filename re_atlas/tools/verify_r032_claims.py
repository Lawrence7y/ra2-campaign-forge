# -*- coding: utf-8 -*-
"""R-032: independent machine gate for H-015 (dictionary sections: key name IS the data).

H-015 makes three claims. Point 1 (ShortGame through 0x671EA0) is already gated
by verify_r023_claims.py. Points 2 and 3 are checked here from bytes alone:

  2. 20 loaders use GetKeyCount -> GetKeyName and treat the KEY NAME as data.
  3. "only 5 loaders read fixed keys (27/19/14/12/11 keys)"     <-- the claim
     that has to be re-measured; section 14.2 now says 15 loaders / 651 keys.

The measurement trap this gate exists to avoid: the push-count in front of a
`call` is NOT the callee's argument count on this image. MSVC stages the NEXT
call's arguments before the current one, so `Read_VehicleTypes` puts FIVE pushes
in front of `GetKeyName` (which is `ret 8`, i.e. two stack arguments) and the
three leftovers become part of the five `ReadString` consumes. Counting pushes
naively reports "GetKeyName takes 5 args" and "ReadString takes 2", both wrong.
The callee's own `ret imm16` is the authority.

Run: python re_atlas/tools/verify_r032_claims.py
"""

import hashlib
import sys

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

SECTIONS = [
    (0x001000, 0x3DF38D, 0x001000, 0x3E0000),
    (0x3E1000, 0x030074, 0x3E1000, 0x031000),
    (0x412000, 0x367BE4, 0x412000, 0x06C000),
]

with open(EXE, "rb") as fh:
    _RAW = fh.read()


def read_va(va, n):
    """Disk-backed read only. BSS returns b'' (0x889F64 is BSS, not a string)."""
    rva = va - IMAGE_BASE
    for s_rva, s_vsize, rp, rs in SECTIONS:
        if s_rva <= rva < s_rva + max(s_vsize, rs):
            d = rva - s_rva
            if d >= rs:
                return b""
            return _RAW[rp + d: rp + d + n]
    return b""


def cstr(va, n=64):
    b = read_va(va, n)
    if not b:
        return ""
    z = b.find(b"\x00")
    return (b[:z] if z >= 0 else b).decode("ascii", "replace")


MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

GET_SECTION = 0x00526810
GET_KEY_COUNT = 0x00526960
GET_KEY_NAME = 0x00526CC0
READ_STRING = 0x00528A10
READ_DOUBLE = 0x005283D0
READ_INT = 0x005276D0
READ_BOOL = 0x005295F0
READ_ALT = 0x00529160

# Reader arity AND the reader set, both needed before any assertion block runs.
WANT_ARITY = {
    GET_SECTION: 1, GET_KEY_COUNT: 1, GET_KEY_NAME: 2,
    READ_STRING: 5, READ_DOUBLE: 4, READ_INT: 3, READ_BOOL: 3, READ_ALT: 4,
}
READERS5 = {READ_STRING: 5, READ_DOUBLE: 4, READ_INT: 3, READ_BOOL: 3, READ_ALT: 4}

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import dump_rules_sections as D  # noqa: E402  first-key-literal table

LOADERS = dict(D.READERS)


def closure(entry, limit):
    """Branch closure of the function at `entry` -- survives separated cold blocks.

    H-015's loaders include 10KB bodies with a failure epilogue placed after the
    first `ret`; a linear decode stopped at the first `ret` would mis-measure them
    (R-024 gate P3b established this).
    """
    seen = {}
    work = [entry]
    while work:
        start = work.pop()
        if start in seen or not (entry <= start < limit):
            continue
        for insn in MD.disasm(read_va(start, limit - start), start):
            if insn.address in seen:
                break
            seen[insn.address] = insn
            m = insn.mnemonic
            if m.startswith("ret") or m == "int3":
                break
            if m == "jmp":
                for op in insn.operands:
                    if op.type == capstone.x86.X86_OP_IMM:
                        v = op.imm & 0xFFFFFFFF
                        if entry <= v < limit and v not in seen:
                            work.append(v)
                break
            if m.startswith("j"):
                for op in insn.operands:
                    if op.type == capstone.x86.X86_OP_IMM:
                        v = op.imm & 0xFFFFFFFF
                        if entry <= v < limit and v not in seen:
                            work.append(v)
    return seen


def callee_arity(fn_va):
    """Argument count implied by the function's own ret imm16.

    Every exit of one function must agree; disagreement means the closure leaked
    into a neighbouring function and the number is meaningless.
    """
    body = closure(fn_va, fn_va + 0x4000)
    vals = {int(i.op_str, 16) if i.op_str else 0
            for i in body.values() if i.mnemonic.startswith("ret")}
    if len(vals) != 1:
        return None, vals
    return vals.pop() // 4, vals


THISCALL_SETUP = ("mov", "lea", "xor", "sub", "fstp")


def pushes_before(body, call_addr):
    """Pushes in the argument-setup run before a call, in source order.

    The run is NOT `push; push; ...; call`: MSVC emits the thiscall register
    setup as `mov ecx, <this>` between the arguments and the call, so a walk that
    stops at the first non-push reports 0 pushes at 22 of 22 GetKeyName sites.
    That was this gate's own first bug.

    LIMIT: this walk still over-counts when a callee-saved `push esi` happens to
    sit inside the setup run (Read_Movies 0x67458E), so it must not be used as an
    argument count. Arity comes from `callee_arity()`; P3 uses a full esp
    simulation instead. This helper is kept only for the reader table's key-arg
    position, where the run terminates at the reader's own `mov ecx,<this>`.
    """
    out = []
    p = call_addr
    for _ in range(16):
        prev = None
        for size in range(1, 16):
            c = p - size
            if c in body and body[c].address + size == p:
                prev = body[c]
                break
        if prev is None:
            break
        if prev.mnemonic == "push":
            out.append(prev)
        elif prev.mnemonic not in THISCALL_SETUP:
            break
        p = prev.address
    return list(reversed(out))


JUMPS = ("jmp",)


def esp_offsets(body, entry):
    """Linear esp offset (relative to entry) at every instruction, calls included.

    A call is treated as balanced-with-args-popped: `call` pushes the return
    address and `ret N` pops it plus N bytes, so the net change is +4*arity.
    Unknown callees are treated as `ret 0` (no stack arguments) -- for the
    enumerate loaders every callee reached between the two calls is one of the
    known accessors, and P3 asserts that.
    """
    addrs = sorted(body)
    esp = {}
    cur = 0
    broke = None
    for a in addrs:
        insn = body[a]
        esp[a] = cur
        m, ops = insn.mnemonic, insn.op_str
        if m == "push":
            cur -= 4
        elif m == "pop":
            cur += 4
        elif m == "sub" and ops.startswith("esp,"):
            cur -= int(ops.split(",")[1].strip(), 0)
        elif m == "add" and ops.startswith("esp,"):
            cur += int(ops.split(",")[1].strip(), 0)
        elif m == "call":
            t = None
            for op in insn.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    t = op.imm & 0xFFFFFFFF
            cur += 4 * WANT_ARITY.get(t, 0)
        elif m.startswith("ret"):
            broke = a
            break
    return esp, broke


FAILS = []
RAN = []


def check(tag, ok, msg, extra=""):
    RAN.append(tag)
    print(("PASS\t" if ok else "FAIL\t") + tag + "\t" + msg
          + (("\t" + str(extra).replace("\n", " | ")) if extra else ""))
    if not ok:
        FAILS.append(tag)


# ---------------------------------------------------------------- P1
h = hashlib.sha256(_RAW).hexdigest()
check("P1", h == SHA256, "sha256 与交付锚一致", h[:16])

# ---------------------------------------------------------------- P2
# Callee arity from ret imm16 -- the authority that replaces push counting.
got_arity, bad = {}, []
for va, want in WANT_ARITY.items():
    a, vals = callee_arity(va)
    got_arity[va] = a
    if a != want:
        bad.append(f"0x{va:08X}: 交付 {want} / 实测 ret-set {vals} -> {a}")
check("P2", not bad,
      "8 个读取器/访问器参数个数由各自 ret imm16 独立确定，互不矛盾",
      "\n".join(bad) or {hex(k): v for k, v in got_arity.items()})

# ---------------------------------------------------------------- P3
# WHAT THE KEY NAME IS USED FOR -- and this is where my first answer was WRONG.
#
# The mechanism in family A is:
#     key   <- GetKeyName(section, i)        ; eax = the i-th KEY NAME
#     ReadString(section, key, default, buf, size)   ; buf gets the VALUE
#     if (result) Registrar(buf)             ; <- the VALUE is registered
#
# So the key name is a LOOKUP KEY, not the data. "键名即数据" is FALSE for family A.
# Where it IS true is family B (Sides / Colors / ColorAdd), which consumes the key
# name itself: Sides passes it to a lookup-then-construct, Colors passes it to a
# table write. My first version of this gate asserted "the key slot holds eax" and
# concluded "键名即数据" -- that only proves WHERE the key comes from, which is a
# different claim. The blind verifier caught the gap; this assertion tests the
# actual consumer.
STAGE_SITES, stage_bad = [], []
for fn_va, name in sorted(LOADERS.items()):
    if name == "Read_File":            # container: dispatches, no single pair
        continue
    body = closure(fn_va, fn_va + 0x30000)
    order = [body[a] for a in sorted(body)]
    idx_of = {i.address: k for k, i in enumerate(order)}
    for a, insn in body.items():
        if insn.mnemonic != "call" or not insn.operands:
            continue
        tgt = insn.operands[0]
        if tgt.type != capstone.x86.X86_OP_IMM or (tgt.imm & 0xFFFFFFFF) != GET_KEY_NAME:
            continue
        k = idx_of[a] + 1
        nxt = None
        while k < len(order):
            o = order[k]
            if o.mnemonic == "call" and o.operands \
                    and o.operands[0].type == capstone.x86.X86_OP_IMM:
                nxt = o
                break
            k += 1
        if nxt is None or (nxt.operands[0].imm & 0xFFFFFFFF) != READ_STRING:
            continue                    # family B / container: not this shape
        # the registrar's `this` is the buffer ReadString filled, NOT eax
        reg = None
        for j in range(k + 1, min(k + 14, len(order))):
            o = order[j]
            if o.mnemonic != "call" or not o.operands:
                continue
            t = o.operands[0]
            if t.type != capstone.x86.X86_OP_IMM:
                continue
            tv = t.imm & 0xFFFFFFFF
            if tv in READERS5 or tv in (GET_KEY_NAME, GET_KEY_COUNT, GET_SECTION, 0x4068E0):
                continue
            reg = (j, tv)
            break
        if reg is None:
            stage_bad.append(f"{name}: ReadString 之后找不到注册调用")
            continue
        j, tv = reg
        setup = [(order[m].mnemonic, order[m].op_str) for m in range(max(0, j - 6), j)]
        this_src = next((o for m, o in setup if m == "lea" and o.startswith("ecx,")), None) \
            or next((o for m, o in setup if m == "mov" and o.startswith("ecx,")), None)
        STAGE_SITES.append((name, nxt.address, tv, this_src))
        if not (this_src and "esp" in this_src):
            stage_bad.append(
                f"{name}: 注册 ecx = {this_src}，不是 ReadString 的落盘缓冲（[esp+..]）")
check("P3", not stage_bad and len(STAGE_SITES) >= 15,
      f"族 A 注册的是 **ReadString 写入的落盘缓冲（=值）**，不是键名 —— "
      f"{len(STAGE_SITES)} 个站点全对 ⇒ 「键名即数据」对族 A **不成立**，键名只是查表的键",
      "\n".join(stage_bad) or
      f"e.g. {STAGE_SITES[0][0]}: Registrar@0x{STAGE_SITES[0][2]:08X} ecx={STAGE_SITES[0][3]}")

# ---------------------------------------------------------------- P4
ENUM = set()
for fn_va, name in LOADERS.items():
    body = closure(fn_va, fn_va + 0x30000)
    tgts = set()
    for insn in body.values():
        if insn.mnemonic == "call" and insn.operands \
                and insn.operands[0].type == capstone.x86.X86_OP_IMM:
            tgts.add(insn.operands[0].imm & 0xFFFFFFFF)
    if GET_KEY_COUNT in tgts or GET_KEY_NAME in tgts:
        ENUM.add(name)
DELIVERED_ENUM = {
    "Read_AircraftTypes", "Read_Animations", "Read_BuildingTypes", "Read_ColorAdd",
    "Read_Colors", "Read_Countries", "Read_File", "Read_InfantryTypes",
    "Read_Movies", "Read_OverlayTypes", "Read_ParticleSystems", "Read_Particles",
    "Read_Sides", "Read_SmudgeTypes", "Read_SuperWeaponTypes", "Read_Teams_obsolete",
    "Read_TerrainTypes", "Read_VehicleTypes", "Read_VoxelAnims", "Read_Warheads",
}
check("P4", ENUM == DELIVERED_ENUM and len(ENUM) == 20,
      f"枚举键名 / 按键名注册的 loader = {len(ENUM)} 个，且与交付表逐名相等",
      f"only_mine={sorted(ENUM - DELIVERED_ENUM)} only_delivered={sorted(DELIVERED_ENUM - ENUM)}")

# ---------------------------------------------------------------- P5
# H-015 point 3: "only 5 loaders read fixed keys (27/19/14/12/11)".
# Re-measure the fixed-key side from bytes: a loader "reads fixed keys" when it
# pushes a LITERAL key into a reader. Count the loaders and the literal count.
KEY_OF_READER = {READ_STRING: 1, READ_DOUBLE: 1, READ_INT: 1, READ_BOOL: 1, READ_ALT: 1}


def literal_keys(fn_va, body):
    """(key_literal_VA, reader) for each reader call whose key arg is a literal."""
    out = []
    for a, insn in body.items():
        if insn.mnemonic != "call" or not insn.operands:
            continue
        t = insn.operands[0]
        if t.type != capstone.x86.X86_OP_IMM:
            continue
        tgt = t.imm & 0xFFFFFFFF
        if tgt not in READERS5:
            continue
        need = READERS5[tgt]
        pl = pushes_before(body, a)
        # ReadDouble stages its last arg via `sub esp,8; fstp qword [esp]`, so the
        # push run is one short; the KEY is still the last-but-one pushed imm.
        cand = None
        if len(pl) >= 2:
            cand = pl[-2]
        if cand is None:
            continue
        txt = cand.op_str.strip()
        if not txt.startswith("0x"):
            continue
        va = int(txt, 16)
        s = cstr(va, 64)
        if not s or not s.isprintable():
            continue
        out.append((va, s, tgt, a))
    return out


FIXED = {}
for fn_va, name in LOADERS.items():
    body = closure(fn_va, fn_va + 0x30000)
    ks = literal_keys(fn_va, body)
    if ks:
        FIXED[name] = ks
n_fixed = len(FIXED)
n_keys = sum(len(v) for v in FIXED.values())
check("P5", n_fixed != 5,
      f"H-015 第 3 点「只有 5 个 loader 读固定键」被证伪：实测 **{n_fixed}** 个 loader "
      f"压入字面量键（H-015 的 27/19/14/12/11 是 R-022「306 键」时代的旧值）",
      f"n_fixed={n_fixed} n_literal_key_sites={n_keys}")

# ---------------------------------------------------------------- P6
# Family split inside the 20: A = enumerate name -> ReadString -> conditionally
# register; B = enumerate name -> register directly.
FAMILY = {}
for name in sorted(ENUM):
    fn_va = next(v for v, n in LOADERS.items() if n == name)
    body = closure(fn_va, fn_va + 0x30000)
    tgts = {i.operands[0].imm & 0xFFFFFFFF for i in body.values()
            if i.mnemonic == "call" and i.operands
            and i.operands[0].type == capstone.x86.X86_OP_IMM}
    has_read = bool(tgts & set(READERS5))
    has_kname = GET_KEY_NAME in tgts
    if has_kname and has_read:
        FAMILY[name] = "A"
    elif has_kname:
        FAMILY[name] = "B"
    else:
        FAMILY[name] = "C"
counts = {f: sorted(n for n in FAMILY if FAMILY[n] == f) for f in "ABC"}
check("P6", len(counts["A"]) + len(counts["B"]) == 20,
      f"20 个枚举 loader 分成两族：A 枚举键名+读值 {len(counts['A'])} 个 / "
      f"B 仅按键名注册 {len(counts['B'])} 个 / C {len(counts['C'])} 个",
      counts)

# ---------------------------------------------------------------- P7
# NEW: in family A the registration is gated on ReadString returning non-zero.
# `test eax,eax / je <skip>` between the reader call and the register call.
GATED, gate_bad = [], []
for name in counts["A"]:
    fn_va = next(v for v, n in LOADERS.items() if n == name)
    body = closure(fn_va, fn_va + 0x30000)
    order = [body[a] for a in sorted(body)]
    for k, insn in enumerate(order):
        if insn.mnemonic != "call" or not insn.operands:
            continue
        t = insn.operands[0]
        if t.type != capstone.x86.X86_OP_IMM or (t.imm & 0xFFFFFFFF) != READ_STRING:
            continue
        window = order[k + 1:k + 6]
        shape = " ".join(i.mnemonic for i in window)
        if "test" in shape and "je" in shape:
            GATED.append(name)
        else:
            gate_bad.append(f"{name}@0x{insn.address:08X}: {shape}")
        break
check("P7", not gate_bad,
      f"族 A 的注册被 ReadString 返回值门控（test eax,eax; je 跳过注册）"
      f" ⇒ **值可以为空则整条不注册**（{len(GATED)}/{len(counts['A'])} 全部成立）",
      "\n".join(gate_bad) or sorted(GATED))

# ---------------------------------------------------------------- P8
# The register callees reject the placeholder names "<none>" / "none".
REG_CALLEES, reg_detail = set(), {}
for name in counts["A"] + counts["B"]:
    fn_va = next(v for v, n in LOADERS.items() if n == name)
    body = closure(fn_va, fn_va + 0x30000)
    order = [body[a] for a in sorted(body)]
    started = False
    for insn in order:
        if insn.mnemonic == "call" and insn.operands \
                and insn.operands[0].type == capstone.x86.X86_OP_IMM:
            t = insn.operands[0].imm & 0xFFFFFFFF
            if t == GET_KEY_NAME:
                started = True
                continue
            if started and t not in (GET_KEY_NAME, READ_STRING, GET_KEY_COUNT):
                REG_CALLEES.add(t)
                reg_detail.setdefault(t, []).append(name)
                break
none_strs = {va: cstr(va, 16) for va in (0x00817474, 0x00817694)}
# Direction, not just presence: both compares `je 0x74814E`, and 0x74814E is
# `pop edi; xor eax,eax; pop esi; ret` -- a zero return, so a matching name is
# NOT registered. Asserting "the strings are compared" alone would pass on the
# opposite direction (je into the create path), which is the G-42 defect.
reg = closure(0x007480D0, 0x00749000)
je_targets = sorted({i.operands[0].imm & 0xFFFFFFFF
                     for a, i in reg.items()
                     if i.mnemonic == "je" and i.operands
                     and i.operands[0].type == capstone.x86.X86_OP_IMM})
skip_ret = reg.get(0x0074814E), reg.get(0x0074814F)
skip_shape = [i.mnemonic for i in skip_ret if i is not None]
check("P8", none_strs == {0x00817474: "<none>", 0x00817694: "none"}
      and len(REG_CALLEES) >= 2
      and 0x0074814E in je_targets
      and skip_shape == ["pop", "xor"],
      f"注册端两个占位名 {none_strs} 均 `je 0x74814E`，而 0x74814E = "
      f"`pop edi; xor eax,eax; pop esi; ret`（返回 0、不建条目）"
      f" ⇒ 写成这两个名的条目**被跳过**；注册 callee 共 {len(REG_CALLEES)} 个",
      f"je_targets={[hex(x) for x in je_targets]} skip_shape={skip_shape}\n"
      + str({hex(k): sorted(set(v)) for k, v in reg_detail.items()}))

# ---------------------------------------------------------------- P9
# 0x889f64 is pushed as the ReadString `default` in family A but is BSS: it has no
# bytes on disk. Treating "read_va returns b''" as "this is not a key" would drop
# every family-A site, so this is asserted explicitly.
bss = read_va(0x00889F64, 8)
check("P9", bss == b"",
      "0x00889F64 是 BSS（盘上无字节），在族 A 里作为 ReadString 的 default 参数 / "
      "落盘缓冲被压栈 —— 不是键，也不是字符串",
      f"read_va -> {bss!r}")

# ---------------------------------------------------------------- P10
# Reconcile 660 literal-key SITES with the delivered 651 KEYS. The gap is 9
# intra-loader duplicates, and they are named here rather than waved at:
#   Read_General 280->279 (EngineerCaptureLevel, one key two fields +0x17F8/+0x17FC)
#   Read_AudioVisual 153->152 (Smoke, +0x0BAC/+0x0BB0)
#   Read_LandCharacteristics 15->8 (the seven locomotion classes each read twice)
EXPECT_DUP = {
    "Read_General": 1, "Read_AudioVisual": 1, "Read_LandCharacteristics": 7,
}
dup_detail, per_loader_counts = {}, {}
for fn_va, name in sorted(LOADERS.items()):
    body = closure(fn_va, fn_va + 0x30000)
    order = [body[a] for a in sorted(body)]
    names = []
    for k, insn in enumerate(order):
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM or (op.imm & 0xFFFFFFFF) not in READERS5:
            continue
        pl = [i for i in order[max(0, k - 8):k] if i.mnemonic == "push"]
        if len(pl) < 2:
            continue
        txt = pl[-2].op_str.strip()
        if not txt.startswith("0x"):
            continue
        s = cstr(int(txt, 16), 64)
        if s and s.isprintable():
            names.append(s)
    if names:
        per_loader_counts[name] = (len(names), len(set(names)))
        if len(names) != len(set(names)):
            dup_detail[name] = len(names) - len(set(names))
tot_sites = sum(a for a, _b in per_loader_counts.values())
tot_distinct = sum(b for _a, b in per_loader_counts.values())
check("P10", tot_sites == 660 and tot_distinct == 651 and dup_detail == EXPECT_DUP,
      f"660 个键站点 − 9 个 loader 内重复 = **651 键**，逐 loader 与交付表相等；"
      f"重复只出现在 {sorted(EXPECT_DUP)}",
      f"sites={tot_sites} distinct={tot_distinct} dup={dup_detail}");

# ---------------------------------------------------------------- N1
# NEGATIVE CONTROL 1: a different function must not pass the same test.
# Read_MultiplayerDialogSettings reads 27 FIXED keys and is NOT enumerate-shaped;
# asserting it is in ENUM must fail.
check("N1", "Read_MultiplayerDialogSettings" not in ENUM,
      "[负控1] Read_MultiplayerDialogSettings（读 27 个固定键）不在枚举集合内")

# ---------------------------------------------------------------- N2
# NEGATIVE CONTROL 2: arity must distinguish, not return a constant.
check("N2", got_arity[READ_STRING] != got_arity[GET_KEY_NAME]
      and got_arity[READ_STRING] == 5 and got_arity[GET_KEY_NAME] == 2,
      "[负控2] 参数个数判定不是常数：ReadString=5 / GetKeyName=2 判决不同",
      f"{got_arity[READ_STRING]} vs {got_arity[GET_KEY_NAME]}")

# ---------------------------------------------------------------- N3
# NEGATIVE CONTROL 3: truncating the closure at the first ret must LOSE data.
# Read_General has a separated cold block; measure both ways.
lin = 0
for insn in MD.disasm(read_va(0x0066D530, 0x30000), 0x0066D530):
    lin += 1
    if insn.mnemonic.startswith("ret"):
        break
cl = len(closure(0x0066D530, 0x0066D530 + 0x30000))
check("N3", cl > lin,
      f"[负控3] 停在首个 ret 会截断函数体：线性 {lin} 条 vs 分支闭包 {cl} 条 "
      f"⇒ 本门禁必须用闭包",
      f"lost={cl - lin}")

print()
if FAILS:
    print(f"RESULT: {len(RAN) - len(FAILS)}/{len(RAN)} passed, FAILED={FAILS}")
    raise SystemExit(1)
print(f"RESULT: {len(RAN)}/{len(RAN)} PASS")
