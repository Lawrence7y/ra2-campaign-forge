"""S8: who else writes the placement latch `[obj+0x74]` (byte) and the
`+0x80` / `+0x81` veto flags that gate 0x5F5850?

0x5F5850 (the shared predicate of all three slot-73 dispatchers) is:
    if ([obj+0x81] != 0)                      return 0     ; hard veto
    mode==2 : return ([obj+0x80]==0 && [obj+0x74]!=0) after [vptr+0x134]()
    mode 1/3: if ([obj+0x74]!=0)  return 0    ; already in world -> NO attach
              [obj+0x74]=1 ; [vptr+0x134]()
    mode 0  : if ([obj+0x74]==0)  return 0    ; already out      -> NO detach
              [obj+0x74]=0

=> a byte-store to [obj+0x74] anywhere else is a path that can make the later
   detach (mode 0) a no-op, i.e. the chain is never cleaned.

Run: python s8_latch.py > ..\\EVIDENCE\\s8_latch.log 2>&1
"""
import capstone
import w152_core as C

X = capstone.x86
DISPS = {0x74: "placement latch (+0x74)", 0x80: "veto/flag (+0x80)",
         0x81: "hard veto (+0x81)"}


def main():
    hits = []
    for entry in C.ENTRIES:
        for ins in C.disas_fn(entry):
            if not ins.mnemonic.startswith("mov") or len(ins.operands) < 2:
                continue
            dst = ins.operands[0]
            if dst.type != X.X86_OP_MEM or dst.mem.index != 0:
                continue
            if dst.mem.disp in DISPS and dst.size == 1:
                hits.append((ins.address, entry, dst.mem.disp, C.fmt(ins)))
    print("=== byte-stores to the latch / veto flags: %d ===" % len(hits))
    for a, e, d, txt in sorted(hits):
        print("%s   fn=%s   [%s]" % (txt, C.fn_label(e), DISPS[d]))
    print("")
    print("=== grouped by displacement ===")
    for d, label in sorted(DISPS.items()):
        sel = [h for h in hits if h[2] == d]
        print("disp 0x%02X %-24s stores=%d functions=%d" % (
            d, label, len(sel), len({h[1] for h in sel})))
        for a, e, _, txt in sorted(sel):
            print("      %s  fn=%s" % (txt, C.fn_label(e)))


main()
