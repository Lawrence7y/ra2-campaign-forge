import struct
from pathlib import Path
import capstone
from pe_iat_rsrc import MiniPE

WORK = Path(__file__).resolve().parent
GAMEMD = WORK / "gamemd.exe"
DDRAW = WORK / "ddraw.dll"

def disasm_range(pe: MiniPE, start_va: int, end_va: int, md: capstone.Cs, title: str):
    foff = pe.va_to_foff(start_va)
    size = end_va - start_va
    code = pe.raw[foff:foff + size]
    print(f"\n=== {title}: 0x{start_va:08X}..0x{end_va:08X} (foff 0x{foff:06X}, {size} B) ===")
    for insn in md.disasm(code, start_va):
        if insn.address >= end_va:
            break
        ins_foff = pe.va_to_foff(insn.address)
        print(f"0x{insn.address:08X} (0x{ins_foff:06X}) {insn.bytes.hex():20s} {insn.mnemonic:8s} {insn.op_str}")

def main():
    pe = MiniPE(GAMEMD.read_bytes())
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    disasm_range(pe, 0x004A3B40, 0x004A3B76, md, "Load_Resource_Helper (0x4A3B40)")
    disasm_range(pe, 0x00622650, 0x00622720, md, "Dialog_Create_Helper (0x622650)")
    disasm_range(pe, 0x00622720, 0x00622800, md, "Dialog_Destroy_Helper (0x622720)")
    disasm_range(pe, 0x00622800, 0x00622920, md, "Dialog_Show_Or_Init (0x622800)")
    disasm_range(pe, 0x00623120, 0x00623200, md, "Dialog_Pump_Helper (0x623120)")
    disasm_range(pe, 0x0052D080, 0x0052D150, md, "Other DialogBoxParamA caller (0x52D080)")
    disasm_range(pe, 0x004C84D0, 0x004C85D0, md, "Other DialogBox caller (0x4C84D0)")

    d_pe = MiniPE(DDRAW.read_bytes())
    print("\n=== ddraw.dll Exports ===")
    for ordv, frva, name, fwd in d_pe.parse_exports():
        print(f"  ord={ordv:3d} RVA=0x{frva:08X} name={name} {('-> ' + fwd) if fwd else ''}")

if __name__ == "__main__":
    main()
