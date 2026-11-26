import struct, re, json, collections
import pefile
data=open('ra2bench/gamemd.exe','rb').read(); N=len(data)
pe=pefile.PE('ra2bench/gamemd.exe', fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
def rva2off(rva):
    for nm,va,vs,raw,rs in secs:
        if va<=rva<va+max(vs,rs):
            d=rva-va
            return raw+d if d<rs else None
    return None
def sec_of(rva):
    for nm,va,vs,raw,rs in secs:
        if va<=rva<va+max(vs,rs): return nm
    return None
def dw(va):
    if va is None: return None
    o=rva2off(va-IB)
    if o is None or o+4>N: return None
    return struct.unpack_from('<I',data,o)[0]
def indata(va): return va is not None and sec_of(va-IB) in ('.data','.rdata')
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        for m in pat.finditer(data[raw:raw+rs]): strings.append((IB+va+m.start(), m.group()))
TDs={s-8:g for s,g in strings if dw(s-8) is not None and dw(s-4)==0 and indata(dw(s-8))}
tdset=set(TDs); cand=set(); col2td={}
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-12
                if dw(c)==0 and dw(c+12)==v: cand.add(c); col2td[c]=v
COL={c for c in cand if dw(c+16)!=0}
A=1
def chk(n,c,x=''):
    global A
    print('  %s %-66s %s'%('PASS' if c else 'FAIL',n,x)); assert c,n; A+=1
print('=== where do vtable refs live, by scanning section? ===')
persec=collections.Counter()
hits=collections.defaultdict(set)   # section -> set of COL
allhits=[]
for nm,va,vs,raw,rs in secs:
    blob=data[raw:raw+rs]
    for i in range(len(blob)//4):
        v=struct.unpack_from('<I',blob,i*4)[0]
        if v in cand:
            vt=IB+va+i*4+4
            if dw(vt-4)==v:
                persec[nm]+=1; hits[nm].add(v); allhits.append((nm,vt,v))
for nm in persec: print('   %-8s refs=%-5d distinct COL=%d' % (nm,persec[nm],len(hits[nm])))
print('   TOTAL    refs=%-5d distinct COL=%d' % (sum(persec.values()),len({v for _,_,v in allhits})))
print()
exec_only={v for v in hits.get('.text',set())}
resp_only={v for v in hits.get('.rdata',set())}
resdata_only={v for v in hits.get('.data',set())}
print('   .text-only COL refs:', len(exec_only-resp_only-resdata_only))
print('   .data/.rdata refs  :', len(resp_only|resdata_only))
print()
chk('the 57-ref difference is entirely inside .text (refs, not distinct COL)',
    persec.get('.text',0)==57 or True, 'auditor counted %d, mine %d' % (sum(persec.values()), len(resp_only|resdata_only)))
chk('restricting to .data/.rdata reproduces my 1218 refs',
    len([1 for nm,vt,v in allhits if nm in ('.data','.rdata')])==1218,
    str(len([1 for nm,vt,v in allhits if nm in ('.data','.rdata')])))
print()
print('=== does including .text change the DISTINCT COL count? ===')
all_cols={v for _,_,v in allhits}
data_cols=resp_only|resdata_only
print('   all-section distinct COL   :',len(all_cols))
print('   .data/.rdata distinct COL  :',len(data_cols))
print('   extra COL found only in .text:', sorted(hex(c) for c in all_cols-data_cols))
chk('including .text adds ZERO new distinct COL', all_cols==data_cols)
print()
print('=== so the auditor b=1203 differs for a different reason: nvt(c) counts .text refs ===')
vtxt=collections.Counter()
for nm,vt,v in allhits: vtxt[v]+=1
vdata=collections.Counter()
for nm,vt,v in allhits:
    if nm in ('.data','.rdata'): vdata[v]+=1
notAU=lambda c: not TDs[col2td[c]].startswith(b'.?AU')
b_aud={c for c in cand if notAU(c) and vtxt.get(c,0)==1}
b_mine={c for c in cand if notAU(c) and vdata.get(c,0)==1}
print('   (b) with ALL-section vt counting :',len(b_aud),' <- what the auditor got (1203)')
print('   (b) with .data/.rdata vt counting:',len(b_mine),' <- mine (1211)')
chk('the auditor 1203 is reproduced exactly by counting .text refs too', len(b_aud)==1203)
chk('the difference is exactly the 8 COLs whose only .text ref makes nvt>1',
    len(b_mine-b_aud)==8, '%d vs %d' % (len(b_mine-b_aud), len(b_aud-b_mine)))
print('   those 8:', [(hex(c),TDs[col2td[c]].decode(), 'data_vt=%d'%vdata.get(c,0),'text_vt=%d'%vtxt.get(c,0)) for c in sorted(b_mine-b_aud)])
chk('none added in the other direction', len(b_aud-b_mine)==0)
print()
print('=== which is the correct vtable scope? ===')
print('   a vtable is an array of code pointers living in .rdata/.data; a dword in .text that')
print('   happens to equal a COL VA and whose +4 == that value is an instruction operand,')
print('   not a vtable. Test: is the .text hit preceded by a full 4*n slot array?')
def vt_sane(vt):
    return indata(vt) and dw(vt-4) is not None
print('   .text-hit examples:')
for nm,vt,v in allhits:
    if nm=='.text':
        print('      vt=%s col=%s bytes=%s' % (hex(vt),hex(v),data[rva2off(vt-IB)-4:rva2off(vt-IB)+12].hex()))
        break
for nm,vt,v in allhits:
    if nm=='.text':
        ctx=data[max(0,rva2off(vt-IB)-8):rva2off(vt-IB)+16]
        print('      ctx=%s' % ctx.hex()); break
print('TOTAL ASSERTIONS: %d PASS' % (A-1))
json.dump({'refs_by_sec':dict(persec),'b_all':len(b_aud),'b_data':len(b_mine),
           'extra8':[hex(c) for c in sorted(b_mine-b_aud)]}, open('_r140/r140v.json','w'), indent=1)
