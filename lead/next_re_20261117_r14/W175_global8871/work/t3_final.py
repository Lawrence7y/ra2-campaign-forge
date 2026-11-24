"""Final combined: verify write addresses, trace values, confirm +0x172C key, byte-channel cross-check."""
import sys, os, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

# --- byte-channel independent scan for writes to the globals ---
P("=== BYTE-CHANNEL: patterns writing absolute [0xA8ED6B] / [0xB73550] ===")
# A8ED6B little-endian = 6B ED A8 00 ; B73550 = 50 35 B7 00
for s in BIN.sections:
    buf=BIN.pe.__data__[s["raw"]:s["raw"]+s["rawsize"]]
    pats={
      'A8_88_1D(ebx)':b'\x88\x1d\x6b\xed\xa8\x00',
      'A8_88_05(eax/al)':b'\x88\x05\x6b\xed\xa8\x00',
      'A8_88_0D(ecx/cl)':b'\x88\x0d\x6b\xed\xa8\x00',
      'A8_88_15(edx/dl)':b'\x88\x15\x6b\xed\xa8\x00',
      'A8_C6_05(imm)':b'\xc6\x05\x6b\xed\xa8\x00',
      'B7_89_1D(ebx)':b'\x89\x1d\x50\x35\xb7\x00',
      'B7_89_05(eax)':b'\x89\x05\x50\x35\xb7\x00',
      'B7_89_0D(ecx)':b'\x89\x0d\x50\x35\xb7\x00',
      'B7_89_15(edx)':b'\x89\x15\x50\x35\xb7\x00',
    }
    for nm,pat in pats.items():
        i=0
        while True:
            j=buf.find(pat,i)
            if j<0: break
            va=s["va"]+j
            P("  %-18s %08X  %s"%(nm,va," ".join("%02X"%b for b in buf[j:j+8])))
            i=j+1

# --- verify disputed addresses ---
P("\n=== raw byte verification ===")
for va in [0x77780A,0x77780E,0x777CD6,0x52F63E,0x5A922F,0x5A95A1]:
    P("  %08X: %s"%(va," ".join("%02X"%b for b in BIN.read(va,8))))

# --- trace values at write sites (context) ---
sites=[(0x52F63E,"A8ED6B"),(0x5A922F,"A8ED6B"),(0x5A95A1,"A8ED6B"),
       (0x77780E,"B73550"),(0x777CD6,"B73550")]
P("\n=== context around each write site (value trace) ===")
for va,nm in sites:
    start=va-0x30
    P("\n  --- %s write @%08X ---"%(nm,va))
    P(fmt(disasm(start,0x40,stop_at=va+8)))

# --- confirm +0x172C key association from proper-boundary disasm ---
P("\n=== +0x172C write context (0x66BA90..0x66BAB0) from proper boundary ===")
P(fmt(disasm(0x66BA88,0x30)))

with open(EVID+r"\t3_final_verify.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("written; lines=%d"%len(out))
