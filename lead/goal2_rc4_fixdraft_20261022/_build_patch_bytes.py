# -*- coding: utf-8 -*-
"""RC-4 修复补丁字节生成 + 自校验（待办 12，离线，不部署）。

方案 A（trampoline）：
  0x724730 处前 5 字节改成 `jmp cave`（E9 rel32）
  0x724735 处 3 字节 nop 填充（原来 0x724730..0x724734 共 5 字节 = sub esp,0xc(3) + push ebp(1) + mov ebp,ecx 的前 1 字节）

  ★ 精确边界：
    0x724730  83 ec 0c      sub esp,0xc      (3 字节)  → 0x724733
    0x724733  55            push ebp         (1 字节)  → 0x724734
    0x724734  8b e9         mov ebp,ecx      (2 字节)  → 0x724736
    0x724736  56            push esi         (1 字节)  → 0x724737
    0x724737  8b 85 50 02 00 00  mov eax,[ebp+0x250]

  ⇒ 前 5 字节 = 0x724730..0x724734 = `83 ec 0c 55 8b`（sub+push+mov 的第一字节）
  ⇒ 若只覆盖 5 字节，`mov ebp,ecx` 会被截断（剩 `e9` 单字节）⇒ **不可行**

  改用：覆盖前 **6** 字节（0x724730..0x724735 = sub(3)+push(1)+mov(2)），
  正好是 `83 ec 0c 55 8b e9`，6 字节。用 `E9 rel32`(5) + `90`(1) 填充。

  cave 里执行：
    sub esp,0xc          ; 原指令
    push ebp             ; 原指令
    mov  ebp, ecx        ; 原指令（此时 ecx 已验非 0）
    push esi             ; 原指令
    jmp  0x724737        ; 回到崩溃点（ebp != 0 ⇒ 安全）

  守卫必须在 `mov ebp,ecx` 之前判 ecx：
    test ecx, ecx
    jz   .null
    ...原指令...
    jmp 0x724737
  .null:
    xor eax, eax
    ret 4

  完整 cave：
    85 c9                  test ecx, ecx          (2)
    74 0a                  jz   .null             (2)   ; 跳过 10 字节
    83 ec 0c               sub esp, 0xc           (3)
    55                     push ebp               (1)
    8b e9                  mov ebp, ecx           (2)
    56                     push esi               (1)
    e9 <rel32>             jmp 0x724737           (5)
  .null:
    31 c0                  xor eax, eax           (2)
    c2 04 00               ret 4                  (3)
  合计 2+2+3+1+2+1+5+2+3 = 21 字节

  ★ jz 的位移：jz 在 cave+2，长度 2，结束 cave+4；
    .null 在 cave+16；16-4 = 12 = 0x0C。所以 `74 0c`。
  ★ jmp 的位移：jmp 在 cave+11，长度 5，结束 cave+16；
    目标 0x724737；rel32 = 0x724737 - (cave+16)
"""
import hashlib
import struct
import sys
from pathlib import Path

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"

HOOK = 0x724730
HOOK_LEN = 6                  # 覆盖 sub esp,0xc + push ebp + mov ebp,ecx
RESUME = 0x724737             # mov eax,[ebp+0x250]
CAVE = 0x00B95700             # .detour 段尾部全零区起点

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


def build_cave(cave_va):
    """生成 cave 字节。"""
    b = bytearray()
    # test ecx, ecx
    b += b"\x85\xc9"
    # jz .null  (placeholder, fix later)
    jz_pos = len(b)
    b += b"\x74\x00"
    # sub esp, 0xc
    b += b"\x83\xec\x0c"
    # push ebp
    b += b"\x55"
    # mov ebp, ecx
    b += b"\x8b\xe9"
    # push esi
    b += b"\x56"
    # jmp RESUME  (placeholder)
    jmp_pos = len(b)
    b += b"\xe9\x00\x00\x00\x00"
    # .null:
    null_pos = len(b)
    # xor eax, eax
    b += b"\x31\xc0"
    # ret 4
    b += b"\xc2\x04\x00"

    # fix jz rel8: target null_pos, jz ends at jz_pos+2
    jz_rel = null_pos - (jz_pos + 2)
    assert -128 <= jz_rel <= 127, f"jz rel8 out of range: {jz_rel}"
    b[jz_pos + 1] = jz_rel & 0xFF

    # fix jmp rel32: target RESUME, jmp ends at jmp_pos+5
    jmp_rel = (RESUME - (cave_va + jmp_pos + 5)) & 0xFFFFFFFF
    struct.pack_into("<I", b, jmp_pos + 1, jmp_rel)

    return bytes(b), {"jz_rel": jz_rel, "jmp_rel": jmp_rel,
                      "null_pos": null_pos, "len": len(b)}


def main():
    print("=" * 78)
    print("== STEP 0  identity")
    print("=" * 78)
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"sha256 : {sha}")
    if not chk("sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        return 1

    print()
    print("=" * 78)
    print("== STEP 1  original bytes at hook point")
    print("=" * 78)
    e = struct.unpack_from("<I", data, 0x3C)[0]
    ib = struct.unpack_from("<I", data, e + 0x18 + 0x1C)[0]
    nsec = struct.unpack_from("<H", data, e + 0x06)[0]
    optsz = struct.unpack_from("<H", data, e + 0x14)[0]
    secoff = e + 0x18 + optsz
    secs = []
    for i in range(nsec):
        o = secoff + i * 40
        nm = data[o:o + 8].rstrip(b"\x00").decode("ascii", "ignore")
        vs, va, rs, rp = struct.unpack_from("<IIII", data, o + 8)
        secs.append({"name": nm, "vsize": vs, "va": va, "rawsize": rs, "rawptr": rp})

    def va2off(va):
        rva = va - ib
        for s in secs:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                d = rva - s["va"]
                return s["rawptr"] + d if d < s["rawsize"] else None
        return None

    orig = data[va2off(HOOK):va2off(HOOK) + HOOK_LEN]
    print(f"  original {HOOK_LEN} bytes at 0x{HOOK:X}: {orig.hex(' ')}")
    expect = bytes.fromhex("83ec0c558be9")
    chk(f"original bytes == {expect.hex(' ')} (sub esp,0xc; push ebp; mov ebp,ecx)",
        orig == expect, orig.hex(" "))

    print()
    print("=" * 78)
    print("== STEP 2  cave region is all zero")
    print("=" * 78)
    cave_off = va2off(CAVE)
    print(f"  cave VA 0x{CAVE:X} -> file offset 0x{cave_off:X}")
    cave_region = data[cave_off:cave_off + 64]
    print(f"  first 32 bytes: {cave_region[:32].hex(' ')}")
    chk("cave region is all zero (64 bytes)", all(b == 0 for b in cave_region),
        "zero" if all(b == 0 for b in cave_region) else "NOT ZERO")

    # 确认 cave 落在 .detour 段且可执行
    det = next((s for s in secs if s["name"] == ".detour"), None)
    chk(".detour section exists", det is not None, det["name"] if det else "missing")
    if det:
        in_det = det["va"] + ib <= CAVE < det["va"] + ib + det["rawsize"]
        chk("cave VA lies inside .detour", in_det, f"0x{CAVE:X}")

    print()
    print("=" * 78)
    print("== STEP 3  build cave bytes")
    print("=" * 78)
    cave, info = build_cave(CAVE)
    print(f"  cave length: {len(cave)} bytes")
    print(f"  cave bytes : {cave.hex(' ')}")
    print(f"  jz rel8 = {info['jz_rel']} (0x{info['jz_rel'] & 0xFF:02X})")
    print(f"  jmp rel32 = 0x{info['jmp_rel']:08X}")
    print(f"  .null at cave+{info['null_pos']} = 0x{CAVE + info['null_pos']:X}")
    chk("cave fits in available space (< 2304 bytes)", len(cave) < 2304, str(len(cave)))
    chk("jz rel8 in range", -128 <= info["jz_rel"] <= 127, str(info["jz_rel"]))

    print()
    print("=" * 78)
    print("== STEP 4  build hook bytes (jmp cave)")
    print("=" * 78)
    # E9 rel32 at HOOK, then pad to HOOK_LEN
    rel32 = (CAVE - (HOOK + 5)) & 0xFFFFFFFF
    hook = b"\xe9" + struct.pack("<I", rel32)
    pad = HOOK_LEN - len(hook)
    hook = hook + b"\x90" * pad
    print(f"  jmp rel32 = 0x{rel32:08X}  (target 0x{CAVE:X} - (0x{HOOK:X}+5))")
    print(f"  hook bytes: {hook.hex(' ')}  ({len(hook)} bytes)")
    chk("hook length == HOOK_LEN", len(hook) == HOOK_LEN, str(len(hook)))

    print()
    print("=" * 78)
    print("== STEP 5  semantic verification via capstone")
    print("=" * 78)
    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        print("  disassemble cave:")
        for i in md.disasm(cave, CAVE):
            print(f"    {i.address:08X}  {i.bytes.hex():<22} {i.mnemonic} {i.op_str}")
        print("  disassemble hook:")
        for i in md.disasm(hook, HOOK):
            print(f"    {i.address:08X}  {i.bytes.hex():<22} {i.mnemonic} {i.op_str}")

        # 逐条核对语义
        ins = list(md.disasm(cave, CAVE))
        chk("cave[0] is test ecx,ecx", ins[0].mnemonic == "test" and "ecx" in ins[0].op_str,
            f"{ins[0].mnemonic} {ins[0].op_str}")
        chk("cave[1] is jz/jz short", ins[1].mnemonic in ("je", "jz"),
            f"{ins[1].mnemonic} {ins[1].op_str}")
        # jz 目标 == .null
        tgt = int(ins[1].op_str, 16) if ins[1].op_str.startswith("0x") else None
        chk("jz target == .null address", tgt == CAVE + info["null_pos"],
            f"0x{tgt:X}" if tgt else "n/a")
        # 最后一条是 ret 4
        chk("last cave insn is ret 4", ins[-1].mnemonic == "ret"
            and ins[-1].op_str.strip() == "4", f"{ins[-1].mnemonic} {ins[-1].op_str}")
        # jmp 目标 == RESUME
        jmps = [i for i in ins if i.mnemonic == "jmp"]
        chk("cave has exactly 1 jmp", len(jmps) == 1, str(len(jmps)))
        if jmps:
            jt = int(jmps[0].op_str, 16)
            chk("jmp target == RESUME 0x724737", jt == RESUME, f"0x{jt:X}")
    except ImportError:
        print("  (capstone unavailable, skipping semantic check)")
        chk("capstone available", False, "import failed")

    print()
    print("=" * 78)
    print("== STEP 6  patch summary (NOT APPLIED)")
    print("=" * 78)
    print(f"  hook  : 0x{HOOK:X}  {orig.hex(' ')}  ->  {hook.hex(' ')}")
    print(f"  cave  : 0x{CAVE:X}  {cave.hex(' ')}")
    print(f"  cave len = {len(cave)} bytes; .detour has 2304 free bytes at this address")
    print("  ★ 本脚本**不写任何文件**，只生成并校验字节。")

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
