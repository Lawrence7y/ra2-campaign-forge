# -*- coding: utf-8 -*-
"""w-detect2: ③b 严格档检测器（含 dec/jne 计数循环、内存形状、错误码、跳表）。"""
import os,sys,csv,json
sys.path.insert(0,os.path.dirname(__file__))
import ax_lib
from capstone import *
CLS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
CAND=["0040BA50","0040CDC0","00410220","00410230","00410BE0","0050EA00","00512D30",
"00513100","005134D0","005F9720","006F3F40","006F4A70","006F6CA0","00708D70",
"00709A30","00709A40","0070C250","0070E280","0070E2B0","00711EB0","00711F00","007171A0"]
ext={}; meta={}
for r in csv.DictReader(open(CLS,encoding='utf-8'),delimiter='\t'):
    if r['entry'].upper() in CAND:
        ext[r['entry'].upper()]=(int(r['ext_lo'],16),int(r['ext_hi'],16))
        meta[r['entry'].upper()]=r['name']
pe=ax_lib.load(); MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

def mem_dst(i):
    if ',' not in i.op_str: return ''
    return i.op_str.split(',')[0].strip()

def analyze(e):
    lo,hi=ext[e]; ins=list(MD.disasm(pe.buf[pe.off(lo):pe.off(lo)+(hi-lo)],lo))
    addrs=[i.address for i in ins]; idx={a:k for k,a in enumerate(addrs)}
    jt=[]; err=[]; loops=[]; memshape_w=0; vtw=0
    gates={}; calls=[]
    for k,i in enumerate(ins):
        if i.mnemonic=='jmp' and '*' in i.op_str and 'ptr' in i.op_str: jt.append((i.address-lo,i.op_str))
        if i.mnemonic=='cmp' and any(x in i.op_str for x in ['-1','0x80004002','0x7fff','0xffff','0x8000']):
            for z in ins[k+1:k+9]:
                if z.mnemonic.startswith('j') or z.mnemonic.startswith('ret') or z.mnemonic.startswith('set') or z.mnemonic.startswith('cmov'):
                    err.append((i.address-lo,i.op_str)); break
        d=mem_dst(i)
        if d.startswith(('dword ptr','word ptr','byte ptr')) and 'esp' not in d and 'ebp' not in d:
            memshape_w+=1
            if ('0x7e' in d or '0x7f' in d) and i.mnemonic=='mov': vtw+=1
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            try:
                t=int(i.op_str,16); gates.setdefault(t,[]).append((i.address-lo,i.mnemonic))
            except: pass
            ti=idx.get(t)
            if ti is not None and ti<=k:
                body=ins[ti:k+1]
                if len(body)>=3:
                    w=bc=adv=False
                    for z in body:
                        dd=mem_dst(z)
                        if z.mnemonic in ('mov','or','and','add','sub','xor','inc','dec') and dd.startswith(('dword ptr','word ptr','byte ptr')): w=True
                        if z.mnemonic in ('cmp','test','dec'): bc=True
                        if z.mnemonic in ('inc','dec','add','sub') and any(reg in z.op_str for reg in ('esi','edi','ebx','eax','ecx','edx','ebp')): adv=True
                    if w and bc and adv: loops.append((t-lo,i.address-lo,len(body)))
        if i.mnemonic=='call': calls.append(i.op_str)
    ms = vtw>=2 or memshape_w>=10
    strict = bool(jt or err or ms or loops)
    distinct_calls=sorted(set(calls))
    guard_loose = strict or (len(gates)>=3 and len(distinct_calls)>=3)
    return dict(name=meta[e],n=len(ins),size=hi-lo,jt=jt,err=err,loops=loops,
                memshape_w=memshape_w,vtw=vtw,ms=ms,strict=strict,
                ngates=len(gates),ndistinct_calls=len(distinct_calls),guard_loose=guard_loose,
                distinct_calls=distinct_calls[:12])

if __name__=='__main__':
    res={}
    for e in CAND:
        res[e]=analyze(e); r=res[e]
        print("%s %-36s strict=%s loose=%s jt=%d err=%d loop=%d ms=%s(w%d,vt%d) gates=%d callees=%d" %
              (e,r['name'][:36],r['strict'],r['guard_loose'],len(r['jt']),len(r['err']),len(r['loops']),r['ms'],r['memshape_w'],r['vtw'],r['ngates'],r['ndistinct_calls']))
    json.dump(res,open(os.path.join(os.path.dirname(__file__),'detect2.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
