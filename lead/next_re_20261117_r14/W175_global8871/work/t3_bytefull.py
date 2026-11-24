"""Verify 0x777D7E boundary; comprehensive byte-channel write scan for both globals."""
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

P("=== raw bytes @0x777D7E ===")
P("  "+" ".join("%02X"%b for b in BIN.read(0x777D60,0x40)))
P("disasm starting exactly at 0x777D7E:")
P(fmt(disasm(0x777D7E,0x10)))

# find function entries in 0x777000..0x778000 via call/jmp targets (byte channel)
calls,jmps,stats=A.sweep_calls(BIN)
ents=sorted(set([t for t in list(calls)+list(jmps) if 0x777000<=t<0x778000]))
P("\ncall/jmp targets in 0x777000..0x778000: %s"%[hex(x) for x in ents])

# comprehensive byte-channel scan across all sections
P("\n=== comprehensive BYTE-CHANNEL write patterns ===")
patterns={
 # A8ED6B byte writes: 88 /r with mod=00 rm=101 (disp32), reg varies
 'A8_88_1D_bl':b'\x88\x1d\x6b\xed\xa8\x00',
 'A8_88_05_al':b'\x88\x05\x6b\xed\xa8\x00',
 'A8_88_0D_cl':b'\x88\x0d\x6b\xed\xa8\x00',
 'A8_88_15_dl':b'\x88\x15\x6b\xed\xa8\x00',
 'A8_88_35_si':b'\x88\x35\x6b\xed\xa8\x00',
 'A8_88_3D_di':b'\x88\x3d\x6b\xed\xa8\x00',
 'A8_A2_moffs_al':b'\xa2\x6b\xed\xa8\x00',
 'A8_C6_05_imm':b'\xc6\x05\x6b\xed\xa8\x00',
 # B73550 dword writes
 'B7_89_1D_ebx':b'\x89\x1d\x50\x35\xb7\x00',
 'B7_89_05_eax':b'\x89\x05\x50\x35\xb7\x00',
 'B7_89_0D_ecx':b'\x89\x0d\x50\x35\xb7\x00',
 'B7_89_15_edx':b'\x89\x15\x50\x35\xb7\x00',
 'B7_89_35_esi':b'\x89\x35\x50\x35\xb7\x00',
 'B7_89_3D_edi':b'\x89\x3d\x50\x35\xb7\x00',
 'B7_A3_moffs_eax':b'\xa3\x50\x35\xb7\x00',
 'B7_C7_05_imm':b'\xc7\x05\x50\x35\xb7\x00',
}
allhits=[]
for s in BIN.sections:
    buf=BIN.pe.__data__[s["raw"]:s["raw"]+s["rawsize"]]
    for nm,pat in patterns.items():
        i=0
        while True:
            j=buf.find(pat,i)
            if j<0: break
            va=s["va"]+j
            extra=pat[-1] if nm.endswith('imm') else None
            allhits.append((va,nm,s["name"]))
            P("  %-18s %08X [%s]"%(nm,va,s["name"]))
            i=j+1
P("\ntotal byte-channel write-pattern hits: %d"%len(allhits))

with open(EVID+r"\t3_bytechannel_full.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("\n".join(out[:50]))
