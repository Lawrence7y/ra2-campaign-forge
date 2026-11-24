from pathlib import Path
import capstone
from pe_iat_rsrc import MiniPE, GAMEMD
from r2_r3_r4_deep import build_iat_map, disasm_range, find_imm_calls_or_refs

WORK = Path(__file__).resolve().parent
EVIDENCE = WORK.parent / "EVIDENCE"


def main():
    pe = MiniPE(GAMEMD.read_bytes())
    iat_map = build_iat_map(pe)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    out = []
    # Find GetClassNameA and DefWindowProcA/CallWindowProcA IAT slots
    target = {"GetClassNameA", "EnumChildWindows", "CallWindowProcA"}
    for dll, _iat_rva, entries in pe.parse_imports():
        for slot_va, _slot_rva, fname in entries:
            if fname in target:
                refs = find_imm_calls_or_refs(pe, md, slot_va)
                out.append(f"=== {dll}!{fname} @ 0x{slot_va:08X} ({len(refs)} refs) ===")
                for sec, va, hx, txt in refs:
                    out.append(f"  [{sec}] 0x{va:08X} {hx:<18} {txt}")
    out.append("")

    # Also find all SetWindowLongA with GWL_WNDPROC (-4 = 0xFFFFFFFC) or around 0x60Fxxx
    swl_refs = find_imm_calls_or_refs(pe, md, 0x007E1470)
    out.append(f"=== SetWindowLongA refs around 0x60xxxx..0x62xxxx ===")
    for sec, va, hx, txt in swl_refs:
        if 0x600000 <= va <= 0x635000:
            out.append(f"  [{sec}] 0x{va:08X} {hx:<18} {txt}")
    out.append("")

    ranges = [
        (0x0060F320, 0x0060F4C0, "EnumChildWindows cb 0x60F320"),
        (0x0060F760, 0x0060F940, "EnumChildWindows cb 0x60F760"),
        (0x0060F9A0, 0x0060FB60, "EnumChildWindows cb 0x60F9A0"),
        (0x0060FE90, 0x0060FF60, "Subclass installer 0x60FE90"),
        (0x00610CA0, 0x00610F20, "Subclass WndProc 0x610CA0"),
        (0x00615420, 0x00615540, "Handler of 0x4D4 / 0x497 around 0x61545E"),
        (0x00471330, 0x00471420, "Handler of 0x4D3/0x4D5/0x4D7/0x4D8 at 0x471330"),
        (0x006041B0, 0x00604260, "Badge ID switch at 0x6041B0 (tooltip/STT?)"),
        (0x00603F00, 0x00603FE0, "ownrdraw tooltip/hit helper 0x603F00"),
    ]
    dis_lines = []
    for s, e, title in ranges:
        dis_lines += disasm_range(pe, md, iat_map, s, e, title)

    (EVIDENCE / "r2_subclass_stdout.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    (EVIDENCE / "r2_subclass_disasm.txt").write_text("\n".join(dis_lines) + "\n", encoding="utf-8")
    print(f"Wrote r2_subclass_stdout.txt ({len(out)} lines) and r2_subclass_disasm.txt ({len(dis_lines)} lines)")


if __name__ == "__main__":
    main()
