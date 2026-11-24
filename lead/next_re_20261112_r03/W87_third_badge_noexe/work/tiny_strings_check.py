import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r03\W87_third_badge_noexe")
data = (BASE / "work" / "gamemd.exe").read_bytes()
EVID = BASE / "EVIDENCE"

pe_off = struct.unpack_from("<I", data, 0x3C)[0]
num_sec = struct.unpack_from("<H", data, pe_off + 6)[0]
opt_sz = struct.unpack_from("<H", data, pe_off + 20)[0]
image_base = struct.unpack_from("<I", data, pe_off + 24 + 28)[0]
sec_off = pe_off + 24 + opt_sz
sections = []
for i in range(num_sec):
    s = sec_off + i * 40
    name = data[s:s+8].split(b"\x00", 1)[0].decode("ascii", errors="replace")
    vsize, vaddr, rsize, rptr = struct.unpack_from("<4I", data, s + 8)
    sections.append((name, image_base + vaddr, vsize, rptr, rsize))

def va_to_foff(va):
    for name, sva, vsz, rptr, rsz in sections:
        span = max(vsz, rsz)
        if sva <= va < sva + span:
            off = va - sva
            if off < rsz:
                return rptr + off
    return None

def read_cstr(va):
    f = va_to_foff(va)
    if f is None:
        return None
    end = data.find(b"\x00", f, f + 256)
    return data[f:end if end != -1 else f+64].decode("ascii", errors="replace")

lines = []
for va in [0x84639C, 0x846374, 0x821D30, 0x821D1C, 0x835958]:
    lines.append(f"0x{va:08X} -> {read_cstr(va)!r}")

# Decode jump table at 0x616354 (pointers) and 0x616383 (index table?)
lines.append("\n=== Static_Handler Jump Table @0x616354 ===")
f_jt = va_to_foff(0x616354)
for idx in range(12):
    val = struct.unpack_from("<I", data, f_jt + idx * 4)[0]
    lines.append(f"  JT[{idx:2d}] = 0x{val:08X}")

md = Cs(CS_ARCH_X86, CS_MODE_32)
def dump(sva, eva, label):
    lines.append(f"\n=== {label} [0x{sva:08X}-0x{eva:08X}] ===")
    f = va_to_foff(sva)
    for insn in md.disasm(data[f:f+(eva-sva)], sva):
        if insn.address >= eva:
            break
        lines.append(f"0x{insn.address:08X} (foff 0x{va_to_foff(insn.address):06X}): {insn.bytes.hex():<22} {insn.mnemonic} {insn.op_str}")

dump(0x615457, 0x61559D, "Static_Handler_Switch_615457")
dump(0x615B6B, 0x615BD0, "Static_Handler_Msg_0x10_to_0x496")
dump(0x616698, 0x6167B5, "Button_Style3_Msg_0xF0_to_0x203_plus")
dump(0x616848, 0x616890, "Button_Style3_Default_0x61685a")
dump(0x74FDB0, 0x74FE20, "VerQuery_Func_Head_74FDB0")

(EVID / "tiny_strings_check.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote tiny_strings_check.txt ({len(lines)} lines)")
