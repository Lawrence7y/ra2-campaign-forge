import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
for a in (0x7fa4c8,0x7fa580,0x7fa698,0x80efa0):
    namestr=COL[G[a][0]]['name']
    nbc=P.dw(a+8); bca=P.dw(a+12)
    print('CHD 0x%x %s nbc=%d bca=0x%x attr=%d'%(a,namestr[:44],nbc,bca,P.dw(a+4)))
    print('  BCA dwords:',[hex(P.dw(bca+4*j)) for j in range(nbc)])
    for j in range(nbc):
        b=P.dw(bca+4*j)
        print('    BCD 0x%x td=%s ncb=%d mdisp=%d pdisp=%d vdisp=%d attr=%d'%(b,
            (P.cstr(P.dw(b)+8,60) or b'?').decode('latin1')[:40],P.dw(b+4),s32(P.dw(b+8)),s32(P.dw(b+12)),P.dw(b+16),P.dw(b+20)))
    print('  raw a..a+gap:')
    ln = (0x7fa580-a) if a==0x7fa4c8 else 160
    for o in range(0,ln,16):
        row=[P.dw(a+o+k) for k in range(0,16,4)]
        print('   +%3d  %s'%(o,' '.join('%08x'%r for r in row)))
