
import os, capstone, pefile
p=r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe'
out=r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S10_K11/EVIDENCE'
pe=pefile.PE(p); ib=pe.OPTIONAL_HEADER.ImageBase
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail=True; md.skipdata=True
def dump(start, end, fn):
    rva=start-ib
    n=end-start
    data=pe.get_data(rva,n)
    lines=[]
    lines.append(f'# target={p}')
    lines.append(f'# imagebase=0x{ib:08X} start=0x{start:08X} end=0x{end:08X} bytes={n}')
    for i in md.disasm(data,start):
        if i.id==0:
            lines.append(f'0x{i.address:08X}  {i.bytes.hex()}  db {i.mnemonic} {i.op_str}'.rstrip())
        else:
            lines.append(f'0x{i.address:08X}  {i.bytes.hex():<24} {i.mnemonic:<8} {i.op_str}'.rstrip())
    open(os.path.join(out,fn),'w',encoding='utf-8').write('\n'.join(lines)+'\n')
    print('wrote', fn, 'lines', len(lines))
dump(0x004DFCB0,0x004DFE00,'disasm_004DFCB0.txt')
dump(0x004DFE00,0x004DFF60,'disasm_004DFE00.txt')
