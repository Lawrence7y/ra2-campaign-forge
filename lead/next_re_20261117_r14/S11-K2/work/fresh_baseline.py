"""S11-K2 baseline variants: reconcile task-cited §969 numbers with this binary."""
from pehelp import rd, sections, IMAGE_BASE, u32, is_code, disasm
import json
# raw file whole (all sections) and per-section counts of B8 imm32 C3
nm,vo,vs,rs,pr=[s for s in sections() if s[0]=='.text'][0]
text=rd(IMAGE_BASE+vo,rs)
def cnt_b8(blob):
    return sum(1 for i in range(len(blob)-5) if blob[i]==0xB8 and blob[i+5]==0xC3)
print('raw B8 imm32 C3 in .text(raw) =',cnt_b8(text))
whole=open(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe','rb').read()
print('raw B8 imm32 C3 in WHOLE FILE =',cnt_b8(whole))
# ret 0xC2 0C 00 pattern
print('ret 0xC (C2 0C 00) in .text =',sum(1 for i in range(len(text)-2) if text[i]==0xC2 and text[i+1]==0x0C and text[i+2]==0x00))
# 66 B8 imm16 C3 variant
print('66 B8 imm16 C3 in .text =',sum(1 for i in range(len(text)-5) if text[i]==0x66 and text[i+1]==0xB8 and text[i+4]==0xC3))
# how many raw B8..C3 are 16B aligned / 4B aligned
locs=[IMAGE_BASE+vo+i for i in range(len(text)-5) if text[i]==0xB8 and text[i+5]==0xC3]
print('aligned16 =',sum(1 for a in locs if a%16==0),'aligned4 =',sum(1 for a in locs if a%4==0))
