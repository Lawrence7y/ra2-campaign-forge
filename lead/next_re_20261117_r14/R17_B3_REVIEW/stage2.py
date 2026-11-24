
import json, os, sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_B3_REVIEW")
import importlib.util
spec = importlib.util.spec_from_file_location("w", r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_B3_REVIEW\work.py")
# avoid re-running prints: re-declare minimal here instead of importing
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, x86_const
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_B3_REVIEW"
def u16(b,o): return int.from_bytes(b[o:o+2],'little')
def u32(b,o): return int.from_bytes(b[o:o+4],'little')
data = open(EXE,'rb').read()
pe = u32(data,0x3C); opt = pe+24; IMGB=u32(data,opt+28); nsec=u16(data,pe+6); optsz=u16(data,pe+20)
SECS=[]
for i in range(nsec):
    o=opt+optsz+i*40
    SECS.append(dict(name=data[o:o+8].rstrip(b'\0').decode('latin1'),va=IMGB+u32(data,o+12),vsz=u32(data,o+8),rsz=u32(data,o+16),raw=u32(data,o+20)))
def rd(va,n):
    for s in SECS:
        if s['raw'] and s['va']<=va<s['va']+s['rsz']:
            off=s['raw']+(va-s['va']); return data[off:off+n]
    return b''
def dword(va):
    b=rd(va,4); return int.from_bytes(b,'little') if len(b)==4 else None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
HOSTS=[(0x43B680,0x43B740),(0x43B740,0x43BCDE),(0x43BCF0,0x43C0D0)]
SLOTS={0x7E3E90,0x7E3E98,0x7E3EA0,0x7E3EBC}
lines=[]
sites=[]
for host,end in HOSTS:
    blk=rd(host,end-host)
    ins=list(md.disasm(blk,host))
    # assert full coverage to end
    cov = (ins[-1].address+ins[-1].size) if ins else host
    lines.append("# ---- host %#x fn_end %#x bytes %d insns %d coverage_end %#x %s" % (host,end,len(blk),len(ins),cov, "FULL" if cov==end else "GAP"))
    if cov!=end:
        lines.append("# TAIL GAP: %s" % rd(cov,end-cov).hex())
    for i in ins:
        mark=''
        ops=''
        if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==x86_const.X86_OP_MEM and i.operands[1].type==x86_const.X86_OP_IMM:
            imm=i.operands[1].imm & 0xFFFFFFFF
            if imm in SLOTS:
                mark='  <<< SITE'
                sites.append(dict(host=host,fn_end=end,addr=i.address,size=i.size,insn=i.mnemonic+' '+i.op_str,imm=imm,
                                  mem_base=i.reg_name(i.operands[0].mem.base) if i.operands[0].mem.base else '',
                                  mem_disp=i.operands[0].mem.disp))
        lines.append("%#010x  %-24s %s %s%s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str, mark))
open(os.path.join(OUT,'disasm_anchored.txt'),'w',encoding='utf8').write("\n".join(lines))
json.dump(sites, open(os.path.join(OUT,'stage2_sites.json'),'w'), indent=1)
print("sites found:", len(sites))
for s in sites: print("%#x host %#x end %#x %s base=%s disp=%d" % (s['addr'],s['host'],s['fn_end'],s['insn'],s['mem_base'],s['mem_disp']))
print("total insn lines:", len(lines))
