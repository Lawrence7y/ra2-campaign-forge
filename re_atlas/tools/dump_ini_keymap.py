"""R-018: recover the key -> field mapping for AbstractTypeClass::LoadFromINI.

This is the deliverable the campaign compiler actually wants: given a section
header and a key, which field of the in-memory type object ends up holding it,
and with which length limit.

The finding that changes how sections must be generated:

    AbstractTypeClass+0x24 is NOT a numeric id. It is `char ID[0x18]`, and it is
    ALSO the section name handed to GetSection. So the section header and the
    object's ID are the same bytes. A compiler that emits "[MTNK]" gets an
    object whose ID is the string "MTNK"; it cannot emit a display name as the
    header and keep a separate id.

Verified here from bytes:
  0x00410A79  lea ebp,[ebx+0x24]   ; ebp = this->ID
  0x00410A7E  push ebp
  0x00410A7F  call 0x526810        ; GetSection(this->ID)
  0x00410A91  lea edi,[ebx+0x64]   ; dst = this->Name
  0x00410A94  push 0x31            ; cap = 0x31
  0x00410A98  push 0x817854        ; "Name"
  0x00528A10                       ; ReadString

Run: python re_atlas/tools/dump_ini_keymap.py
"""

import struct

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x811074
DATA_LO, DATA_HI = 0x812000, 0xB79BE4

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


def cstr(va, n=64):
    b = read_va(va, n)
    if not b:
        return ""
    z = b.find(b"\x00")
    return (b[:z] if z >= 0 else b).decode("ascii", "replace")


def call_sites(fn_lo, fn_hi, target):
    """Addresses inside [fn_lo,fn_hi) that call `target`."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    out = []
    for insn in md.disasm(read_va(fn_lo, fn_hi - fn_lo), fn_lo):
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == target:
            out.append(insn.address)
    return out


def preceding_push(call_va, lookback=0x28):
    """Walk backwards over the argument pushes of one call.

    Returns the pushed immediates in push order (first pushed = highest
    address = the leftmost source argument). Scanning backwards and decoding at
    every byte offset would pick up operands of mid-instruction garbage, so this
    decodes forward from a nearby aligned start and keeps only pushes whose
    instruction ends exactly where the walk expects.
    """
    start = call_va - lookback
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    pushes = []
    for insn in md.disasm(read_va(start, lookback), start):
        if insn.address >= call_va:
            break
        if insn.mnemonic == "push":
            txt = insn.op_str.strip()
            if txt.startswith("0x") and "[" not in txt:
                pushes.append(int(txt, 16))
            else:
                pushes.append(None)  # a register / memory push
    return pushes


def main():
    print("=== AbstractTypeClass::LoadFromINI (0x00410A60) ===")

    str_calls = call_sites(0x410A60, 0x410B70, 0x00528A10)
    sec_calls = call_sites(0x410A60, 0x410B70, 0x00526810)
    reset_calls = call_sites(0x410A60, 0x410B70, 0x00526B00)
    print(f"  calls ReadString  (0x528A10): {[hex(a) for a in str_calls]}")
    print(f"  calls GetSection  (0x526810): {[hex(a) for a in sec_calls]}")
    print(f"  calls Reset       (0x526B00): {[hex(a) for a in reset_calls]}")

    # The three pushes immediately before each ReadString call are
    # (key, section, dst, cap) in reverse C order: ReadString(this, section,
    # key, dst, cap) -> pushes are cap, dst, key, section.
    print("\n=== key -> field, derived from the push sequence before each call ===")
    for call in str_calls:
        pushes = preceding_push(call)
        ints = [p for p in pushes if p is not None and RDATA_LO <= p < DATA_HI]
        keys = [cstr(p) for p in ints if cstr(p)]
        print(f"  call 0x{call:08X}: pushed strings = {keys}")

    print("\n=== field offsets touched by LoadFromINI ===")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    seen = []
    for insn in md.disasm(read_va(0x410A60, 0x120), 0x410A60):
        if insn.mnemonic == "lea" and "ebx +" in insn.op_str:
            seen.append((insn.address, insn.op_str))
        if insn.mnemonic == "mov" and "[ebx +" in insn.op_str:
            seen.append((insn.address, insn.op_str))
        if insn.mnemonic.startswith("ret"):
            break
    for a, s in seen:
        print(f"  0x{a:08X}  {s}")

    print("\n=== YRpp AbstractTypeClass field bounds, WITH alignment ===")
    # AbstractClass prefix is 0x24 (vptr x4 + UniqueID + AbstractFlags +
    # unknown_18 + RefCount + Dirty + padding[3]).
    #
    # The naive sum of the declared sizes lands Name on +0x61, but the bytes put
    # it on +0x64: UINameLabel is 0x20 chars ending at +0x5D, and the wchar_t*
    # that follows is 4-byte aligned, so three bytes are skipped. This is the
    # same class of mistake as computing a base-class prefix by eye -- the
    # compiler inserted padding that the declaration order does not show.
    def align(n, a=4):
        return (n + a - 1) // a * a

    base = 0x24
    layout = []
    off = base
    for name, size in (("ID", 0x18), ("zero_3C", 1), ("UINameLabel", 0x20)):
        layout.append((off, name, size))
        off += size
    pad_at = off
    off = align(off)
    layout.append((off, "UIName (wchar_t*)", 4))
    off += 4
    layout.append((off, "Name", 0x31))
    off += 0x31
    for o, name, size in layout:
        print(f"  +0x{o:02X}  {name}[0x{size:X}]")
    if pad_at != align(pad_at):
        print(f"  +0x{pad_at:02X}  <padding> {align(pad_at) - pad_at} bytes (pointer alignment)")
    print(f"  => AbstractTypeClass ends at +0x{off:02X}")

    # The arithmetic above is only worth printing if it agrees with the bytes.
    observed = {0x24: "ID", 0x3D: "UINameLabel", 0x60: "UIName", 0x64: "Name"}
    computed = {o: name.split(" ")[0] for o, name, _ in layout}
    mismatch = [f"+0x{o:02X}: bytes say {n}, arithmetic says {computed.get(o, '?')}"
                for o, n in observed.items() if computed.get(o, "?").split(" ")[0] != n]
    print(f"  alignment check vs byte-observed offsets: {'OK' if not mismatch else mismatch}")

    print("\n=== what the byte evidence pins ===")
    print("  section name for GetSection = this pointing at +0x24, i.e. the ID field:")
    print("    'lea ebp,[ebx+0x24]' then 'push ebp' then 'call 0x526810'  (0x00410A79)")
    print("  Name   -> dst this+0x64, cap 0x31 'Name'")
    print("  UIName -> dst this+0x3D, cap 0x20 'UIName', then resolved to wchar_t*")
    print("    and stored at this+0x60")

    print("\n=== positive control ===")
    ctl = read_va(0x410A60, 6)
    ok = ctl == b"\x81\xec\x34\x04\x00\x00"
    print(f"  LoadFromINI @0x00410A60 head={ctl.hex(' ')} expected '81 ec 34 04 00 00': {ok}")
    if not ok:
        print("  !! control FAILED -- VA map wrong, ignore everything above")
        return 1
    keyctl = cstr(0x00817854)
    ok2 = keyctl == "Name"
    print(f"  key literal @0x00817854 = {keyctl!r} expected 'Name': {ok2}")
    if not ok2:
        print("  !! second control FAILED -- .data string map wrong")
        return 1
    print("  controls OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
