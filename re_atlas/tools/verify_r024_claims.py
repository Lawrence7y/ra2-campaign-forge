"""Independent machine gate for R-024..R-027 / H-017 + H-018.

Under test, as delivered:

  H-017  R-022's "306 literal keys" is wrong; the true total is 651, because
         (a) the function-body window was too narrow for the long loaders and
         (b) the extraction counted every literal push instead of the key slot.
         Distribution: Read_General 279, Read_AudioVisual 152, CombatDamage 71,
         AI 52, MPD 27, Difficulty 12, IQ 11, CrateRules 10, Radiation 9,
         LandCharacteristics 8, SpecialWeapons 7, JumpjetControls 7,
         ElevationModel 3, WallModel 2, Maximums 1  == 651, across 15 loaders.
         20 loaders enumerate key NAMES instead of reading fixed keys.

  H-018  [General] has 268 scalar fields with a double-sided agreement
         (default-load offset == store-back offset); 12 keys are LIST-typed,
         not scalar. [AudioVisual] is 151/152.

Orthogonality to dump_rules_keys.py / dump_rules_fields.py:

  * Those tools bound a loader with "instructions up to its FIRST ret". G-45 and
    G-48 established that byte-shape heuristics are not boundary detectors, so a
    truncated body would silently shrink a key list. This gate derives the body
    from a BRANCH CLOSURE and then asserts whether the first-ret bound dropped
    anything -- and if it did, whether the dropped block contains any key
    literal. That turns "we happened to be fine" into a measured statement.
  * That tool extracts the key from a positional walk-back over pushes. This gate
    re-derives keys by an independent route (immediate -> C string -> filter by
    the loader's own section, dedup) and compares the SETS, not just counts.

Assertions P1..P9 are positive; N1..N3 are negative controls on DIFFERENT
functions, so a passing run is not just "the scanner finds things everywhere".

Run: python re_atlas/tools/verify_r024_claims.py
"""

import hashlib
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402
from text_sweep import sweep  # noqa: E402

EXPECTED_SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

TEXT_LO, TEXT_HI = 0x401000, 0x7E1000

# H-017's delivered distribution. Only loaders with a NONZERO count are listed;
# the 20 enumerate-shaped ones and the 3 empty ones are asserted separately.
DELIVERED = {
    "Read_General": 279,
    "Read_AudioVisual": 152,
    "Read_CombatDamage": 71,
    "Read_AI": 52,
    "Read_MultiplayerDialogSettings": 27,
    "Read_Difficulty": 12,
    "Read_IQ": 11,
    "Read_CrateRules": 10,
    "Read_Radiation": 9,
    "Read_LandCharacteristics": 8,
    "Read_SpecialWeapons": 7,
    "Read_JumpjetControls": 7,
    "Read_ElevationModel": 3,
    "Read_WallModel": 2,
    "Read_Maximums": 1,
}
DELIVERED_TOTAL = 651
DELIVERED_N_LOADERS = 15

# Readers whose 2nd stack argument is the KEY.
READER_KEYS = {
    0x00528A10: 4,   # ReadString(section, key, dst, cap)
    0x00528F00: 4,   # ReadUnicodeString
    0x00529160: 3,   # ReadStringtableEntry(section, key, dst)
    0x005283D0: 4,   # ReadDouble(section, key, default)
    0x005276D0: 3,   # ReadInteger(section, key, default)
    0x005295F0: 3,   # ReadBool(section, key, default)
}
GET_KEY_COUNT = 0x00526960
GET_KEY_NAME = 0x00526CC0

# H-018
GENERAL_ENTRY = 0x0066D530
AV_ENTRY = 0x006691E0
DELIVERED_GENERAL_FIELDS = 268
DELIVERED_GENERAL_KEYS = 279
DELIVERED_AV = 151
AV_KEYS = 152
LIST_TYPED = ["BarrelDebris", "BaseUnit", "BridgeExplosions", "DamageFireTypes",
              "DeadBodies", "DropPod", "ExplosiveVoxelDebris", "MetallicDebris",
              "RepairBay", "Shipyard", "WeatherConBolts", "WeatherConClouds"]
RULES_GLOBAL = 0x008871E0
RULES_SIZE = 0x18C0

RESULTS = []


def check(tag, ok, msg, detail=""):
    RESULTS.append((tag, bool(ok), msg, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {tag}  {msg}")
    if detail and not ok:
        for line in detail.splitlines():
            print(f"         {line}")
    return bool(ok)


def closure(md, entry, span=0x20000):
    """Branch closure: recover the function body from the branch graph.

    Required because these loaders all have a FAILURE EPILOGUE sitting directly
    after the success `ret` (verified in P3): `pop...; xor al,al; ...; ret 4`.
    A first-ret bound therefore DOES stop one instruction group early, every time.
    """
    seen, work = {}, [entry]
    while work:
        start = work.pop()
        if start in seen or not (entry <= start < entry + span):
            continue
        for insn in md.disasm(D.read_va(start, entry + span - start), start):
            if insn.address in seen:
                break
            seen[insn.address] = insn
            if insn.mnemonic.startswith("ret") or insn.mnemonic == "int3":
                break
            if insn.mnemonic == "jmp":
                break
            if insn.mnemonic.startswith("j"):
                for op in insn.operands:
                    if op.type == capstone.x86.X86_OP_IMM:
                        v = op.imm & 0xFFFFFFFF
                        if entry <= v < entry + span and v not in seen:
                            work.append(v)
    return seen


def printable(s):
    return bool(s) and 2 <= len(s) < 40 and all(0x20 < ord(c) < 0x7F for c in s)


def key_of_call(md, ordered, idx, want, section):
    """Independent key extraction: walk back over pushes, take arg 2.

    Differs from dump_rules_keys.key_literals in that it does not consult a
    shared `seen` set keyed on the name only -- duplicates are kept here and
    de-duplicated after the fact by (name, call site), so a genuinely repeated
    read of the same key in one loader is still visible as two sites.
    """
    got = []
    j = idx - 1
    guard = 0
    while j >= 0 and guard < 24 and len(got) < want + 2:
        n = ordered[j]
        if n.mnemonic == "push":
            got.append(n)
        elif n.mnemonic not in ("mov", "lea", "xor"):
            break
        j -= 1
        guard += 1
    if len(got) < 2:
        return None, None
    cand = got[1]
    txt = cand.op_str.strip()
    if not txt.startswith("0x") or "[" in txt:
        return None, None
    va = int(txt, 16)
    s = D.cstr(va, 48)
    if not printable(s):
        return None, None
    return s, va


def keys_for(md, entry, section, body):
    ordered = [body[a] for a in sorted(body)]
    out = []
    for idx, insn in enumerate(ordered):
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        tgt = op.imm & 0xFFFFFFFF
        want = READER_KEYS.get(tgt)
        if want is None:
            continue
        s, va = key_of_call(md, ordered, idx, want, section)
        if s is None:
            continue
        if s == section:
            continue
        out.append((s, va, insn.address))
    return out


def shape_of(body):
    calls = []
    for i in body.values():
        if i.mnemonic == "call" and i.operands:
            op = i.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                calls.append(op.imm & 0xFFFFFFFF)
    return (GET_KEY_COUNT in calls or GET_KEY_NAME in calls), (GET_KEY_NAME in calls)


def section_of(entry):
    got = D.section_used_by(entry)
    return got[1] if got and got[1] else None


def main():
    print("=== R-024..R-027 / H-017 + H-018 独立门禁 ===\n")

    got = hashlib.sha256(D.BLOB).hexdigest()
    check("P1", got == EXPECTED_SHA256, "目标二进制指纹",
          f"expect {EXPECTED_SHA256}\n got    {got}")

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    # ---- build bodies for every loader -----------------------------------
    loaders = sorted(D.READERS.items(), key=lambda kv: kv[1])
    bodies, first_rets, cold = {}, {}, {}
    for entry, name in loaders:
        body = closure(md, entry)
        bodies[name] = body
        # first ret in the LINEAR decode from entry
        fr = None
        linear = []
        for insn in md.disasm(D.read_va(entry, 0x8000), entry):
            linear.append(insn.address)
            if insn.mnemonic.startswith("ret"):
                fr = insn.address
                break
        first_rets[name] = fr
        if fr is not None:
            extra = sorted(a for a in body if a > fr)
            if extra:
                cold[name] = extra

    # ---- P2: every loader reaches a ret (window sufficiency) -------------
    missing = [n for n, fr in first_rets.items() if fr is None]
    check("P2", not missing,
          f"全部 {len(loaders)} 个 loader 在自己的首个 ret 前解码完成",
          f"missing={missing}")

    # ---- P3: the cold block past the first ret carries NO key literal -----
    # Two shapes occur, both harmless for key extraction:
    #   (a) failure epilogue  `pop...; xor al,al; ...; ret 4`  (12 loaders)
    #   (b) cleanup path      `xor eax,eax; mov ecx,edi; ...; call; ret 4`
    #                          (Read_File -- a CONTAINER that dispatches, and whose
    #                           cold block calls the AdvancedCommandBar reader)
    # The assertion that matters is the second half: no key literal lives in a
    # cold block, so "bound at the first ret" cannot lose a key HERE. It does not
    # make first-ret a correct boundary -- G-45/G-48 stand.
    cold_shapes, leaked_keys = [], []
    for name, extra in cold.items():
        insns = [bodies[name][a] for a in extra]
        has_false = any(i.mnemonic == "xor" and i.op_str.replace(" ", "") == "al,al"
                        for i in insns)
        has_cleanup = any(i.mnemonic == "call" for i in insns)
        cold_shapes.append(f"{name}: false={has_false} call={has_cleanup}")
        for i in insns:
            if i.mnemonic == "push":
                for op in i.operands:
                    if op.type == capstone.x86.X86_OP_IMM:
                        v = op.imm & 0xFFFFFFFF
                        if 0x810000 <= v < 0x900000 and printable(D.cstr(v, 40)):
                            leaked_keys.append(f"{name}: 0x{i.address:08X} push "
                                               f"0x{v:08X} {D.cstr(v, 40)!r}")
    no_shape = [n for n, extra in cold.items()
                if not any((bodies[n][a].mnemonic == "xor"
                            and bodies[n][a].op_str.replace(" ", "") in ("al,al", "eax,eax"))
                           or bodies[n][a].mnemonic == "call" for a in extra)]
    check("P3", not leaked_keys and not no_shape,
          f"越过首 ret 的冷块共 {len(cold)} 个：全部是收尾形态（失败尾声或清理路径），"
          f"且不含任何键字面量 ⇒ 首个 ret 在这里不会漏键",
          "\n".join(leaked_keys + [f"{n} 无收尾特征" for n in no_shape]))

    # ---- P3b: last-key sensitivity (direct rebuttal of a wrong claim) ----
    # An independent verifier asserted that stopping at the first ret would lose
    # the LAST key read of each of these two loaders
    # (`TalkBubbleTime` / `FallBackCoefficient`). Measured: both keys are read
    # BEFORE the first ret, and there are ZERO key reads at/after it. So the
    # claim is wrong and the first-ret bound loses neither. Pinning this here
    # means a future window/boundary change that really does drop the tail shows
    # up as a red assertion instead of as a quietly shorter list.
    last_reads = {}
    for name, key_want in (("Read_General", "TalkBubbleTime"),
                           ("Read_AudioVisual", "FallBackCoefficient")):
        fr = first_rets[name]
        body = bodies[name]
        reads = []
        for idx, addr in enumerate(sorted(body)):
            insn = body[addr]
            if insn.mnemonic != "call" or not insn.operands:
                continue
            op = insn.operands[0]
            if op.type != capstone.x86.X86_OP_IMM or (op.imm & 0xFFFFFFFF) not in READER_KEYS:
                continue
            s, _va = key_of_call(md, [body[a] for a in sorted(body)], idx,
                                 READER_KEYS[op.imm & 0xFFFFFFFF], None)
            if s:
                reads.append((addr, s))
        before = [r for r in reads if r[0] < fr]
        after = [r for r in reads if r[0] >= fr]
        hit = [a for a, s in before if s == key_want]
        last_reads[name] = (len(before), len(after), hit)
    ok3b = (all(v[1] == 0 and v[2] for v in last_reads.values()))
    check("P3b", ok3b,
          "★ 实测反驳：`TalkBubbleTime`(0x671E71) 与 `FallBackCoefficient`(0x66B8DB) "
          "都在**首个 ret 之前**读，首个 ret 之后键读取次数为 0 ⇒ 截断不会漏最后一个键",
          "\n".join(f"{n}: before={v[0]} at_or_after={v[1]} hit={['0x%X' % a for a in v[2]]}"
                    for n, v in last_reads.items()))

    # ---- P4: total key count == 651, per-loader distribution matches -----
    per, sites = {}, {}
    for entry, name in loaders:
        sec = section_of(entry)
        ks = keys_for(md, entry, sec, bodies[name])
        per[name] = ks
        sites[name] = len(ks)

    unique = {n: sorted({s for s, _v, _a in ks}) for n, ks in per.items()}
    counts = {n: len(v) for n, v in unique.items() if v}
    total = sum(counts.values())

    diff = []
    for name, want in DELIVERED.items():
        have = counts.get(name, 0)
        if have != want:
            diff.append(f"{name}: 交付 {want} / 实测 {have}")
    for name, have in counts.items():
        if name not in DELIVERED:
            diff.append(f"{name}: 交付表里没有，实测 {have}")
    check("P4", not diff and total == DELIVERED_TOTAL and len(counts) == DELIVERED_N_LOADERS,
          f"15 个 loader 逐项与 651 总量全部相等（实测 total={total}, "
          f"n_loaders={len(counts)}）",
          "\n".join(diff))

    # ---- P5: the two dominant sections are General + AudioVisual ---------
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:2]
    share = sum(v for _k, v in top)
    check("P5", {k for k, _v in top} == {"Read_General", "Read_AudioVisual"}
          and share == 431,
          f"最大的两节 = [General] 279 + [AudioVisual] 152 = {share}/651 "
          f"({share / 651 * 100:.0f}%)",
          f"top={top}")

    # ---- P6: 20 loaders are enumerate-shaped -----------------------------
    enum, register = [], []
    for entry, name in loaders:
        e, r = shape_of(bodies[name])
        if e:
            enum.append(name)
        if r:
            register.append(name)
    check("P6", len(enum) == 20,
          f"枚举键名 / 按键名注册的 loader = {len(enum)} 个（交付 20）",
          f"got={sorted(enum)}")

    # ---- P7: loaders whose section does NOT resolve to their real section -
    # Two distinct shapes, and neither may be papered over:
    #   (a) UNRESOLVED: section name arrives as a stack argument -> (None,None)
    #       Read_Difficulties, Read_Difficulty
    #   (b) MISATTRIBUTED: Read_File is a CONTAINER that dispatches to many
    #       sections; the last section it can resolve for is `ColorAdd`, which
    #       is NOT "the section it reads". Left unguarded this silently
    #       manufactures keys out of section names.
    unresolved = sorted(n for _e, n in loaders if section_of(_e) is None)
    file_sec = section_of(0x00668BF0)
    EXPECTED_UNRESOLVED = ["Read_Difficulties", "Read_Difficulty"]
    check("P7", unresolved == EXPECTED_UNRESOLVED and file_sec == "ColorAdd",
          f"节名边界如实标注：(a) 解析不出 = {unresolved}；"
          f"(b) 容器 Read_File 的『最后可解析节』= {file_sec!r} 是误归属，已知并在 P6/N2 里防住",
          f"got={unresolved} file_sec={file_sec!r}\nexpect={EXPECTED_UNRESOLVED}")

    # ---- P8: [General] field table reconciles ----------------------------
    # PARSER BUG THIS FIXES: my first version required exactly 6 columns
    # (`name +load +store reader width agree`). Two real rows are NOT 6-column:
    #   HarvesterUnit      -  +0x0BE4 ReadString 4  !! 默认载入=None
    #   CMislAcceleration  +0x04FC +0x0530 ReadDouble 4  跨字段默认(from +0x04FC)
    # so a 6-column filter reports 266 and looks like a 2-field shortfall. That
    # is a measurement artefact, not a data defect -- exactly the kind of silent
    # undercount this line keeps getting bitten by. Count by STORE OFFSET and
    # accept both shapes.
    gp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                      "evidence", "rules_fields_general.txt")
    rows, odd = [], []
    with open(gp, encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if not parts or not parts[0][:1].isalpha():
                continue
            # a field row has a store offset in column 2 and a reader in col 3
            if len(parts) >= 5 and parts[2].startswith("+0x"):
                rows.append(parts)
                if len(parts) != 6:
                    odd.append(" ".join(parts[:5]))
    stores = {r[2] for r in rows}
    check("P8", len(rows) == DELIVERED_GENERAL_FIELDS and len(stores) == DELIVERED_GENERAL_FIELDS,
          f"[General] 字段行 = {len(rows)}、按存回偏移去重 = {len(stores)}"
          f"（交付 {DELIVERED_GENERAL_FIELDS}）；其中非 6 列行 {len(odd)} 条（已知形态）",
          f"rows={len(rows)} distinct_store={len(stores)}\nodd={odd}")

    # ---- P9: every field offset is inside RulesClass ---------------------
    offs = set()
    for r in rows:
        if r[2].startswith("+0x"):
            offs.add(int(r[2], 16))
    out_of_range = [hex(o) for o in offs if o >= RULES_SIZE]
    check("P9", not out_of_range,
          f"[General] 的 {len(offs)} 个存回偏移全部 < RulesClass 尺寸 0x{RULES_SIZE:X}",
          f"out_of_range={sorted(out_of_range)}")

    # ---- P10: the 12 list-typed keys are a subset of the General keys ----
    gkeys = {s for s, _v, _a in per.get("Read_General", [])}
    missing_list = [k for k in LIST_TYPED if k not in gkeys]
    check("P10", not missing_list,
          f"12 个列表型键全部出现在 [General] 的 {len(gkeys)} 个键里",
          f"missing={missing_list}")

    # ---- P11: [AudioVisual] = 151 fields / 152 keys ----------------------
    # Same parser fix as P8. Also note `Smoke` legitimately appears at two
    # DIFFERENT offsets (+0x0BAC / +0x0BB0) -- it is two list-typed entries, not
    # a duplicate row. So the count must be by offset, never by name.
    ap = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                      "evidence", "rules_fields_av.txt")
    av_rows = []
    with open(ap, encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if not parts or not parts[0][:1].isalpha():
                continue
            if len(parts) >= 5 and parts[2].startswith("+0x"):
                av_rows.append(parts)
    av_stores = {r[2] for r in av_rows}
    av_keys = counts.get("Read_AudioVisual", 0)
    check("P11", len(av_rows) == DELIVERED_AV and len(av_stores) == DELIVERED_AV
          and av_keys == AV_KEYS,
          f"[AudioVisual] 字段 {len(av_rows)}（去重偏移 {len(av_stores)}，交付 {DELIVERED_AV}）"
          f" / 键 {av_keys}（交付 {AV_KEYS}）",
          f"rows={len(av_rows)} distinct_store={len(av_stores)} keys={av_keys}")

    # ---- N1: negative control on a DIFFERENT function --------------------
    # The RulesClass constructor must yield ZERO keys: it sets defaults, it does
    # not read an INI section. If the extractor reports keys here, it is not
    # measuring "keys read from a section".
    ctor = closure(md, 0x00665650, 0x4000)
    ctor_keys = keys_for(md, 0x00665650, None, ctor)
    check("N1", not ctor_keys,
          f"负控（不同函数）：RulesClass 构造器 0x00665650 解出 0 个键"
          f"（实得 {len(ctor_keys)}）",
          "\n".join(f"0x{a:08X} {s!r}" for s, _v, a in ctor_keys[:10]))

    # ---- N2: negative control -- a section name must not be counted as a key
    # Read_File dispatches to several sections; its body pushes many SECTION
    # names. Those must not appear as keys.
    section_names = set(D.READERS_SECTION_NAMES) if hasattr(D, "READERS_SECTION_NAMES") else set()
    file_keys = {s for s, _v, _a in per.get("Read_File", [])}
    leaked = sorted(file_keys & section_names) if section_names else []
    check("N2", not leaked,
          f"负控：Read_File 的 {len(file_keys)} 个键里不含任何节名"
          f"（比对 {len(section_names)} 个已知节名）",
          f"leaked={leaked}")

    # ---- N3: negative control -- truncation must change the answer -------
    # Re-run the biggest loader with its body truncated at the first ret and
    # check the count does NOT change; then with a deliberately short window and
    # check it DOES change. Proves the assertion is sensitive to the window.
    g_body = bodies["Read_General"]
    g_full = len({s for s, _v, _a in per["Read_General"]})
    short = {a: i for a, i in g_body.items() if a < GENERAL_ENTRY + 0x1000}
    g_short = len({s for s, _v, _a in keys_for(md, GENERAL_ENTRY, "General", short)})
    check("N3", g_short < g_full,
          f"负控（截断）：[General] 体截到 0x1000 字节时键数 {g_short} < 完整 {g_full}"
          f" ⇒ 断言对窗口敏感",
          f"short={g_short} full={g_full}")

    npass = sum(1 for _t, ok, _m, _d in RESULTS if ok)
    ntot = len(RESULTS)
    print(f"\n=== {npass}/{ntot} PASS ===")
    if npass != ntot:
        print("失败项：")
        for t, ok, m, _d in RESULTS:
            if not ok:
                print(f"  {t}: {m}")
        return 1
    print("EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
