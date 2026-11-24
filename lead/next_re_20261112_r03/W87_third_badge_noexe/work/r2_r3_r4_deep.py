import struct
from pathlib import Path
import capstone
from pe_iat_rsrc import MiniPE, GAMEMD, DDRAW

WORK = Path(__file__).resolve().parent
EVIDENCE = WORK.parent / "EVIDENCE"


def build_iat_map(pe: MiniPE) -> dict[int, str]:
    iat_map = {}
    for dll, _iat_rva, entries in pe.parse_imports():
        for slot_va, _slot_rva, fname in entries:
            iat_map[slot_va] = f"{dll}!{fname}"
    return iat_map


def va_to_foff_strict(pe: MiniPE, va: int) -> int | None:
    rva = va - pe.image_base
    for s in pe.sections:
        if s["rva"] <= rva < s["rva"] + s["raw_size"]:
            off = s["raw_ptr"] + (rva - s["rva"])
            if off < len(pe.raw):
                return off
    return None


def read_cstr_va(pe: MiniPE, va: int, max_len: int = 128) -> str | None:
    foff = va_to_foff_strict(pe, va)
    if foff is None:
        return None
    end = pe.raw.find(b"\x00", foff, min(len(pe.raw), foff + max_len))
    if end == -1:
        return None
    blob = pe.raw[foff:end]
    try:
        s = blob.decode("ascii")
        if all(32 <= ord(c) < 127 for c in s) and len(s) > 0:
            return s
    except UnicodeDecodeError:
        pass
    return None


def annotate_insn(pe: MiniPE, iat_map: dict[int, str], insn) -> str:
    notes = []
    # Direct IAT memory reference [0x7e1xxx]
    for op in insn.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
            addr = op.mem.disp & 0xFFFFFFFF
            if addr in iat_map:
                notes.append(iat_map[addr])
        elif op.type == capstone.x86.X86_OP_IMM:
            imm = op.imm & 0xFFFFFFFF
            if imm in iat_map:
                notes.append(iat_map[imm])
            elif 0x007E1000 <= imm < 0x00B7A000:
                s = read_cstr_va(pe, imm)
                if s:
                    notes.append(f'"{s}"')
    return (" ; " + ", ".join(notes)) if notes else ""


def disasm_range(pe: MiniPE, md, iat_map: dict[int, str], start_va: int, end_va: int, title: str):
    lines = [f"=== {title} (VA 0x{start_va:08X}..0x{end_va:08X}) ==="]
    foff = va_to_foff_strict(pe, start_va)
    if foff is None:
        lines.append(f"  <unmapped start VA 0x{start_va:08X}>")
        return lines
    code = pe.raw[foff:foff + (end_va - start_va)]
    for insn in md.disasm(code, start_va):
        rva = insn.address - pe.image_base
        f = va_to_foff_strict(pe, insn.address)
        bhex = insn.bytes.hex()
        note = annotate_insn(pe, iat_map, insn)
        lines.append(
            f"0x{insn.address:08X} (RVA 0x{rva:06X}, foff 0x{f:06X}) {bhex:<22} {insn.mnemonic:<8} {insn.op_str}{note}"
        )
    lines.append("")
    return lines


def find_imm_calls_or_refs(pe: MiniPE, md, target_va: int, sec_names=(".text", ".detour")):
    """Find call/jmp/mov/push/mem references to target_va across code sections."""
    hits = []
    tbytes = struct.pack("<I", target_va)
    for s in pe.sections:
        if s["name"] not in sec_names:
            continue
        sec_raw = pe.raw[s["raw_ptr"]:s["raw_ptr"] + s["raw_size"]]
        sec_va = pe.image_base + s["rva"]
        # Scan for exact LE32 immediate/displacement
        pos = 0
        while True:
            idx = sec_raw.find(tbytes, pos)
            if idx == -1:
                break
            pos = idx + 1
            # Disassemble around idx - 4..idx + 6 to verify aligned instruction
            start = max(0, idx - 6)
            for off in range(start, idx + 1):
                insns = list(md.disasm(sec_raw[off:off + 12], sec_va + off, count=1))
                if not insns:
                    continue
                ins = insns[0]
                if ins.address <= sec_va + idx < ins.address + ins.size:
                    hits.append((s["name"], ins.address, sec_raw[off:off + ins.size].hex(), f"{ins.mnemonic} {ins.op_str}"))
                    break
        # Also scan for rel32 E8/E9 to target_va
        for opcode in (0xE8, 0xE9):
            b = bytes([opcode])
            pos = 0
            while True:
                idx = sec_raw.find(b, pos)
                if idx == -1:
                    break
                pos = idx + 1
                if idx + 5 > len(sec_raw):
                    break
                ins_va = sec_va + idx
                rel = struct.unpack_from("<i", sec_raw, idx + 1)[0]
                if (ins_va + 5 + rel) & 0xFFFFFFFF == target_va:
                    mnem = "call" if opcode == 0xE8 else "jmp"
                    hits.append((s["name"], ins_va, sec_raw[idx:idx + 5].hex(), f"{mnem} 0x{target_va:08X}"))
    # deduplicate preserving order
    seen = set()
    uniq = []
    for h in hits:
        if h[1] not in seen:
            seen.add(h[1])
            uniq.append(h)
    return sorted(uniq, key=lambda x: x[1])


def find_const_refs(pe: MiniPE, md, const_val: int, sec_names=(".text", ".detour")):
    """Find instructions using const_val as imm32 (68/81/B8..BF/C7) or matching instruction operand."""
    hits = []
    tbytes = struct.pack("<I", const_val)
    for s in pe.sections:
        if s["name"] not in sec_names:
            continue
        sec_raw = pe.raw[s["raw_ptr"]:s["raw_ptr"] + s["raw_size"]]
        sec_va = pe.image_base + s["rva"]
        pos = 0
        while True:
            idx = sec_raw.find(tbytes, pos)
            if idx == -1:
                break
            pos = idx + 1
            for back in range(1, 7):
                if idx - back < 0:
                    break
                insns = list(md.disasm(sec_raw[idx - back:idx + 6], sec_va + idx - back, count=1))
                if not insns:
                    continue
                ins = insns[0]
                if ins.address + ins.size == sec_va + idx + 4 or (ins.address <= sec_va + idx and ins.address + ins.size >= sec_va + idx + 4):
                    has_imm = any(
                        op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == const_val
                        for op in ins.operands
                    )
                    if has_imm:
                        hits.append((s["name"], ins.address, ins.bytes.hex(), f"{ins.mnemonic} {ins.op_str}"))
                        break
    seen = set()
    uniq = []
    for h in hits:
        if h[1] not in seen:
            seen.add(h[1])
            uniq.append(h)
    return sorted(uniq, key=lambda x: x[1])


def main():
    raw_exe = GAMEMD.read_bytes()
    pe = MiniPE(raw_exe)
    iat_map = build_iat_map(pe)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    out = []
    out.append("=== W87 DEEP PROBE (R1 / R2 / R3 / R4) ===")
    out.append("gamemd.exe sections (VA, VSize, RawPtr, RawSize):")
    for s in pe.sections:
        out.append(
            f"  {s['name']:<8} VA=0x{s['va']:08X} VSize=0x{s['vsize']:X} "
            f"RawPtr=0x{s['raw_ptr']:06X} RawSize=0x{s['raw_size']:X} Char=0x{s['char']:08X}"
        )
    out.append("")

    # Resolve all IAT slots used in 0x52EC00..0x52F3EA
    out.append("=== IAT Slots Referenced in 0x52EC00..0x52F3EA ===")
    wnd_slots = [
        0x7E13B0, 0x7E13B4, 0x7E13B8, 0x7E13BC, 0x7E13F8, 0x7E13FC,
        0x7E1450, 0x7E1470, 0x7E1474, 0x7E1490, 0x7E1498, 0x7E14A0,
        0x7E14A4, 0x7E14A8, 0x7E14AC, 0x7E14B8, 0x7E14C4, 0x7E1394,
        0x7E13D4, 0x7E13D8, 0x7E13F0, 0x7E1404, 0x7E1508,
    ]
    for sl in sorted(set(wnd_slots)):
        out.append(f"  0x{sl:08X} -> {iat_map.get(sl, '<UNKNOWN>')}")
    out.append("")

    # Disassemble R1 & R2 functions
    extra_disasm = []
    extra_disasm += disasm_range(pe, md, iat_map, 0x0052DF20, 0x0052DFA0, "Campaign_Menu_Dialog_Entry")
    extra_disasm += disasm_range(pe, md, iat_map, 0x004A3B40, 0x004A3B80, "Load_Resource_Helper")
    extra_disasm += disasm_range(pe, md, iat_map, 0x00622650, 0x00622960, "Dialog_Create_Helper & EnumChildWindows setup")
    extra_disasm += disasm_range(pe, md, iat_map, 0x00622B50, 0x00622E40, "Base_Dialog_WndProc_Helper (called at 0x52EC1D)")

    # Find EnumChildWindows / SetWindowLongA(-4) callbacks and custom messages 0x4D3/0x4D4/0x4D5/0x4D7
    out.append("=== Custom Message Constant Hits across .text & .detour ===")
    for msg in (0x4D3, 0x4D4, 0x4D5, 0x4D7, 0x4B2, 0x4CD, 0x497, 0x4D8):
        hits = find_const_refs(pe, md, msg)
        out.append(f"  msg 0x{msg:X} ({len(hits)} hits):")
        for sec, va, hx, txt in hits[:40]:
            out.append(f"    [{sec}] 0x{va:08X} {hx:<20} {txt}")
    out.append("")

    # Inspect SetWindowLongA (-4 GWL_WNDPROC) callers near 0x622xxx or all occurrences
    swl_hits = find_imm_calls_or_refs(pe, md, 0x007E1470)
    out.append(f"=== All SetWindowLongA (IAT 0x7E1470) refs in .text/.detour ({len(swl_hits)}) ===")
    for sec, va, hx, txt in swl_hits:
        foff = va_to_foff_strict(pe, va)
        pre = list(md.disasm(pe.raw[foff - 28:foff], va - 28))
        ctx = " | ".join(f"{i.mnemonic} {i.op_str}" for i in pre[-4:])
        out.append(f"  [{sec}] 0x{va:08X} ({txt})  <- {ctx}")
    out.append("")

    # Disassemble any SetWindowLongA proc around 0x622xxx or 0x60Fxxx if referenced in 0x622650..0x622E40
    # Wait: let's also check strings in campaign menu data pointers
    out.append("=== Campaign Menu Data Pointers & Strings ===")
    ptrs = [
        0x825C68, 0x825C6C, 0x825C70, 0x825C74, 0x825C78, 0x825C7C, 0x825C20,
        0x825FB8, 0x8263B0, 0x8263C8, 0x8263E0, 0x8263F0, 0x826408,
    ]
    for p in ptrs:
        foff = va_to_foff_strict(pe, p)
        if foff is not None:
            dw = struct.unpack_from("<I", pe.raw, foff)[0]
            s_direct = read_cstr_va(pe, p)
            s_indirect = read_cstr_va(pe, dw) if 0x400000 <= dw < 0xB96000 else None
            out.append(f"  0x{p:08X}: dword=0x{dw:08X} direct={s_direct!r} indirect={s_indirect!r}")
    out.append("")

    # R3: Control IDs 1820 (0x71C), 1959 (0x7A7), 1960 (0x7A8), 1770 (0x6EA), 1771 (0x6EB), 1772 (0x6EC)
    out.append("=== R3: Campaign Control ID Hits across .text & .detour ===")
    for cid in (1770, 1771, 1772, 1820, 1959, 1960):
        hits = find_const_refs(pe, md, cid)
        out.append(f"  ID {cid} (0x{cid:X}): {len(hits)} hits")
        for sec, va, hx, txt in hits:
            out.append(f"    [{sec}] 0x{va:08X} {hx:<20} {txt}")
    out.append("")

    # R1: Check EntryPoint, .detour section, DirectDrawCreate callers, ddraw.dll strings, GetFileVersionInfo callers
    out.append("=== R1: EntryPoint, .detour, and ddraw.dll references in gamemd.exe ===")
    extra_disasm += disasm_range(pe, md, iat_map, pe.image_base + pe.entry_rva, pe.image_base + pe.entry_rva + 0x90, "PE EntryPoint")
    for s in pe.sections:
        if s["name"] == ".detour":
            sec_raw = pe.raw[s["raw_ptr"]:s["raw_ptr"] + s["raw_size"]]
            # Dump printable ASCII strings >=4 chars in .detour
            detour_strs = []
            cur = bytearray()
            start_off = 0
            for i, b in enumerate(sec_raw):
                if 32 <= b < 127:
                    if not cur:
                        start_off = i
                    cur.append(b)
                else:
                    if len(cur) >= 4:
                        detour_strs.append((s["va"] + start_off, cur.decode("ascii")))
                    cur.clear()
            out.append(f"  .detour raw_size={s['raw_size']} B, strings={detour_strs}")
            # Disassemble beginning of .detour
            extra_disasm += disasm_range(pe, md, iat_map, s["va"], s["va"] + min(0x180, s["raw_size"]), ".detour head")

    # Search all sections for 'ddraw' (case-insensitive ASCII and UTF-16LE)
    for enc_name, pat in [
        ("ASCII", b"ddraw"),
        ("UTF-16LE", "ddraw".encode("utf-16le")),
    ]:
        raw_low = raw_exe.lower() if enc_name == "ASCII" else raw_exe
        # Wait: case-insensitive search properly
        found_locs = []
        if enc_name == "ASCII":
            idx = 0
            low = raw_exe.lower()
            while True:
                k = low.find(b"ddraw", idx)
                if k == -1:
                    break
                found_locs.append((k, raw_exe[max(0, k - 8):k + 32]))
                idx = k + 1
        else:
            for p_str in ("ddraw", "DDRAW", "Ddraw"):
                pb = p_str.encode("utf-16le")
                idx = 0
                while True:
                    k = raw_exe.find(pb, idx)
                    if k == -1:
                        break
                    found_locs.append((k, raw_exe[max(0, k - 8):k + 32]))
                    idx = k + 2
        out.append(f"  gamemd.exe '{enc_name}' ddraw hits ({len(found_locs)}):")
        for off, snip in found_locs:
            out.append(f"    foff=0x{off:06X}: {snip!r}")

    # DirectDrawCreate IAT (0x7E1048) and VERSION.dll IAT refs
    for dll, _iat_rva, entries in pe.parse_imports():
        if dll.upper() in ("DDRAW.DLL", "VERSION.DLL"):
            for slot_va, _slot_rva, fname in entries:
                refs = find_imm_calls_or_refs(pe, md, slot_va)
                out.append(f"  Refs to {dll}!{fname} (0x{slot_va:08X}): {len(refs)}")
                for sec, va, hx, txt in refs[:15]:
                    out.append(f"    [{sec}] 0x{va:08X} {hx:<18} {txt}")
    out.append("")

    # R4: All Resource & Dialog creation API IAT slots and refs
    out.append("=== R4: Exhaustive Resource & Dialog API Refs ===")
    target_apis = {
        "FindResourceA", "FindResourceW", "LoadResource", "LockResource", "SizeofResource",
        "DialogBoxParamA", "DialogBoxParamW", "DialogBoxIndirectParamA", "DialogBoxIndirectParamW",
        "CreateDialogParamA", "CreateDialogParamW", "CreateDialogIndirectParamA", "CreateDialogIndirectParamW",
    }
    for dll, _iat_rva, entries in pe.parse_imports():
        for slot_va, _slot_rva, fname in entries:
            if fname in target_apis:
                refs = find_imm_calls_or_refs(pe, md, slot_va)
                out.append(f"  {dll}!{fname} @ IAT 0x{slot_va:08X}: {len(refs)} refs")
                for sec, va, hx, txt in refs:
                    out.append(f"    [{sec}] 0x{va:08X} {hx:<18} {txt}")

    load_res_callers = find_imm_calls_or_refs(pe, md, 0x004A3B40)
    out.append(f"  Callers/refs to 0x004A3B40 (Load_Resource_Helper): {len(load_res_callers)}")
    for sec, va, hx, txt in load_res_callers:
        out.append(f"    [{sec}] 0x{va:08X} {hx:<18} {txt}")

    dlg_helper_callers = find_imm_calls_or_refs(pe, md, 0x00622650)
    out.append(f"  Callers/refs to 0x00622650 (Dialog_Create_Helper): {len(dlg_helper_callers)}")
    for sec, va, hx, txt in dlg_helper_callers:
        out.append(f"    [{sec}] 0x{va:08X} {hx:<18} {txt}")
    out.append("")

    # R3 & R4: Exhaustive string scan across .rdata + .data + .detour (exact disk spans)
    out.append("=== R3/R4: String Scan (.rdata + .data + .detour, ASCII + UTF-16LE, with Positive Controls) ===")
    scan_sections = [s for s in pe.sections if s["name"] in (".rdata", ".data", ".detour")]
    total_scan_bytes = sum(s["raw_size"] for s in scan_sections)
    out.append(f"  Scanned sections: {[(s['name'], hex(s['va']), s['raw_size']) for s in scan_sections]}, total={total_scan_bytes} bytes")
    keywords = [
        # Positive controls
        "CAMPAIGN.PCX", "GUI:CampaignMenu", "DIALOG.PAL", "BATTLEMD", "BootCamp",
        # R3 candidates
        "ControlID", "CtrlID", "Remap", "DialogID", "BadgeID",
        # R4 candidates
        "DLGTEMPLATE", ".DLG", "DIALOG.INI", "UI.INI", "MENU.INI", "DialogTemplate",
    ]
    for kw in keywords:
        asc_hits = []
        u16_hits = []
        pat_a = kw.lower().encode("ascii")
        # For UTF-16LE, test exact & lower/upper
        pats_u = {kw.encode("utf-16le"), kw.lower().encode("utf-16le"), kw.upper().encode("utf-16le")}
        for s in scan_sections:
            blob = pe.raw[s["raw_ptr"]:s["raw_ptr"] + s["raw_size"]]
            low = blob.lower()
            pos = 0
            while True:
                k = low.find(pat_a, pos)
                if k == -1:
                    break
                ctx = blob[max(0, k - 4):k + len(kw) + 16].split(b"\x00", 1)[0]
                asc_hits.append((s["name"], s["va"] + k, ctx.decode("ascii", "replace")))
                pos = k + 1
            for pu in pats_u:
                pos = 0
                while True:
                    k = blob.find(pu, pos)
                    if k == -1:
                        break
                    u16_hits.append((s["name"], s["va"] + k))
                    pos = k + 2
        out.append(f"  kw={kw!r}: ASCII={len(asc_hits)} {asc_hits[:5]}, UTF-16LE={len(u16_hits)} {u16_hits[:5]}")
    out.append("")

    # Inspect work\ddraw.dll
    raw_dd = DDRAW.read_bytes()
    pe_dd = MiniPE(raw_dd)
    out.append("=== R1: work\\ddraw.dll PE & cnc-ddraw metadata ===")
    out.append(f"  Size={len(raw_dd)} B ImageBase=0x{pe_dd.image_base:08X} SizeOfImage=0x{pe_dd.size_of_image:08X} EntryRVA=0x{pe_dd.entry_rva:08X}")
    out.append("  Sections:")
    for s in pe_dd.sections:
        out.append(f"    {s['name']:<8} VA=0x{s['va']:08X} VSize=0x{s['vsize']:X} RawPtr=0x{s['raw_ptr']:06X} RawSize=0x{s['raw_size']:X}")
    out.append("  Imports of ddraw.dll:")
    for dll, _iat_rva, entries in pe_dd.parse_imports():
        names = [fname for _sva, _srva, fname in entries]
        out.append(f"    {dll} ({len(names)}): {names}")
    for marker in (b"cnc-ddraw", b"GameHandlesClose", b"DirectDrawCreate"):
        c = raw_dd.count(marker)
        out.append(f"  ddraw.dll occurrences of {marker!r}: {c}")

    (EVIDENCE / "r2_r3_r4_deep_stdout.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    (EVIDENCE / "r1_r2_dialog_helpers.txt").write_text("\n".join(extra_disasm) + "\n", encoding="utf-8")
    print(f"Wrote r2_r3_r4_deep_stdout.txt ({len(out)} lines) and r1_r2_dialog_helpers.txt ({len(extra_disasm)} lines)")


if __name__ == "__main__":
    main()
