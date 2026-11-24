"""Find static constructors / writers for selected BSS globals by raw byte pattern (non-atlas channel)."""
import pefile, struct, os
R=r"D:\Project\ra2-campaign-forge"
BIN=os.path.join(R,'ra2youli','gamemd.exe')
EV=os.path.join(R,'lead','next_re_20261116_r12','W160_aidispatch','EVIDENCE')
pe=pefile.PE(BIN,fast_load=True)
ts=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
base=0x400000+ts.VirtualAddress
data=open(BIN,'rb').read(); blob=data[ts.PointerToRawData:ts.PointerToRawData+ts.SizeOfRawData]
targets={
'0x87F778':0x87F778,'0xA83E04':0xA83E04,'0xA83E10':0xA83E10,
'0xA83E34':0xA83E34,'0xA83E40':0xA83E40,'0x887324':0x887324,
'0x8B40CC':0x8B40CC,'0x8B40D8':0x8B40D8,
}
# patterns: mov [imm32],imm32 (C7 05), mov [imm32],reg (89 /r), mov reg,[imm32] (A1 /8B 0D), lea reg,[imm32]
pats=[('C705',bytes.fromhex('c705')),('A1',bytes.fromhex('a1')),('8B0D',bytes.fromhex('8b0d'))]
import re
out=[]
for name,va in targets.items():
    needle=struct.pack('<I',va)
    hits=[]
    for i in range(len(blob)-4):
        if blob[i:i+4]!=needle: continue
        # preceding opcode window
        pre=blob[max(0,i-4):i]
        hits.append((base+i, pre.hex(), blob[i:i+16].hex()))
    out.append((name,va,hits))
    print(f'\n{name} ({len(hits)} raw occurrences in .text):')
    for h in hits: print(f'  {h[0]:08X} pre={h[1]} bytes={h[2]}')
with open(os.path.join(EV,'W160_bss_writer_scan.txt'),'w',encoding='utf-8') as f:
    for name,va,hits in out:
        f.write(f'{name} {len(hits)}\n')
        for h in hits: f.write(f'  {h[0]:08X} pre={h[1]} bytes={h[2]}\n')
