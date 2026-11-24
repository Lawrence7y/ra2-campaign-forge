import struct
from pathlib import Path
import capstone
from pe_iat_rsrc import MiniPE

WORK = Path(__file__).resolve().parent
GAMEMD = WORK / "gamemd.exe"
DDRAW = WORK / "ddraw.dll"

def disasm_range(pe: MiniPE, start_va: int, end_va: int, md: capstone.Cs):
    foff = pe.va_to_foff(start_va)
    size = end_va - start_va
    code = pe.raw[foff:foff + size]
    print(f"\n=== Disassembly 0x{start_va:08X}..0x{end_va:08X} (foff 0x{foff:06X}, {size} B) ===")
    for insn in md.disasm(code, start_va):
        if insn.address >= end_va:
            break
        ins_foff = pe.va_to_foff(insn.address)
        print(f"0x{insn.address:08X} (0x{ins_foff:06X}) {insn.bytes.hex():20s} {insn.mnemonic:8s} {insn.op_str}")

def find_imm32_in_text(pe: MiniPE, val: int, label: str, md: capstone.Cs):
    text = [s for s in pe.sections if s["name"] == ".text"][0]
    t_raw = text["raw_ptr"]
    t_va = text["va"]
    t_bytes = pe.raw[t_raw:t_raw + text["vsize"]]
    pat = struct.pack("<I", val)
    print(f"\n=== References to {label} (0x{val:08X}) in .text ===")
    idx = 0
    hits = []
    while True:
        pos = t_bytes.find(pat, idx)
        if pos < 0:
            break
        idx = pos + 1
        va = t_va + pos
        foff = t_raw + pos
        # disasm small window around pos-5..pos+10
        w_start = max(0, pos - 6)
        insns = list(md.disasm(t_bytes[w_start:pos + 12], t_va + w_start))
        matched = [f"0x{x.address:08X}: {x.bytes.hex()} | {x.mnemonic} {x.op_str}" for x in insns if pat in x.bytes]
        print(f"  pos VA=0x{va:08X} (foff 0x{foff:06X}) -> {matched if matched else 'raw'}")
        hits.append(va)
    return hits

def find_calls_to(pe: MiniPE, target_va: int, label: str):
    text = [s for s in pe.sections if s["name"] == ".text"][0]
    t_raw = text["raw_ptr"]
    t_va = text["va"]
    t_bytes = pe.raw[t_raw:t_raw + text["vsize"]]
    print(f"\n=== Direct E8 call / E9 jmp to {label} (0x{target_va:08X}) in .text ===")
    for i in range(len(t_bytes) - 5):
        op = t_bytes[i]
        if op in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", t_bytes, i + 1)[0]
            src_va = t_va + i
            if src_va + 5 + rel == target_va:
                print(f"  VA 0x{src_va:08X} (foff 0x{t_raw + i:06X}): {'call' if op==0xE8 else 'jmp'} 0x{target_va:08X}")

def main():
    raw = GAMEMD.read_bytes()
    pe = MiniPE(raw)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    # 1. Who references 0x0052EC00 (campaign menu WndProc)?
    find_imm32_in_text(pe, 0x0052EC00, "CampaignWndProc", md)

    # 2. Who references 0x00000094 (148) via push imm32 or mov?
    find_imm32_in_text(pe, 0x00000094, "imm32 0x94 (148)", md)

    # 3. Disassemble around 0x0052DEC0..0x0052E0C0 (mentioned in W61 as dialog caller!) and 0x0052D090..0x0052D140 and 0x00622650..0x00622730
    disasm_range(pe, 0x0052DF00, 0x0052E0C0, md)
    disasm_range(pe, 0x0052D080, 0x0052D150, md)
    disasm_range(pe, 0x00622650, 0x00622760, md)
    disasm_range(pe, 0x004C84D0, 0x004C85D0, md)
    disasm_range(pe, 0x004A3B30, 0x004A3BA0, md)

    # 4. Check callers of DialogBoxParamA thunk (0x007C8680), DialogBoxIndirectParamA thunk (0x007C8686), CreateDialogIndirectParamA thunk (0x007C87A0), CreateDialogParamA thunk (0x007C8704)
    for t_va, lbl in [
        (0x007C8680, "thunk DialogBoxParamA"),
        (0x007C8686, "thunk DialogBoxIndirectParamA"),
        (0x007C87A0, "thunk CreateDialogIndirectParamA"),
        (0x007C8704, "thunk CreateDialogParamA"),
        (0x007C8434, "thunk FindResourceA"),
        (0x007C842E, "thunk LoadResource"),
        (0x007C8428, "thunk LockResource"),
        (0x00622650, "Run_Dialog / CreateDialog helper?"),
    ]:
        find_calls_to(pe, t_va, lbl)

    # 5. Also dump ddraw.dll exports cleanly
    d_pe = MiniPE(DDRAW.read_bytes())
    print("\n=== ddraw.dll Exports ===")
    for ordv, frva, name, fwd in d_pe.parse_exports():
        print(f"  ord={ordv:3d} RVA=0x{frva:08X} name={name} {('-> ' + fwd) if fwd else ''}")

if __name__ == "__main__":
    main()
