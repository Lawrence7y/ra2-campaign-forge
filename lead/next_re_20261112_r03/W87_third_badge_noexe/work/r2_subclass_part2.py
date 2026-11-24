from pathlib import Path
import capstone
from pe_iat_rsrc import MiniPE, GAMEMD
from r2_r3_r4_deep import build_iat_map, disasm_range

WORK = Path(__file__).resolve().parent
EVIDENCE = WORK.parent / "EVIDENCE"


def main():
    pe = MiniPE(GAMEMD.read_bytes())
    iat_map = build_iat_map(pe)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    ranges = [
        (0x0060FC80, 0x0060FE95, "0x60F9A0 class switch tail (before 0x60FE90)"),
        (0x00610F10, 0x00611200, "0x610CA0 Subclass WndProc continuation"),
        (0x00612A60, 0x00612CA0, "Subclass proc 0x612A60 (Static/default?)"),
        (0x006163A0, 0x006165A0, "Subclass proc 0x6163A0 (Button? cl==3)"),
        (0x00615457, 0x00615560, "0x615457 (msg 0x4D4 / 0x497)"),
        (0x00615F80, 0x00616140, "0x615F8A (msg 0x4D4 handler target)"),
        (0x006040B0, 0x006041B0, "0x6040B0 (before 0x6041B0)"),
        (0x0052DF65, 0x0052E0A0, "Campaign_Menu_Dialog_Entry after Dialog_Create_Helper"),
        (0x00471350, 0x00471420, "0x471350 (0x4D3/0x4D5/0x4D7 caller)"),
    ]
    lines = []
    for s, e, title in ranges:
        lines += disasm_range(pe, md, iat_map, s, e, title)

    (EVIDENCE / "r2_subclass_part2.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote r2_subclass_part2.txt ({len(lines)} lines)")


if __name__ == "__main__":
    main()
