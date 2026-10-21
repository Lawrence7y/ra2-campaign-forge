"""R-022: per-loader INI key inventory for RulesClass.

The campaign compiler's third question (after "which section" and "which key
maps to which field") is "which keys does this loader actually read". That
decides what has to be present in a generated rulesmd.ini, and it is the level at
which a silently-ignored key shows up.

Scope and honesty about it: only keys pushed as STRING LITERALS are recovered.
Keys held in a register, built at run time, or taken from a BSS buffer cannot be
seen statically, and several loaders enumerate the section's key NAMES instead of
reading fixed keys at all (Read_Sides, Read_BuildingTypes). The tool therefore
reports per loader both the recovered literals AND whether the loader uses the
"enumerate keys" shape, rather than implying the list is complete.

Run: python re_atlas/tools/dump_rules_keys.py
"""

import os
import re
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402  (read_va with per-section bounds)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

# Loader bodies are bounded by their own FIRST `ret`.
#
# The window must be generous enough not to cut a real body short: the biggest
# loader here is Read_AudioVisual (0x6691E0 -> first ret at 0x66B8EE, 0x2710
# bytes = 10 KB). An earlier version used 0x1000 and therefore reported a
# TRUNCATED key list for four loaders -- Read_AI, Read_AudioVisual,
# Read_CombatDamage and Read_General -- without any indication that it had run
# out of window. 0x8000 clears every loader in the table with margin; the tool
# now ALSO reports any loader that fails to reach a `ret`, so a future window
# shortfall shows up instead of silently shrinking a key list.
WINDOW = 0x8000

GET_KEY_COUNT = 0x00526960
GET_KEY_NAME = 0x00526CC0

# Reader -> number of (section, key, ...) stack arguments that carry data.
# Only the readers whose argument 2 is the KEY are listed; GetSection/GetKeyCount
# take the section only and have no key to recover.
READER_KEYS = {
    0x00528A10: 4,   # ReadString(section, key, dst, cap)
    0x00528F00: 4,   # ReadUnicodeString
    0x00529160: 3,   # ReadStringtableEntry(section, key, dst)
    0x005283D0: 4,   # ReadDouble(section, key, default)
    0x005276D0: 3,   # ReadInteger(section, key, default)
    0x005295F0: 3,   # ReadBool(section, key, default)
}

_TRUNCATED = []


def body_insns(fn_va, window=WINDOW):
    out = []
    ended = False
    for insn in md.disasm(D.read_va(fn_va, window), fn_va):
        out.append(insn)
        if insn.mnemonic.startswith("ret"):
            ended = True
            break
    if not ended:
        _TRUNCATED.append(fn_va)
    return out


def printable(s):
    return bool(s) and 2 <= len(s) < 40 and all(0x20 < ord(c) < 0x7F for c in s)


def is_section_operand(insn, insns_index, insns):
    """True when this push is a SECTION name being handed to a delegate.

    Read_File pushes `Warheads` immediately before `call GetKeyCount` and before
    `call GetKeyName`, and pushes `Easy` / `Normal` / `Difficult` immediately
    before `call Read_Difficulty` (whose section name is a PARAMETER). None of
    those are keys it reads -- they are the sections it dispatches to, and
    reporting them as keys invented four entries in a loader that reads none.

    The test is positional rather than name-based on purpose: a set of known
    section names cannot work here because the list sections (`Warheads`,
    `Easy`, ...) are exactly the ones missing from the pointer table.
    """
    for nxt in insns[insns_index + 1: insns_index + 9]:
        if nxt.mnemonic != "call" or not nxt.operands:
            # argument setup between the push and the call is normal
            # (`push 0x83a0d0; mov ecx,esi; call GetKeyCount`)
            continue
        op = nxt.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            return False
        # GetSection / GetKeyCount / GetKeyName take the section first, and
        # Read_Difficulty takes it as the first stack parameter.
        return (op.imm & 0xFFFFFFFF) in (0x00526810, 0x00526960, 0x00526CC0,
                                         0x0066D270)
    return False


def is_key_by_variable_name(insn, insns_index, insns):
    """True when this push is the SECTION half of a run-time keyed read.

    Read_File has two shapes, and the section is on DIFFERENT sides in each:

        push <key from GetKeyName>     ; eax
        push 0x83A0D0                  ; "Warheads"  <- section, AFTER the key
        call ReadString

        push 0x83A0D0                  ; "Warheads"  <- section, BEFORE the key
        push eax                       ; key from GetKeyName
        call ReadString

    So the test cannot be positional on the section alone. What identifies the
    pair is: within a short window around this push there is a reader call
    (ReadString/ReadStringtableEntry), AND one of the pushes in that window is a
    REGISTER carrying a value from GetKeyName (0x526CC0). When both hold, the
    immediate in the window is the section, not a key.

    A looser version of this suppressed Read_AI's `BuildConst`, which sits in
    `push <dst>; push 0x889f64; push BuildConst; push <sec>` and has no
    GetKeyName in the window -- the control caught it.
    """
    lo = max(0, insns_index - 6)
    hi = min(len(insns), insns_index + 7)
    win = insns[lo:hi]
    has_reader = False
    for n in win:
        if n.mnemonic == "call" and n.operands:
            op = n.operands[0]
            if op.type == capstone.x86.X86_OP_IMM and                     (op.imm & 0xFFFFFFFF) in (0x00528A10, 0x00529160):
                has_reader = True
                break
    if not has_reader:
        return False
    for n in win:
        if n.mnemonic == "call" and n.operands:
            op = n.operands[0]
            if op.type == capstone.x86.X86_OP_IMM and                     (op.imm & 0xFFFFFFFF) == 0x00526CC0:
                return True
    return False


def key_literals(insns, section=None):
    """The key of each reader call, taken from the argument right before it.

    Call shape for every reader in this file:

        push <default value or dst>     ; argument 3+
        push <KEY literal>              ; argument 2 -- this is the key
        push <section>                  ; argument 1
        mov  ecx, <this>
        call ReadInteger / ReadBool / ...

    so the key is the LAST immediate-string push before the call, and a function
    body can contain hundreds of these. Collecting every literal push in the body
    (the previous approach) over-counts whenever a helper argument is itself a
    string, and under-counts nothing but cannot say which call a key belongs to.

    The section name is the push immediately before the call and is excluded by
    position (and by equality when `section` is known). Section names that are
    being handed to a delegate (`Warheads`, `Easy`, ...) never precede a key read
    in this shape, so they drop out naturally.
    """
    out = []
    seen = set()
    for idx, insn in enumerate(insns):
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        tgt = op.imm & 0xFFFFFFFF
        if tgt not in READER_KEYS:
            continue
        want = READER_KEYS[tgt]          # how many stack args the reader takes
        # Walk back over the argument setup (skipping mov/lea this-pointer work)
        # and collect the pushed immediates in reverse order.
        got = []
        j = idx - 1
        guard = 0
        while j >= 0 and guard < 24 and len(got) < want + 2:
            n = insns[j]
            if n.mnemonic == "push":
                got.append(n)
            elif n.mnemonic not in ("mov", "lea", "xor"):
                break
            j -= 1
            guard += 1
        if not got:
            continue
        # got[0] is the section (last pushed), got[1] is the key for the
        # (section, key, ...) readers.
        if len(got) < 2:
            continue
        cand = got[1]
        txt = cand.op_str.strip()
        if not txt.startswith("0x") or "[" in txt:
            continue
        s = D.cstr(int(txt, 16), 48)
        if not printable(s):
            continue
        if s == section or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def shape_flags(insns):
    """How this loader addresses keys -- matters as much as the literal list."""
    calls = []
    for insn in insns:
        if insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                calls.append(op.imm & 0xFFFFFFFF)
    return {
        "enumerates_keys": GET_KEY_COUNT in calls or GET_KEY_NAME in calls,
        "registers_keys": any(c == GET_KEY_NAME for c in calls),
    }


# Functions that dispatch to several sections and therefore have no single
# section name. section_used_by() returns the LAST section it can resolve for
# these, which is not "the section this function reads" -- reporting it as such
# made Read_File come out as section 'ColorAdd' with four fake keys
# (Warheads / Easy / Normal / Difficult), all of which are SECTION names.
CONTAINERS = {"Read_File"}



def multi_section_count(insns):
    """How many GetSection/GetKeyCount calls the body makes."""
    n = 0
    for insn in insns:
        if insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) in (0x00526810, 0x00526960):
                n += 1
    return n


def main():
    rows = []
    for fn_va, name in sorted(D.READERS.items(), key=lambda kv: kv[1]):
        insns = body_insns(fn_va)
        got = D.section_used_by(fn_va)
        sec = got[1] if got and got[1] else None
        nsec = multi_section_count(insns)
        if name in CONTAINERS or nsec > 2:
            sec = None          # dispatches to several sections: no single answer
        keys = key_literals(insns, sec)
        flags = shape_flags(insns)
        rows.append((name, fn_va, sec, keys, flags, len(insns), nsec))

    print("=== 每个 loader 读到的键字面量（按 loader 分组）===")
    total = 0
    for name, fn_va, sec, keys, flags, n_insn, nsec in rows:
        total += len(keys)
        mode = []
        if flags["enumerates_keys"]:
            mode.append("枚举键名")
        if flags["registers_keys"]:
            mode.append("按键名注册")
        tag = f"  [{'/'.join(mode)}]" if mode else ""
        print(f"\n  {name}  0x{fn_va:08X}  节={sec!r}  指令 {n_insn}{tag}")
        if keys:
            for k in keys:
                print(f"      {k}")
        else:
            print("      （无字面量键）")
    print(f"\n  字面量键合计: {total}")

    print("\n=== 形态统计 ===")
    enum = [r[0] for r in rows if r[4]["enumerates_keys"]]
    nokey = [r[0] for r in rows if not r[3]]
    print(f"  枚举键名 / 按键名注册的 loader: {len(enum)} -> {enum}")
    print(f"  无字面量键的 loader: {len(nokey)} -> {nokey}")
    print("  ▲ 这两类 loader 的键集合无法从静态字面量得出，"
          "生成的 INI 必须按社区文档补全。")

    print("\n=== 正对照 ===")
    ok = True
    # Read_AI is known to push BuildConst/BuildPower as literals.
    ai = next((r for r in rows if r[0] == "Read_AI"), None)
    if ai is None or "BuildConst" not in ai[3]:
        print("  !! Read_AI 的字面量键里没有 'BuildConst'")
        ok = False
    # Read_Sides enumerates key names rather than reading fixed keys.
    sides = next((r for r in rows if r[0] == "Read_Sides"), None)
    if sides is None or not sides[4]["enumerates_keys"]:
        print("  !! Read_Sides 未被判为「枚举键名」形态")
        ok = False
    if total < 100:
        print(f"  !! 字面量键总数只有 {total}，少于 100 —— 判据可能失效")
        ok = False
    # CROSS-TOOL CONTROL: Read_MultiplayerDialogSettings must yield exactly the
    # 27 keys that dump_rules_fields.py recovers from the STRUCT (offset table +
    # ctor defaults), by name. Two completely different methods -- one reads call
    # arguments, the other reads struct stores -- producing the same 27 names is
    # the strongest check available without a second model family.
    MPD = {"MinMoney", "Money", "MaxMoney", "MoneyIncrement", "MinUnitCount",
           "UnitCount", "MaxUnitCount", "TechLevel", "GameSpeed", "AIDifficulty",
           "AIPlayers", "BridgeDestruction", "ShadowGrow", "Shroud", "Bases",
           "TiberiumGrows", "Crates", "CaptureTheFlag", "HarvesterTruce",
           "MultiEngineer", "AlliesAllowed", "ShortGame", "FogOfWar",
           "MCVRedeploys", "SuperWeaponsAllowed", "BuildOffAlly",
           "AllyChangeAllowed"}
    mpd = next((r for r in rows if r[0] == "Read_MultiplayerDialogSettings"), None)
    if mpd is None or set(mpd[3]) != MPD:
        got = set(mpd[3]) if mpd else set()
        print(f"  !! Read_MultiplayerDialogSettings 的键与字段表不一致：")
        print(f"      多出 {sorted(got - MPD)}")
        print(f"      缺少 {sorted(MPD - got)}")
        ok = False
    # Every loader must reach its own ret inside the window. A truncated body
    # silently loses keys, which is indistinguishable from "the loader does not
    # read them".
    if _TRUNCATED:
        print(f"  !! 这些 loader 没在窗口内走到 ret（键清单被截断）："
              f"{[hex(v) for v in _TRUNCATED]}")
        ok = False
    if not ok:
        print("  正对照失败 —— 以上结果不可信")
        return 1
    print("  正对照通过（Read_AI 含 BuildConst / Read_Sides 枚举键名 / 总键数≥100 / "
          "全部 loader 走到 ret / MPD 27 键与字段表逐名相等）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
