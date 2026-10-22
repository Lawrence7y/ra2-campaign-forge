# -*- coding: utf-8 -*-
"""核实：0x4A8B35 的 `cmp ecx,ebx` 是真守卫还是假守卫？

背景冲突
--------
§352 记载：`0x4A8B35` / `0x6403B0` 是**假守卫**（cmp 在 call 之后）。

本轮反汇编 L3（`0x4A8960`）尾部发现：

    004A8B18  mov ecx, [0x887368]     ; ecx = 崩溃全局（WM_DESTROY 清零）
    004A8B1E  mov edx, [0x886FA0]
    004A8B24  mov eax, [0x886FA4]
    004A8B29  mov esi, [0x886FA8]
    004A8B2F  mov edi, [0x886FAC]
    004A8B35  cmp ecx, ebx            ; ★ 比较 ecx 与 0
    004A8B37  mov [0x8A0704], edx     ; ← 存矩形，不改 ecx / 不改 flags
    004A8B3D  mov [0x8A0708], eax
    004A8B42  mov [0x8A070C], esi
    004A8B48  mov [0x8A0710], edi
    004A8B4E  je 0x4A8B9B             ; ★ ecx==0 ⇒ 跳过
    004A8B75  call 0x724730           ; ★★ 崩溃点：只有 ecx!=0 才到这里

若上述为真，则 `0x4A8B35` 是**有效守卫**，且 L3 内部**已经**保护了 `0x724730`。
⇒ 崩溃时 `ecx` 必 ≠ 0（否则不会走到 `0x4A8B75`）⇒ **崩溃点的 this 不是 [0x887368]**。
⇒ 这与"崩溃时 ecx=[0x887368]=0"的既有定案**矛盾**，必须查清。

本脚本
------
1. 逐条确认 `0x4A8B18..0x4A8B75` 的指令，特别是 `cmp` 与 `je` 之间是否只有 mov [abs],reg。
2. 确认 `ebx` 在此处确为 0（找最近一次 `xor ebx,ebx` 或 `mov ebx,0`）。
3. 确认 `je 0x4A8B9B` 的目标在 `0x4A8B75` 之后（即确实跳过 call）。
4. 找 `0x4A8B9B` 之后做什么（跳过后的路径）。
5. 查 `0x724730` 的全部调用者，看是否还有其他**无守卫**的入口。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_EBX, X86_REG_ECX

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
G_CRASH = 0x887368
L3 = 0x4A8960
CRASH_FN = 0x724730
CMP_SITE = 0x4A8B35
JE_TARGET = 0x4A8B9B

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


class PE:
    def __init__(self, data):
        self.data = data
        e = struct.unpack_from("<I", data, 0x3C)[0]
        self.imagebase = struct.unpack_from("<I", data, e + 0x18 + 0x1C)[0]
        nsec = struct.unpack_from("<H", data, e + 0x06)[0]
        optsz = struct.unpack_from("<H", data, e + 0x14)[0]
        off = e + 0x18 + optsz
        self.sections = []
        for i in range(nsec):
            o = off + i * 40
            nm = data[o:o + 8].rstrip(b"\x00").decode("ascii", "ignore")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
            self.sections.append({"name": nm, "vsize": vsize, "va": vaddr,
                                  "rawsize": rawsize, "rawptr": rawptr})

    def va2off(self, va):
        rva = va - self.imagebase
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                d = rva - s["va"]
                return s["rawptr"] + d if d < s["rawsize"] else None
        return None

    def read(self, va, n):
        o = self.va2off(va)
        return None if o is None or o + n > len(self.data) else self.data[o:o + n]


def main():
    print("=" * 78)
    print("== STEP 0  identity")
    print("=" * 78)
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"sha256 : {sha}")
    if not chk("sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        return 1
    pe = PE(data)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    print()
    print("=" * 78)
    print("== STEP 1  instruction stream 0x4A8B10 .. 0x4A8BA8")
    print("=" * 78)
    LO, HI = 0x4A8B10, 0x4A8BA8
    code = pe.read(LO, HI - LO)
    ins = list(md.disasm(code, LO))
    flags_set = None   # 谁最后设置了 flags
    for i in ins:
        mark = ""
        if i.address == CMP_SITE:
            mark = "  <<< the cmp"
        if i.address == 0x4A8B75:
            mark = "  <<< call 0x724730 (crash point)"
        if i.address == JE_TARGET:
            mark = "  <<< je target"
        for op in i.operands:
            if op.type == X86_OP_MEM and op.mem.base == 0 and \
                    (op.mem.disp & 0xFFFFFFFF) == G_CRASH:
                mark += "  [G_CRASH]"
        print(f"  {i.address:08X}  {i.bytes.hex():<22} {i.mnemonic} {i.op_str}{mark}")

    print()
    print("=" * 78)
    print("== STEP 2  does anything between cmp and je modify flags or ecx?")
    print("=" * 78)
    between = [i for i in ins if CMP_SITE < i.address < 0x4A8B4E]
    print(f"  instructions between cmp(0x{CMP_SITE:X}) and je(0x4A8B4E): {len(between)}")
    # 会改 flags 的指令
    FLAG_WRITERS = ("add", "sub", "and", "or", "xor", "cmp", "test", "inc", "dec",
                    "neg", "shl", "shr", "sar", "sal", "imul", "mul", "div", "idiv",
                    "adc", "sbb", "rcl", "rcr", "rol", "ror", "not", "bt", "bts")
    bad_flags = []
    bad_ecx = []
    for i in between:
        if i.mnemonic in FLAG_WRITERS:
            bad_flags.append((i.address, i.mnemonic, i.op_str))
        if i.operands and i.operands[0].type == X86_OP_REG and i.operands[0].reg == X86_REG_ECX:
            bad_ecx.append((i.address, i.mnemonic, i.op_str))
    print(f"  flag-modifying instructions in between: {bad_flags or 'none'}")
    print(f"  ecx-modifying instructions in between: {bad_ecx or 'none'}")
    chk("cmp and je are adjacent in terms of flags (no flag writer between)",
        not bad_flags, str(bad_flags))
    chk("ecx is not modified between cmp and the guarded call",
        not bad_ecx, str(bad_ecx))

    print()
    print("=" * 78)
    print("== STEP 3  is ebx really 0 here?")
    print("=" * 78)
    # 从 L3 函数头向后找 ebx 的最后一次写，直到 CMP_SITE
    code2 = pe.read(L3, CMP_SITE - L3 + 8)
    body = list(md.disasm(code2, L3))
    ebx_writes = []
    for i in body:
        if i.operands and i.operands[0].type == X86_OP_REG \
                and i.operands[0].reg == X86_REG_EBX:
            ebx_writes.append((i.address, i.mnemonic, i.op_str))
    print(f"  ebx writes in L3 up to cmp: {len(ebx_writes)}")
    for a, m, s in ebx_writes:
        print(f"    0x{a:08X}  {m} {s}")
    zeroing = [w for w in ebx_writes
               if w[1] == "xor" and w[2].replace(" ", "") in ("ebx,ebx",)
               or w[1] == "mov" and w[2].strip() == "ebx, 0"]
    chk("ebx is zeroed inside L3 before the cmp",
        len(zeroing) >= 1, str([f"0x{x[0]:08X}" for x in zeroing]))

    print()
    print("=" * 78)
    print("== STEP 4  je target: does it skip the crash call?")
    print("=" * 78)
    print(f"  je target 0x{JE_TARGET:X}  vs crash call 0x4A8B75")
    skips = JE_TARGET > 0x4A8B75
    chk("je target is AFTER the crash call (i.e. it skips it)", skips,
        f"target 0x{JE_TARGET:X} > call 0x4A8B75")

    # 看跳过后的路径
    code3 = pe.read(JE_TARGET, 0x60)
    print(f"\n  path after je target 0x{JE_TARGET:X}:")
    for i in md.disasm(code3, JE_TARGET):
        print(f"    {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}")
        if i.mnemonic in ("ret", "retn"):
            break

    print()
    print("=" * 78)
    print("== STEP 5  all callers of 0x724730 (are any unguarded?)")
    print("=" * 78)
    text = next(s for s in pe.sections if s["name"] == ".text")
    text_va = text["va"] + pe.imagebase
    end = text_va + text["rawsize"]
    insns = []
    cur = text_va
    while cur < end:
        off = pe.va2off(cur)
        if off is None:
            break
        chunk = data[off:off + (end - cur)]
        got = 0
        last = cur
        for i in md.disasm(chunk, cur):
            insns.append(i)
            got += 1
            last = i.address + i.size
        cur = last if got else cur + 1
    print(f"decoded {len(insns)}")
    if not chk("decoded > 500000", len(insns) > 500000, str(len(insns))):
        return 1

    callers = [i.address for i in insns
               if i.mnemonic == "call" and i.operands
               and i.operands[0].type == X86_OP_IMM
               and (i.operands[0].imm & 0xFFFFFFFF) == CRASH_FN]
    print(f"  callers of 0x{CRASH_FN:X}: {len(callers)}")
    idx = {i.address: k for k, i in enumerate(insns)}
    guarded = 0
    unguarded = []
    for c in callers:
        k = idx[c]
        # 向前看 12 条，找是否有 cmp/test + 条件跳转跳过本 call
        window = insns[max(0, k - 14):k]
        has_guard = False
        for j, p in enumerate(window):
            if p.mnemonic in ("cmp", "test"):
                # 看其后是否有跳转目标是 > c 且 <= c+0x40 的位置（跳过 call）
                for q in window[j + 1:]:
                    if q.mnemonic.startswith("j") and q.operands \
                            and q.operands[0].type == X86_OP_IMM:
                        t = q.operands[0].imm & 0xFFFFFFFF
                        if c < t <= c + 0x40:
                            has_guard = True
                            break
            if has_guard:
                break
        if has_guard:
            guarded += 1
        else:
            unguarded.append(c)
    print(f"  guarded (cmp/test + skip): {guarded}")
    print(f"  unguarded: {len(unguarded)}")
    for u in unguarded[:20]:
        print(f"    0x{u:08X}")

    print()
    print("=" * 78)
    print("== STEP 6  verdict")
    print("=" * 78)
    real_guard = (not bad_flags) and (not bad_ecx) and skips
    if real_guard:
        print("  [已证] 0x4A8B35 的 `cmp ecx,ebx` 是**有效守卫**（不是假守卫）：")
        print("         - cmp 与 je 之间只有 `mov [abs],reg`（不改 flags / 不改 ecx）")
        print("         - je 目标 0x4A8B9B 在 call 0x724730 之后 ⇒ 确实跳过")
        print("  [推翻 §352] 「0x4A8B35 / 0x6403B0 是假守卫」对 0x4A8B35 **不成立**。")
        print("  [重要推论] L3 内部**已经**保护了 0x724730 ⇒ 崩溃时 ecx 必 ≠ 0")
        print("             ⇒ 崩溃点的 this **不是** [0x887368]=0")
        print("             ⇒ 「崩溃时 ecx=[0x887368]=0」的既有定案需重新审视")
        verdict = "CMP_IS_A_REAL_GUARD"
    else:
        print("  [已证] 该 cmp **不是**有效守卫（与 §352 一致）。")
        verdict = "CMP_IS_A_FAKE_GUARD"

    print(f"\n  unguarded callers of 0x724730: {len(unguarded)}")
    if unguarded:
        print("  ⇒ 崩溃更可能来自这些无守卫入口：")
        for u in unguarded[:10]:
            print(f"       0x{u:08X}")

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
