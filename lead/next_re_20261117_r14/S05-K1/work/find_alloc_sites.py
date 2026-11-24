"""T2: GetSize bidirectional check - find push <size> allocation sites.
Read-only on gamemd.exe.
"""
import pefile, struct, os, json, bisect, collections

ROOT = os.path.join('D:', os.sep, 'Project', 'ra2-campaign-forge')
PE_PATH = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
OUT_DIR = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'S05-K1', 'EVIDENCE')

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.skipdata = True; MD.detail = True

pe = pefile.PE(PE_PATH)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode('ascii','replace')
    SECS.append({'name':nm,'va':s.VirtualAddress+IB,'vs':s.Misc_VirtualSize,
                 'raw':s.PointerToRawData,'rs':s.SizeOfRawData})
DATA = open(PE_PATH,'rb').read()
SECMAP = {s['name']:s for s in SECS}
TEXT = SECMAP['.text']

def off(va):
    for s in SECS:
        if s['va'] <= va < s['va']+max(s['vs'],s['rs']):
            d = va-s['va']
            if d < s['rs']: return s['raw']+d
    return None
def sec_of(va):
    for s in SECS:
        if s['va'] <= va < s['va']+max(s['vs'],s['rs']): return s['name']
    return None

# atlas funcs
funcs=[]
with open(ATLAS) as f:
    f.readline()
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)<2: continue
        try: funcs.append((int(p[0],16),int(p[1],10)))
        except: pass
funcs.sort(); starts=[e for e,_ in funcs]
def enclosing(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0:
        e,sz=funcs[i]
        if e<=va<e+max(sz,1): return e,sz
    return None,None

SIZES = {
    'BuildingClass':0x720, 'UnitClass':0x8E8,
    'InfantryClass':0x6F0, 'AircraftClass':0x6D8,
}

def find_push(size):
    """bytes 68 <imm32LE> in .text"""
    pat = b'\x68'+struct.pack('<I',size)
    lo,hi=TEXT['raw'],TEXT['raw']+TEXT['rs']
    hits=[]; i=DATA.find(pat,lo,hi)
    while i!=-1:
        va=TEXT['va']+(i-TEXT['raw'])
        hits.append(va)
        i=DATA.find(pat,i+1,hi)
    return hits

def disasm_from(va,n=18):
    o=off(va)
    if o is None: return []
    out=[]
    for insn in MD.disasm(DATA[o:o+80],va):
        out.append(insn)
        if len(out)>=n: break
    return out

result={'sizes':SIZES,'sites':{},'operator_new_candidates':collections.Counter()}
for nm,size in SIZES.items():
    hits=find_push(size)
    sites=[]
    for h in hits:
        insns=disasm_from(h,18)
        calls=[]
        for ins in insns[1:]:  # skip the push itself
            if ins.mnemonic in ('call','jmp'):
                try:
                    ops=ins.operands
                    if ops and ops[0].type==X86_OP_IMM:
                        calls.append((ins.address,ins.mnemonic,ops[0].imm))
                except: pass
        fe,fsz=enclosing(h)
        first_call = calls[0][2] if calls else None
        if first_call: result['operator_new_candidates'][first_call]+=1
        sites.append({'push_va':'%08X'%h,'func':('%08X'%fe) if fe else None,
                      'fsz':fsz,'first_call':('%08X'%first_call) if first_call else None,
                      'calls':[('%08X'%c[2]) for c in calls[:4]]})
    result['sites'][nm]=sites
    print('=== %s size=0x%X push sites=%d' % (nm,size,len(hits)))
    for s in sites[:20]:
        print('   push@%s func=%s firstcall=%s calls=%s' % (
            s['push_va'],s['func'],s['first_call'],s['calls']))

print('\n=== first-call target histogram (all sizes) ===')
for t,c in result['operator_new_candidates'].most_common(20):
    print('   %08X : %d' % (t,c))

outp=os.path.join(OUT_DIR,'getsize_alloc_sites.json')
with open(outp,'w',encoding='utf-8') as f:
    json.dump(result,f,indent=1,ensure_ascii=False)
print('WROTE',outp)
