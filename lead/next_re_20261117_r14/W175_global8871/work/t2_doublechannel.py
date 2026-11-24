"""Double-channel byte scan for +0x1808/+0x172C writes; trace ebx at 0x6677B3."""
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib as A
sys.path.insert(0, os.path.dirname(__file__))
from wbase import BIN, md, disasm, fmt

EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W175_global8871\EVIDENCE"
out=[]
def P(s=""): out.append(str(s))

# byte-channel: mov [esi+disp32], r32  (89 86/9E/A6/AE/B6/BE ...) and mov [esi+disp32],imm32 (C7 86...)
P("=== BYTE-CHANNEL writes to [esi+0x1808] / [esi+0x172C] ===")
t=BIN.text
buf=BIN.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
import struct
for disp,tag in [(0x1808,'1808'),(0x172c,'172C')]:
    db=struct.pack('<I',disp)
    # 89 /r with rm=110 (disp32) -> modrm 0x86 | reg<<3 ; reg 0=eax..3=ebx..7=edi
    for reg in range(8):
        pat=b'\x89'+bytes([0x86|(reg<<3)])+db
        i=0
        while True:
            j=buf.find(pat,i)
            if j<0: break
            P("  +%s mov[r32] reg%d @ %08X"%(tag,reg,t["va"]+j))
            i=j+1
    pat=b'\xc7\x86'+db
    i=0
    while True:
        j=buf.find(pat,i)
        if j<0: break
        imm=struct.unpack('<I',buf[j+6:j+10])[0]
        P("  +%s mov imm32 @ %08X imm=0x%X"%(tag,t["va"]+j,imm))
        i=j+1

# trace ebx at 0x6677B3: find a boundary that disassembles cleanly up to it.
# Use byte-channel call/jmp targets as candidate starts.
P("\n=== ebx trace toward 0x6677B3 ===")
calls,jmps,stats=A.sweep_calls(BIN)
cands=sorted([x for x in list(calls)+list(jmps) if 0x665650<=x<0x6677B3])
P("candidate boundaries: %s"%[hex(x) for x in cands[-8:]])
for st in cands[-6:]:
    ins=disasm(st,0x6677B3-st+8,stop_at=0x6677B3+1)
    if ins and ins[-1].address==0x6677B3:
        P("  clean from %08X:"%st)
        P(fmt([i for i in ins if i.address>=0x667780]))
        break
else:
    P("  no clean boundary reached target; raw bytes show 89 9E (mov [esi+0x1808], ebx)")

with open(EVID+r"\t2_doublechannel.txt","w",encoding="utf-8") as f: f.write("\n".join(out)+"\n")
print("\n".join(out[:60]))
