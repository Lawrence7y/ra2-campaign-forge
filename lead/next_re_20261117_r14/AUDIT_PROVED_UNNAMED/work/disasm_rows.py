
import sys, json, pefile
from capstone import *
from capstone.x86 import *

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b'\x00').decode('latin1'), IB + s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
data = open(EXE,'rb').read()

def sec_of(va):
    for n,b,vs,pr,rs in secs:
        if b <= va < b+max(vs,rs): return (n,b,vs,pr,rs)
    return None

def read(va, n):
    s = sec_of(va)
    if not s: return b''
    n_name,b,vs,pr,rs = s
    off = pr + (va-b)
    return data[off:off+n]

def dword(va):
    b = read(va,4)
    return int.from_bytes(b,'little') if len(b)==4 else None

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

def disasm(va, maxbytes):
    buf = read(va, maxbytes)
    out=[]
    for ins in md.disasm(buf, va):
        out.append(ins)
        if ins.size==0: break
    return out

PAD = {0xCC, 0x90, 0x00}

def func_bounds(entry, hint):
    """linear sweep; return (insns, end_va, flags)"""
    insns = disasm(entry, 4000)
    end = entry
    stop = None
    for i,ins in enumerate(insns):
        end = ins.address + ins.size
        m = ins.mnemonic
        if m=='ret' or m.startswith('ret'):
            stop=('ret', i); break
        if m=='jmp' or m=='ljmp':
            stop=('jmp', i); break
        if m=='int3' and i>0:
            stop=('int3', i); break
        if ins.size>1 and ins.bytes[0]==0xCC:
            pass
    return insns, end, stop

ATLAS = {}
for ln in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv', encoding='utf-8'):
    p = ln.rstrip('\n').split('\t')
    if len(p)<6 or p[0]=='entry': continue
    try: ATLAS[int(p[0],16)] = (int(p[1]), int(p[2]), int(p[3]), int(p[4]))
    except: pass

def rtti_name(vt):
    col = dword(vt-4)
    if not col: return None
    td = dword(col+0xC)
    if not td: return None
    nm = read(td+8, 128).split(b'\x00')[0]
    try: return nm.decode('latin1')
    except: return None

def analyze(entry):
    hint = ATLAS.get(entry,(0,0,0,0))[0]
    insns, end, stop = func_bounds(entry, hint)
    reads=set(); writes=set(); calls=[]; globals_r=set(); globals_w=set()
    imms=[]; strings=[]; vts=[]
    thisregs = set(['ecx']) if True else set()
    # alias propagation
    insns = [i for i in insns if i.id != 0]
    for ins in insns:
        ops = ins.operands
        m = ins.mnemonic
        if m=='mov' and len(ops)==2 and ops[0].type==CS_OP_REG and ops[1].type==CS_OP_REG and ops[1].reg==X86_REG_ECX:
            thisregs.add(ins.reg_name(ops[0].reg))
        elif m=='mov' and len(ops)>=2 and ops[0].type==CS_OP_REG and ops[1].type==CS_OP_REG and ins.reg_name(ops[1].reg) in thisregs:
            thisregs.add(ins.reg_name(ops[0].reg))
    thisregs.discard('ecx')  # ecx itself handled
    thisregs.add('ecx')
    for ins in insns:
        m=ins.mnemonic
        for idx,op in enumerate(ins.operands):
            if op.type==CS_OP_MEM:
                base = ins.reg_name(op.mem.base) if op.mem.base else None
                disp = op.mem.disp
                if op.mem.base==0 and op.mem.index==0 and disp:
                    if idx==0: globals_w.add(disp)
                    else: globals_r.add(disp)
                elif base in thisregs and idx==0:
                    writes.add((base,disp))
                elif base in thisregs:
                    reads.add((base,disp))
            if op.type==CS_OP_IMM:
                v=op.imm
                if 0x400000 <= v < 0x400000+0x600000:
                    imms.append(v)
                    if idx>0 and m=='mov' and ins.operands[0].type==CS_OP_MEM:
                        vts.append(v)
    # calls
    for ins in insns:
        if ins.mnemonic in ('call','jmp'):
            for op in ins.operands:
                if op.type==CS_OP_IMM: calls.append((ins.address, ins.mnemonic, op.imm))
    # ascii near immediates: check whether imm points to ascii
    for v in set(imms):
        b = read(v, 24)
        if b and all(32<=c<127 or c==0 for c in b[:8]) and sum(1 for c in b if c==0)<20:
            s = b.split(b'\x00')[0]
            if len(s)>=4: strings.append((hex(v), s.decode('latin1')))
    vtinfo=[]
    for v in set(vts):
        nm = rtti_name(v)
        vtinfo.append((hex(v), nm))
    nb = read(end, 8)
    pad_after = all(c in PAD for c in nb[:8]) if nb else True
    nextatlas = end in ATLAS
    return dict(entry=entry, atlas_size=hint, my_size=end-entry, n_insns=len(insns),
                stop=stop, pad_after=pad_after, nextatlas=nextatlas,
                reads=sorted(reads), writes=sorted(writes),
                globals_r=sorted(globals_r), globals_w=sorted(globals_w),
                calls=calls[:40], strings=strings[:10], vt=vtinfo)

if __name__=='__main__':
    entries=[int(x,16) for x in sys.argv[1:]]
    res={}
    for e in entries:
        a=analyze(e)
        res['%08X'%e]=a
        # dump asm
        insns,end,stop = func_bounds(e, ATLAS.get(e,(0,0,0,0))[0])
        with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_PROVED_UNNAMED\EVIDENCE\asm_%08X.txt'%e,'w',encoding='utf-8') as f:
            f.write('# entry=%08X atlas_size=%d my_size=%d n_insns=%d stop=%s pad_after=%s\n'%(e,ATLAS.get(e,(0,0,0,0))[0],end-e,len(insns),stop,a['pad_after']))
            for ins in insns:
                f.write('%08X  %-24s %s %s\n'%(ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    print(json.dumps(res, ensure_ascii=False, default=str))
