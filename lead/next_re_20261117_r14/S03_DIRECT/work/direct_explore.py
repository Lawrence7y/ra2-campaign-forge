import pefile, struct, json
from capstone import *
from capstone.x86 import X86_INS_CALL

ROOT = r'D:\Project\ra2-campaign-forge'
BIN = ROOT + r'\ra2youli\gamemd.exe'
COV = ROOT + r'\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATLAS = ROOT + r'\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
OUT = ROOT + r'\lead\next_re_20261117_r14\S03_DIRECT\work'

data = open(BIN,'rb').read()
pe = pefile.PE(BIN)
sec = [x for x in pe.sections if x.Name.rstrip(b'\x00')==b'.text'][0]
base = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress
vsize = sec.Misc_VirtualSize
rawptr = sec.PointerToRawData
code = data[rawptr:rawptr+vsize]

# --- atlas: entry -> size, and function ranges ---
atlas = {}
with open(ATLAS,encoding='utf-8',errors='replace') as f:
    hdr=f.readline()
    for line in f:
        c=line.rstrip('\n').split('\t')
        if not c[0]: continue
        try: e=int(c[0],16)
        except: continue
        atlas[e]=int(c[1])
# ranges sorted
ranges = sorted([(e,e+sz) for e,sz in atlas.items()])
import bisect
starts=[r[0] for r in ranges]
def find_caller(addr):
    i=bisect.bisect_right(starts,addr)-1
    if i>=0 and ranges[i][0]<=addr<ranges[i][1]:
        return ranges[i]
    return None

# --- coverage S03 [静态推断], atlas∩coverage only ---
rows=[]
with open(COV,encoding='utf-8',errors='replace') as f:
    hd=f.readline().rstrip('\n').split('\t')
    for line in f:
        c=line.rstrip('\n').split('\t')
        if len(c)<5: continue
        if c[1]!='S03' or c[4]!='[静态推断]': continue
        e=int(c[0],16)
        if e not in atlas: continue
        rows.append({'entry':e,'name':c[2],'sem':c[3],'grade':c[4],'size':atlas[e]})
print('working surface rows:',len(rows))

# --- scan E8@boundary, build target->sites ---
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True; md.detail=False
target_sites={}  # target -> list of (site, caller_start, caller_end)
ninsn=0; ne8=0
for insn in md.disasm(code, base):
    ninsn+=1
    b=insn.bytes
    if len(b)==5 and b[0]==0xE8 and insn.id==X86_INS_CALL:
        ne8+=1
        site=insn.address
        rel=struct.unpack('<i',b[1:5])[0]
        tgt=site+5+rel
        if tgt&0xFFFFFFFF==tgt or True:
            target_sites.setdefault(tgt&0xFFFFFFFF,[]).append(site)
print('ninsn',ninsn,'E8@boundary',ne8,'distinct targets',len(target_sites))

# --- for each row: direct call sites, non-self-loop ---
summary=[]
for r in rows:
    e=r['entry']
    sites=target_sites.get(e,[])
    valid=[]; selfloop=[]; outside=[]
    for s in sites:
        caller=find_caller(s)
        if caller is None:
            outside.append(s); continue
        cs,ce=caller
        if cs<=e<ce:
            selfloop.append((s,cs,ce))
        else:
            valid.append((s,cs,ce))
    summary.append({'entry':e,'name':r['name'],'nsites':len(sites),'nvalid':len(valid),'nself':len(selfloop),'noutside':len(outside),'valid':valid[:5],'self':selfloop[:3],'size':r['size']})

import collections
withcall=[x for x in summary if x['nvalid']>0]
print('\nrows with >=1 valid direct call:',len(withcall))
print('rows with any call site:',sum(1 for x in summary if x['nsites']>0))
print('rows with call sites but all self-loop:',sum(1 for x in summary if x['nsites']>0 and x['nvalid']==0 and x['nself']>0))
for x in withcall[:40]:
    print('  %08X %-32s valid=%d sites=%s size=%d'%(x['entry'],x['name'][:32],x['nvalid'],[hex(s) for s,_,_ in x['valid']],x['size']))
json.dump({'summary':summary,'ninsn':ninsn,'ne8':ne8},open(OUT+r'\direct_explore.json','w'),indent=1)
print('\nwrote direct_explore.json')
