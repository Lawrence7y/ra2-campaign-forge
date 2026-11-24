
import pefile, capstone, json, os
from collections import deque
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True); IMAGE = pe.OPTIONAL_HEADER.ImageBase
SEC=[]
for s in pe.sections:
    SEC.append((s.Name.rstrip(b'\x00').decode('latin1'), s.VirtualAddress+IMAGE, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
text=[s for s in SEC if s[0]=='.text'][0]
TB,TS,TP,TR = text[1],text[2],text[3],text[4]
RAW=open(EXE,'rb').read(); tdata=RAW[TP:TP+TR]
def sec_of(va):
    for n,b,vs,pr,rs in SEC:
        if b <= va < b+max(vs,rs): return n,b,pr,vs
    return None
def rd(va,n=4):
    s=sec_of(va)
    if not s: return None
    nme,b,pr,vs = s
    off = pr + (va-b)
    if off<0 or off+n>len(RAW): return None
    return RAW[off:off+n]
def dword(va):
    b=rd(va,4)
    return None if b is None else int.from_bytes(b,'little')

md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
ENT=set(json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\entries.json'))['e8'])

def insn_at(va):
    off=va-TB
    if off<0 or off>=TS: return None
    for i in md.disasm(tdata[off:off+16], va): return i
    return None
def dtgt(i):
    if not i.operands: return None
    m=i.mnemonic
    if (m=='call' or m=='jmp' or m.startswith('j') or m in ('loop','loope','loopne')) and i.operands[0].type==capstone.x86.X86_OP_IMM:
        return i.operands[0].imm
    return None

def extent(entry, maxbytes=6000):
    seen={}; work=deque([entry]); visited=set()
    while work:
        va=work.popleft()
        while True:
            if va in visited: break
            if va<TB or va>=TB+TS: break
            if va-entry>maxbytes: break
            if va!=entry and va in ENT and seen: break
            i=insn_at(va)
            if i is None: break
            visited.add(va); seen[va]=i
            m=i.mnemonic
            if m.startswith('ret'): break
            if m=='jmp':
                t=dtgt(i)
                if t is not None and entry<=t<entry+maxbytes: va=t; continue
                break
            if m.startswith('j') or m in ('loop','loope','loopne'):
                t=dtgt(i)
                if t is not None and entry<=t<entry+maxbytes: work.append(t)
                va=i.address+i.size; continue
            if m in ('int3','hlt'): break
            va=i.address+i.size
    return [seen[a] for a in sorted(seen)]

def memops(i):
    r=[];w=[]
    try:
        for op in i.operands:
            if op.type==capstone.x86.X86_OP_MEM:
                if op.access & capstone.CS_AC_WRITE: w.append(i.op_str)
                elif op.access & capstone.CS_AC_READ: r.append(i.op_str)
    except Exception: pass
    return r,w

def analyze(entry):
    body=extent(entry)
    if not body: return None
    F={'entry':hex(entry),'n':len(body),'span':(body[-1].address+body[-1].size)-entry,
       'jcc':0,'loops':[],'calls':[],'jtabs':[],'err_neg1':[],'pushsz':[],'vt_write':[],
       'ret_forms':{},'loads_globals':0}
    addr2i={i.address:i for i in body}
    for i in body:
        m=i.mnemonic
        if m.startswith('j') and m!='jmp':
            F['jcc']+=1
            t=dtgt(i)
            if t is not None and t<=i.address:
                # 循环体：t..i.address 之间是否有 读→判→写
                seg=[a for a in sorted(addr2i) if t<=a<=i.address]
                reads=writes=0; has_cmp=False
                for a in seg:
                    ii=addr2i[a]
                    r,w=memops(ii)
                    reads+= 1 if r else 0; writes+= 1 if w else 0
                    if ii.mnemonic.startswith('cmp') or ii.mnemonic in ('test',): has_cmp=True
                F['loops'].append({'back':hex(i.address),'head':hex(t),'n':len(seg),'reads':reads,'writes':writes,'has_cmp':has_cmp})
        if m=='jmp':
            for op in i.operands:
                if op.type==capstone.x86.X86_OP_MEM and op.mem.index!=0:
                    tbl=op.mem.disp; tg=[]
                    for k in range(0,40):
                        v=dword(tbl+4*k)
                        if v is None: break
                        s=sec_of(v)
                        if not s or s[0]!='.text': break
                        tg.append(v)
                    ncase=None
                    # 前一条 cmp reg, imm
                    idx=[a for a in sorted(addr2i)].index(i.address)
                    for j in range(max(0,idx-4), idx):
                        ii=addr2i[sorted(addr2i)[j]]
                        if ii.mnemonic=='cmp' and ii.operands and ii.operands[1].type==capstone.x86.X86_OP_IMM:
                            ncase=ii.operands[1].imm
                    F['jtabs'].append({'at':hex(i.address),'table':hex(tbl),'n_targets':len(tg),
                                       'targets':[hex(x) for x in tg[:16]],'cmp_bound':ncase,
                                       'guard':[aa.mnemonic for aa in body if abs(aa.address-i.address)<12]})
        if m=='call' and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM:
            F['calls'].append(hex(i.operands[0].imm))
        if m.startswith('ret'):
            k=i.mnemonic+' '+i.op_str; F['ret_forms'][k]=F['ret_forms'].get(k,0)+1
        if m=='or' and 'eax' in i.op_str and 'ffffffff' in i.op_str: F['err_neg1'].append(hex(i.address))
        if m=='mov' and i.op_str.endswith(', 0xffffffff'): F['err_neg1'].append(hex(i.address))
        if m=='push' and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM:
            v=i.operands[0].imm
            if 0x10<=v<=0x2000: F['pushsz'].append((hex(i.address),hex(v)))
        if m=='mov' and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_MEM and i.operands[1].type==capstone.x86.X86_OP_IMM:
            tgt=i.operands[1].imm
            s=sec_of(tgt)
            if s and s[0]=='.rdata': F['vt_write'].append((hex(i.address), hex(tgt)))
    F['n_callees']=len(set(F['calls']))
    F['n_calls']=len(F['calls'])
    return F

import sys
rows=[]
for line in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\weak105.tsv',encoding='utf-8'):
    f=line.rstrip('\n').split('\t')
    if len(f)<5 or f[0]=='entry' or f[1]=='S22': continue
    rows.append({'entry':f[0],'sub':f[1],'nm':f[2],'cls':f[3],'sem':f[4]})
out=[]
for r in rows:
    F=analyze(int(r['entry'],16))
    if F is None: F={'entry':r['entry'],'error':'nobody'}
    F.update({'sub':r['sub'],'cls':r['cls'],'nm':r['nm'],'sem':r['sem']})
    out.append(F)
json.dump(out, open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\feats2.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('analyzed', len(out))
for F in out:
    if 'error' in F: print('ERR',F['entry']); continue
    jt = ';'.join('%s n=%d bound=%s'%(t['table'],t['n_targets'],t['cmp_bound']) for t in F['jtabs'])
    lp = ';'.join('R%d/W%d/%s'%(l['reads'],l['writes'],'C' if l['has_cmp'] else '-') for l in F['loops'])
    print('%s %s %-3s n=%-4d jcc=%-3d loops=[%s] jt=[%s] err=%d vt=%d push=%d calls=%d' % (
      F['entry'],F['cls'],F['sub'],F['n'],F['jcc'],lp,jt,len(F['err_neg1']),len(F['vt_write']),len(F['pushsz']),F['n_calls']))
