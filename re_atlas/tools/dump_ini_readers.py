"""R-017: recover the per-key semantics of the INIClass read family.

The campaign compiler's real question is not "what functions exist" but "which
key is consumed by which field, and with what parsing". This tool settles the
parsing half for the readers whose behaviour is decided by data tables in the
image, and prints the shared entry skeleton so the shared half is visible.

What is actually decided by bytes here:

- ReadBool (0x5295F0) does NOT parse the characters itself. It takes the FIRST
  byte of the value, uppercases it (0x7C97D3 = toupper), maps it through a
  0x2A-entry byte table at 0x5297B4 into a 3-way dispatch (0x5297A8), where
  class 0 = false, class 1 = true, class 2 = fall through to the caller's
  default. So "0"/"f"/"n" -> false, "1"/"t"/"y" -> true, anything else ->
  default, and the check is CASE-INSENSITIVE because of the toupper.
- WriteBool writes the literal "yes" (0x825BF8) or "no" (0x825BF4), so the
  reader and writer agree on only "y"/"n" and the numeric forms.
- ReadInteger (0x5276D0) checks the LAST byte of the value (0x7CAFF4 is
  toupper, compared against 'h' = 0x68). Trailing 'h' -> sscanf with "%xh"
  (0x825BB4, hex); otherwise strtol (0x7C9BFD). So "100h" is hex 0x100.

Both are byte-level facts, and both are the kind of thing a compiler gets wrong
because YRpp's headers say only `ReadBool` / `ReadInteger` with no parsing rule.

Run: python re_atlas/tools/dump_ini_readers.py
"""

import struct

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000

with open(EXE, "rb") as fh:
    BLOB = fh.read()


def read_va(va, n):
    fo = va - IMAGE_BASE
    if fo < 0 or fo >= len(BLOB):
        return b""
    return BLOB[fo:fo + n]


def u32(va):
    b = read_va(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


def u8(va):
    b = read_va(va, 1)
    return b[0] if b else None


def cstr(va, n=32):
    b = read_va(va, n)
    if not b:
        return ""
    z = b.find(b"\x00")
    return (b[:z] if z >= 0 else b).decode("ascii", "replace")


def disas(va, max_bytes=0x80, limit=40):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    out = []
    for insn in md.disasm(read_va(va, max_bytes), va):
        out.append((insn.address, insn.bytes.hex(" "), insn.mnemonic, insn.op_str))
        if insn.mnemonic.startswith("ret"):
            break
        if len(out) >= limit:
            break
    return out


# (address, name, role) for the shared read/write entry points.
FAMILY = [
    (0x00528A10, "ReadString", "返回拷贝长度, ret 0x14"),
    (0x00528F00, "ReadUnicodeString", "先 mov eax,0x5014 建栈帧, ret 0x14"),
    (0x00529160, "ReadStringtableEntry", "sub esp,0x414 (1KB 缓冲), ret 0x10"),
    (0x005283D0, "ReadDouble", "浮点, 默认值经 PUSH_VAR64"),
    (0x005276D0, "ReadInteger", "见下: 尾字符 'h' 走十六进制"),
    (0x005295F0, "ReadBool", "见下: 首字符查表三元分派"),
    (0x00528660, "WriteString", "sub esp,0x38"),
    (0x00529560, "WriteBool", "写 yes/no 字面量"),
    (0x00528E00, "WriteUnicodeString", "转义 Unicode"),
]

# ReadBool's 3-way dispatch. Index = toupper(first char) - '0', valid 0..0x29.
DISPATCH_CLASSES = {0: "FALSE", 1: "TRUE", 2: "DEFAULT (caller's value)"}


def main():
    print("=== read/write family entry points ===")
    for va, name, note in FAMILY:
        b = read_va(va, 8)
        print(f"  0x{va:08X}  {name:22s} {note:34s} head={b.hex(' ')}")

    print("\n=== helper identity (checked by bytes, not by name) ===")
    for va, label, why in (
        (0x007C97D3, "toupper", "'a'..'z' (0x61..0x7A) then sub 0x20"),
        (0x007CAFF4, "tolower", "'A'..'Z' (0x41..0x5A) then ADD 0x20"),
        (0x007C9BFD, "strtol wrapper", "push arg; call 0x7C9B72; pop; ret"),
        (0x007CA530, "sscanf", "sub esp,0x20; mov [ebp-0x14],0x49"),
    ):
        ins = disas(va, max_bytes=0x40, limit=6)
        first = " / ".join(f"{mn} {ops}" for _, _, mn, ops in ins[:3])
        print(f"  0x{va:08X}  {label:16s} {why}")
        print(f"              {first}")

    print("\n=== format / literal strings the readers and writers use ===")
    for va, label in (
        (0x00825BB4, "ReadInteger hex format"),
        (0x00825BB8, "0x825BB8 (adjacent)"),
        (0x00825BF4, "WriteBool false"),
        (0x00825BF8, "WriteBool true"),
        (0x00825BFC, "0x825BFC (adjacent)"),
    ):
        print(f"  0x{va:08X}  {label:22s} {cstr(va)!r}")

    print("\n=== ReadBool: first-char -> dispatch class table (0x5297B4, 0x2A entries) ===")
    print("  index = toupper(first_byte_of_value) - '0'")
    rows = []
    for i in range(0x2A):
        cls = u8(0x5297B4 + i)
        ch = chr(i + 0x30)
        rows.append((i, ch, cls))
    for i, ch, cls in rows:
        if cls != 2:  # only the interesting entries
            print(f"  {i:02X}  '{ch}'  class={cls}  {DISPATCH_CLASSES.get(cls, '?')}")
    n_true = sum(1 for _, _, c in rows if c == 1)
    n_false = sum(1 for _, _, c in rows if c == 0)
    n_dflt = sum(1 for _, _, c in rows if c == 2)
    print(f"  合计: FALSE={n_false}  TRUE={n_true}  DEFAULT={n_dflt}  (总 {len(rows)})")

    print("\n=== ReadBool: jump table (0x5297A8) and its three bodies ===")
    for k in range(3):
        target = u32(0x5297A8 + 4 * k)
        print(f"  class {k} ({DISPATCH_CLASSES[k]:28s}) -> 0x{target:08X}")
    for k in range(3):
        target = u32(0x5297A8 + 4 * k)
        tail = " / ".join(f"{mn} {ops}" for _, _, mn, ops in disas(target, max_bytes=0x20, limit=6))
        print(f"    0x{target:08X}: {tail}")

    print("\n=== ReadInteger: trailing-byte test (LAST byte, tolower'd, vs 'h' = 0x68) ===")
    # 0x527877 is a real branch target inside ReadInteger; starting anywhere
    # earlier mid-instruction disassembles garbage ("cli"), which is exactly the
    # kind of window mistake this tool is meant to catch.
    for addr, raw, mn, ops in disas(0x527877, max_bytes=0x40, limit=12):
        print(f"  {addr:08X}  {raw:<21} {mn} {ops}")

    print("\n=== positive control ===")
    # ReadString must exist and start with the same `sub esp,0xC` shape as the
    # rest of the family; if the VA map were wrong this would print garbage.
    ctl = read_va(0x00528A10, 3)
    ok = ctl == b"\x83\xec\x0c"
    print(f"  ReadString @0x00528A10 head={ctl.hex(' ')} expected='83 ec 0c': {ok}")
    if not ok:
        print("  !! control FAILED -- VA map is wrong, ignore every result above")
        return 1
    print("  control OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
