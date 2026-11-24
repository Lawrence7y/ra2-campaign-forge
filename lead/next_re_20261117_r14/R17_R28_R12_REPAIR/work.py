#!/usr/bin/env python3
# R17-R28-R12-REPAIR: trusted-entry host/fn_end reattribution + Q1-Q4. Static read-only on image.
import os, re, csv, json, struct, hashlib, collections, bisect
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

IMG = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
R12 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R12_VT_OFFSET"
OUT = os.path.dirname(os.path.abspath(__file__))
EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
DISPS = (0x124, 0x1AC)
REGS = ('eax','ecx','edx','ebx','esp','ebp','esi','edi')
# Known ctor entries from R17-R11-CTOR-CHAIN plus the R17-R26 anchored host.
KNOWN_CTORS = {0x43B680,0x43B740,0x6F2B40,0x65A750,0x5B2DA0,0x6F4300,0x65A7E0,0x5F3B50,0x5A6510}
MD = Cs(CS_ARCH_X86, CS_MODE_32)

def hx(x): return '0x%X' % x if x is not None else 'UNRESOLVED'

def load():
    b=open(IMG,'rb').read()
    sha=hashlib.sha256(b).hexdigest().upper()
    if sha!=EXPECT: raise SystemExit('SHA MISMATCH '+sha)
    pe=pefile.PE(data=b)
    IB=pe.OPTIONAL_HEADER.ImageBase
    secs={}
    for s in pe.sections:
        n=s.Name.decode('latin1').rstrip('\0')
        secs[n]=dict(va=IB+s.VirtualAddress,rva=s.VirtualAddress,raw=s.PointerToRawData,size=s.SizeOfRawData,vsize=s.Misc_VirtualSize)
    return b,sha,IB,secs

def off_va(b,secs,va):
    r=va-secs['.text']['va']+secs['.text']['rva']
    for n,s in secs.items():
        if s['rva']<=r<s['rva']+s['size']:
            return s['raw']+(r-s['rva'])
    return None

def u32(b,o): return struct.unpack_from('<I',b,o)[0] if o is not None and 0<=o+4<=len(b) else None

def collect_vtable_entries(b,secs):
    # Exact R17-R26 RTTI chain: .data TD -> .rdata COL -> vtable[-4] -> contiguous .text slot values.
    text,rdata,data=secs['.text'],secs['.rdata'],secs['.data']
    code_lo,code_hi=text['va'],text['va']+text['vsize']
    printable=bytes(range(0x20,0x7f))
    def u32va(va): return u32(b,off_va(b,secs,va))
    td={}
    raw_da,end_da=data['raw'],data['raw']+data['size']
    for o in range(raw_da,end_da-8):
        if b[o:o+3]!=b'.?A': continue
        j=o+3
        while j<end_da and b[j] in printable and j-o<300: j+=1
        if j>=end_da or b[j]!=0 or j-o<8: continue
        name_va=data['va']+(o-raw_da)
        tdva=name_va-8
        vf=u32va(tdva); spare=u32va(tdva+4)
        if vf==0x7F9594 and spare==0: td.setdefault(tdva,b[o:j].decode('ascii'))
    col={}
    raw_rd,end_rd=rdata['raw'],rdata['raw']+rdata['size']
    for o in range(raw_rd,end_rd-24,4):
        ptd=u32(b,o+12)
        if ptd not in td: continue
        cd=u32(b,o+16); co=off_va(b,secs,cd)
        if co is None or co+16>len(b): continue
        sig,attr,nbases,basearr=struct.unpack_from('<IIII',b,co)
        if sig==0 and attr<0x100 and 0<nbases<0x1000 and off_va(b,secs,basearr) is not None:
            col.setdefault(rdata['va']+(o-raw_rd),td[ptd])
    entries=set(); vtables=0; slots=0
    for o in range(raw_rd,end_rd-4,4):
        c=u32(b,o)
        if c not in col: continue
        vbase=rdata['va']+(o-raw_rd+4)
        vo=off_va(b,secs,vbase)
        if vo is None or vo<raw_rd or vo>=end_rd: continue
        n=0; p=vo
        while p+4<=end_rd:
            v=u32(b,p)
            if v is None or not (code_lo<=v<code_hi): break
            entries.add(v); n+=1; p+=4
        if n: vtables+=1
        slots+=n
    return sorted(entries),dict(td=len(td),col=len(col),vtables=vtables,slots=slots,rdata_bytes=end_rd-raw_rd,data_bytes=end_da-raw_da)

def read_hits():
    with open(os.path.join(R12,'hits.tsv'),newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f,delimiter='\t'))

def collect_structural_entries(b,secs):
    # Additional trusted starts: direct E8 rel32 call targets and starts after structural padding.
    # These are instruction-boundary anchors, not C3/C2 byte scans.
    t=secs['.text']; s=t['raw']; e=s+t['size']; code_lo=t['va']; code_hi=t['va']+t['vsize']
    out=set(); calls=0
    for i in range(s,e-4):
        if b[i]!=0xE8: continue
        site=code_lo+(i-s); rel=struct.unpack_from('<i',b,i+1)[0]; dst=site+5+rel
        if code_lo<=dst<code_hi:
            out.add(dst); calls+=1
    i=s
    pads=0
    while i<len(b):
        c=b[i]
        if c in (0x90,0xCC):
            j=i
            while j<len(b) and b[j]==c: j+=1
            if (c==0x90 and j-i>=4) or (c==0xCC and j-i>=2):
                va=code_lo+(j-s)
                if code_lo<=va<code_hi: out.add(va); pads+=1
            i=j
        else: i+=1
    return sorted(out),dict(direct_call_targets=calls,padding_starts=pads)

def validate_candidate(b,secs,e,site):
    off=off_va(b,secs,e)
    if off is None: return None
    t=secs['.text']; maxoff=min(t['raw']+t['size'],off+0x8000)
    reach=False
    for ins in MD.disasm(b[off:maxoff],e):
        if ins.address==site: reach=True
        if ins.mnemonic in ('ret','retf'):
            return ins.address+ins.size if reach else None
    return None

def build_entry_map(b,secs,entries):
    text=secs['.text']; code_hi=text['va']+text['size']
    site_set={int(r['site'],16) for r in read_hits()}
    info={}
    # Strict linear decode from each trusted entry to its first decoded ret; no C3/C2 byte search.
    for e in entries:
        off=off_va(b,secs,e)
        if off is None or off>=text['raw']+text['size']: continue
        maxoff=min(text['raw']+text['size'],off+0x8000)
        bounds=set(); fnend=None
        for ins in MD.disasm(b[off:maxoff],e):
            if ins.address in site_set: bounds.add(ins.address)
            if ins.mnemonic in ('ret','retf'):
                fnend=ins.address+ins.size
                break
        if fnend is not None and fnend<=code_hi:
            info[e]=dict(fnend=fnend,bounds=bounds)
    site_host={}
    for e,ii in info.items():
        for s in ii['bounds']:
            if e<=s<ii['fnend']:
                # nearest trusted entry wins
                if s not in site_host or e<site_host[s]: site_host[s]=e
    return info,site_host

def source_at(b,secs,host,site,base_reg):
    off=off_va(b,secs,host); endoff=off_va(b,secs,site)+16
    last=''; bn=base_reg.lower()
    if off is None or endoff is None: return last
    for x in MD.disasm(b[off:min(endoff,len(b))],host):
        if x.address>=site: break
        if x.mnemonic in ('mov','lea','xor','pop','add','sub') and re.match(r'^'+bn+r'\b',x.op_str,re.I):
            last=x.mnemonic+' '+x.op_str
    return last

def vptr_writer(b,secs,host,fnend):
    ho=off_va(b,secs,host); fo=off_va(b,secs,fnend)
    if ho is None or fo is None: return False
    pat=b'\xC7\x06'+struct.pack('<I',0x7E3EBC)
    return b.find(pat,ho,min(fo+16,len(b)))>=0

def stackish(src):
    return bool(re.search(r'\b(esp|ebp)\b',src,re.I))

def objectish(src,base_reg):
    # object/register transfer: base register loaded from object pointer/member rather than a raw stack slot.
    s=src.lower(); br=base_reg.lower()
    if not s: return False
    if re.match(r'^(mov|lea)\s+'+re.escape(br)+r'\b',s):
        # ebp/esp appears only as a pointer source, not as the destination base register.
        if br not in ('ebp','esp') and stackish(s):
            # [ebp] / [ebp+positive] / [esp+...] member or vptr load counts as object-derived unless a stack-local marker is explicit.
            if re.search(r'\[ebp\s*\]|\[ebp\s*\+\s*0x',s): return True
            if re.search(r'\[ebp\s*-\s*0x',s): return False
            if re.search(r'\[esp\s*\+',s): return False
            if re.search(r'\b(eax|ecx|edx|ebx|esi|edi)\b',s): return True
        if not stackish(s) and re.search(r'\b(eax|ecx|edx|ebx|esi|edi)\b',s): return True
    return False

def corrected_verdict(src,base_reg,has_writer):
    if has_writer and re.search(r'\[esi\]',src,re.I): return 'CALLER_CANDIDATE'
    if base_reg.lower() in ('esp','ebp'): return 'NON_TARGET(base from stack)'
    if stackish(src) and not objectish(src,base_reg): return 'NON_TARGET(base from stack)'
    return 'NO_CALLER_LINK'

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
def scan_disp(data,s,e,prefs,disp):
    out=[]; dl=struct.pack('<I',disp)
    for pref in prefs:
        pat=bytes(pref)+dl; p=s
        while True:
            i=data.find(pat,p,e)
            if i<0: break
            out.append(i); p=i+1
    return set(out)
def recount_shapes(b,secs):
    t=secs['.text']; s=t['raw']; e=s+t['size']
    pf_call=pref_ff(2); pf_jmp=pref_ff(4); pf_mov=pref_8b()
    pf_cmp=pref_any(0x3B)+pref_any(0x39); pf_test=pref_any(0x85)
    pf_cmpi=pref_reg(0x80,7)+pref_reg(0x81,7)+pref_reg(0x83,7)
    pf_testi=pref_reg(0xF6,0)+pref_reg(0xF7,0)
    c={}
    for name,prefs in [('call',pf_call),('jmp',pf_jmp),('mov',pf_mov),('other_cmp',pf_cmp),('other_test',pf_test),('other_cmp_imm',pf_cmpi),('other_test_imm',pf_testi)]:
        for d in DISPS:
            c[(name,d)]=len(scan_disp(b,s,e,prefs,d))
    c[('stack_ff5424',0)]=len(set(i for i in range(s,e-3) if b[i:i+3]==b'\xff\x54\x24'))
    return c,t['size']

def write_tsv(path,header,rows):
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(header); w.writerows(rows)

def main():
    b,sha,IB,secs=load()
    entries,vinfo=collect_vtable_entries(b,secs)
    known=sorted(x for x in KNOWN_CTORS if secs['.text']['va']<=x<secs['.text']['va']+secs['.text']['vsize'])
    struct_entries,sentry=collect_structural_entries(b,secs)
    all_entries=sorted(set(entries)|set(known)|set(struct_entries))
    with open(os.path.join(OUT,'entries.json'),'w',encoding='utf-8') as f:
        json.dump(dict(image=IMG,sha256=sha,image_base=hx(IB),vtable_count=vinfo['vtables'],vtable_slot_count=vinfo['slots'],vtable_unique_entry_count=len(entries),known_ctors=[hx(x) for x in known],structural_entry_count=len(struct_entries),structural=sentry,total_entry_count=len(all_entries),rdata_bytes=vinfo['rdata_bytes'],data_bytes=vinfo['data_bytes']),f,indent=2)
    rows=read_hits()
    info,site_host=build_entry_map(b,secs,all_entries)
    legacy=set()
    for r in rows:
        site=int(r['site'],16)
        if site in site_host: continue
        cand=int(r['host'],16)
        if validate_candidate(b,secs,cand,site) is not None: legacy.add(cand)
    if legacy:
        all_entries=sorted(set(all_entries)|legacy)
        info,site_host=build_entry_map(b,secs,all_entries)
    out=[]; host_ch=[]; end_ch=[]; assert_flips=[]; nonstack=[]; unresolved=[]
    for r in rows:
        site=int(r['site'],16); base=r['base_reg']; oldh=r['host']; olde=r['fn_end']
        h=site_host.get(site)
        if h is None:
            unresolved.append(r['site'])
            nh=oldh; nf=olde; na=r['position_assert']; nsrc=r['base_source']; nv='UNRESOLVED'; reason='trusted-entry decode unresolved'
        else:
            fn=info[h]['fnend']
            nh=hx(h); nf=hx(fn); na=str(bool(h<=site<fn))
            nsrc=source_at(b,secs,h,site,base)
            nv=corrected_verdict(nsrc,base,vptr_writer(b,secs,h,fn))
            reason=[]
            if nh!=oldh: reason.append('host: trusted entry + strict decode (no C3/C2 byte scan)')
            if nf!=olde: reason.append('fn_end: first decoded ret end from trusted entry')
            if na!=r['position_assert']: reason.append('position_assert recomputed')
            if nv!=r['verdict']: reason.append('verdict recomputed from corrected host/source')
            reason='; '.join(reason) if reason else 'unchanged'
        if nh!=oldh: host_ch.append(r)
        if nf!=olde: end_ch.append(r)
        if na!=r['position_assert']: assert_flips.append((r,na))
        if r['verdict']=='NON_TARGET(base from stack)' and nv!='NON_TARGET(base from stack)':
            nonstack.append((r,nsrc,nv))
        out.append([r['site'],r['class'],r['disp'],oldh,nh,olde,nf,r['verdict'],nv,reason,nsrc])
    write_tsv(os.path.join(OUT,'host_fix.tsv'),['site','class','disp','old_host','new_host','old_fn_end','new_fn_end','old_verdict','suggested_verdict','change_reason','recomputed_base_source'],out)
    counts,text_bytes=recount_shapes(b,secs)
    exp={( 'call',0x124):181,('call',0x1AC):86,('jmp',0x124):0,('jmp',0x1AC):0,('mov',0x124):55,('mov',0x1AC):15,('other_cmp',0x124):1,('other_cmp',0x1AC):0,('other_cmp_imm',0x124):0,('other_cmp_imm',0x1AC):0,('other_test',0x124):0,('other_test',0x1AC):0,('other_test_imm',0x124):7,('other_test_imm',0x1AC):0,('stack_ff5424',0):9}
    stats=[]
    def add(kind,group,metric,value,detail=''):
        stats.append([kind,group,metric,value,detail])
    add('Q1','ALL','rows',len(rows))
    add('Q1','ALL','host_changed',len(host_ch))
    add('Q1','ALL','fn_end_changed',len(end_ch))
    add('Q1','ALL','assert_flipped',len(assert_flips))
    add('Q1','ALL','unresolved',len(unresolved),','.join(unresolved))
    for cls in sorted({r['class'] for r in rows}):
        sub=[r for r in rows if r['class']==cls]
        hs=sum(1 for r in sub if site_host.get(int(r['site'],16)) is not None and hx(site_host[int(r['site'],16)])!=r['host'])
        es=sum(1 for r in sub if (site_host.get(int(r['site'],16)) is not None and hx(info[site_host[int(r['site'],16)]]['fnend'])!=r['fn_end']))
        af=sum(1 for r,n in assert_flips if r['class']==cls)
        add('Q1',cls,'rows',len(sub)); add('Q1',cls,'host_changed',hs); add('Q1',cls,'fn_end_changed',es); add('Q1',cls,'assert_flipped',af)
    empty=sum(1 for r in rows if not r['base_source'].strip())
    ns=sum(1 for r in rows if r['verdict']=='NON_TARGET(base from stack)')
    add('Q2','ALL','base_source_empty',empty)
    add('Q2','ALL','verdict_non_target_stack',ns)
    add('Q2','ALL','non_target_reclassified',len(nonstack))
    for r,src,nv in nonstack:
        add('Q2','MISJUDGED',r['site'],1,r['base_reg']+' | '+r['base_source']+' => '+src+' | '+nv)
    add('Q3','ALL','rows_written',len(out))
    for k,v in sorted(counts.items()):
        d=k[1]
        add('Q4',k[0]+('@'+hx(d) if d else ''),'recount',v,'expected='+str(exp.get(k,'?')))
    add('SCAN','image','sha256',sha)
    add('SCAN','.text','bytes',secs['.text']['size'])
    add('SCAN','.rdata','bytes',vinfo['rdata_bytes'])
    add('SCAN','.data','bytes',vinfo['data_bytes'])
    write_tsv(os.path.join(OUT,'stats.tsv'),['section','group','metric','value','detail'],stats)
    result=dict(sha256=sha,image_base=hx(IB),rows=len(rows),host_changed=len(host_ch),fn_end_changed=len(end_ch),assert_flipped=len(assert_flips),unresolved=unresolved,base_source_empty=empty,non_target_stack=ns,non_target_reclassified=len(nonstack),counts={str(k):v for k,v in counts.items()},expected_match=all(counts.get(k)==v for k,v in exp.items()),vinfo=vinfo,total_entries=len(all_entries),structural=sentry,known_ctors=[hx(x) for x in known])
    with open(os.path.join(OUT,'interim.json'),'w',encoding='utf-8') as f: json.dump(result,f,indent=2,ensure_ascii=False)
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__': main()
