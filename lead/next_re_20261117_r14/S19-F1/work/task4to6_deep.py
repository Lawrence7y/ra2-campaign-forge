"""S19 tasks 3-6: EVA QueueVoice internals, VQA callers/entry, volume storage."""
import os, struct
import common as C

b = C.Bin(); at = C.Atlas(); E = os.path.join(C.CARD, "EVIDENCE")
calls, jmps, st = C.sweep_calls(b)
im = C.sweep_imm(b)

# EVA QueueVoice + enqueue decision full dumps
for va, sz, nm in [(0x752700, 0x200, "EVA_QueueVoice"),
                   (0x752480, 0x2c0, "EVA_enqueue")]:
    C.dump(b, va, sz, os.path.join(E, "task4_%s_%08X.txt" % (nm, va)))

# VQA callers full dumps
for va in (0x5C0080, 0x5C02F0):
    e, r = at.containing(va)
    sz = r.get("_size") if r else 0x300
    try: sz = int(sz)
    except Exception: sz = 0x300
    C.dump(b, va, min(sz + 16, 0x1200), os.path.join(E, "task5_VQA_caller_%08X.txt" % va))
    print("VQA caller %08X fn=%s size=%s" % (va, ("%08X" % e) if e else "GAP", sz))

# find loops containing call 0x759C30: backwards jcc/jmp from call site
print("\n=== back-edges around VQA Advance_Frame call sites ===")
for site in calls.get(0x759C30, []):
    print(" call site %08X" % site)
    for insn in C.disasm(b, site - 0x120, 0x140):
        if insn.mnemonic in ("jmp", "je", "jne", "jl", "jge", "jb", "jbe", "ja", "jae") and \
           insn.op_str.startswith("0x") and int(insn.op_str, 16) <= site:
            print("   back-edge %08X %s %s" % (insn.address, insn.mnemonic, insn.op_str))

# byte scan for VQA/volume string VAs
print("\n=== byte refs to VQA / volume string VAs ===")
data = b.pe.__data__
for va, nm in [(0x83D88B, "%s.VQA"), (0x83E3E2, "SCORE.VQA"),
               (0x832FB5, "SoundVolume=%f fmt"), (0x832FC9, "VoiceVolume=%f fmt"),
               (0x832FA1, "ScoreVolume=%f fmt"), (0x81B1CD, "FinalMovie")]:
    pat = struct.pack("<I", va)
    hits = []; i = 0
    while True:
        i = data.find(pat, i)
        if i < 0: break
        where = "?"
        for s in b.sections:
            if s["raw"] <= i < s["raw"] + s["rawsize"]:
                where = "%08X" % (s["va"] + i - s["raw"]); break
        hits.append(where); i += 1
    print("  %08X %-22s hits=%d %s" % (va, nm, len(hits), hits[:12]))

# imm xrefs for volume format strings
print("\n=== imm xrefs for volume format strings ===")
for va in (0x832FB5, 0x832FC9, 0x832FA1, 0x81B1CD):
    refs = im.get(va, [])
    print("  %08X refs=%d" % (va, len(refs)))
    for r in refs[:8]:
        s = int(r["site"], 16); e, rec = at.containing(s)
        print("     %s fn=%s %s" % (r["site"], ("%08X" % e) if e else "GAP", r["insn"]))
