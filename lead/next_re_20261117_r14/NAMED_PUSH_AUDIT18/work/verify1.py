"""Verify callee contracts, primary vtable slot0, RTTI details, install-site host classification."""
from re_lib import *

out=[]
def P(s=''):
    out.append(str(s)); print(s)

P('=== CALLEE CONTRACTS / VT PRIMARY / RTTI / INSTALL HOSTS ===')
P()

# --- 1. Write wrapper 0x00410320 and read wrapper 0x00410380 ---
for name,va in [('WRITE 00410320',0x00410320),('READ 00410380',0x00410380)]:
    P('## %s body:'%name)
    for a,m,o,b,t in disasm(va, 0x80):
        P('  '+t)
        if m.startswith('ret'): break
    P()

# --- 2. Primary vtable check: slot0 == 00410260 for each primary vt ---
prim = {
 0x006E3E30:0x007F443C, 0x006E57A0:0x007F44E0, 0x006E6470:0x007F45C4,
 0x0071F930:0x007F5578, 0x0071FA80:0x007F5578,
 0x00726860:0x007F5858, 0x007268D0:0x007F5858, 0x00726950:0x007F5858,
 0x00727BF0:0x007F5904, 0x00727C80:0x007F5904,
}
P('=== PRIMARY VTABLE slot0 check (slot0==00410260 => QueryInterface primary) ===')
for e,vt in prim.items():
    slots=[u32(vt+4*i) for i in range(10)]
    col=u32(vt-4); ptd=u32(col+0xC); pchd=u32(col+0x10)
    P('%08X vt=%08X COL=%08X sig=%d pTD=%08X pCHD=%08X'%(e,vt,col,u32(col),ptd,pchd))
    P('   slot0..9 = '+' '.join('%08X'%s for s in slots))
    P('   TD+8 magic=%s inline="%s" u32(TD+8)=%08X mapped_as_ptr=%s'%(
        bytes_at(ptd+8,4).hex(), cstr(ptd+8), u32(ptd+8), mapped(u32(ptd+8),1)))
P()

# --- 3. Find implementations: verify -1 sentinel (or eax,0xffffffff) ---
P('=== FIND implementations -1 sentinel check ===')
for fva in [0x004E0550,0x004E0440,0x0071FE30,0x0071FD20,0x004EA650,0x004EA540]:
    P('Find %08X:'%fva)
    ins=disasm(fva,0x80)
    for a,m,o,b,t in ins:
        P('  '+t)
        if m.startswith('ret'): break
    P()

open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT18\work\verify1.txt','w',encoding='utf-8').write('\n'.join(out))
print('WROTE verify1.txt')
