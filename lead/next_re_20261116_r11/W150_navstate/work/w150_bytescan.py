#!/usr/bin/env python3
"""W150: independent RAW BYTE scan for absolute memory writes to a watchlist of VAs.

No capstone, no Ghidra.  Pure opcode-byte patterns, so this is evidence the Ghidra
reference model cannot fake (and vice versa: it can produce false positives when a
6-byte pattern happens to straddle two instructions, which is why every hit is also
cross-checked against the Ghidra reference list in w150_sweep.log).

Patterns (x86-32, absolute [disp32] forms):
   C7 05 <a32> <imm32>        mov  dword ptr [a], imm32
   A3 <a32>                   mov  [a], eax
   89 <modrm 05/0D/15/1D/25/2D/35/3D> <a32>   mov  [a], r32
   88 <... 05-reg family>     mov  [a], r8      (byte stores)
   66 C7 05 <a32> <imm16>     mov  word ptr [a], imm16
   C6 05 <a32> <imm8>         mov  byte ptr [a], imm8
   FF 05 <a32>                inc  dword ptr [a]
   FF 0D <a32>                dec  dword ptr [a]
   F7 /5 ..                   (skipped, ambiguous)
Also records PLAIN IMMEDIATE APPEARANCES of the 4-byte address (read-side hint,
   used only to bound how many places *mention* the address).
"""
import struct
import sys
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

WATCH = {
    0x00A8B238: "mode_selector_0_5",
    0x00A8B230: "game_logic_singleton_ptr",
    0x00A83D48: "skip_frame_flag",
    0x00A8D5F8: "option_flags_attract",
    0x00A8ED84: "logic_frame_counter",
    0x00A8ED80: "focus_flag",
    0x00A8E9A0: "G_INGAME_candidate",
    0x00A8EDD8: "exit_state",
    0x00AA0430: "pump_counter",
    0x00B73550: "hwnd",
    0x00B07784: "target_frame",
    0x00B04880: "mpdebug_flag",
}

# modrm second byte -> register name, for 89/88 /r with mod=00 rm=101
MODRM_RM5 = {
    0x05: "eax", 0x0D: "ecx", 0x15: "edx", 0x1D: "ebx",
    0x25: "esp", 0x2D: "ebp", 0x35: "esi", 0x3D: "edi",
}


def main():
    pe = pefile.PE(EXE, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    text = None
    for s in pe.sections:
        nm = s.Name.rstrip(b"\x00").decode("latin1")
        if nm == ".text":
            text = s
    if text is None:
        print("no .text")
        return 1
    va_lo = base + text.VirtualAddress
    raw = text.get_data()
    print(f"# EXE {EXE}")
    print(f"# imageBase=0x{base:08x} .text va=0x{va_lo:08x} rawlen=0x{len(raw):x} vsize=0x{text.Misc_VirtualSize:x}")
    print(f"# watch entries = {len(WATCH)}")

    hits = []
    for tgt, label in WATCH.items():
        a32 = struct.pack("<I", tgt)
        n_mention = 0
        i = raw.find(a32)
        while i >= 0:
            n_mention += 1
            i = raw.find(a32, i + 1)
        print(f"## {tgt:08x} {label}: 4-byte immediate appears {n_mention} times in .text")

        for i in range(len(raw) - 6):
            if raw[i:i + 2] == b"\xC7\x05" and raw[i + 2:i + 6] == a32:
                imm = struct.unpack("<I", raw[i + 6:i + 10])[0] if i + 10 <= len(raw) else None
                hits.append((tgt, label, va_lo + i, 10, "mov dword [a],imm32",
                             f"imm=0x{imm:x}" if imm is not None else "trunc"))
            elif raw[i] == 0xA3 and raw[i + 1:i + 5] == a32:
                hits.append((tgt, label, va_lo + i, 5, "mov [a],eax", ""))
            elif raw[i] == 0x89 and raw[i + 1] in MODRM_RM5 and raw[i + 2:i + 6] == a32:
                hits.append((tgt, label, va_lo + i, 6,
                             f"mov [a],{MODRM_RM5[raw[i + 1]]}", ""))
            elif raw[i] == 0x88 and raw[i + 1] in MODRM_RM5 and raw[i + 2:i + 6] == a32:
                hits.append((tgt, label, va_lo + i, 6,
                             f"mov byte [a],{MODRM_RM5[raw[i + 1]][:2]}l", ""))
            elif raw[i:i + 3] == b"\x66\xC7\x05" and raw[i + 3:i + 7] == a32:
                imm = struct.unpack("<H", raw[i + 7:i + 9])[0] if i + 9 <= len(raw) else None
                hits.append((tgt, label, va_lo + i, 9, "mov word [a],imm16",
                             f"imm=0x{imm:x}" if imm is not None else "trunc"))
            elif raw[i:i + 2] == b"\xC6\x05" and raw[i + 2:i + 6] == a32:
                imm = raw[i + 6] if i + 6 < len(raw) else None
                hits.append((tgt, label, va_lo + i, 7, "mov byte [a],imm8",
                             f"imm=0x{imm:x}" if imm is not None else "trunc"))
            elif raw[i:i + 2] == b"\xFF\x05" and raw[i + 2:i + 6] == a32:
                hits.append((tgt, label, va_lo + i, 6, "inc dword [a]", ""))
            elif raw[i:i + 2] == b"\xFF\x0D" and raw[i + 2:i + 6] == a32:
                hits.append((tgt, label, va_lo + i, 6, "dec dword [a]", ""))

    print("\n# W|target|label|site_va|len|form|extra")
    hits.sort(key=lambda h: (h[0], h[2]))
    for tgt, label, va, ln, form, extra in hits:
        print(f"W|{tgt:08x}|{label}|{va:08x}|{ln}|{form}|{extra}")

    print("\n# per-target write-site counts")
    from collections import Counter
    c = Counter(h[0] for h in hits)
    for tgt, label in WATCH.items():
        print(f"C|{tgt:08x}|{label}|{c.get(tgt,0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
