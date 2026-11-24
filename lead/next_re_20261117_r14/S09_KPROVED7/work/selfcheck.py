"""Self-check v2: only validate instruction-relative anchors (leading +0xNN of each
anchor token in the '锚 ...；④' section) against EVIDENCE; field/slot/vtable offsets
like [ecx+0x30] or +0x88 are operands/disk text, not instruction anchors."""
import sys, io, json, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
D = BASE + r'\S09_KPROVED7'
EV = D + r'\EVIDENCE'
rows=[l.rstrip('\n').split('\t') for l in open(D+r'\coverage_delta.tsv',encoding='utf-8')]
data=rows[1:]
print('delta data rows =',len(data))
forb=['未证','未定','弱信号','线索','槽语义']
fail=0
for p in data:
    entry,sub,name,sem,grade,evp=p
    cls=name.split('::')[0]
    hits=[w for w in forb if w in sem]
    if hits: print('FAIL forbidden',entry,hits); fail+=1
    if ('归共同基类%s、name栏同类'%cls) not in sem:
        print('FAIL name/② class mismatch',entry,cls); fail+=1
    if grade!='[已证]': print('FAIL grade',entry,grade); fail+=1
    for f in evp.split(';'):
        if not os.path.exists(D+'\\'+f.replace('/','\\')):
            print('FAIL missing evidence',entry,f); fail+=1
    # anchor section only
    m=re.search(r'锚 (.*?)；④',sem)
    if not m: print('FAIL no anchor section',entry); fail+=1; continue
    anchor=m.group(1)
    dis=open(EV+r'\DISASM_%s.txt'%entry,encoding='utf-8').read()
    disoff=set(int(x,16) for x in re.findall(r'\+0x([0-9A-Fa-f]{4})',dis))
    for tok in anchor.split(' / '):
        ma=re.match(r'\+0x([0-9A-Fa-f]{2,4})',tok.strip())
        if ma:
            v=int(ma.group(1),16)
            if v not in disoff:
                print('FAIL anchor offset not in EVIDENCE',entry,'+0x%x'%v); fail+=1
print('selfcheck fails =',fail)
# exclusion
excl=set()
for card in ['S09_KPROVED','S09_KPROVED2','S09_KPROVED3','S09_KPROVED4','S09_KPROVED5','S09_KPROVED6']:
    for l in open(BASE+'\\'+card+r'\coverage_delta.tsv',encoding='utf-8'):
        e=l.split('\t')[0].strip()
        if e and e!='entry': excl.add(e)
for card in ['SEMFIX_SLOTS2','SEMFIX_SLOTS3']:
    for l in open(BASE+'\\'+card+r'\coverage_delta.tsv',encoding='utf-8'):
        pp=l.split('\t')
        if len(pp)>=2 and pp[1].strip()=='S09': excl.add(pp[0].strip())
excl|={'00654320','0069DEB0'}
for p in data:
    if p[0] in excl: print('FAIL in exclusion',p[0]); fail+=1
print('final fails =',fail)
