# S19-F1 independent xref channel (Ghidra). Run as analyzeHeadless -noanalysis -postScript.
from __future__ import print_function

af = currentProgram.getAddressFactory()
rm = currentProgram.getReferenceManager()

TARGETS = [0x750920, 0x7509E0, 0x750E20, 0x406F70, 0x752700,
           0x752480, 0x752760, 0x759C30, 0x407B60, 0x409470,
           0x7C89DA, 0x7209D0, 0x720EA0]

for va in TARGETS:
    try:
        addr = af.getDefaultAddressSpace().getAddress(int(va))
        it = rm.getReferencesTo(addr)
        sites = []
        while it.hasNext():
            sites.append(str(it.next().getFromAddress()))
        print("S19F1_XREF %08X %d" % (va, len(sites)))
        for s in sorted(sites):
            print("S19F1_SITE %08X %s" % (va, s))
    except Exception as e:
        print("S19F1_XREF %08X ERROR %s" % (va, e))
