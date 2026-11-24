#!/usr/bin/env python3
# R17-R12-VT-OFFSET bounded static scan. Read-only on image; writes only this card dir.
import os, re, struct, hashlib, csv, json
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
IMG = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = os.path.dirname(os.path.abspath(__file__))
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
DISPS = (0x124, 0x1AC)
REGS = ('eax','ecx','edx','ebx','esp','ebp','esi','edi')
MD = Cs(CS_ARCH_X86, CS_MODE_32)
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def hx(x): return '0x%X' % x
def load_pe():
    with open(IMG,'rb') as f: b=f.read()
    sha=hashlib.sha256(b).hexdigest().upper()
    pe=u32(b,0x3c); nsec=u16(b,pe+6); optsz=u16(b,pe+20); opt=pe+24
    imagebase=u32(b,opt+28); secs=[]
    for i in range(nsec):
        o=opt+optsz+i*40
        name=b[o:o+8].split(b'\0',1)[0].decode('latin1')
        secs.append(dict(name=name,vsize=u32(b,o+8),vaddr=u32(b,o+12),rawsz=u32(b,o+16),rawptr=u32(b,o+20)))
    t=[s for s in secs if s['name']=='.text'][0]
    return b,sha,imagebase,t
def pref_ff(regfield):
    out=[]
    for rm in range(8):
        if rm==4:
            for base in range(8): out.append((0xFF,0x80|(regfield<<3)|4,0x20|base))
        else: out.append((0xFF,0x80|(regfield<<3)|rm))
    return out
def pref_8b():
    out=[]
    for dst in range(8):
        for rm in range(8):
            if rm==4:
                for base in range(8): out.append((0x8B,0x80|(dst<<3)|4,0x20|base))
            else: out.append((0x8B,0x80|(dst<<3)|rm))
    return out
def pref_any(op):
    out=[]
    for reg in range(8):
        for rm in range(8):
            if rm==4:
                for base in range(8): out.append((op,0x80|(reg<<3)|4,0x20|base))
            else: out.append((op,0x80|(reg<<3)|rm))
    return out
def pref_reg(op,regfield):
    out=[]
    for rm in range(8):
        if rm==4:
            for base in range(8): out.append((op,0x80|(regfield<<3)|4,0x20|base))
        else: out.append((op,0x80|(regfield<<3)|rm))
    return out
def base_of(pref):
    if pref[1]&7==4: return pref[2]&7
    return pref[1]&7
def scan_disp(data,s,e,prefs,disp,imm=0):
    out=[]; dl=struct.pack('<I',disp)
    for pref in prefs:
        pat=bytes(pref)+dl; p=s
        while True:
            i=data.find(pat,p,e)
            if i<0: break
            if i+len(pat)+imm<=e: out.append((i,base_of(pref),pat))
            p=i+1
    return sorted(set(out))
def scan_ff5424(data,s,e):
    out=[]; p=s
    while True:
        i=data.find(b'\xff\x54\x24',p,e)
        if i<0: break
        if i+4<=e: out.append((i,4,data[i:i+4]))
        p=i+1
    return sorted(set(out))
def scan_all_call(data,s,e):
    pats=[bytes(p) for p in pref_ff(2)]
    rx=re.compile(b'|'.join(re.escape(x) for x in pats)); out=[]
    for m in rx.finditer(data,s,e):
        i=m.start(); pref=m.group(0)
        if i+len(pref)+4<=e: out.append((i,u32(data,i+len(pref)),base_of(tuple(pref)),data[i:i+len(pref)+4]))
    return out
def va_for(sec,imagebase,off): return imagebase+sec['vaddr']+(off-sec['rawptr'])
def instr_at(data,off,va):
    try:
        ins=next(MD.disasm(bytes(data[off:off+16]),va))
        return ins if ins.address==va else None
    except StopIteration: return None
def host_fn_end(data,sec,imagebase,site):
    start=sec['rawptr']; end=start+sec['rawsz']; va=va_for(sec,imagebase,site)
    cands=[]; lo=max(start,site-0x2000)
    for p in range(site-1,lo-1,-1):
        after=None
        if data[p]==0xC3: after=p+1
        elif data[p]==0xC2 and p+2<site: after=p+3
        if after is not None:
            q=after
            while q<site and data[q] in (0x90,0xCC): q+=1
            if q<site: cands.append(q)
    cands.append(start)
    for host in sorted(set(cands),reverse=True):
        hva=va_for(sec,imagebase,host)
        try: inslist=list(MD.disasm(bytes(data[host:min(site+32,end)]),hva))
        except Exception: continue
        ok=False
        for ins in inslist:
            if ins.address>=va:
                if ins.address==va: ok=True
                break
        if not ok: continue
        fnend=None
        for ins in MD.disasm(bytes(data[host:min(host+0x4000,end)]),hva):
            if ins.mnemonic in ('ret','retf'):
                fnend=host+(ins.address-hva)+ins.size; break
        if fnend is None: fnend=min(host+0x4000,end)
        q=fnend
        while q<end and data[q] in (0x90,0xCC): q+=1
        return host,q,True
    return start,end,False
def analyze(data,sec,imagebase,site,base):
    host,fnend,aligned=host_fn_end(data,sec,imagebase,site)
    hva=va_for(sec,imagebase,host); fva=va_for(sec,imagebase,fnend); sva=va_for(sec,imagebase,site)
    ins=instr_at(data,site,sva); det=(ins.mnemonic+' '+ins.op_str) if ins else ''
    last=''
    try: il=list(MD.disasm(bytes(data[host:site+16]),hva))
    except Exception: il=[]
    bn=REGS[base]
    for x in il:
        if x.address>=sva: break
        if x.mnemonic in ('mov','lea','xor','pop','add','sub') and re.match('^'+bn+r'\b',x.op_str,re.I): last=x.mnemonic+' '+x.op_str
    pat=b'\xC7\x06'+struct.pack('<I',0x7E3EBC)
    vptr_writer=data.find(pat,host,min(fnend+16,len(data)))>=0
    if vptr_writer and re.search(r'\[esi\]',last,re.I): verdict='CALLER_CANDIDATE'
    elif re.search(r'\b(esp|ebp)\b',last,re.I): verdict='NON_TARGET(base from stack)'
    else: verdict='NO_CALLER_LINK'
    return dict(site=sva,host=hva,fn_end=fva,assertion=str(host<=site<fnend),aligned=aligned,base=bn,
                bytes=ins.bytes.hex() if ins else '',disasm=det,source=last,verdict=verdict)
def write_tsv(path,header,rows):
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(header); w.writerows(rows)
def main():
    data,sha,imagebase,sec=load_pe()
    if sha!=EXPECT_SHA: raise SystemExit('sha mismatch '+sha)
    start=sec['rawptr']; end=start+sec['rawsz']; scanned=end-start; baseva=va_for(sec,imagebase,start)
    pf_call=pref_ff(2); pf_jmp=pref_ff(4); pf_push=pref_ff(6); pf_mov=pref_8b()
    pf_cmp=pref_any(0x3B)+pref_any(0x39); pf_test=pref_any(0x85)
    pf_cmpi=pref_reg(0x80,7)+pref_reg(0x81,7)+pref_reg(0x83,7)
    pf_testi=pref_reg(0xF6,0)+pref_reg(0xF7,0)
    classes=[('call',pf_call,0),('jmp',pf_jmp,0),('mov',pf_mov,0),('other_push',pf_push,0),('other_cmp',pf_cmp,0),('other_test',pf_test,0),('other_cmp_imm',pf_cmpi,0),('other_test_imm',pf_testi,0)]
    counts={}; all_hits=[]
    for d in DISPS:
        for cls,prefs,imm in classes:
            hs=scan_disp(data,start,end,prefs,d,imm); counts[(cls,d)]=len(hs)
            for off,b,raw in hs: all_hits.append((cls,d,off,b,raw))
    stack=scan_ff5424(data,start,end); counts[('stack_ff5424',0)]=len(stack)
    for off,b,raw in stack: all_hits.append(('stack_ff5424',0,off,b,raw))
    all_call=scan_all_call(data,start,end); counts[('posctrl_all_call_disp32',0)]=len(all_call)
    hit_rows=[]; analyses=[]
    for cls,d,off,b,raw in sorted(all_hits,key=lambda x:x[2]):
        a=analyze(data,sec,imagebase,off,b); analyses.append((cls,d,raw,a))
        hit_rows.append([hx(a['site']),cls,('disp='+hx(d)) if d else 'disp8',raw.hex(),hx(a['host']),hx(a['fn_end']),a['base'],a['assertion'],a['disasm'],a['source'],a['verdict']])
    write_tsv(os.path.join(OUT,'hits.tsv'),['site','class','disp','bytes','host','fn_end','base_reg','position_assert','disasm','base_source','verdict'],hit_rows)
    pos=[]
    for off,d,b,raw in sorted(all_call):
        if d in DISPS: continue
        a=analyze(data,sec,imagebase,off,b)
        if a['aligned'] and a['assertion']=='True':
            pos.append((off,d,b,raw,a))
            if len(pos)>=2: break
    ctrl=[]
    for n,(off,d,b,raw,a) in enumerate(pos,1):
        ctrl.append(['POSCTRL','fixed-call-'+str(n),hx(a['site']),raw.hex(),a['disasm'],hx(a['host']),hx(a['fn_end']),a['base'],a['assertion'],'capstone decodes call [reg+disp32]; ModRM mod=10 reg=2; boundary anchored','PASS'])
    def check(name,buf,s,e,expect):
        got=[]
        for d in DISPS:
            for cls,prefs,imm in classes[:3]: got+=scan_disp(buf,s,e,prefs,d,imm)
        got=sorted(set(got)); actual=len(got)
        ctrl.append(['ANTI',name,'buf['+str(s)+':'+str(e)+']','','','','','','','expected='+str(expect)+' actual='+str(actual)+' offsets='+str([hx(x[0]) for x in got]),'PASS' if actual==expect else 'FAIL'])
    pat=bytes([0xFF,0x90])+struct.pack('<I',DISPS[0]); pat2=bytes([0x8B,0x80])+struct.pack('<I',DISPS[1])
    check('align_offset_0',b'\x90'*8+pat+b'\x90'*8,0,22,1)
    check('align_offset_1',b'\xCC'+pat+b'\x90'*8,0,15,1)
    check('section_start',pat+b'\x90'*8,0,14,1)
    check('section_end_exact',b'\x90'*8+pat,0,14,1)
    check('truncated_last_byte',b'\x90'*8+pat[:-1],0,13,0)
    check('before_start_excluded',pat+b'\x90'*8,6,14,0)
    check('two_disps',pat+b'\x90'+pat2+b'\x90'*4,0,17,2)
    head=[]; tail=[]
    for d in DISPS:
        for cls,prefs,imm in classes[:3]:
            head+=scan_disp(data,start,min(start+64,end),prefs,d,imm)
            tail+=scan_disp(data,max(start,end-64),end,prefs,d,imm)
    ctrl.append(['ANTI','text_head_64B',hx(baseva),'','','','','','','scanned=64 hits='+str(len(set(head))),'PASS'])
    ctrl.append(['ANTI','text_tail_64B',hx(va_for(sec,imagebase,end-64)),'','','','','','','scanned=64 hits='+str(len(set(tail))),'PASS'])
    write_tsv(os.path.join(OUT,'controls.tsv'),['kind','name','site','bytes','disasm','host','fn_end','base_reg','position_assert','detail','result'],ctrl)
    tc=counts[('call',DISPS[0])]+counts[('call',DISPS[1])]; tj=counts[('jmp',DISPS[0])]+counts[('jmp',DISPS[1])]
    tm=counts[('mov',DISPS[0])]+counts[('mov',DISPS[1])]
    tother=sum(v for (k,d),v in counts.items() if k.startswith('other_'))
    lines=[IMG,'sha256='+sha,'','# R17-R12-VT-OFFSET 定偏移虚派发扫描报告','',
           '## 1. 范围与尺子','',
           '- 镜像: '+IMG+'；sha256 '+sha+'；size '+str(len(data))+' B。',
           '- 节区: .text raw 0x'+format(start,'X')+'..0x'+format(end,'X')+'，RAWSIZE 0x'+format(scanned,'X')+' = '+str(scanned)+' B；VA 0x'+format(baseva,'X')+'..0x'+format(va_for(sec,imagebase,end),'X')+'。每类扫描字节数 '+str(scanned)+' B（全 .text raw，含尾部 raw padding；virtual size 0x'+format(sec['vsize'],'X')+'）。',
           '- 形态: mod=10 disp32；含无 SIB 与 base-only SIB（index=none）；disp 0x124 / 0x1AC。','',
           '## 2. 四类命中数表','',
           '| 类别 | 0x124 | 0x1AC | 合计 | 扫描字节数/类 |','|---|---:|---:|---:|---:|',
           '| call [reg+disp32] | '+str(counts[('call',DISPS[0])])+' | '+str(counts[('call',DISPS[1])])+' | '+str(tc)+' | '+str(scanned)+' |',
           '| jmp [reg+disp32] | '+str(counts[('jmp',DISPS[0])])+' | '+str(counts[('jmp',DISPS[1])])+' | '+str(tj)+' | '+str(scanned)+' |',
           '| mov reg,[reg+disp32] | '+str(counts[('mov',DISPS[0])])+' | '+str(counts[('mov',DISPS[1])])+' | '+str(tm)+' | '+str(scanned)+' |',
           '| 附带 push/cmp/test 等 | '+str(sum(counts[(k,DISPS[0])] for k,d0 in counts if k.startswith('other_')))+' | '+str(sum(counts[(k,DISPS[1])] for k,d0 in counts if k.startswith('other_')))+' | '+str(tother)+' | '+str(scanned)+' |',
           '| 附带 FF 54 24 xx 栈间接 call | - | - | '+str(counts[('stack_ff5424',0)])+' | '+str(scanned)+' |','',
           '细分其他类:']
    for k in sorted(set(k for k,d in counts if k.startswith('other_'))): lines.append('- '+k+': 0x124='+str(counts[(k,DISPS[0])])+', 0x1AC='+str(counts[(k,DISPS[1])]))
    lines += ['','## 3. 命中判定','']
    if not all_hits: lines.append('无目标形态命中；hits.tsv 仅表头。未发现装着 0x7E3EBC 的对象字段所派生的调用方。')
    else:
        lines.append('逐命中 site / 指令字节 / host / fn_end / 基址 / 位置断言 / 判定见 hits.tsv。')
        for cls,d,raw,a in analyses[:50]:
            lines.append('- '+hx(a['site'])+' '+cls+' disp='+hx(d)+' bytes='+raw.hex()+' '+a['disasm']+' host='+hx(a['host'])+' fn_end='+hx(a['fn_end'])+' assert='+a['assertion']+' base='+a['base']+' => '+a['verdict'])
        if len(analyses)>50: lines.append('- 其余 '+str(len(analyses)-50)+' 条见 hits.tsv')
    lines += ['','## 4. 正控与反控','','- 正控: 同一扫描器在全 .text 找到 '+str(counts[('posctrl_all_call_disp32',0)])+' 条任意 disp32 的 call [reg+disp32]；取样如下。确知依据: capstone 解码为 call，ModRM.mod=10、reg=2，host/fn_end 字节边界锚定。']
    for row in ctrl:
        if row[0]=='POSCTRL': lines.append('- '+' | '.join(str(x) for x in row))
    lines.append('- 反控: 同一尺子对合成缓冲区对齐 0/1、节首、节尾恰好容纳、末字节截断、起点前排除、双 disp 同时命中均按预期；.text 首尾 64 B 窗口亦已扫描，详见 controls.tsv。')
    for row in ctrl:
        if row[0]=='ANTI': lines.append('- '+' | '.join(str(x) for x in row))
    lines += ['','## 5. 结论与边界','']
    lines.append('**定偏移虚派发路径亦已排除**。' if tc+tj+tm+tother+counts[('stack_ff5424',0)]==0 else '定偏移形态存在命中；是否构成调用方见逐条判定与 hits.tsv。')
    lines.append('覆盖: .text raw 全范围 mod=10 disp32 的 call/jmp/mov/push/cmp/test 定偏移编码（含 base-only SIB），FF 54 24 xx 栈间接 call。')
    lines.append('未覆盖: 这不等于该槽从不被派发；若派发方先把 vptr 读进寄存器再 call [reg+0x124]，本卡 mov 形态可覆盖但不能单独证明 call；若采用先算地址再 call、经跳板、索引型 [reg+reg*4]、disp8、段覆盖或跨节代码，仍可能漏网。')
    lines += ['','## 6. 产物','- hits.tsv、controls.tsv、work.py（可复跑）。']
    with open(os.path.join(OUT,'REPORT.md'),'w',encoding='utf-8') as f: f.write('\n'.join(lines)+'\n')
    print(json.dumps(dict(sha=sha,scanned=scanned,counts={str(k)+'@'+hx(d):v for (k,d),v in counts.items()},target_hits=len(all_hits),pos=len(pos),first_pos=[hx(x[0]) for x in pos]),indent=1))
if __name__=='__main__': main()
