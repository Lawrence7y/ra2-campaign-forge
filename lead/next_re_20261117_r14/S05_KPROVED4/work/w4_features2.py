# -*- coding: utf-8 -*-
"""S05-KPROVED4 · 精确 ③b 特征扫描：返回码集 / 跳表 / 回边循环+写 / -1 哨兵后续动作。"""
import json, capstone, ax_lib

CAND = [
 "0040BA50","0040CDC0","00410220","00410230","00410BE0","0050EA00","00512D30",
 "00513100","005134D0","005F9720","005F9950","006F3F40","006F4A70","006F6CA0",
 "006FFBE0","00703860","00704350","00708D70","00709A30","00709A40","0070C250",
 "0070E280","0070E2B0","00711EB0","00711F00","007171A0",
]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
md.skipdata=True; md.detail=False

def disasm(pe,e,n=0x4000):
    code=pe.bytes_at(e,n); out=[]
    for i in md.disasm(code,e):
        out.append(i)
        if i.mnemonic in ('ret','retf') and len(out)>3:
            nxt=i.address+i.size; tail=pe.bytes_at(nxt,16) or b''
            if sum(1 for b in tail[:8] if b in (0xCC,0x90))>=5: break
    return out

def analyze(ent):
    pe=ax_lib.load(); e=int(ent,16); ins=disasm(pe,e)
    addrs=[i.address for i in ins]
    retconsts=[]; jmptables=[]; backedges=[]; sentinel1=[]; retlist=[]
    for k,i in enumerate(ins):
        off=i.address-e; m=i.mnemonic; o=i.op_str
        if m in ('ret','retf') or m.startswith('ret '):
            retlist.append(off)
            # 往前找最近的 mov eax,imm / mov al,imm / xor eax,eax
            for j in range(k-1,max(-1,k-9),-1):
                p=ins[j]; po=p.op_str
                if p.mnemonic=='mov' and (po.startswith('eax,') or po.startswith('al,')) and '0x' in po:
                    retconsts.append((hex(off),hex(p.address-e),po)); break
                if p.mnemonic in ('xor','sub') and po.startswith('eax,eax'):
                    retconsts.append((hex(off),hex(p.address-e),'eax=0')); break
                if p.mnemonic=='lea' and ',[ecx' in po or (p.mnemonic=='mov' and p.op_str.startswith('eax,ecx')):
                    break
        if m=='jmp' and '[' in o and ('*' in o or 'dword' in o):
            jmptables.append((hex(off),m,o))
        if m.startswith('j'):
            # 目标解析
            tok=o.replace('0x','')
            try:
                tgt=int(tok,16)
                if tgt<=i.address and tgt>=e:
                    backedges.append((hex(off),m,o,hex(tgt-e)))
            except: pass
        if m.startswith('cmp') and ('-1' in o):
            sentinel1.append((hex(off),m,o))
    # distinct ret consts
    consts=sorted({c[2] for c in retconsts})
    return dict(size=hex(ins[-1].address+ins[-1].size-e),n=len(ins),
                n_ret=len(retlist), n_retconst=len(retconsts), consts=consts,
                n_jmptable=len(jmptables), jmptables=jmptables[:10],
                n_back=len(backedges), backedges=backedges[:12],
                n_sent1=len(sentinel1), sent1=sentinel1[:12])

if __name__=='__main__':
    out={}
    for ent in CAND:
        r=analyze(ent); out[ent]=r
        print('%s size=%-8s n=%-4d ret=%-3d retconst=%-2d jmptbl=%-2d back=%-2d sent1=%d consts=%s' %
              (ent,r['size'],r['n'],r['n_ret'],r['n_retconst'],r['n_jmptable'],r['n_back'],r['n_sent1'],r['consts'][:12]))
    with open('features2.json','w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=1)
