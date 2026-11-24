import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r03\W87_third_badge_noexe")
EXE_PATH = BASE / "work" / "gamemd.exe"
EVID = BASE / "EVIDENCE"

data = EXE_PATH.read_bytes()

# Parse PE sections
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

def va_to_foff(va: int):
    for name, sva, vsz, rptr, rsz in sections:
        span = max(vsz, rsz)
        if sva <= va < sva + span:
            off = va - sva
            if off < rsz:
                return rptr + off
    return None

def foff_to_va(foff: int):
    for name, sva, vsz, rptr, rsz in sections:
        if rptr <= foff < rptr + rsz:
            return sva + (foff - rptr)
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32)

def disasm_range(start_va: int, end_va: int, label: str, out_lines: list):
    out_lines.append(f"=== {label} [0x{start_va:08X} - 0x{end_va:08X}] ===")
    foff = va_to_foff(start_va)
    if foff is None:
        out_lines.append("  <unmapped>")
        return
    code = data[foff:foff + (end_va - start_va)]
    for insn in md.disasm(code, start_va):
        if insn.address >= end_va:
            break
        rva = insn.address - image_base
        ifoff = va_to_foff(insn.address)
        bhex = insn.bytes.hex()
        out_lines.append(f"0x{insn.address:08X} (RVA 0x{rva:06X}, foff 0x{ifoff:06X}): {bhex:<24} {insn.mnemonic} {insn.op_str}")
    out_lines.append("")

stdout_lines = []
disasm_lines = []

# 1. Disassemble requested ranges
ranges = [
    (0x6153E0, 0x615460, "Static_Handler_Head"),
    (0x61559D, 0x615690, "Static_Handler_WM_PAINT"),
    (0x615BD0, 0x6163A5, "Static_Handler_Tail_And_JumpTable"),
    (0x6C9310, 0x6C93F0, "Msg_0x4D3_0x4D5_0x4D7_Hit_6C9310"),
    (0x612B70, 0x612C60, "Button_OwnerDraw_Handler_Head"),
    (0x6163A0, 0x616460, "Button_Style3_Handler_Head"),
    (0x602F40, 0x602FC0, "ID_1820_Caller_602F40"),
    (0x603550, 0x6035B0, "ID_1820_Caller_603550"),
    (0x608640, 0x6086D0, "ID_1959_1960_Site_608640"),
    (0x46DF80, 0x46DFB5, "ID_1820_Site_46DF80"),
    (0x4C8500, 0x4C8595, "Dialog_Loader_4C8500"),
]

for sva, eva, lbl in ranges:
    disasm_range(sva, eva, lbl, disasm_lines)

# 2. Scan .text for relative E8/E9 targeting VERSION.dll thunks 0x7C89E0, 0x7C89E6, 0x7C89EC
# Also check IAT slots for VERSION.dll in .rdata
targets = {0x7C89E0: "GetFileVersionInfoSizeA_thunk", 0x7C89E6: "GetFileVersionInfoA_thunk", 0x7C89EC: "VerQueryValueA_thunk"}
text_sec = [s for s in sections if s[0] == ".text"][0]
_, text_va, text_vsz, text_rptr, text_rsz = text_sec
text_bytes = data[text_rptr:text_rptr + text_rsz]

stdout_lines.append("=== Callers of VERSION.dll thunks in .text ===")
for t_va, t_name in targets.items():
    hits = []
    for i in range(len(text_bytes) - 5):
        op = text_bytes[i]
        if op in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", text_bytes, i + 1)[0]
            caller_va = text_va + i
            dest = caller_va + 5 + rel
            if dest == t_va:
                hits.append((caller_va, text_rptr + i, op))
    stdout_lines.append(f"{t_name} (0x{t_va:08X}): {len(hits)} hits")
    for cva, cfoff, op in hits:
        stdout_lines.append(f"  0x{cva:08X} (foff 0x{cfoff:06X}) op=0x{op:02X}")
        disasm_range(cva - 0x20, cva + 0x20, f"Caller_of_{t_name}_0x{cva:08X}", disasm_lines)

# 3. Direct check of VERSION.dll IAT slots in .text/.rdata (ff 15 / ff 25 / a1 etc.)
# First dump thunk bytes at 0x7C89D0..0x7C89F8
disasm_range(0x7C89D0, 0x7C89F8, "Thunks_DDRAW_VERSION", disasm_lines)

# 4. Parse RT_DIALOG 148 directly from work\gamemd.exe .rsrc
rsrc_sec = [s for s in sections if s[0] == ".rsrc"][0]
_, rsrc_va, rsrc_vsz, rsrc_rptr, rsrc_rsz = rsrc_sec

def read_rsrc_dir(off):
    _, _, _, _, n_named, n_id = struct.unpack_from("<IIHHHH", data, rsrc_rptr + off)
    entries = []
    pos = rsrc_rptr + off + 16
    for _ in range(n_named + n_id):
        name_or_id, data_or_sub = struct.unpack_from("<II", data, pos)
        entries.append((name_or_id, data_or_sub))
        pos += 8
    return entries

dlg148_info = None
for tid, tsub in read_rsrc_dir(0):
    if tid == 5:  # RT_DIALOG
        for did, dsub in read_rsrc_dir(tsub & 0x7FFFFFFF):
            if did == 148:
                for lid, ldata in read_rsrc_dir(dsub & 0x7FFFFFFF):
                    data_rva, size, cp, _ = struct.unpack_from("<4I", data, rsrc_rptr + (ldata & 0x7FFFFFFF))
                    data_foff = va_to_foff(image_base + data_rva)
                    dlg148_info = (lid, data_rva, size, data_foff)

stdout_lines.append("")
stdout_lines.append("=== RT_DIALOG 148 Parsed from work\\gamemd.exe ===")
if dlg148_info:
    lid, data_rva, size, data_foff = dlg148_info
    stdout_lines.append(f"Lang=0x{lid:04X}, DataRVA=0x{data_rva:06X}, FileOffset=0x{data_foff:06X}, Size={size} B")
    blob = data[data_foff:data_foff + size]
    dlgVer, sig, helpID, exStyle, style, cDlgItems, x, y, cx, cy = struct.unpack_from("<HHIIIhhhhh", blob, 0)
    stdout_lines.append(f"DLGTEMPLATEEX: dlgVer=0x{dlgVer:04X} sig=0x{sig:04X} helpID={helpID} exStyle=0x{exStyle:08X} style=0x{style:08X} cDlgItems={cDlgItems} rect=({x},{y},{cx},{cy})")
    p = 26
    def read_sz_or_ord(buf, idx):
        w = struct.unpack_from("<H", buf, idx)[0]
        if w == 0x0000:
            return ("", idx + 2)
        if w == 0xFFFF:
            ord_val = struct.unpack_from("<H", buf, idx + 2)[0]
            return (f"#{ord_val}", idx + 4)
        end = idx
        while struct.unpack_from("<H", buf, end)[0] != 0:
            end += 2
        s = buf[idx:end].decode("utf-16le", errors="replace")
        return (s, end + 2)

    menu, p = read_sz_or_ord(blob, p)
    cls, p = read_sz_or_ord(blob, p)
    title, p = read_sz_or_ord(blob, p)
    stdout_lines.append(f"  menu={menu!r} class={cls!r} title={title!r}")
    if style & 0x40:
        pt_sz, weight, italic, charset = struct.unpack_from("<HHBB", blob, p)
        p += 6
        face, p = read_sz_or_ord(blob, p)
        stdout_lines.append(f"  font={face!r} pt={pt_sz} weight={weight} italic={italic} charset={charset}")
    for i in range(cDlgItems):
        p = (p + 3) & ~3
        item_start = p
        ihelp, iex, istyle, ix, iy, icx, icy, iid = struct.unpack_from("<IIIhhhhI", blob, p)
        p += 24
        icls, p = read_sz_or_ord(blob, p)
        ititle, p = read_sz_or_ord(blob, p)
        extra_cnt = struct.unpack_from("<H", blob, p)[0]
        p += 2 + extra_cnt
        item_len = p - item_start
        stdout_lines.append(f"  Item[{i:02d}] @+0x{item_start:03X} ({item_len:2d}B): id={iid:4d} (0x{iid:03X}) cls={icls:<8} rect=({ix:3d},{iy:3d},{icx:3d}x{icy:3d}) style=0x{istyle:08X} ex=0x{iex:08X} title={ititle!r} extra={extra_cnt}")
    stdout_lines.append(f"  End offset={p}, Size={size}, Trailing={size - p} B")

(EVID / "r2_r3_final_check_stdout.txt").write_text("\n".join(stdout_lines), encoding="utf-8")
(EVID / "r2_r3_final_disasm.txt").write_text("\n".join(disasm_lines), encoding="utf-8")
print(f"Wrote r2_r3_final_check_stdout.txt ({len(stdout_lines)} lines) and r2_r3_final_disasm.txt ({len(disasm_lines)} lines)")
