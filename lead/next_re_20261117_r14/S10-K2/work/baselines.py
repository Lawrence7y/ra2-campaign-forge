"""
S10-K2 baselines (R14 discipline 1): measure判据 baseline BEFORE claiming N/N.
- B8 imm32 C3 count in .text (expect 666 strict / 837 loose per STATUS_BOARD R14)
- ret 0xC count (expect 672 per §969)
- 16B-aligned address baseline in .text (expect 36.5% are sweep starts per §952)
"""
import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\work')
from pehelp import rd, sections, IMAGE_BASE
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
tsec=[s for s in sections() if s[0]=='.text'][0]
nm,vaoff,vsize,rsize,praw=tsec
tlo=IMAGE_BASE+vaoff; thi=IMAGE_BASE+vaoff+min(vsize,rsize)
blob=rd(tlo,thi-tlo)
L=[]
def P(s=''):
    L.append(str(s)); print(s)

P('===== S10-K2 BASELINE MEASUREMENTS (.text, capstone skipdata=True) =====')
P('.text range: %08X..%08X (%d bytes)'%(tlo,thi,thi-tlo))
# strict B8 imm32 C3: B8 <4 imm> C3
strict=sum(1 for i in range(len(blob)-5) if blob[i]==0xB8 and blob[i+5]==0xC3)
# loose B8 imm32 ... (C3 not required at +5): count B8 followed by any 4 bytes where a C3 appears within next 16 (approx)
loose=sum(1 for i in range(len(blob)-4) if blob[i]==0xB8)
P('B8 imm32 C3 (strict, +5==C3): %d  [STATUS_BOARD: 666]'%strict)
P('B8 imm32 anywhere (loose, no C3 req): %d  [STATUS_BOARD: 837]'%loose)
# ret 0xC2 0C 00
retc=sum(1 for i in range(len(blob)-2) if blob[i]==0xC2 and blob[i+1]==0x0C and blob[i+2]==0x00)
P('ret 0xC (C2 0C 00) byte hits: %d  [§969: 672]'%retc)
# 16B aligned baseline: fraction of 16B-aligned addrs that are capstone sweep starts
ins=list(md.disasm(blob,tlo))
starts={x.address for x in ins}
aligned=[a for a in range(tlo,thi,16)]
aligned_starts=sum(1 for a in aligned if a in starts)
P('16B-aligned addresses: %d ; of these are capstone sweep starts: %d (%.1f%%)  [§952: 36.5%%]'%
  (len(aligned),aligned_starts,100.0*aligned_starts/len(aligned)))
P('total .text instructions (skipdata=True): %d'%len(ins))
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\EVIDENCE\baselines.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(L)+'\n')
