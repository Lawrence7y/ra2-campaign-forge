"""S08-K1 reusable PE + capstone helper (all disasm uses skipdata=True).
Independent implementation: does not import audit_lib.
Run from project root: D:\\Project\\ra2-campaign-forge
"""
import struct, json, os
import pefile
import capstone

EXE = os.path.abspath(r"ra2youli\gamemd.exe")
ATLAS = os.path.abspath(r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")

class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in self.pe.sections:
            nm = s.Name.decode('latin1').rstrip('\x00')
            self.secs.append(dict(name=nm, va=self.ib+s.VirtualAddress,
                vsize=s.Misc_VirtualSize, raw=s.PointerToRawData,
                rawsize=s.SizeOfRawData))
    def sec(self, name):
        for s in self.secs:
            if s['name'] == name:
                return s
        raise KeyError(name)
    def read(self, va, n):
        for s in self.secs:
            if s['va'] <= va and va+n <= s['va']+s['rawsize']:
                off = s['raw']+(va-s['va'])
                return self.pe.__data__[off:off+n]
        raise ValueError('VA %08X+%d out of raw range' % (va, n))
    def u8(self, va): return self.read(va,1)[0]
    def u16(self, va): return struct.unpack('<H', self.read(va,2))[0]
    def u32(self, va): return struct.unpack('<I', self.read(va,4))[0]
    def i32(self, va): return struct.unpack('<i', self.read(va,4))[0]
    def secbuf(self, name):
        s = self.sec(name)
        return self.pe.__data__[s['raw']:s['raw']+s['rawsize']]
    def va2fo(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va']+s['rawsize']:
                return s['raw']+(va-s['va'])
        raise ValueError('no FO for %08X' % va)

def md(skip=True, detail=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = detail
    m.skipdata = skip
    return m

def dis(b, start, max_bytes, stop_at=None):
    """Linear disasm from start with skipdata=True. Returns capstone insn list."""
    m = md(True, True)
    data = b.read(start, max_bytes)
    out=[]
    for ins in m.disasm(data, start):
        out.append(ins)
        if stop_at is not None and ins.address >= stop_at:
            break
    return out

def fmt(ins):
    return '%08X  %-20s %-8s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str)

def dump(b, start, max_bytes, stop_at=None):
    return '\n'.join(fmt(i) for i in dis(b,start,max_bytes,stop_at))

def load_atlas(path=ATLAS):
    rows=[]
    with open(path, encoding='utf-8', errors='replace') as f:
        hdr=f.readline().rstrip('\n').split('\t')
        for line in f:
            p=line.rstrip('\n').split('\t')
            if len(p)<2: continue
            try:
                e=int(p[0],16); sz=int(p[1])
            except Exception: continue
            rows.append(dict(entry=e,size=sz,n_instr=int(p[2]) if p[2] else 0,
                n_callers=int(p[3]) if p[3] else 0,
                n_callees=int(p[4]) if p[4] else 0))
    rows.sort(key=lambda r:r['entry'])
    return rows

def atlas_find(rows, va):
    """Channel A: find atlas function whose [entry, entry+size) contains va."""
    lo,hi=0,len(rows)-1; best=None
    while lo<=hi:
        mid=(lo+hi)//2; r=rows[mid]
        if r['entry']<=va: best=r; lo=mid+1
        else: hi=mid-1
    if best and best['entry']<=va<best['entry']+best['size']:
        return best
    return None

def sweep_text(b):
    """Channel B: full .text linear sweep. Collect call/jmp rel32 and imm32 operand refs."""
    m=md(True,True); t=b.sec('.text'); data=b.secbuf('.text')
    calls={}; jmps={}; imm32={}; n=0; nskip=0
    for ins in m.disasm(data, t['va']):
        if ins.id==0:
            nskip+=ins.size; continue
        n+=1
        if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
            calls.setdefault(int(ins.op_str,16),[]).append(ins.address)
        elif ins.mnemonic=='jmp' and ins.op_str.startswith('0x'):
            jmps.setdefault(int(ins.op_str,16),[]).append(ins.address)
        # imm32 that looks like a code address
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_IMM:
                v=op.imm & 0xFFFFFFFF
                if t['va'] <= v < t['va']+t['rawsize']:
                    imm32.setdefault(v,[]).append(ins.address)
    return dict(calls=calls,jmps=jmps,imm32=imm32,
                meta=dict(insns=n,skipped_bytes=nskip,text_bytes=len(data)))

def save_sweep(sw, path):
    def conv(v):
        if isinstance(v,dict):
            return {('%x'%kk if isinstance(kk,int) else kk):vv for kk,vv in v.items()}
        return v
    with open(path,'w',encoding='utf-8') as f:
        json.dump({k:conv(v) for k,v in sw.items()}, f)

def load_sweep(path):
    with open(path,encoding='utf-8') as f: d=json.load(f)
    out={}
    for k,v in d.items():
        if isinstance(v,dict):
            conv={}
            for kk,vv in v.items():
                try: key=int(kk,16)
                except Exception: key=kk
                conv[key]=vv
            out[k]=conv
        else: out[k]=v
    return out

if __name__=='__main__':
    b=Bin()
    print('ImageBase', hex(b.ib))
    for s in b.secs:
        print('  %-8s va=%08X vsize=%08X raw=%08X rawsize=%08X'%(s['name'],s['va'],s['vsize'],s['raw'],s['rawsize']))
