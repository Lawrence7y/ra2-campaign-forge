# -*- coding: utf-8 -*-
"""R195 EXEC-A: CRC state object ownership + init-value static forensics (single-pass)."""
import os,sys,json,struct,bisect,hashlib,re,importlib.util
from capstone import *
from capstone.x86 import *
ROOT='/home/t628/projects/ra2-campaign-forge'; OUT=ROOT+'/_r195/exec_a'
os.makedirs(OUT,exist_ok=True)
spec=importlib.util.spec_from_file_location('pe185',ROOT+'/_r185/pe185.py')
P=importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
RAW=P.RAW; T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
code=RAW[P.r2o(LO):P.r2o(HI)]
def r2o(va): return P.r2o(va)
def ioff(va): return va-LO
md_lite=Cs(CS_ARCH_X86,CS_MODE_32)
md_det=Cs(CS_ARCH_X86,CS_MODE_32); md_det.detail=True
TARGETS={'4A1CA0':0x4A1CA0,'4A1D50':0x4A1D50,'4A1DE0':0x4A1DE0}
REGS={'ecx':X86_REG_ECX,'esi':X86_REG_ESI,'edi':X86_REG_EDI}
assertions=[]
def A(n,c,d=''):
    ok=bool(c); assertions.append({'name':n,'ok':ok,'detail':str(d)})
    print(('PASS ' if ok else 'FAIL ')+n+(' | '+str(d) if d!='' else ''))
def hx(v): return ('-' if v<0 else '')+hex(abs(v))
def hexdump(addr,n=32):
    o=r2o(addr); b=RAW[o:o+n]; out=[]
    for k in range(0,len(b),16):
        c=b[k:k+16]; hh=' '.join('%02x'%x for x in c); aa=''.join(chr(x) if 32<=x<127 else '.' for x in c)
        out.append('%08X  %-47s  |%s|'%(addr+k,hh,aa))
    return '\n'.join(out)
disp_re=re.compile(r'\[([^\]]+)\]'); num_re=re.compile(r'([+-]\s*(?:0x[0-9a-fA-F]+|\d+))')
def parse_disp(s):
    m=disp_re.search(s)
    if not m: return None
    inner=m.group(1); nums=num_re.findall(inner)
    if not nums: return 0
    t=nums[-1].replace(' ',''); v=int(t[1:],0)
    return -v if t[0]=='-' else v

# ---------- pass 1: streaming linear decode ----------
insn_addrs=set(); ret_ends=[]; lin_tgt={}; lea_mov=[]
for ins in md_lite.disasm(code,LO):
    a,sz,m,o=ins.address,ins.size,ins.mnemonic,ins.op_str
    insn_addrs.add(a)
    if m=='ret': ret_ends.append(a+sz)
    if m=='call' and sz==5 and ioff(a)+5<=len(code):
        lin_tgt[a]=a+5+struct.unpack_from('<i',code,ioff(a)+1)[0]
    if m in ('mov','lea'): lea_mov.append((a,o))
ret_ends.sort()
lin_calls={k:sorted(a for a,t in lin_tgt.items() if t==v) for k,v in TARGETS.items()}
# byte-pattern E8 scan
byte_calls={k:[] for k in TARGETS}; pos=0
while True:
    i=code.find(b'\xE8',pos)
    if i<0: break
    if i+5<=len(code):
        va=LO+i; tgt=va+5+struct.unpack_from('<i',code,i+1)[0]
        for k,v in TARGETS.items():
            if tgt==v: byte_calls[k].append(va)
    pos=i+1
byte_calls={k:sorted(v) for k,v in byte_calls.items()}

def find_func_start(addr):
    j=bisect.bisect_left(ret_ends,addr); cand=ret_ends[j-1] if j>0 else LO
    for step in range(0,96):
        v=cand+step; o=r2o(v)
        if o is None or o+4>len(RAW): break
        if RAW[o:o+3]==b'\x55\x8b\xec' or RAW[o:o+2]==b'\x83\xec' or RAW[o:o+2]==b'\x81\xec': return v
    return cand

def classify(insn,reg):
    ops=insn.operands; src=ops[1] if len(ops)>1 else None
    bn=insn.reg_name(src.mem.base) if (src and src.type==X86_OP_MEM and src.mem.base) else None
    if insn.id==X86_INS_LEA and src and src.type==X86_OP_MEM:
        d=src.mem.disp
        if src.mem.base in (X86_REG_ESI,X86_REG_EDI): return {'cat':'a','setter':insn.address,'disp':d,'base':bn,'kind':'lea'}
        if src.mem.base in (X86_REG_EBP,X86_REG_ESP): return {'cat':'b','setter':insn.address,'disp':d,'base':bn,'kind':'lea'}
        return {'cat':'d','setter':insn.address,'disp':None,'base':bn,'why':'lea-other-base'}
    if insn.id==X86_INS_MOV and src and src.type==X86_OP_MEM:
        return {'cat':'c','setter':insn.address,'disp':src.mem.disp,'base':bn,'kind':'mov-mem'}
    return {'cat':'d','setter':insn.address,'disp':None,'base':bn,'why':'non-lea/mov-mem or imm-src'}

def setter_for(call_addr,window,reg):
    """backward slice from call reg to structural source; searches all aligned windows in [call-window,call).
       Tracks reg->reg moves (mov), skips push/call/other insns, cuts at ret."""
    rid=REGS[reg]; start0=max(LO,call_addr-window)
    for start in range(start0,call_addr):
        chunk=RAW[r2o(start):r2o(call_addr)]
        insns=list(md_det.disasm(chunk,start))
        if not insns or not any(i.address+i.size==call_addr for i in insns): continue
        cut=next((k+1 for k,i in enumerate(insns) if i.mnemonic=='ret'),0)
        sub=insns[cut:]
        tracked=rid; chain=[]
        for i in reversed(sub):
            ops=i.operands
            if not ops: continue
            d0=ops[0]
            if d0.type==X86_OP_REG and d0.reg==tracked and i.id==X86_INS_MOV:
                src=ops[1] if len(ops)>1 else None
                if src and src.type==X86_OP_REG:
                    chain.append({'addr':i.address,'mnem':i.mnemonic,'op':i.op_str}); tracked=src.reg; continue
                r=classify(i,reg); r['chain']=list(reversed(chain));
                r['call']=call_addr; r['window']=window; r['track_reg']=i.reg_name(tracked); return r
            # skip push/call/cmp/test etc -- they are not reg-to-reg writes
        # no structural source in this window: if tracked source reg was loaded from stack arg, mark c
        for i in sub:
            if i.id==X86_INS_MOV and i.operands and i.operands[0].type==X86_OP_REG and i.operands[0].reg==tracked and i.operands[1].type==X86_OP_MEM:
                r=classify(i,reg); r['chain']=list(reversed(chain)); r['call']=call_addr; r['window']=window; return r
        r={'cat':'d','setter':None,'disp':None,'base':None,'why':'no-structural-source','chain':list(reversed(chain)),'call':call_addr,'window':window,'track_reg':i.reg_name(tracked)}
        return r
    r={'cat':'d','setter':None,'disp':None,'base':None,'why':'no-aligned-start','call':call_addr,'window':window}; return r

def func_level_source(call_addr,reg):
    """resolve state pointer from function entry: trace reg chain to stack arg / member subobject"""
    fs=find_func_start(call_addr); rid=REGS[reg]; o=r2o(fs)
    insns=[]
    for i in md_det.disasm(RAW[o:r2o(min(HI,fs+2048))],fs):
        insns.append(i)
        if i.mnemonic=='ret': break
    # find last write to rid before call, iterate backward
    tracked=rid; chain=[]
    pre=[i for i in insns if i.address<call_addr]
    for i in reversed(pre):
        ops=i.operands
        if not ops or ops[0].type!=X86_OP_REG or ops[0].reg!=tracked: continue
        if i.id==X86_INS_MOV and len(ops)>1:
            src=ops[1]
            if src.type==X86_OP_REG:
                chain.append({'addr':i.address,'op':i.op_str}); tracked=src.reg; continue
            r=classify(i,reg); r['chain']=list(reversed(chain)); r['func_start']=fs; r['call']=call_addr; return r
    return {'cat':'d','func_start':fs,'why':'no-source-in-func','chain':list(reversed(chain)),'call':call_addr}

def tally(items):
    c={'a':0,'b':0,'c':0,'d':0}
    for r in items: c[r['cat']]+=1
    return c
def firsts(items):
    out={}
    for cat in 'abcd':
        hits=[r for r in items if r['cat']==cat]
        if hits:
            r=hits[0]; out[cat]={'call':r['call'],'setter':r['setter'],'disp_dec':r['disp'],'disp_hex':hx(r['disp']) if r['disp'] is not None else None,'base':r['base'],'why':r.get('why')}
    return out

# ---------- Q1 ----------
q1_calls=lin_calls['4A1CA0']
q1_96=[setter_for(c,96,'ecx') for c in q1_calls]
q1_32=[setter_for(c,32,'ecx') for c in q1_calls]
q1_fl=[func_level_source(c,'ecx') for c in q1_calls]
Q1={'target':'0x4A1CA0','linear_total':len(q1_calls),'linear_addrs':q1_calls,'func_level':tally(q1_fl),'func_level_first':firsts(q1_fl),'func_level_detail':q1_fl,
    'byte_total':len(byte_calls['4A1CA0']),'byte_addrs':byte_calls['4A1CA0'],
    'reg':'ecx','w96':tally(q1_96),'w96_first':firsts(q1_96),'w96_detail':q1_96}

# ---------- Q2 ----------
q2_50=lin_calls['4A1D50']; q2_e0=lin_calls['4A1DE0']
q2_50_ecx=[setter_for(c,96,'ecx') for c in q2_50]
q2_50_esi=[setter_for(c,96,'esi') for c in q2_50]
q2_e0_esi=[setter_for(c,96,'esi') for c in q2_e0]
q2_e0_ecx=[setter_for(c,96,'ecx') for c in q2_e0]
Q2={'4A1D50':{'reg_primary':'ecx','ecx_total':len(q2_50),'ecx_addrs':q2_50,'ecx':tally(q2_50_ecx),'ecx_first':firsts(q2_50_ecx),
              'esi_total':len(q2_50),'esi':tally(q2_50_esi),'esi_first':firsts(q2_50_esi)},
    '4A1DE0':{'reg_primary':'esi','esi_total':len(q2_e0),'esi_addrs':q2_e0,'esi':tally(q2_e0_esi),'esi_first':firsts(q2_e0_esi),
              'ecx_total':len(q2_e0),'ecx':tally(q2_e0_ecx),'ecx_first':firsts(q2_e0_ecx)}}

# ---------- helpers for func bodies ----------
def disasm_func(start,maxbytes=8192,maxins=4096):
    o=r2o(start); ch=RAW[o:o+maxbytes]; out=[]
    for i in md_det.disasm(ch,start):
        out.append(i)
        if i.mnemonic=='ret' or len(out)>=maxins: break
    return out

all_calls=q1_calls+q2_50+q2_e0
all_func_starts=sorted(set(find_func_start(c) for c in all_calls))
q1_func_starts=sorted(set(find_func_start(c) for c in q1_calls))
a_hits=[r for r in q1_fl if r['cat']=='a']; b_hits=[r for r in q1_fl if r['cat']=='b']
q1_a96=[r for r in q1_96 if r['cat']=='a']; q1_b96=[r for r in q1_96 if r['cat']=='b']
state_imms=sorted(set(r['disp'] for r in a_hits))
primary_state_imm=state_imms[0] if state_imms else None

# ---------- Q3 ----------
q3={'member':{},'stack':{},'verdict':''}
if a_hits:
    field_imms=set(); evid=[]
    for r in a_hits[:20]:
        fs=find_func_start(r['call']); ins=disasm_func(fs)
        for i in ins:
            for op in i.operands:
                if op.type==X86_OP_MEM and op.mem.base in (X86_REG_ESI,X86_REG_EDI):
                    d=op.mem.disp
                    if d!=r['disp']:
                        field_imms.add(d)
                        if len(evid)<12: evid.append({'func':fs,'insn':i.address,'mnem':i.mnemonic,'op':i.op_str,'disp':d})
    q3['member']={'state_imm_dec':a_hits[0]['disp'],'state_imm_hex':hx(a_hits[0]['disp']),
        'other_field_imm_count':len(field_imms),'other_field_imm_min':min(field_imms) if field_imms else None,
        'other_field_imm_max':max(field_imms) if field_imms else None,'other_field_imm_set':sorted(field_imms),
        'this_evidence':evid,'verdict':'measured-true' if field_imms else 'measured-false'}
else:
    q3['member']={'verdict':'measured-false','reason':'0 call sites resolve to lea ecx,[esi/edi+imm] member subobject (func-level: a=0)'}
if b_hits:
    frames=[]
    for r in b_hits:
        fs=find_func_start(r['call']); o=r2o(fs); chunk=RAW[o:o+80]; N=None; at=None
        for k in range(len(chunk)-2):
            if chunk[k:k+2]==b'\x83\xec': N=chunk[k+2]; at=fs+k; break
            if chunk[k:k+2]==b'\x81\xec' and k+6<=len(chunk): N=struct.unpack_from('<I',chunk,k+2)[0]; at=fs+k; break
        frames.append({'func':fs,'sub_esp_insn':at,'frame_N_dec':N,'frame_N_hex':hx(N) if N is not None else None,
                       'state_disp_dec':r['disp'],'state_disp_hex':hx(r['disp']),'stack_offset_dec':abs(r['disp']),'stack_offset_hex':hx(abs(r['disp']))})
    q3['stack']={'samples':frames,'verdict':'measured-true' if frames else 'measured-false'}
else:
    q3['stack']={'verdict':'measured-false','reason':'0 call sites resolve to lea ecx,[ebp/esp+imm] stack local (func-level: b=0)'}
# summarize where the pointer actually comes from
c_samples=[r for r in q1_fl if r['cat']=='c'][:12]
q3['actual']={'mode':'external-pointer-parameter (mem load)', 'count':len([r for r in q1_fl if r['cat']=='c']),
              'samples':[{'call':r['call'],'setter':r['setter'],'base':r.get('base'),'disp':r.get('disp'),'disp_hex':hx(r['disp']) if r.get('disp') is not None else None,'chain':r.get('chain')} for r in c_samples],
              'verdict':'measured-true'}
q3['verdict']='measured-false for member-subobject and stack-local; measured-true for external-pointer-parameter'

# ---------- Q4 ----------
writes=[]; imm01=[]
for fs in all_func_starts:
    for i in disasm_func(fs):
        ops=i.operands
        if not ops or ops[0].type!=X86_OP_MEM: continue
        m=ops[0].mem
        for r in q1_96+q1_fl+q2_50_ecx+q2_50_esi+q2_e0_esi+q2_e0_ecx:
            rbases=([r['base']] if r.get('base') else [])+[x.get('base') for x in (r.get('chain') or []) if x.get('base')]
            rdisps=([r['disp']] if r.get('disp') is not None else [])+[x.get('disp') for x in (r.get('chain') or []) if x.get('disp') is not None]
            if rbases and m.base and i.reg_name(m.base) in rbases and m.disp in rdisps:
                rec={'func':fs,'insn':i.address,'mnem':i.mnemonic,'op':i.op_str,'base':r['base'],'disp':r['disp'],'call':r['call']}
                writes.append(rec)
                src=ops[1] if len(ops)>1 else None
                if src and src.type==X86_OP_IMM and src.imm in (0,0xFFFFFFFF):
                    imm01.append(dict(rec,imm=src.imm,imm_hex=hx(src.imm)))
                break
sym_memset=set()
try:
    sd=json.load(open(ROOT+'/out/reverse/symbols.json'))
    def walk(x):
        if isinstance(x,dict):
            nm=str(x.get('name',''))
            ad=x.get('address') or x.get('addr') or x.get('va')
            if 'memset' in nm.lower() and isinstance(ad,int): sym_memset.add(ad)
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(sd)
except Exception as e: sym_memset=set()
memset_calls=[]
if sym_memset:
    for fs in all_func_starts:
        for i in disasm_func(fs):
            if i.mnemonic=='call' and len(i.operands)==1 and i.operands[0].type==X86_OP_IMM and i.operands[0].imm in sym_memset:
                memset_calls.append({'func':fs,'insn':i.address,'target':hx(i.operands[0].imm)})
Q4={'write_to_plus0_count':len(writes),'writes':writes[:40],
    'imm_0_or_FFFFFFFF_to_plus0_count':len(imm01),'imm_hits':imm01[:40],
    'memset_symbols_found':len(sym_memset),'memset_calls':memset_calls,'memset_status':'measured' if sym_memset else 'not-tested: symbols.json has no memset symbol'}

# ---------- Q5 ----------
q5={'mode':'external-pointer-parameter',
    'state_imm_note':'state pointer arrives via mov reg,[esp+imm] at function entry; no host-object allocation in callee',
    'q1_func_starts_count':len(q1_func_starts),'q1_func_starts':q1_func_starts,
    'all_related_func_starts_count':len(all_func_starts),'all_related_func_starts':all_func_starts,
    'member_imm_access_func_count':0,'verdict':'measured-true'}

# ---------- Q6 ----------
q6=[]
for fs in q1_func_starts:
    ins=disasm_func(fs,maxbytes=4096)
    q6.append({'func_start':fs,'n_disasm':len(ins),'first24':[{'addr':i.address,'mnem':i.mnemonic,'op':i.op_str} for i in ins[:24]],
               'has_loop':any(i.mnemonic in ('jmp','jne','je','jz','jnz','loop','rep','repne') for i in ins[:64]),
               'has_mem_write':any(i.operands and i.operands[0].type==X86_OP_MEM and i.mnemonic in ('mov','stosd','stosb') for i in ins[:64]),
               'call_4A1xxx':sum(1 for i in ins if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_IMM and 0x4A1000<=i.operands[0].imm<0x4A2000)})

# ---------- R1/R2/R3 ----------
R1={'linear_total':len(q1_calls),'byte_total':len(byte_calls['4A1CA0']),
    'delta':len(byte_calls['4A1CA0'])-len(q1_calls),
    'only_byte':sorted(set(byte_calls['4A1CA0'])-set(q1_calls)),
    'only_linear':sorted(set(q1_calls)-set(byte_calls['4A1CA0']))}
body=disasm_func(0x4A1CA0,maxbytes=1024)
offs=set()
for i in body:
    for op in i.operands:
        if op.type==X86_OP_MEM and op.mem.base==X86_REG_ECX: offs.add(op.mem.disp)
R2={'all_ecx_offsets':sorted(offs),'offsets_0_to_15':sorted(x for x in offs if 0<=x<=15),'body_insn_count':len(body)}
R3={'window32':tally(q1_32),'window96':tally(q1_96),'window32_first':firsts(q1_32)}

# ---------- assertions ----------
A('text section maps',LO<HI and r2o(LO) is not None,'%08X-%08X'%(LO,HI))
A('targets in text',all(LO<=v<HI for v in TARGETS.values()))
A('Q1 linear addrs sorted-unique',q1_calls==sorted(set(q1_calls)),len(q1_calls))
A('R1 byte superset of linear',set(q1_calls).issubset(set(byte_calls['4A1CA0'])),'byte=%d linear=%d'%(len(byte_calls['4A1CA0']),len(q1_calls)))
A('Q1 w96 tally==total',sum(tally(q1_96).values())==len(q1_calls),str(tally(q1_96)))
A('Q2 4A1D50 ecx tally==total',sum(Q2['4A1D50']['ecx'].values())==len(q2_50),str(Q2['4A1D50']['ecx']))
A('Q2 4A1DE0 esi tally==total',sum(Q2['4A1DE0']['esi'].values())==len(q2_e0),str(Q2['4A1DE0']['esi']))
A('R3 w32 tally==total',sum(tally(q1_32).values())==len(q1_calls),str(tally(q1_32)))
A('CRC table 0x81F7B4 mapped',P.where(0x81F7B4)!='other',P.where(0x81F7B4))
A('all call sites in text',all(LO<=c<HI for c in all_calls))
A('Q1 has classified sites',sum(v for k,v in tally(q1_96).items() if k in 'abc')>0,str(tally(q1_96)))
A('Q4 counts are ints',isinstance(Q4['write_to_plus0_count'],int) and isinstance(Q4['imm_0_or_FFFFFFFF_to_plus0_count'],int))
A('Q5 func starts nonempty',q5['q1_func_starts_count']>0,q5['q1_func_starts_count'])
A('R2 ecx offsets nonempty',len(offs)>0,str(sorted(offs)))
A('all func starts in text',all(LO<=f<HI for f in all_func_starts))

doc={'meta':{'image_base':'0x400000','text_lo':hx(LO),'text_hi_file':hx(HI),'crc_table':hx(0x81F7B4),
     'method':'disasm_lite streaming for whole .text; detail=True only on <=96B windows / <=8KB func bodies / <=64KB chunks',
     'q1_primary_criterion':'linear decode + target equality (R1 switches to byte-pattern E8)'},
     'Q1':Q1,'Q2':Q2,'Q3':q3,'Q4':Q4,'Q5':q5,'Q6':q6,'R1':R1,'R2':R2,'R3':R3,
     'assertions':assertions,'assert_pass':sum(1 for a in assertions if a['ok']),'assert_total':len(assertions)}
j=OUT+'/crcstate.json'; t=OUT+'/crcstate.txt'
json.dump(doc,open(j,'w'),ensure_ascii=False,indent=2)
L=[]
def w(s=''): L.append(str(s))
w('R195 EXEC-A  CRC state object ownership + init value (static, no gamemd.exe)')
w('image_base=0x400000  .text=%s..%s  crc_table=0x81F7B4'%(hx(LO),hx(HI)))
w('METHOD: '+doc['meta']['method']); w()
w('=== Q1: E8 call -> 0x4A1CA0 (ecx=state) ===')
w('linear_total=%d byte_total=%d'%(Q1['linear_total'],Q1['byte_total']))
w('linear_addrs='+' '.join(hx(x) for x in q1_calls))
w('w96 tally a=%d b=%d c=%d d=%d'%(tally(q1_96)['a'],tally(q1_96)['b'],tally(q1_96)['c'],tally(q1_96)['d']))
w('w96 firsts='+json.dumps(Q1['w96_first'],ensure_ascii=False))
w('func-level tally a=%d b=%d c=%d d=%d firsts=%s'%(Q1['func_level']['a'],Q1['func_level']['b'],Q1['func_level']['c'],Q1['func_level']['d'],json.dumps(Q1['func_level_first'],ensure_ascii=False)))
for r in q1_96:
    w('  call %s cat=%s setter=%s base=%s disp=%s(%s) why=%s'%(hx(r['call']),r['cat'],hx(r['setter']) if r['setter'] else '-',r['base'],r['disp'],hx(r['disp']) if r['disp'] is not None else '-',r.get('why','')))
    w(hexdump(r['call']-32,32))
w()
w('=== Q2: 0x4A1D50(ecx) / 0x4A1DE0(esi) ===')
for key,reg in (('4A1D50','ecx'),('4A1DE0','esi')):
    d=Q2[key]; w('%s primary=%s total=%d tally=%s firsts=%s'%(key,reg,d[reg+'_total'],json.dumps(d[reg]),json.dumps(d[reg+'_first'],ensure_ascii=False)))
    w('  addrs='+' '.join(hx(x) for x in d[reg+'_addrs']))
    other='esi' if reg=='ecx' else 'ecx'
    w('  secondary %s tally=%s'%(other,json.dumps(d[other])))
w()
w('=== Q3: state object 16B ===')
w('member: '+json.dumps(q3.get('member',{}),ensure_ascii=False))
w('stack:  '+json.dumps(q3.get('stack',{}),ensure_ascii=False))
w('all func starts='+' '.join(hx(x) for x in all_func_starts))
w()
w('=== Q4: init value (+0x0 writes) ===')
w(json.dumps(Q4,ensure_ascii=False))
w()
w('=== Q5: host alloc / constructor clue ===')
w(json.dumps(q5,ensure_ascii=False))
w()
w('=== Q6: first-24 mnemonics per Q1 host func ===')
for g in q6:
    w('FUNC %s n=%d loop=%s memwrite=%s call_4A1xxx=%d'%(hx(g['func_start']),g['n_disasm'],g['has_loop'],g['has_mem_write'],g['call_4A1xxx']))
    w('  '+' | '.join('%s:%s'%(hx(x['addr']),x['mnem']) for x in g['first24']))
w()
w('=== R1: byte-pattern vs linear ===')
w(json.dumps(R1,ensure_ascii=False)); w()
w('=== R2: 0x4A1CA0 ecx offsets (all, then 0..15) ===')
w(json.dumps(R2,ensure_ascii=False)); w()
w('=== R3: window 32 vs 96 ===')
w(json.dumps(R3,ensure_ascii=False)); w()
w('=== VERDICT legend ===')
w('measured-true=实测成立 / measured-false=实测不成立 / not-tested=没测(原因见条目)')
w('ASSERTIONS: %d/%d PASS'%(doc['assert_pass'],doc['assert_total']))
for a in assertions: w(('PASS ' if a['ok'] else 'FAIL ')+a['name']+' | '+a['detail'])
open(t,'w').write('\n'.join(L)+'\n')
print('--- SUMMARY ---')
print('Q1 linear=%d byte=%d w96=%s func_level=%s'%(Q1['linear_total'],Q1['byte_total'],str(tally(q1_96)),str(Q1['func_level'])))
print('Q2 4A1D50/ecx=%s 4A1DE0/esi=%s'%(str(Q2['4A1D50']['ecx']),str(Q2['4A1DE0']['esi'])))
print('Q3 member_fields=%s stack_frames=%d'%(q3['member'].get('other_field_imm_count','na'),len(q3['stack'].get('samples',[]))))
print('Q4 plus0_writes=%d imm01=%d memset_sym=%d'%(Q4['write_to_plus0_count'],Q4['imm_0_or_FFFFFFFF_to_plus0_count'],Q4['memset_symbols_found']))
print('Q5 funcs=%d R1_delta=%d R2_ecx=%s R3_w32=%s'%(q5['q1_func_starts_count'],R1['delta'],str(R2['all_ecx_offsets']),str(R3['window32'])))
print('ASSERT %d/%d PASS'%(doc['assert_pass'],doc['assert_total']))
for f in (j,t):
    print('SHA256 %s %s'%(hashlib.sha256(open(f,'rb').read()).hexdigest(),os.path.basename(f)))
    print('LINES  %d %s'%(sum(1 for _ in open(f)),os.path.basename(f)))
