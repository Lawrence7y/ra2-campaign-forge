#!/usr/bin/env python3
# S20-DIRECT full .text scanner. Read-only on target exe.
# Writes only under S20_DIRECT/EVIDENCE and S20_DIRECT/work.
import sys, os, json, struct, hashlib
import pefile, capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
OUT = os.path.join(ROOT, "lead", "next_re_20261117_r14", "S20_DIRECT")
EV  = os.path.join(OUT, "EVIDENCE")
WK  = os.path.join(OUT, "work")
os.makedirs(EV, exist_ok=True); os.makedirs(WK, exist_ok=True)

SHA_EXPECTED = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

def main():
    data = open(EXE, "rb").read()
    sha = hashlib.sha256(data).hexdigest().upper()
    assert sha == SHA_EXPECTED, f"EXE sha mismatch: {sha}"
    pe = pefile.PE(EXE, fast_load=True)
    IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
    sec = None
    for s in pe.sections:
        if s.Name.rstrip(b"\x00").decode(errors="replace") == ".text":
            sec = s; break
    assert sec is not None
    va = IMAGE_BASE + sec.VirtualAddress
    raw = sec.PointerToRawData
    vsize = sec.Misc_VirtualSize
    rsize = sec.SizeOfRawData
    code = data[raw:raw+rsize]
    print(f"PE ImageBase=0x{IMAGE_BASE:X} .text VA=0x{va:X} VSize=0x{vsize:X} RawSize=0x{rsize:X}")

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True

    n_insn = 0
    n_e8_bytes = 0          # raw 0xE8 bytes in .text
    n_e8_boundary = 0       # E8 instructions at instruction boundary (capstone)
    n_calls_true = 0        # insn.id == X86_INS_CALL and opcode E8 (rel32)
    n_e8_other = 0          # E8 at boundary but not a rel32 call (data prefix etc)
    boundary = {}           # addr -> size (for all decoded insns)
    call_sites = []         # dicts: site, size, target, rel32
    fwd_insns = []          # small forward-decoded stream for 19 self-test

    offset = 0
    while offset < len(code):
        addr = va + offset
        insns = list(md.disasm(code[offset:], addr, count=1))
        if not insns:
            # skipdata should always yield something; guard
            ins = next(md.disasm(code[offset:offset+1], addr), None)
            if ins is None:
                offset += 1; continue
            size = ins.size
        else:
            ins = insns[0]
            size = ins.size
        b = code[offset:offset+size]
        n_insn += 1
        boundary[addr] = size
        if b[0] == 0xE8:
            n_e8_boundary += 1
            if len(b) >= 5 and ins.id == capstone.x86.X86_INS_CALL and len(ins.operands)==1 and ins.operands[0].type==capstone.x86.X86_OP_IMM:
                rel32 = struct.unpack('<i', b[1:5])[0]
                target = (addr + 5 + rel32) & 0xFFFFFFFF
                call_sites.append((addr, size, target, rel32))
                n_calls_true += 1
            else:
                n_e8_other += 1
        offset += size

    # raw E8 byte count
    n_e8_bytes = code.count(b"\xE8")
    covered = offset
    pct = 100.0 * covered / len(code) if len(code) else 0.0
    print(f"scan: instructions={n_insn} covered_bytes={covered}/{len(code)} ({pct:.4f}%)")
    print(f"E8 raw_bytes={n_e8_bytes} E8_at_boundary={n_e8_boundary} true_rel32_calls={n_calls_true} E8_other={n_e8_other}")
    # self-test 19: find any insn with mem operand, verify op.index attribute semantics
    idx19 = "n/a"
    for a in range(va, va+min(len(code), 0x2000)):
        pass
    # do a dedicated small disasm for 19
    probe = list(md.disasm(code[:0x4000], va))
    op19 = None
    for ins in probe:
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                op19 = op
                break
        if op19: break
    if op19:
        idx19 = f"mem.index={op19.mem.index!r} (int expected 0 for no index), has_attr_op_index={hasattr(op19,'index')}"
    print("19-self-test:", idx19)

    # Save full call-site index TSv (large ~68k rows fine)
    with open(os.path.join(WK,"all_direct_call_sites.tsv"),"w",encoding="utf-8") as f:
        f.write("site\tsize\ttarget\trel32\n")
        for a,s,t,r in call_sites:
            f.write(f"{a:08X}\t{s}\t{t:08X}\t{r}\n")
    # Save scan stats
    stats = dict(sha=sha, image_base=IMAGE_BASE, text_va=va, text_vsize=vsize, text_rawsize=rsize,
                 instructions=n_insn, covered_bytes=covered, text_bytes=len(code), coverage_pct=pct,
                 e8_raw_bytes=n_e8_bytes, e8_at_boundary=n_e8_boundary,
                 true_rel32_calls=n_calls_true, e8_other=n_e8_other, idx19=idx19)
    json.dump(stats, open(os.path.join(EV,"scan_stats.json"),"w",encoding="utf-8"), indent=2)
    print("wrote", os.path.join(EV,"scan_stats.json"))

if __name__ == "__main__":
    main()
