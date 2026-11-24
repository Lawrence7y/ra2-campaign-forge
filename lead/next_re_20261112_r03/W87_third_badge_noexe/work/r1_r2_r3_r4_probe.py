import struct
from pathlib import Path
import capstone
from pe_iat_rsrc import MiniPE

WORK = Path(__file__).resolve().parent
EVIDENCE = WORK.parent / "EVIDENCE"
GAMEMD = WORK / "gamemd.exe"

def disasm_to_list(pe: MiniPE, start_va: int, end_va: int, md: capstone.Cs):
    foff = pe.va_to_foff(start_va)
    code = pe.raw[foff:foff + (end_va - start_va)]
    lines = []
    for insn in md.disasm(code, start_va):
        if insn.address >= end_va:
            break
        ins_foff = pe.va_to_foff(insn.address)
        lines.append(f"0x{insn.address:08X} (0x{ins_foff:06X}) {insn.bytes.hex():20s} {insn.mnemonic:8s} {insn.op_str}")
    return lines

def main():
    pe = MiniPE(GAMEMD.read_bytes())
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    # 1. Full disassembly of 0x52EC00..0x52F3E8 -> EVIDENCE\wndproc_52EC00_full.txt
    wnd_lines = disasm_to_list(pe, 0x0052EC00, 0x0052F3EA, md)
    (EVIDENCE / "wndproc_52EC00_full.txt").write_text("\n".join(wnd_lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(wnd_lines)} lines to wndproc_52EC00_full.txt")

    # 2. Disassemble 0x52D090..0x52D110, 0x775700..0x775790, 0x777080..0x777150, 0x5D4E70..0x5D4F00
    extra = []
    for title, s, e in [
        ("0x52D090..0x52D110 (DialogBoxParamA site)", 0x0052D090, 0x0052D110),
        ("0x775700..0x775790 (CreateDialogIndirectParamA site 2)", 0x00775700, 0x00775790),
        ("0x777080..0x777180 (called after Dialog_Create_Helper)", 0x00777080, 0x00777180),
        ("0x5D4E70..0x5D4F10 (called inside Dialog_Create_Helper)", 0x005D4E70, 0x005D4F10),
        ("0x7775C0..0x777700 (dialog wrapper WndProc?)", 0x007775C0, 0x00777700),
    ]:
        extra.append(f"=== {title} ===")
        extra.extend(disasm_to_list(pe, s, e, md))
        extra.append("")
    (EVIDENCE / "r1_r2_extra_disasm.txt").write_text("\n".join(extra) + "\n", encoding="utf-8")
    print(f"Wrote {len(extra)} lines to r1_r2_extra_disasm.txt")

    # 3. Check 0x52EC00..0x52F3E8 for control IDs: 1820 (0x71C), 1959 (0x7A7), 1960 (0x7A8), 1038 (0x40E), 1670 (0x686), 1295 (0x50F), 1109 (0x455)
    # Also check ALL immediate constants in 0x52EC00..0x52F3E8
    foff = pe.va_to_foff(0x0052EC00)
    code = pe.raw[foff:foff + (0x0052F3EA - 0x0052EC00)]
    print("\n=== Control ID / constant hits in 0x52EC00..0x52F3EA ===")
    ids = {
        0x40E: "1038 (GUI:Load)",
        0x455: "1109 (ListBox)",
        0x50F: "1295 (Slider)",
        0x670: "1648 (GUI:Harder)",
        0x686: "1670 (GUI:Back)",
        0x694: "1684 (GUI:CampaignMenu)",
        0x695: "1685 (GUI:Blank)",
        0x6EA: "1770 (Allied badge)",
        0x6EB: "1771 (Tut badge)",
        0x6EC: "1772 (Soviet badge)",
        0x71C: "1820 (Static 61x33)",
        0x71E: "1822 (GUI:Difficulty)",
        0x7A7: "1959 (Static 415x13)",
        0x7A8: "1960 (Static 420x13)",
        0x111: "WM_COMMAND",
        0x4D3: "0x4D3",
        0x4D4: "0x4D4",
        0x4D5: "0x4D5",
        0x4D7: "0x4D7",
        0x4B2: "0x4B2",
    }
    for insn in md.disasm(code, 0x0052EC00):
        for k, lbl in ids.items():
            hexk = f"0x{k:x}"
            if hexk in insn.op_str:
                print(f"  0x{insn.address:08X}: {insn.mnemonic} {insn.op_str}  [{lbl}]")

    # 4. Check ALL 56 SetWindowLongA (IAT 0x007E1470) call sites for GWL_ID (-12 = 0xfffffff4)
    text = [s for s in pe.sections if s["name"] == ".text"][0]
    t_raw, t_va, t_size = text["raw_ptr"], text["va"], text["vsize"]
    t_bytes = pe.raw[t_raw:t_raw + t_size]
    pat_swl = struct.pack("<I", 0x007E1470)
    print("\n=== Checking all SetWindowLongA (0x7E1470) call contexts for GWL_ID (-12) ===")
    idx = 0
    swl_hits = 0
    gwl_id_hits = 0
    while True:
        pos = t_bytes.find(pat_swl, idx)
        if pos < 0:
            break
        idx = pos + 1
        swl_hits += 1
        win = t_bytes[max(0, pos - 24):pos + 8]
        # look for 6A F4 (push -12) or 68 F4 FF FF FF
        insns = list(md.disasm(win, t_va + max(0, pos - 24)))
        ctx = " ; ".join(f"{x.mnemonic} {x.op_str}" for x in insns[-6:])
        if "-0xc" in ctx or "fffffff4" in ctx:
            gwl_id_hits += 1
            print(f"  GWL_ID CANDIDATE at 0x{t_va + pos:08X}: {ctx}")
    print(f"Total SetWindowLongA IAT refs={swl_hits}, GWL_ID(-12) candidates={gwl_id_hits}")

    # 5. Check xyr.dll in .detour and string scan in .rdata/.data for dialog externalization / ddraw
    print("\n=== Checking xyr.dll / .detour details ===")
    for s in pe.sections:
        if s["name"] == ".detour":
            det = pe.raw[s["raw_ptr"]:s["raw_ptr"] + s["vsize"]]
            # extract ascii strings >= 4 chars
            cur = []
            for i, b in enumerate(det):
                if 32 <= b < 127:
                    cur.append(chr(b))
                else:
                    if len(cur) >= 4:
                        print(f"  .detour+0x{i-len(cur):04X} (VA 0x{s['va']+i-len(cur):08X}): {''.join(cur)}")
                    cur = []

    print("\n=== String scan in .rdata (0x7E1000..0x811074) and .data (0x812000..0x87E000) ===")
    keywords = [b"dialog", b"Dialog", b"DIALOG", b".dlg", b".DLG", b"template", b"Template",
                b"1770", b"1771", b"1772", b"Campaign", b"CAMPAIGN", b"ddraw", b"DDRAW", b"ControlID", b"CtrlID"]
    for sname in (".rdata", ".data"):
        sec = [s for s in pe.sections if s["name"] == sname][0]
        sb = pe.raw[sec["raw_ptr"]:sec["raw_ptr"] + min(sec["vsize"], sec["raw_size"])]
        print(f"  Section {sname}: VA=0x{sec['va']:08X}, scanned={len(sb)} B")
        for kw in keywords:
            pos = 0
            found = []
            while True:
                p = sb.find(kw, pos)
                if p < 0:
                    break
                pos = p + 1
                # extract surrounding printable string
                l = p
                while l > 0 and 32 <= sb[l - 1] < 127:
                    l -= 1
                r = p + len(kw)
                while r < len(sb) and 32 <= sb[r] < 127:
                    r += 1
                s_str = sb[l:r].decode("ascii", "replace")
                found.append((sec["va"] + l, s_str[:100]))
            if found:
                print(f"    kw={kw.decode()!r}: {len(found)} hits -> {found[:10]}")

if __name__ == "__main__":
    main()
